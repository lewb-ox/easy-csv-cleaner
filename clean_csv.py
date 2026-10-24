import argparse
import csv
import io
from pathlib import Path
from threading import Event
from typing import TextIO


class CleaningCancelled(Exception):
    """Raised when a user requests cancellation during CSV processing."""


def clean_csv_stream(infile: TextIO, outfile: TextIO, cancel_event: Event | None = None) -> tuple[int, int]:
    """Clean CSV data between text streams and return row counts."""
    rows_fixed = 0
    total_rows = 0

    reader = csv.reader(infile)
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        if cancel_event and cancel_event.is_set():
            raise CleaningCancelled
        total_rows += 1
        new_row = []
        row_changed = False
        for field in row:
            if "\n" in field or "\r" in field:
                field = field.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
                row_changed = True
            new_row.append(field)
        if row_changed:
            rows_fixed += 1
        writer.writerow(new_row)

    return total_rows, rows_fixed


def clean_csv(
    input_path: str | Path,
    output_path: str | Path | None = None,
    cancel_event: Event | None = None,
) -> tuple[Path, int, int]:
    """Clean a CSV file, optionally writing to a chosen destination."""
    input_file = Path(input_path).expanduser()
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = Path(output_path).expanduser() if output_path else input_file.with_name(
        f"{input_file.stem}-clean{input_file.suffix}"
    )

    with input_file.open("r", newline="", encoding="utf-8-sig") as infile, \
         output_file.open("w", newline="", encoding="utf-8") as outfile:
        try:
            total_rows, rows_fixed = clean_csv_stream(infile, outfile, cancel_event)
        except CleaningCancelled:
            output_file.unlink(missing_ok=True)
            raise

    return output_file, total_rows, rows_fixed


def clean_csv_text(data: bytes, outfile: TextIO) -> tuple[int, int]:
    """Clean UTF-8 CSV bytes from a ZIP member into a text output stream."""
    text = data.decode("utf-8-sig")
    return clean_csv_stream(io.StringIO(text, newline=""), outfile)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove embedded line breaks from CSV fields.")
    parser.add_argument("input_csv", type=Path, help="CSV file to clean")
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    args = parser.parse_args()

    try:
        output_file, total_rows, rows_fixed = clean_csv(args.input_csv, args.output)
    except (OSError, csv.Error) as error:
        parser.error(str(error))

    print(f"Total rows processed: {total_rows}")
    print(f"Rows with embedded linebreaks fixed: {rows_fixed}")
    print(f"Clean file written to: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
