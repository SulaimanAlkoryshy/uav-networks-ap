# Plan — UAV Networks, Access Point scenario (Case 2)

**How we work.** One stage at a time, each ending with a clear "done" check. Each stage records
the report's suggestion **and** an independent opinion, tests them on the real data, and writes
the evidence to `STAGEn-DECISIONS.md` and `BUILD-LOG.md`. Report suggestions are suggestions,
not mandates.

---

## Schedule at a glance

| Stage | Focus | Status |
|------|-------|--------|
| — | Download UAV-NIDD, convert the AP `.xlsx` to CSV | ✅ done |
| 1 | Preprocessing, shortcut check & feature selection | ✅ done |
| 2 | Class balancing | ✅ done |
| 3 | Binary (Normal vs Attack) + capture-artifact check | ✅ done |
| 4 | Multi-class (10 attacks + Normal) | ✅ done |
| 5 | Model benchmarking | ✅ done |
| 6 | Interpretability, CPU cost, reproducibility | ✅ done |
| — | Show the work: `results.html`, `student_review` (AR), `REPORT` | ✅ done |
| 7 | Time-aware split (stronger leakage test) | ⬜ open (optional) |

---

## Prerequisite — get the data ✅
- [x] `UAV-NDD CSV.zip` (302 MB) from Zenodo record 15125851 → `data/raw/`.
- [x] `Access Point Case2 Label.xlsx` → `data/processed/ap_raw.csv` (631,356 × 51) with
  `src/convert_ap_xlsx_to_csv.py`.

## Stage 1 — Preprocessing & feature selection ✅
- [x] **1.1** Load; inspect real columns, dtypes, label values.
- [x] **1.2** Fix the label (`Normal` header → `Class`; `Ewil Twin` → `Evil Twin`).
- [x] **1.3** Make numeric (hex parsed, other text → -1; no rows dropped — measured why).
- [x] **1.4** Drop constant columns.
- [x] **1.5** Shortcut check (one column at a time) → time/order + IP columns found.
- [x] **1.6** Split 80/20 stratified, seed 42.
- [x] **1.7** PCC |corr| > 0.85 (train only).
- [x] **1.8** Top-25: report = ANOVA, search = RF importance.

*Report suggestions:* PCC 0.85; ANOVA top-25. → kept PCC; ANOVA picked the leaky columns.

## Stage 2 — Class balancing ✅
- [x] **2.1** Baseline macro-F1 without balancing.
- [x] **2.2–2.3** under + Borderline-SMOTE, and class_weight, compared.

*Report suggestion:* +0.18 macro-F1 from balancing. → did not reproduce (≤ 0.01).

## Stage 3 — Binary ✅
- [x] **3.1** RF, 5-fold CV + held-out test + trivial baseline.
- [x] **3.2** Leakage sanity check → capture-setup artifact found (`frame.encap_type`).

## Stage 4 — Multi-class ✅
- [x] **4.1** All 11 classes, per-class P/R/F1.
- [x] **4.2** Minority decision: keep Reconnaissance (40 rows), flag as unreliable.

## Stage 5 — Benchmarking ✅
- [x] **5.2** RF vs XGBoost vs DT vs LR vs Linear SVM.
- [x] **5.3** Target macro-F1 ≥ 0.90: met only with leakage; honest best 0.898 (XGBoost).
- [~] **5.1** Cross-scenario — out of scope (AP only).

## Stage 6 — Reproducibility, interpretability, cost ✅
- [x] **6.1** `run_all.py` reproduces every number; same-seed re-train → identical predictions.
- [x] **6.2** Impurity + permutation importance.
- [x] **6.3** CPU training / inference time, model size.

## Stage 7 — Time-aware split (optional, open)
- [ ] Within each class, train on the earlier 80% of packets (by capture time), test on the last 20%.
- [ ] Compare with the random split. A big drop = the random split was flattering the score.

---

## Deliberately not in this project
- **Deep learning** — CPU-only, lightweight requirement (NFR-2); out of GP1 scope.
- **Other scenarios (UAV, GCS)** — this project covers the Access Point scenario only.
- **Live / on-drone deployment** — software-only; edge cost is checked, not built.
