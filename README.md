# Easy CSV Cleaner

A small cross-platform Python app that replaces embedded line breaks in CSV fields with spaces.

## Install the macOS app

Download a macOS ZIP from this repository's [GitHub Releases](https://github.com/lewb-ox/easy-csv-cleaner/releases):

- **arm64** for Apple Silicon Macs (M-series chips).
- **x86_64** for Intel Macs.

Unzip it, drag **Easy CSV Cleaner.app** into **Applications**, and double-click it.
Python and Tkinter are bundled; recipients do not need to install them.
Use **Browse...** to select a CSV or ZIP, then **Clean CSV** to choose where to save the result.

These builds are ad-hoc signed, **not Apple notarized**. If macOS blocks the first
launch, attempt to open the app, then go to **System Settings → Privacy & Security →
Open Anyway** if you trust the download. See [Apple's guidance for opening apps](https://support.apple.com/en-gb/102445).
For distribution without this security exception, an Apple Developer ID certificate
and Apple notarization are required; neither is configured in this repository.

Each ZIP has a matching `.sha256` file. To verify a download, put both files in the
same folder and run `shasum -a 256 -c EasyCsvCleaner-1.0.0-macOS-arm64.zip.sha256`,
substituting the actual filename.

## Requirements

For running from source or building (not required for the packaged app):

- Python 3.10 or newer
- Tkinter (included with most Python installations; on some Linux distributions it is installed separately)

## Desktop app

Launch the app:

```bash
python app.py
```

On Windows, use `py app.py` if `python` is not the Python command on your system. On macOS, use `python3 app.py` if needed.

## Build a macOS app locally

Build on a Mac using Python 3.13 from [python.org](https://www.python.org/downloads/macos/),
including Tcl/Tk. From the project folder:

```bash
python3 -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements-build.txt
bash build_macos.sh
```

This creates `dist/Easy CSV Cleaner.app`, plus a versioned ZIP and SHA-256 checksum
ready to attach to a GitHub release. `VERSION` sets the default app version.
For example, an Apple Silicon build of version 1.0.0 produces
`dist/EasyCsvCleaner-1.0.0-macOS-arm64.zip`. Build on Intel for an Intel download;
these are separate native apps. Windows cannot build the macOS bundle.

The build checks the ad-hoc code signature and runs the **packaged executable**
with `--smoke-test`, exercising Tk startup and cleaning a CSV and a CSV inside a ZIP.
It needs a macOS graphical session. Complete the manual checklist below as well.
The bundle uses PyInstaller's default icon.

Advanced overrides: `APP_PYTHON` selects another virtual environment's absolute
Python path, `APP_VERSION=1.2.3` overrides the version, and `APP_ARCH` explicitly
selects `arm64` or `x86_64` when the Python installation supports that architecture.

## Build and distribute through GitHub

The **Build macOS apps** workflow builds on macOS 14 (Apple Silicon) and macOS 15
(Intel). These are build environments; older macOS versions still need testing
before claiming support. It also builds relevant pull requests. To test without
creating a release, run it from **Actions → Build macOS apps → Run workflow** and
download the two architecture artifacts.

To prepare a release, commit and push the packaging files, update `VERSION` for
the release, then tag the corresponding commit (for example):

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow uses the tag as the bundle version and creates a **draft GitHub
release** containing both ZIPs and checksums after both builds pass. Download and
test both apps, complete the checklist, then publish the draft from **Releases**.
Tags must use `vMAJOR.MINOR.PATCH` with numeric components. GitHub Actions must be
enabled; the release job uses the repository's automatic `GITHUB_TOKEN` with
`contents: write`, so no personal access token is needed.

## Build a Windows executable

On Windows, use Python 3.10 or newer. From PowerShell in the project folder, install the build dependency and create the executable:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
./build_windows.bat
```

Use a standard python.org installation with Tcl/Tk included. The build script prefers `.build-venv\Scripts\python.exe` when it exists, then falls back to `.venv\Scripts\python.exe`.

The double-clickable, windowed executable is created at `dist\EasyCsvCleaner.exe`. It bundles Python and Tkinter, so the recipient does not need to install Python. Build it on Windows; a Windows build does not create a macOS app. The executable is unsigned, so Windows SmartScreen may show a warning when it is first downloaded or launched.

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
- On Windows, check behavior when the chosen destination is open in another app. On macOS, test the downloaded, unzipped app from Applications on both Apple Silicon and Intel, including the first-launch security prompt, native dialogs and quitting during cleaning.

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
