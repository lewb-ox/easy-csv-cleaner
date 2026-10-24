# Easy CSV Cleaner

Remove unwanted line breaks inside CSV cells with a simple desktop app for Windows and macOS. Choose a CSV file, or a CSV inside a ZIP archive, and save a cleaned copy.

For example, a cell containing:

```text
First line
Second line
```

becomes `First line Second line`. The CSV rows and columns stay in place.

## Download

**[Download the latest release](https://github.com/lewb-ox/easy-csv-cleaner/releases/latest)**

Under **Assets**, choose the download for your computer:

| Your computer | Download to choose |
| --- | --- |
| Windows | The Windows `.exe` file, or the ZIP containing it |
| Mac with Apple Silicon (M-series chip) | The macOS ZIP with `arm64` in its name |
| Mac with an Intel processor | The macOS ZIP with `x86_64` in its name |

On a Mac, open **Apple menu → About This Mac** to check your chip or processor. Use the release notes for version-specific compatibility information.

You do not need to install Python or any other dependencies. The **Source code** downloads are for developers; choose an app download from the list above.

## Install and open

### Windows

1. Download the Windows app. If it comes in a ZIP, extract it first.
2. Open `EasyCsvCleaner.exe`.

The Windows app is unsigned, so Windows may show a security warning. Check that you downloaded it from this project's release page before proceeding. On a managed work computer, contact your IT support team if the app is blocked.

### macOS

1. Download and unzip the file for your Mac.
2. Drag **Easy CSV Cleaner.app** into **Applications**.
3. Open it from **Applications**.

The macOS app is not Apple notarized. If macOS says the developer cannot be verified or Apple cannot check the app, first try opening it, then go to **System Settings → Privacy & Security → Open Anyway** if you trust the download. See [Apple's instructions for opening downloaded apps](https://support.apple.com/en-gb/102445). On a managed work Mac, your IT support team may need to help.

## Clean a file

1. Open **Easy CSV Cleaner** and click **Browse...**.
2. Select a `.csv` file or a `.zip` archive containing CSV files.
3. Click **Clean CSV**. For a ZIP, select the CSV you want to clean and click **Select**. Each run cleans one CSV.
4. Choose where to save the cleaned file. The suggested name adds `-clean`, for example `data-clean.csv`.
5. Wait for the completion message. It shows how many rows were processed, how many contained line breaks, and where the cleaned file was saved.

An animated progress bar shows that cleaning is running; it does not show a percentage complete. Click **Cancel** to stop the operation.

## What happens to your files?

- **Your original stays unchanged.** The app prevents you from saving over the input CSV or ZIP.
- **You choose the output.** If the destination already exists, the app asks before replacing it. Cancelling or encountering a cleaning error leaves an existing destination unchanged.
- **Files stay on your computer.** Cleaning runs locally, without uploading your data or requiring an account or internet connection.
- **Only embedded line breaks are replaced.** Line breaks within cells become spaces. CSV formatting, including quoting and line endings, may also be normalized when the file is saved.

For ZIP input, the result is a separate CSV file. The original ZIP is unchanged, and you do not need to extract it yourself. Temporary working files are removed when cleaning finishes, is cancelled, or reports an error.

## Supported files

Use comma-separated CSV files saved as **UTF-8**, with or without a UTF-8 BOM. Quoted cells can contain commas and line breaks. Other delimiters, such as semicolons or tabs, and other text encodings are not selectable.

ZIP archives can contain CSV files in subfolders. Password-protected CSV entries are not supported. The app also limits ZIP processing to 10,000 archive entries, a selected CSV of up to 1 GiB when expanded, and a compression ratio of up to 200:1.

## Troubleshooting

| Problem | What to try |
| --- | --- |
| The file is not valid UTF-8 | Re-export or save it as UTF-8 CSV in the app that created it. |
| The app reports malformed CSV | Check the indicated line in the original file, especially quotation marks, or export a fresh CSV. |
| A field exceeds the supported size | Shorten or split the very large cell, then try again. |
| No CSV is found in a ZIP | Check that the archive contains files ending in `.csv`. |
| A ZIP is encrypted or exceeds a processing limit | Extract the CSV yourself and select it directly. |
| The output cannot be saved | Choose a writable folder and check that the destination file is not open in another app. |

If a problem continues, [report an issue](https://github.com/lewb-ox/easy-csv-cleaner/issues). Include your operating system, app version, what you were doing, and the error message. Remove personal or confidential data from any examples you share.

## Updates

Download a newer version from the [releases page](https://github.com/lewb-ox/easy-csv-cleaner/releases) and replace your existing app. Release notes describe the changes in each version.

## For developers

For running from source, command-line use, building apps, and preparing releases, see [Development and releases](DEVELOPMENT.md).

## License

Use and modify this script freely for your own projects.
