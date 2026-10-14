# UAV Networks — Access Point scenario (Case 2)

A software-only, classical-ML Intrusion Detection System (IDS) for UAV networks, on the
**UAV-NIDD** dataset, **Access Point scenario (UAV-to-AP, Case 2)**.

It follows the same 6-stage plan and the same two-path method as the GSC project
([OS-78/uav-networks](https://github.com/OS-78/uav-networks)), adapted to AP's data.

## Results at a glance (macro-F1)
| | report path (keeps time/IP) | search path (honest) |
|---|---:|---:|
| Binary, 5-fold CV | 1.000 | 1.000 ⚠ capture artifact |
| Multi-class, 5-fold CV (RF) | 0.974 | **0.885** |
| Best model, test (XGBoost) | 0.980 | **0.898** |

Full story: [`docs/FINDINGS-AP.md`](docs/FINDINGS-AP.md) · open **`results.html`** for charts.

## Two things that make AP different
1. **Time leakage**: the capture timestamp alone gives macro-F1 0.92, because every attack was
   captured in its own session. The search path removes time/order + IP columns.
2. **Normal was captured differently** (`frame.encap_type = 23` only on Normal), so binary
   Normal-vs-Attack is trivially 1.000. That is a dataset artifact, not real skill.

Details: [`docs/DATASET-AP.md`](docs/DATASET-AP.md).

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: . .venv/bin/activate
pip install -r requirements.txt
```

## The dataset
Download `UAV-NDD CSV.zip` from **Zenodo record 15125851** (https://zenodo.org/records/15125851),
unzip it, and put `Access Point Case2 Label.xlsx` in `data/raw/`. Then once:
```bash
python src/convert_ap_xlsx_to_csv.py
```

## Run
```bash
python src/run_all.py
```
or a single stage, e.g. `python src/stage4_multiclass.py`.

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

## Docs
- [`docs/DATASET-AP.md`](docs/DATASET-AP.md): the AP data, its problems, and the leakage.
- [`docs/FINDINGS-AP.md`](docs/FINDINGS-AP.md): every stage's numbers and decisions.
- [`docs/EXPLAINED-AR.md`](docs/EXPLAINED-AR.md): شرح المشروع بالعربي (with English ML terms).
- [`docs/ML-METHODOLOGY.md`](docs/ML-METHODOLOGY.md): the rules for honest results (from the GSC project).
- [`docs/REPORT-NOTES.md`](docs/REPORT-NOTES.md): the GP report distilled (from the GSC project).
