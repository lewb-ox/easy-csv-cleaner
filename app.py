import csv
import queue
import tempfile
import threading
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk

from clean_csv import CleaningCancelled, CsvInputError, clean_csv, clean_csv_stream, clean_csv_to_path, same_path

MAX_ARCHIVE_ENTRIES = 10_000
MAX_CSV_MEMBER_BYTES = 1 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


class DestinationDeclined(Exception):
    """Raised when the user declines replacing an existing output."""


class CsvCleanerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Easy CSV Cleaner")
        self.root.minsize(560, 300)
        self.input_path = tk.StringVar()
        self.cancel_event = threading.Event()
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.start_after_id: str | None = None
        self.poll_after_id: str | None = None
        self.worker: threading.Thread | None = None
        self.running = False
        self.closing = False

        main = ttk.Frame(root, padding=24)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Choose a CSV file or ZIP archive", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(
            main,
            text="Select a CSV directly, or a ZIP containing one or more CSV files. Choose where to save the cleaned CSV.",
            wraplength=500,
        ).pack(anchor="w", pady=(8, 18))

        file_row = ttk.Frame(main)
        file_row.pack(fill="x")
        self.path_entry = ttk.Entry(file_row, textvariable=self.input_path)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(file_row, text="Browse...", command=self.choose_file)
        self.browse_button.pack(side="left", padx=(8, 0))

        button_row = ttk.Frame(main)
        button_row.pack(fill="x", pady=(18, 0))
        self.clean_button = ttk.Button(button_row, text="Clean CSV", command=self.run_cleaner)
        self.clean_button.pack(side="right")
        self.cancel_button = ttk.Button(button_row, text="Cancel", command=self.cancel_cleaning, state="disabled")
        self.cancel_button.pack(side="right", padx=(0, 8))

        self.progress_value = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(main, mode="determinate", maximum=100, variable=self.progress_value, length=500)
        self.progress.pack(fill="x", pady=(16, 0))
        self.status = ttk.Label(main, text="", wraplength=500)
        self.status.pack(anchor="w", pady=(10, 0))
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def choose_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select a CSV file or ZIP archive",
            filetypes=[("CSV and ZIP files", "*.csv *.zip"), ("CSV files", "*.csv"), ("ZIP archives", "*.zip"), ("All files", "*.*")],
        )
        if selected:
            self.input_path.set(selected)
            self.progress.stop()
            self.progress_value.set(0)
            self.status.configure(text="")

    def run_cleaner(self) -> None:
        path_text = self.input_path.get().strip()
        if not path_text:
            messagebox.showinfo("Choose a file", "Select a CSV file or ZIP archive first.", parent=self.root)
            return
        selected_path = Path(path_text).expanduser()
        if not selected_path.is_file():
            messagebox.showerror("File not found", f"Could not find: {selected_path}", parent=self.root)
            return

        try:
            job = self.prepare_job(selected_path)
        except DestinationDeclined:
            return
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            messagebox.showerror("Could not open file", str(error), parent=self.root)
            return
        if job is None:
            return

        self.cancel_event.clear()
        self.running = True
        self.clean_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status.configure(text="Starting cleaning...")
        # Keep the busy animation visible briefly, even for very small CSV files.
        self.start_after_id = self.root.after(300, self.start_job, job)

    def prepare_job(self, source: Path) -> tuple[str, Path, object] | None:
        if source.suffix.lower() != ".zip":
            destination = self.choose_output(f"{source.stem}-clean{source.suffix}")
            if destination is None:
                return None
            self.validate_destination(source, destination)
            return ("csv", destination, source)

        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise ValueError(
                    f"This ZIP contains more than {MAX_ARCHIVE_ENTRIES:,} entries and is too large to inspect safely."
                )
            members = [
                item for item in entries
                if not item.is_dir() and PurePosixPath(item.filename).suffix.lower() == ".csv"
            ]
        if not members:
            messagebox.showinfo("No CSV found", "This ZIP archive does not contain any CSV files.", parent=self.root)
            return None
        selected_member = self.choose_member(members)
        if selected_member is None:
            return None
        self.validate_zip_member(selected_member)
        member_path = PurePosixPath(selected_member.filename)
        destination = self.choose_output(f"{member_path.stem}-clean{member_path.suffix}")
        if destination is None:
            return None
        self.validate_destination(source, destination)
        return ("zip", destination, (source, selected_member))

    def validate_destination(self, source: Path, destination: Path) -> None:
        if same_path(source, destination):
            raise ValueError("Choose a different output path so the original file is preserved.")
        if destination.exists() and not messagebox.askyesno(
            "Replace existing file?",
            f"The file already exists:\n{destination}\n\nReplace it after cleaning completes?",
            parent=self.root,
        ):
            raise DestinationDeclined

    @staticmethod
    def validate_zip_member(member: zipfile.ZipInfo) -> None:
        if member.flag_bits & 0x1:
            raise ValueError(f"The selected CSV is encrypted and cannot be opened: {member.filename}")
        if member.file_size > MAX_CSV_MEMBER_BYTES:
            raise ValueError(
                f"The selected CSV expands to {member.file_size / (1024 ** 3):.2f} GiB. "
                f"The current limit is {MAX_CSV_MEMBER_BYTES / (1024 ** 3):.0f} GiB."
            )
        ratio = member.file_size / max(member.compress_size, 1)
        if ratio > MAX_COMPRESSION_RATIO:
            raise ValueError(
                f"The selected CSV has a compression ratio of {ratio:.0f}:1, above the "
                f"{MAX_COMPRESSION_RATIO}:1 safety limit."
            )

    def choose_output(self, suggested_name: str) -> Path | None:
        destination = filedialog.asksaveasfilename(
            title="Save cleaned CSV",
            initialfile=suggested_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        return Path(destination) if destination else None

    def start_job(self, job: tuple[str, Path, object]) -> None:
        self.start_after_id = None
        if self.closing or self.cancel_event.is_set():
            self.result_queue.put(("cancelled", None))
            self.poll_after_id = self.root.after(0, self.poll_result)
            return
        self.progress.configure(mode="indeterminate")
        self.progress_value.set(0)
        self.progress.start(12)
        self.status.configure(text="Cleaning... Click Cancel to stop.")
        self.worker = threading.Thread(target=self.run_job, args=(job,), daemon=True)
        try:
            self.worker.start()
        except Exception as error:
            self.result_queue.put(("error", f"Could not start the cleaning worker: {error}"))
        self.poll_after_id = self.root.after(100, self.poll_result)

    def run_job(self, job: tuple[str, Path, object]) -> None:
        kind, destination, source_info = job
        result: tuple[str, object] = ("error", "The cleaning worker stopped unexpectedly.")
        try:
            if kind == "csv":
                output, total, fixed = clean_csv(source_info, destination, self.cancel_event)
            else:
                archive_path, member = source_info
                total, fixed = self.clean_zip_to_path(archive_path, member, destination)
                output = destination
            result = ("success", (output, total, fixed))
        except CleaningCancelled:
            result = ("cancelled", None)
        except Exception as error:
            if isinstance(error, CsvInputError):
                result = ("error", str(error))
            else:
                # Preserve the traceback for diagnosing unexpected failures.
                import traceback
                detail = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                result = ("error", f"{error}\n\nDetails for troubleshooting:\n{detail}")
        finally:
            self.result_queue.put(result)

    def clean_zip_to_path(self, archive_path: Path, member: zipfile.ZipInfo, destination: Path) -> tuple[int, int]:
        temporary_input: Path | None = None
        try:
            with zipfile.ZipFile(archive_path) as archive:
                current_member = next(
                    (item for item in archive.infolist() if item.header_offset == member.header_offset),
                    None,
                )
                if (
                    current_member is None
                    or current_member.filename != member.filename
                    or current_member.CRC != member.CRC
                    or current_member.file_size != member.file_size
                    or current_member.compress_size != member.compress_size
                ):
                    raise ValueError("The ZIP archive changed after you selected the CSV. Please select it again.")
                self.validate_zip_member(current_member)
                with archive.open(current_member, "r") as binary_source:
                    with tempfile.NamedTemporaryFile(
                        mode="w+b", dir=destination.parent, prefix=f".{destination.name}.", suffix=".input.tmp", delete=False
                    ) as staged_source:
                        temporary_input = Path(staged_source.name)
                        bytes_read = 0
                        while True:
                            if self.cancel_event.is_set():
                                raise CleaningCancelled
                            chunk = binary_source.read(1024 * 1024)
                            if not chunk:
                                break
                            bytes_read += len(chunk)
                            if bytes_read > MAX_CSV_MEMBER_BYTES:
                                raise ValueError("The CSV expanded beyond the 1 GiB safety limit while reading the ZIP.")
                            actual_ratio = bytes_read / max(current_member.compress_size, 1)
                            if actual_ratio > MAX_COMPRESSION_RATIO:
                                raise ValueError(
                                    f"The CSV exceeded the {MAX_COMPRESSION_RATIO}:1 compression ratio safety limit while reading the ZIP."
                                )
                            staged_source.write(chunk)
            try:
                return clean_csv_to_path(temporary_input, destination, self.cancel_event)
            finally:
                temporary_input.unlink(missing_ok=True)
        except BaseException:
            if temporary_input is not None:
                temporary_input.unlink(missing_ok=True)
            raise

    def cancel_cleaning(self) -> None:
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status.configure(text="Stopping after the current row...")

    def poll_result(self) -> None:
        if self.closing:
            self.finish_close_when_ready()
            return
        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.poll_after_id = self.root.after(100, self.poll_result)
            return

        self.poll_after_id = None
        self.progress.stop()
        self.running = False
        self.cancel_button.configure(state="disabled")
        self.clean_button.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.path_entry.configure(state="normal")
        if kind == "success":
            self.progress.configure(mode="determinate")
            self.progress_value.set(100)
            output, total, fixed = payload
            self.status.configure(text=f"Done. {total} rows processed; {fixed} rows fixed.\nSaved: {output}")
            messagebox.showinfo(
                "Cleaning complete",
                f"Rows processed: {total}\nRows with line breaks fixed: {fixed}\n\nSaved to:\n{output}",
                parent=self.root,
            )
        elif kind == "cancelled":
            self.progress.configure(mode="determinate")
            self.progress_value.set(0)
            self.status.configure(text="Cleaning cancelled. Partial output removed.")
        else:
            self.progress.configure(mode="determinate")
            self.progress_value.set(0)
            self.status.configure(text="Cleaning stopped because an error occurred.")
            messagebox.showerror("Could not clean file", payload, parent=self.root)

    def choose_member(self, members: list[zipfile.ZipInfo]) -> zipfile.ZipInfo | None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose CSV in archive")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="Choose a CSV to clean. The expanded size and compression ratio are shown:").pack(
            padx=16, pady=(16, 8), anchor="w"
        )
        values = [
            f"#{index + 1}  {member.filename}  |  {member.file_size / (1024 ** 2):.1f} MiB  |  "
            f"{member.file_size / max(member.compress_size, 1):.1f}:1"
            for index, member in enumerate(members)
        ]
        choice = tk.StringVar(value=values[0])
        ttk.Combobox(dialog, textvariable=choice, values=values, state="readonly", width=60).pack(padx=16, fill="x")
        result: list[zipfile.ZipInfo | None] = [None]

        def accept() -> None:
            result[0] = members[values.index(choice.get())]
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.pack(padx=16, pady=16, anchor="e")
        ttk.Button(buttons, text="Cancel", command=cancel).pack(side="right")
        ttk.Button(buttons, text="Select", command=accept).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        self.root.wait_window(dialog)
        return result[0]

    def close(self) -> None:
        if self.closing:
            return
        if self.running:
            self.closing = True
            self.cancel_event.set()
            if self.start_after_id is not None:
                self.root.after_cancel(self.start_after_id)
                self.start_after_id = None
                self.result_queue.put(("cancelled", None))
            self.status.configure(text="Stopping the current job before closing...")
            self.finish_close_when_ready()
        else:
            self.root.destroy()

    def finish_close_when_ready(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            self.root.after(50, self.finish_close_when_ready)
            return
        if self.poll_after_id is not None:
            try:
                self.root.after_cancel(self.poll_after_id)
            except tk.TclError:
                pass
            self.poll_after_id = None
        self.progress.stop()
        self.running = False
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main() -> None:
    root = tk.Tk()
    CsvCleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
