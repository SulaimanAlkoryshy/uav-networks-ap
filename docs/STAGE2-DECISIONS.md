# STAGE 2 — Class balancing: two opinions + results

Code: `src/stage2_balance.py`. Results: `data/processed/stage2_results.csv`,
`stage2_recall_per_class.csv`. Judged by **test macro-F1** and per-class recall.

## Two opinions
- **Report (FR-4, eq. 4):** Random Undersampling **then** Borderline-SMOTE. Claims about **+0.18**
  macro-F1 vs no balancing, ~+1 pt vs plain SMOTE.
- **Independent:** resampling must be fit on train only (inside the pipeline) [S1]. Random forests
  are often fairly robust to imbalance; **cost-sensitive learning** (`class_weight`) is a simpler
  alternative with no synthetic rows [S3][S4]. Do not over-SMOTE tiny classes: SMOTE from 32
  Reconnaissance rows makes points that are only blends of those 32. Measure, don't assume.

## Setup
- AP imbalance: Brute-Force 172,509 vs Reconnaissance 40 (≈ 4,300 : 1).
- `under_smote`: undersample every class above **30,000** down to 30,000; Borderline-SMOTE every
  class below **5,000** up to 5,000 (k = 5). Full balance would be ~1.9M rows of mostly synthetic data.
- Compared: `none`, `under_smote`, `class_weight="balanced_subsample"`. RF, 100 trees, seed 42.

## Results (test macro-F1)
| path | none | under_smote | class_weight |
|---|---:|---:|---:|
| report | 0.9586 | **0.9691** | 0.9595 |
| search | **0.8860** | 0.8853 | 0.8834 |

Per-class recall that moved (search path):
| class | none | under_smote | class_weight |
|---|---:|---:|---:|
| DDoS | 0.433 | **0.505** | 0.496 |
| MITM | 0.717 | **0.757** | 0.724 |
| Replay | 0.710 | **0.755** | 0.715 |
| De-authentication | **0.960** | 0.928 | 0.914 |
| Evil Twin | **0.866** | 0.851 | 0.864 |

## Reading
1. **The report's +0.18 does not reproduce.** All three strategies are within 0.01 on each path.
2. `under_smote` **moves recall toward the weak classes** (DDoS +0.07, MITM +0.04, Replay +0.05)
   and pays for it on De-authentication — macro-F1 stays flat because the gains and losses cancel.
3. On the report path it helps more (+0.01), mainly through DDoS (0.63 → 0.90 recall).

## Decision
- Keep **`under_smote`** for Stages 3–6: it is the report's method, it lifts the weak attack
  classes' recall, and it makes training much smaller (≈ 210k rows instead of 505k → faster).
- Honest note: on the search path it is a **tie** with no balancing; it is not why the results are good.
- Rejected `class_weight`: never better than the other two here.

## Sources
- [S1] Arp et al., USENIX Security 2022.
- [S3] Han, Wang, Mao, *Borderline-SMOTE: A New Over-Sampling Method in Imbalanced Data Sets Learning*, ICIC 2005.
- [S4] Chawla et al., *SMOTE: Synthetic Minority Over-sampling Technique*, JAIR 2002.
