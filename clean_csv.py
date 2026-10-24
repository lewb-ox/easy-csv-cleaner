import csv
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print(f"Usage: python {Path(sys.argv[0]).name} <input.csv>")
    sys.exit(1)

input_file = Path(sys.argv[1])
if not input_file.is_file():
    print(f"Input file not found: {input_file}")
    sys.exit(1)

output_file = input_file.with_name(f"{input_file.stem}-clean{input_file.suffix}")

rows_fixed = 0
total_rows = 0

with open(input_file, "r", newline="", encoding="utf-8-sig") as infile, \
     open(output_file, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

    for row in reader:
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

print(f"Total rows processed: {total_rows}")
print(f"Rows with embedded linebreaks fixed: {rows_fixed}")
print(f"Clean file written to: {output_file}")
