# UAV Networks — Access Point scenario (Case 2)

A software-only, classical-ML Intrusion Detection System (IDS) for UAV networks, on the
**UAV-NIDD** dataset, **Access Point scenario (UAV-to-AP, Case 2)**. Graduation project.

Built in six stages (preprocess → balance → binary → multi-class → benchmark → analysis), with two
paths through every stage:
- **report**: exactly what the GP report says (all columns kept, ANOVA top-25).
- **search**: the honest version (drops the time/order and IP columns, RF-importance top-25).

## Results at a glance (macro-F1)
| | report path (keeps time/IP) | search path (honest) |
|---|---:|---:|
| Binary, 5-fold CV | 1.000 | 1.000 ⚠ capture artifact |
| Multi-class, 5-fold CV (RF) | 0.974 | **0.885** |
| Best model, test (XGBoost) | 0.980 | **0.898** |

Open **`results.html`** for the charts and confusion matrices. The Arabic explanation is in
**`student_review.pdf`**, and the project report is in **`REPORT.pdf`**.

## Two things that make AP special
1. **Time leakage**: the capture timestamp alone gives macro-F1 0.92, because every attack was
   captured in its own session. The search path removes the time/order and IP columns.
2. **Normal was captured differently** (`frame.encap_type = 23` only on Normal), so binary
   Normal-vs-Attack is trivially 1.000. That comes from the dataset, not from real detection skill.

Details: [`docs/DATASET-AP.md`](docs/DATASET-AP.md).

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: . .venv/bin/activate
pip install -r requirements.txt
```
Team workflow (Git, branches, PRs) in Arabic: [`TEAM-GUIDE.md`](TEAM-GUIDE.md).

## The dataset
Download `UAV-NDD CSV.zip` from **Zenodo record 15125851** (https://zenodo.org/records/15125851),
unzip it, and put `Access Point Case2 Label.xlsx` in `data/raw/`. Then run this once:
```bash
python src/convert_ap_xlsx_to_csv.py
```

## Run
```bash
python src/run_all.py
```
You can also run a single stage, e.g. `python src/stage4_multiclass.py`.

| file | what it does |
|---|---|
| `src/convert_ap_xlsx_to_csv.py` | Excel → `data/processed/ap_raw.csv` (once) |
| `src/stage1_preprocess.py` | clean, shortcut check, split, PCC, top-25 (two paths) |
| `src/stage2_balance.py` | none vs under+Borderline-SMOTE vs class_weight |
| `src/stage3_binary.py` | Normal vs Attack + capture-artifact check |
| `src/stage4_multiclass.py` | 11 classes, per-class F1 |
| `src/stage5_benchmark.py` | RF / XGBoost / DT / LR / Linear SVM |
| `src/stage6_analysis.py` | importance, CPU cost, reproducibility |
| `src/make_report.py` | builds `results.html` from the saved numbers |
| `src/make_student_review.py` | builds `student_review.docx` (Arabic, RTL) |
| `src/make_weekly_report.py` | builds `REPORT.docx` |
| `src/docx_to_pdf.ps1` | .docx → .pdf with Word (Windows) |

## Docs
- [`docs/STATE.md`](docs/STATE.md): where the work stopped (read this first).
- [`docs/PLAN.md`](docs/PLAN.md): the stages and what each must achieve.
- [`docs/BUILD-LOG.md`](docs/BUILD-LOG.md): what was decided and why (append-only).
- [`docs/STAGE1-DECISIONS.md`](docs/STAGE1-DECISIONS.md) … [`STAGE6`](docs/STAGE6-DECISIONS.md): for each step, the report's opinion vs an independent one, with sources.
- [`docs/DATASET-AP.md`](docs/DATASET-AP.md): the AP data, its problems, and the leakage.
- [`docs/FINDINGS-AP.md`](docs/FINDINGS-AP.md): all results on one page.
- [`docs/ML-METHODOLOGY.md`](docs/ML-METHODOLOGY.md): the rules that keep the results honest.
- [`docs/REPORT-NOTES.md`](docs/REPORT-NOTES.md): the GP report distilled for coding.
- [`docs/EXPLAINED-AR.md`](docs/EXPLAINED-AR.md): short Arabic explanation.
