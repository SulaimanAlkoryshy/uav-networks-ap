# STAGE 5 — Model benchmarking: two opinions + results

Code: `src/stage5_benchmark.py`. Results: `data/processed/stage5_benchmark.csv`.

## Two opinions
- **Report (FR-5):** RF primary; benchmark against XGBoost, Decision Tree, SVM, Logistic Regression.
  Target NFR-1: macro-F1 ≥ 0.90. FR-7: also run across all three scenarios.
- **Independent:** on tabular data, gradient-boosted trees and random forests usually beat linear
  models and are hard to beat at all [S10]. Full-kernel SVM does not scale to 500k rows → use a
  linear SVM. Judge every model on the **same** split, samplers and features, honestly (search path).

## Setup
Same `under_smote` for every model; `StandardScaler` only for LR and Linear SVM. Labels encoded
as numbers (XGBoost needs it). XGBoost: 200 trees, depth 6, `hist`. Test macro-F1.

## Results (test macro-F1)
| model | report | search |
|---|---:|---:|
| XGBoost | 0.9795 | **0.8975** |
| RandomForest | 0.9691 | 0.8853 |
| DecisionTree | 0.9747 | 0.8723 |
| LogisticRegression | 0.9092 | 0.6828 |
| LinearSVM | 0.9059 | 0.6801 |

(LinearSVM prints a convergence warning on the search path; it is far behind either way.)

## Reading
1. **Tree models >> linear models** (≈ 0.88–0.90 vs ≈ 0.68 honest). The packet fields are codes
   and flags, which trees split naturally and linear models cannot.
2. On the honest path **XGBoost is best (0.898)**, RF 0.885, DT 0.872.
3. The **≥ 0.90 target** is met by every tree model on the report path — but through time leakage.
   Honestly it is **just missed** (0.898).

## Decision
- **Keep RF as the primary model** (the report's choice) for Stage 6 and the report: it is 0.012
  behind XGBoost, simpler to explain, and its importances are easy to read.
- Record **XGBoost as the best honest model** — the number to quote if the question is "best score".
- FR-7 (cross-scenario) is **out of scope** for this project: it covers the AP scenario only.

## Sources
- [S10] Grinsztajn, Oyallon, Varoquaux, *Why do tree-based models still outperform deep learning on typical tabular data?*, NeurIPS 2022 Datasets & Benchmarks.
- Breiman, *Random Forests*, Machine Learning 2001; Chen & Guestrin, *XGBoost*, KDD 2016.
