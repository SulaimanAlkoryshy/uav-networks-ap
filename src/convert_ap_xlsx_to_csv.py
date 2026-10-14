"""
One-time helper: turn the Access Point (Case 2) Excel file into a plain CSV.

Why this exists:
    The AP scenario file is an Excel (.xlsx) file of about 130 MB. Reading Excel is slow, and
    loading it all at once uses a lot of memory. So we convert it ONCE to a CSV here, reading it
    row by row (streaming) so memory stays low. After this, all our real work just uses the fast
    CSV with pandas.read_csv.

Run it once:
    python src/convert_ap_xlsx_to_csv.py
"""

import csv
from pathlib import Path

from python_calamine import CalamineWorkbook

# where the Excel file is, and where we want the CSV
XLSX_PATH = Path("data/raw/Access Point Case2 Label.xlsx")
CSV_PATH = Path("data/processed/ap_raw.csv")


def main():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)  # make data/processed/ if missing

    print(f"Opening {XLSX_PATH} ...")
    workbook = CalamineWorkbook.from_path(XLSX_PATH)
    print(f"  sheets: {workbook.sheet_names}")
    sheet = workbook.get_sheet_by_index(0)

    rows_written = 0
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # iter_rows() gives us one row at a time, so we never hold the whole file in memory
        for row in sheet.iter_rows():
            writer.writerow(row)
            rows_written += 1
            if rows_written % 100000 == 0:
                print(f"  ... {rows_written} rows")

    print(f"Done. Wrote {rows_written} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
