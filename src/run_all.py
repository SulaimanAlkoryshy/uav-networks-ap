"""
Stage 6.1 — one command reproduces every AP number (NFR-5).

Runs the whole pipeline in order, with the fixed seed baked into each script:
    stage1 -> stage2 -> stage3 -> stage4 -> stage5 -> stage6 -> make_report
    -> make_student_review -> make_weekly_report
(PDFs: powershell -File src/docx_to_pdf.ps1 student_review.docx REPORT.docx)

Run:
    python src/run_all.py
(First make data/processed/ap_raw.csv once:  python src/convert_ap_xlsx_to_csv.py)

Note: this re-runs everything and takes a while. For day-to-day work, run the single stage
script you care about instead.
"""

import subprocess
import sys

STEPS = [
    ("Stage 1  preprocess (2 paths) + shortcut check", "src/stage1_preprocess.py"),
    ("Stage 2  balancing comparison", "src/stage2_balance.py"),
    ("Stage 3  binary model + capture check", "src/stage3_binary.py"),
    ("Stage 4  multi-class model", "src/stage4_multiclass.py"),
    ("Stage 5  model benchmark", "src/stage5_benchmark.py"),
    ("Stage 6  importance + cost + reproducibility", "src/stage6_analysis.py"),
    ("Report   build results.html", "src/make_report.py"),
    ("Docs     build student_review.docx (Arabic)", "src/make_student_review.py"),
    ("Docs     build REPORT.docx", "src/make_weekly_report.py"),
]


def main():
    for title, script in STEPS:
        print(f"\n{'='*70}\n>>> {title}  ({script})\n{'='*70}", flush=True)
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"!! {script} failed (exit {result.returncode}) — stopping.")
            sys.exit(result.returncode)
    print("\nAll stages finished.")


if __name__ == "__main__":
    main()
