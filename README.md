# Easy CSV Cleaner

A simple Python script that removes embedded line breaks from CSV fields and writes a cleaned CSV file.

## What It Does

- Reads data from `input.csv`
- Replaces line breaks inside CSV fields with spaces
- Writes the cleaned data to `output_clean.csv`
- Prints a summary of the rows processed and fixed

## Requirements

- Python 3
- No external packages are required

## Usage

1. Place the CSV file you want to clean in the same folder as `clean_csv.py`.
2. Name the file `input.csv`.
3. Run the script:

```bash
python clean_csv.py
```

The cleaned file will be saved as `output_clean.csv`.

## Customizing File Names

To use different file names, edit these lines near the top of `clean_csv.py`:

```python
input_file = "input.csv"
output_file = "output_clean.csv"
```

## Example Output

```text
Total rows processed: 100
Rows with embedded linebreaks fixed: 4
Clean file written to: output_clean.csv
```

## License

Use and modify this script freely for your own projects.
