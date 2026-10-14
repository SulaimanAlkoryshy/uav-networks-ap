# FINDINGS — AP (Case 2), stage by stage

All numbers below come from real runs (`python src/run_all.py`, SEED = 42). The raw tables are
in `data/processed/stage*.csv`; the visual version is `results.html`.

Two paths, as in the GSC project:
- **report** = the GP report as written (keep every column, ANOVA top-25).
- **search** = honest version (drop 4 time/order + 4 IP columns, RF-importance top-25).

---

## Stage 1 — Preprocessing & feature selection
- 631,356 rows → split 80/20 stratified → **train 505,084 / test 126,272**, all 11 classes in test.
- report: 49 features → PCC dropped 12 → 37 → ANOVA top-25.
- search: 41 features → PCC dropped 11 → 30 → tree top-25.
- 18 features chosen by both. **Only in report:** `frame.number`, `frame.time_relative`,
  `radiotap.rxflags`, `ip.dst`, `ip.proto`, `ip.src`, `ip.ttl` → ANOVA picked the leaky columns.
- Shortcut check: the timestamp column **alone** = macro-F1 **0.923** (see `DATASET-AP.md`).

## Stage 2 — Class balancing (test macro-F1)
| path | none | under_smote | class_weight |
|---|---:|---:|---:|
| report | 0.9586 | **0.9691** | 0.9595 |
| search | **0.8860** | 0.8853 | 0.8834 |

- The report's claimed **+0.18** from balancing does **not** reproduce (changes ≤ 0.01), same as GSC.
- Balancing helps DDoS recall (search 0.43 → 0.51) but costs a little elsewhere.
- **Choice:** keep `under_smote` (report's method, same as GSC project → comparable). Honest note:
  on the search path it is a tie with no balancing.

## Stage 3 — Binary (Normal vs Attack)
| path | CV macro-F1 | Normal recall | Normal precision | MCC | always-Attack baseline |
|---|---:|---:|---:|---:|---:|
| report | 1.000 | 1.00 | 1.00 | 1.00 | 0.443 |
| search | 1.000 | 1.00 | 1.00 | 1.00 | 0.443 |

**Red flag → investigated.** `frame.encap_type` alone separates Normal perfectly (value 23 on
every Normal packet, never on an attack). Dropping the top 1 / 4 / 6 single-column separators still
gives 0.9999 / 0.9998 / 0.930 (`stage3_capture_check.csv`). Normal was **captured with a different
setup**, so the binary task on AP is trivially easy for a reason that would not hold in the field.
→ The binary number is reported, but **not** claimed as real detection ability.

## Stage 4 — Multi-class (11 classes, 5-fold CV)
| path | macro-F1 | weighted-F1 |
|---|---:|---:|
| report | 0.9742 | 0.9751 |
| search | **0.8846** | 0.9492 |

Per-class F1 (search): solved (≥0.99): Brute-Force, DoS, Fake Landing, Normal, Scanning,
Reconnaissance*; good: De-authentication 0.92, Evil Twin 0.85; **weak: MITM 0.72, Replay 0.70,
DDoS 0.55**.
\*Reconnaissance = 1.000 on only **32** training rows — not reliable.
- report path reaches 1.000 on MITM / Replay / Evil Twin only because it keeps the timestamp.
- Interesting contrast with GSC: De-authentication is **easy here (0.92)** but ≈0 in GSC — makes
  sense, de-auth is an 802.11 management-frame attack, visible in packet fields, invisible in flows.

## Stage 5 — Model benchmark (test macro-F1)
| model | report | search |
|---|---:|---:|
| XGBoost | 0.9795 | **0.8975** |
| DecisionTree | 0.9747 | 0.8723 |
| RandomForest | 0.9691 | 0.8853 |
| LogisticRegression | 0.9092 | 0.6828 |
| LinearSVM | 0.9059 | 0.6801 |

- Tree models >> linear models (same as GSC).
- On the honest path **XGBoost is best (0.898)**, RF close (0.885). The **≥ 0.90 target is just
  missed honestly**; it is met by every tree model on the report path — but via time leakage.

## Stage 6 — Interpretability, cost, reproducibility
- **report** permutation importance top-3: `radiotap.rxflags`, `frame.time_relative`,
  `frame.number` → **all time/order columns** = leakage proof.
- **search** top-3: `frame.encap_type`, `wlan_radio.data_rate`, `udp.dstport` → packet
  structure; note `frame.encap_type` is the capture-setup artifact from Stage 3.
- Cost (RF, CPU): train ≈ 2.5 s, inference ≈ 0.0015 ms/packet (~650k packets/s). Model
  134 MB (report) / 227 MB (search).
- Re-train with the same seed → **identical predictions** on both paths.

---

## Honest conclusion (AP)
- The report-style pipeline gets ~0.97–0.98 macro-F1 on AP, but it leans on **timestamps**.
- With time/IP columns removed, the trustworthy multi-class result is **≈ 0.88–0.90**
  (XGBoost 0.898, RF 0.885). Weak classes: **DDoS, Replay, MITM**.
- The binary task is not a fair test on AP because Normal was captured differently.
- Next idea if wanted: a **time-based split** (train on earlier packets, test on later ones per
  class), which is the real test against session leakage.
