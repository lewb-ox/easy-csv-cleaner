import csv
import io
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk

from clean_csv import clean_csv, clean_csv_stream


class CsvCleanerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Easy CSV Cleaner")
        self.root.minsize(560, 250)
        self.input_path = tk.StringVar()

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
        ttk.Entry(file_row, textvariable=self.input_path).pack(side="left", fill="x", expand=True)
        ttk.Button(file_row, text="Browse...", command=self.choose_file).pack(side="left", padx=(8, 0))

        self.clean_button = ttk.Button(main, text="Clean CSV", command=self.run_cleaner)
        self.clean_button.pack(anchor="e", pady=(18, 0))
        self.status = ttk.Label(main, text="", wraplength=500)
        self.status.pack(anchor="w", pady=(14, 0))

    def choose_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select a CSV file or ZIP archive",
            filetypes=[("CSV and ZIP files", "*.csv *.zip"), ("CSV files", "*.csv"), ("ZIP archives", "*.zip"), ("All files", "*.*")],
        )
        if selected:
            self.input_path.set(selected)
            self.status.configure(text="")

    def run_cleaner(self) -> None:
        selected_path = Path(self.input_path.get().strip()).expanduser()
        if not self.input_path.get().strip():
            messagebox.showinfo("Choose a file", "Select a CSV file or ZIP archive first.", parent=self.root)
            return
        if not selected_path.is_file():
            messagebox.showerror("File not found", f"Could not find: {selected_path}", parent=self.root)
            return

        self.clean_button.configure(state="disabled")
        try:
            if selected_path.suffix.lower() == ".zip":
                self.clean_zip(selected_path)
            else:
                self.clean_single_csv(selected_path)
        finally:
            self.clean_button.configure(state="normal")

    def choose_output(self, suggested_name: str) -> Path | None:
        destination = filedialog.asksaveasfilename(
            title="Save cleaned CSV",
            initialfile=suggested_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        return Path(destination) if destination else None

    def clean_single_csv(self, source: Path) -> None:
        destination = self.choose_output(f"{source.stem}-clean{source.suffix}")
        if destination is None:
            return
        try:
            output, total, fixed = clean_csv(source, destination)
        except (OSError, csv.Error, UnicodeError) as error:
            messagebox.showerror("Could not clean file", str(error), parent=self.root)
            return
        self.show_result(output, total, fixed)

    def clean_zip(self, archive_path: Path) -> None:
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = [
                    item for item in archive.infolist()
                    if not item.is_dir() and PurePosixPath(item.filename).suffix.lower() == ".csv"
                ]
                if not members:
                    messagebox.showinfo("No CSV found", "This ZIP archive does not contain any CSV files.", parent=self.root)
                    return

                selected_member = self.choose_member(members)
                if selected_member is None:
                    return

                member_path = PurePosixPath(selected_member.filename)
                suggested_name = f"{member_path.stem}-clean{member_path.suffix}"
                destination = self.choose_output(suggested_name)
                if destination is None:
                    return

                with archive.open(selected_member, "r") as source, destination.open(
                    "w", newline="", encoding="utf-8"
                ) as output:
                    with io.TextIOWrapper(source, encoding="utf-8-sig", newline="") as text_source:
                        total, fixed = clean_csv_stream(text_source, output)
        except (OSError, zipfile.BadZipFile, csv.Error, UnicodeError) as error:
            messagebox.showerror("Could not clean archive", str(error), parent=self.root)
            return
        self.show_result(destination, total, fixed)

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
        combo = ttk.Combobox(dialog, textvariable=choice, values=values, state="readonly", width=60)
        combo.pack(padx=16, fill="x")
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

    def show_result(self, output: Path, total: int, fixed: int) -> None:
        self.status.configure(text=f"Done. {total} rows processed; {fixed} rows fixed.\nSaved: {output}")
        messagebox.showinfo(
            "Cleaning complete",
            f"Rows processed: {total}\nRows with line breaks fixed: {fixed}\n\nSaved to:\n{output}",
            parent=self.root,
        )


def main() -> None:
    root = tk.Tk()
    CsvCleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
