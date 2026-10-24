# Easy CSV Cleaner

A simple Python script that removes embedded line breaks from CSV fields and writes a cleaned CSV file.

## What It Does

- Reads a CSV file specified when you run the script
- Replaces line breaks inside CSV fields with spaces
- Writes the cleaned data beside the input file with `-clean` added before its extension
- Prints a summary of the rows processed and fixed

## Requirements

- Python 3
- No external packages are required

## Usage

Run the script with the CSV file path as an argument:

```bash
python clean_csv.py path/to/your-file.csv
```

The cleaned file is saved in the same folder with `-clean` added before the extension. For example, `data.csv` becomes `data-clean.csv`.

## Example Output

```text
Total rows processed: 100
Rows with embedded linebreaks fixed: 4
Clean file written to: path/to/your-file-clean.csv
```

## License

Use and modify this script freely for your own projects.
