# STAGE 3 — Binary (Normal vs Attack): two opinions + results

Code: `src/stage3_binary.py`. Results: `data/processed/stage3_binary_results.csv`,
`stage3_capture_check.csv`.

## Two opinions
- **Report (FR-1):** Random Forest as the primary model; binary first.
- **Independent:** use **5-fold stratified CV** as the main number plus the held-out test, compare
  with a trivial baseline, and report **MCC** and balanced accuracy next to macro-F1 [S6]. Any
  near-perfect score on a security dataset is a red flag until explained [S1].

## Setup
- Everything that is not `Normal` → `Attack`. In AP, Normal is **not rare**: 103,633 train rows
  (~20%), so the task is about 4 : 1.
- RF + `under_smote` (both sides undersampled to 30,000; SMOTE has nothing to do).

## Results
| path | CV macro-F1 | Normal recall | Normal precision | MCC | balanced acc | test macro-F1 |
|---|---:|---:|---:|---:|---:|---:|
| report | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.000 |
| search | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.000 |
| always "Attack" | — | — | — | — | — | 0.443 (accuracy 0.795) |

## Red flag → investigation (step 3.2)
A perfect score on the **honest** path too means the leak is not the time/IP columns. Two checks
(`capture_check()` in the same file):
1. **One column at a time** (depth-3 tree): `frame.encap_type` alone = **1.000**. Value **23** is on
   **every** Normal packet and on **no** attack packet (attacks: 0, 1, 20, …).
2. **Drop the strongest columns and re-train:**

| columns dropped | which | test macro-F1 |
|---:|---|---:|
| 0 | — | 1.0000 |
| 1 | frame.encap_type | 0.9999 |
| 4 | + arp, eapol.keydes.replay_counter, wlan_radio.data_rate | 0.9998 |
| 6 | + frame.len, udp.dstport | 0.9299 |

**Meaning:** the Normal traffic was recorded with a **different capture setup** (different
encapsulation, so different fields are filled). The difference runs through many columns, so it
cannot be removed by dropping one. The model is mostly recognising "which capture is this".

## Decision
- Report the binary result, but **do not claim it as real normal-vs-attack detection** on AP.
- RF confirmed as a sound primary model (the multi-class task in Stage 4 is the meaningful one).
- No columns were removed from the pipeline for this: dropping 6 columns still leaves 0.93, and
  removing more would also remove real packet information. Instead it is documented everywhere
  (README, DATASET-AP, results.html).

## Open concern
- A fair binary test needs Normal traffic captured with the **same setup** as the attacks. That is
  a dataset limit, not something code can fix.

## Sources
- [S1] Arp et al., USENIX Security 2022.
- [S6] Chicco & Jurman, *The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation*, BMC Genomics 2020.
