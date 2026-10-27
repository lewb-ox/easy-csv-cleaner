import argparse
import csv
import os
from pathlib import Path
import tempfile
from threading import Event
from typing import TextIO


class CleaningCancelled(Exception):
    """Raised when a user requests cancellation during CSV processing."""


class CsvInputError(ValueError):
    """Raised when CSV input cannot be decoded or parsed safely."""


def clean_csv_stream(
    infile: TextIO,
    outfile: TextIO,
    cancel_event: Event | None = None,
    *,
    only_fixed: bool = False,
) -> tuple[int, int]:
    """Clean CSV data, optionally exporting only changed rows, and return counts."""
    rows_fixed = 0
    total_rows = 0

    reader = csv.reader(infile, strict=True)
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        except UnicodeDecodeError as error:
            raise CsvInputError(
                f"The CSV is not valid UTF-8 near physical line {reader.line_num}. "
                "Save or export it as UTF-8, then try again."
            ) from error
        except csv.Error as error:
            if "field larger than field limit" in str(error).lower():
                limit = csv.field_size_limit()
                explanation = (
                    f"A field near physical line {reader.line_num} exceeds the supported "
                    f"field size of {limit:,} characters. Split or shorten that field and retry."
                )
            else:
                explanation = f"Malformed CSV near physical line {reader.line_num}: {error}"
            raise CsvInputError(explanation) from error

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
        if not only_fixed or row_changed:
            writer.writerow(new_row)

    return total_rows, rows_fixed


def clean_csv(
    input_path: str | Path,
    output_path: str | Path | None = None,
    cancel_event: Event | None = None,
    *,
    only_fixed: bool = False,
) -> tuple[Path, int, int]:
    """Clean a CSV file, optionally writing to a chosen destination."""
    input_file = Path(input_path).expanduser()
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = Path(output_path).expanduser() if output_path else input_file.with_name(
        f"{input_file.stem}-clean{input_file.suffix}"
    )

    if same_path(input_file, output_file):
        raise ValueError("The output file cannot be the same as the input file.")

    total_rows, rows_fixed = clean_csv_to_path(
        input_file, output_file, cancel_event, only_fixed=only_fixed
    )

    return output_file, total_rows, rows_fixed


def same_path(first: Path, second: Path) -> bool:
    """Compare paths safely, including aliases and paths that do not exist yet."""
    try:
        return os.path.samefile(first, second)
    except (FileNotFoundError, OSError):
        return first.resolve() == second.resolve()


def clean_csv_to_path(
    input_file: Path,
    output_file: Path,
    cancel_event: Event | None = None,
    *,
    only_fixed: bool = False,
) -> tuple[int, int]:
    """Clean into a temporary sibling, then atomically replace the destination."""
    if not output_file.parent.is_dir():
        raise FileNotFoundError(f"Output folder does not exist: {output_file.parent}")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=output_file.parent,
            prefix=f".{output_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as outfile:
            temporary_path = Path(outfile.name)
            with input_file.open("r", newline="", encoding="utf-8-sig") as infile:
                total_rows, rows_fixed = clean_csv_stream(
                    infile, outfile, cancel_event, only_fixed=only_fixed
                )

        if cancel_event and cancel_event.is_set():
            raise CleaningCancelled
        os.replace(temporary_path, output_file)
        temporary_path = None
        return total_rows, rows_fixed
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove embedded line breaks from CSV fields.")
    parser.add_argument("input_csv", type=Path, help="CSV file to clean")
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    parser.add_argument(
        "--only-fixed",
        action="store_true",
        help="Export only rows whose embedded line breaks were fixed; unchanged headers are omitted",
    )
    args = parser.parse_args()

    try:
        output_file, total_rows, rows_fixed = clean_csv(
            args.input_csv, args.output, only_fixed=args.only_fixed
        )
    except (OSError, csv.Error, CsvInputError) as error:
        parser.error(str(error))

    print(f"Total rows processed: {total_rows}")
    print(f"Rows with embedded linebreaks fixed: {rows_fixed}")
    if args.only_fixed:
        print(f"Rows exported: {rows_fixed}")
    print(f"Clean file written to: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
