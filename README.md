# Easy CSV Cleaner

A small cross-platform Python app that replaces embedded line breaks in CSV fields with spaces.

## Requirements

- Python 3
- Tkinter (included with most Python installations; on some Linux distributions it is installed separately)

## Desktop app

Launch the app:

```bash
python app.py
```

On Windows, use `py app.py` if `python` is not the Python command on your system. On macOS, use `python3 app.py` if needed.

Choose a CSV file or ZIP archive with **Browse...**, then click **Clean CSV**. For a ZIP, the app searches its folders for CSV files. If there is more than one, choose which one to clean. The app then prompts for a destination, suggesting the source name with `-clean` added before the extension (for example, `data.csv` becomes `data-clean.csv`).

While the file is being cleaned, an animated progress bar is shown. Use **Cancel** to stop after the current CSV row; any partial output is removed. If an error occurs, the animation stops and the app displays the error.

The selected CSV is read directly from the ZIP; the archive is not extracted to disk. Only the cleaned CSV is saved to the chosen destination.

## Command line

Clean a CSV file with:

```bash
python clean_csv.py path/to/your-file.csv
```

Pass `-o path/to/output.csv` to choose the output path. Without `-o`, the output is saved beside the input with `-clean` before its extension.

## Example output

```text
Total rows processed: 100
Rows with embedded linebreaks fixed: 4
Clean file written to: path/to/your-file-clean.csv
```

## License

Use and modify this script freely for your own projects.
