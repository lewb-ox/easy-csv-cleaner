# Easy CSV Cleaner

A small cross-platform Python app that replaces embedded line breaks in CSV fields with spaces.

## Requirements

- Python 3.10 or newer
- Tkinter (included with most Python installations; on some Linux distributions it is installed separately)

## Desktop app

Launch the app:

```bash
python app.py
```

On Windows, use `py app.py` if `python` is not the Python command on your system. On macOS, use `python3 app.py` if needed.

Choose a CSV file or ZIP archive with **Browse...**, then click **Clean CSV**. For a ZIP, the app searches its folders for CSV files. If there is more than one, choose which one to clean. The app then prompts for a destination, suggesting the source name with `-clean` added before the extension (for example, `data.csv` becomes `data-clean.csv`).

The cleaner expects UTF-8 text (with or without a UTF-8 BOM) and comma-separated CSV using standard double-quote handling. It parses strictly: malformed quoting stops the operation with a physical line number when available. If decoding fails, save or export the file as UTF-8 and try again. Other encodings and delimiters are not currently selectable.

The output is re-serialized as CSV, so quoting and line endings may be normalized even for rows that did not need line-break cleanup. A blank file reports 0 rows; blank lines are counted as rows; a row is counted as fixed if at least one field had an embedded line break replaced. Fields larger than Python's configured CSV field-size limit are rejected with an explanation. Errors and cancellation do not replace an existing destination.

While the file is being cleaned, an animated progress bar is shown. Use **Cancel** to stop after the current CSV row; any partial output is removed. If an error occurs, the animation stops and the app displays the error.

The selected CSV is read from the ZIP without extracting its folder structure. A temporary staging file is used during cleaning and removed afterward. The chooser shows each CSV's expanded size and compression ratio. To limit memory, disk, and decompression abuse, the app currently rejects archives with more than 10,000 entries, CSV members larger than 1 GiB, and members with compression ratios above 200:1. It also checks actual decompressed bytes while reading, verifies the selected archive member has not changed, and reports corrupt or unsupported ZIP data as an error.

The app prevents choosing the input CSV or ZIP itself as the output. If the destination already exists, it asks before replacing it. It writes to a temporary file first, so cancellation or a cleaning error leaves an existing destination untouched; the finished output replaces it only after cleaning succeeds.

## Windows and macOS verification checklist

Before distributing a release, run the desktop app on each platform and check:

- Select CSV and ZIP files through the native file picker, including paths and filenames with spaces and non-ASCII characters.
- Confirm the save dialog suggests the expected `-clean.csv` filename and cancellation leaves the app idle.
- Try replacing an existing destination: decline and confirm its contents remain unchanged; accept and confirm it is replaced only after success.
- Cancel a large CSV and ZIP job, then confirm the old destination remains intact and temporary files are removed.
- Try a corrupt ZIP, malformed CSV, and non-UTF-8 CSV; confirm the app shows an actionable error and remains usable.
- On Windows, check behavior when the chosen destination is open in another app. On macOS, check the app launches with the intended Python installation and Tkinter is available.

The code has been reviewed for platform-neutral paths and same-folder atomic replacement. The checklist still needs to be run on actual Windows and macOS desktop environments before claiming both platforms have been UI-verified.

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
