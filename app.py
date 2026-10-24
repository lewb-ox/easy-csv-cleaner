import csv
import io
import queue
import threading
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk

from clean_csv import CleaningCancelled, clean_csv, clean_csv_stream


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

        self.progress = ttk.Progressbar(main, mode="indeterminate", length=500)
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
        except (OSError, zipfile.BadZipFile) as error:
            messagebox.showerror("Could not open file", str(error), parent=self.root)
            return
        if job is None:
            return

        self.cancel_event.clear()
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
            return ("csv", destination, source)

        with zipfile.ZipFile(source) as archive:
            members = [
                item for item in archive.infolist()
                if not item.is_dir() and PurePosixPath(item.filename).suffix.lower() == ".csv"
            ]
        if not members:
            messagebox.showinfo("No CSV found", "This ZIP archive does not contain any CSV files.", parent=self.root)
            return None
        selected_member = self.choose_member(members)
        if selected_member is None:
            return None
        member_path = PurePosixPath(selected_member.filename)
        destination = self.choose_output(f"{member_path.stem}-clean{member_path.suffix}")
        if destination is None:
            return None
        return ("zip", destination, (source, selected_member))

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
        self.progress.start(12)
        self.status.configure(text="Cleaning... Click Cancel to stop.")
        self.worker = threading.Thread(target=self.run_job, args=(job,), daemon=True)
        self.worker.start()
        self.poll_after_id = self.root.after(100, self.poll_result)

    def run_job(self, job: tuple[str, Path, object]) -> None:
        kind, destination, source_info = job
        try:
            if kind == "csv":
                output, total, fixed = clean_csv(source_info, destination, self.cancel_event)
            else:
                archive_path, member = source_info
                with zipfile.ZipFile(archive_path) as archive, archive.open(member, "r") as binary_source:
                    with io.TextIOWrapper(binary_source, encoding="utf-8-sig", newline="") as source, destination.open(
                        "w", newline="", encoding="utf-8"
                    ) as output_file:
                        try:
                            total, fixed = clean_csv_stream(source, output_file, self.cancel_event)
                        except CleaningCancelled:
                            output_file.close()
                            destination.unlink(missing_ok=True)
                            raise
                output = destination
            self.result_queue.put(("success", (output, total, fixed)))
        except CleaningCancelled:
            self.result_queue.put(("cancelled", None))
        except (OSError, zipfile.BadZipFile, csv.Error, UnicodeError, RuntimeError) as error:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
            self.result_queue.put(("error", str(error)))

    def cancel_cleaning(self) -> None:
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status.configure(text="Stopping after the current row...")

    def poll_result(self) -> None:
        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.poll_after_id = self.root.after(100, self.poll_result)
            return

        self.poll_after_id = None
        self.progress.stop()
        self.cancel_button.configure(state="disabled")
        self.clean_button.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.path_entry.configure(state="normal")
        if kind == "success":
            output, total, fixed = payload
            self.status.configure(text=f"Done. {total} rows processed; {fixed} rows fixed.\nSaved: {output}")
            messagebox.showinfo(
                "Cleaning complete",
                f"Rows processed: {total}\nRows with line breaks fixed: {fixed}\n\nSaved to:\n{output}",
                parent=self.root,
            )
        elif kind == "cancelled":
            self.status.configure(text="Cleaning cancelled. Partial output removed.")
        else:
            self.status.configure(text="Cleaning stopped because an error occurred.")
            messagebox.showerror("Could not clean file", payload, parent=self.root)

    def choose_member(self, members: list[zipfile.ZipInfo]) -> zipfile.ZipInfo | None:
        if len(members) == 1:
            return members[0]
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose CSV in archive")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="This archive contains multiple CSV files. Choose one to clean:").pack(
            padx=16, pady=(16, 8), anchor="w"
        )
        values = [member.filename for member in members]
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
        if self.cancel_event.is_set() or self.clean_button.instate(["disabled"]):
            self.cancel_event.set()
            self.root.after(50, self.close_when_finished)
        else:
            self.root.destroy()

    def close_when_finished(self) -> None:
        if self.worker.is_alive():
            self.root.after(50, self.close_when_finished)
        else:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    CsvCleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
