# STAGE 4 — Multi-class (11 classes): two opinions + results

Code: `src/stage4_multiclass.py`. Results: `data/processed/stage4_multiclass_results.csv`,
`stage4_per_class_f1.csv`.

## Two opinions
- **Report (FR-2, step 4.2):** extend RF to all attack classes; macro-F1 + per-class; decide what
  to do with extreme-minority classes (very small classes may not suit SMOTE).
- **Independent:** keep every class (dropping a weak class hides the failure); report per-class
  precision / recall / F1 from **pooled 5-fold CV** so even small classes are tested several times;
  flag classes whose score rests on very few real samples.

## Setup
RF (100 trees) + `under_smote`, samplers refit inside each fold. Seed 42.

## Results (5-fold CV)
| path | macro-F1 | weighted-F1 |
|---|---:|---:|
| report (keeps time/IP) | 0.9742 | 0.9751 |
| search (honest) | **0.8846** | 0.9492 |

| class | train rows | report F1 | search F1 | search recall | search precision |
|---|---:|---:|---:|---:|---:|
| Brute-Force | 138,007 | 1.000 | 0.999 | 0.998 | 1.000 |
| DoS | 18,890 | 1.000 | 1.000 | 1.000 | 1.000 |
| Normal | 103,633 | 1.000 | 1.000 | 1.000 | 1.000 |
| Scanning | 56,255 | 1.000 | 1.000 | 1.000 | 1.000 |
| Fake Landing | 19,667 | 1.000 | 0.994 | 0.999 | 0.988 |
| Reconnaissance | **32** | 1.000 | 1.000 | 1.000 | 1.000 |
| De-authentication | 124,451 | 0.945 | 0.923 | 0.937 | 0.909 |
| Evil Twin | 8,027 | 1.000 | 0.850 | 0.834 | 0.867 |
| MITM | 4,013 | 1.000 | **0.718** | 0.765 | 0.677 |
| Replay | 6,820 | 1.000 | **0.697** | 0.745 | 0.655 |
| DDoS | 25,289 | 0.771 | **0.549** | 0.494 | 0.618 |

## Reading
1. The **0.09 gap** (0.974 vs 0.885) is what the time/IP columns buy. The report path is perfect on
   Evil Twin, MITM and Replay only because it can read the clock.
2. Honest weak spots: **DDoS** (confused with DoS — they differ in how many sources, which a
   single packet barely shows), **Replay** and **MITM** (replayed / relayed packets look like
   normal-looking packets by design).
3. **De-authentication is good (0.92)**: it is an 802.11 management-frame attack, visible in
   packet fields.
4. **Reconnaissance = 1.000 from 32 rows** is not reliable. SMOTE lifted 32 real rows to 5,000
   blended ones; the score shows those 40 packets are distinctive, not that the class is solved.

## Decision (step 4.2 — minority classes)
- **Keep all 11 classes.** Reconnaissance stays, with a reliability warning in every report.
- Keep the SMOTE floor at 5,000 (same rule for every class), noted as heavy extrapolation for
  Reconnaissance.

## Open concerns
- DDoS vs DoS: flow-style counts (packets per source over a window) would likely help, but the AP
  file is per-packet. A windowed feature is a possible later experiment.
