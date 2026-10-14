# STAGE 6 — Interpretability, CPU cost, reproducibility: two opinions + results

Code: `src/stage6_analysis.py`, `src/run_all.py`. Results: `data/processed/stage6_*.csv`.

## Two opinions
- **Report (NFR-4, NFR-2, NFR-5):** tree feature-importance report; light enough for CPU / edge;
  fixed seed reproduces every number.
- **Independent:** impurity importance is biased toward features with many distinct values
  [S5] — exactly the clock-like columns — so also use **permutation importance** (drop in
  macro-F1 when a feature is shuffled, on held-out data) [S12]. Run it with `n_jobs=1`: parallel
  workers each copy the model and can exhaust RAM. For reproducibility, don't just fix the seed —
  **re-train and compare the predictions**.

## 6.2 Feature importance (permutation, top 5)
| rank | report path | search path |
|---:|---|---|
| 1 | radiotap.rxflags (radio clock) | frame.encap_type |
| 2 | frame.time_relative (timestamp) | wlan_radio.data_rate |
| 3 | frame.number (packet index) | udp.dstport |
| 4 | wlan.seq | data.len |
| 5 | wlan.fc.moredata | wlan.seq |

- Report path: the top 3 are **all time/order columns** → the clearest proof of the leakage.
- Search path: packet-structure fields. `frame.encap_type` at #1 is the capture-setup artifact
  from Stage 3 (it separates Normal) — so even the honest model partly reads the capture setup.

## 6.3 CPU cost (RF + under_smote)
| path | train | inference (126,272 packets) | throughput | model size |
|---|---:|---:|---:|---:|
| report | 2.5 s | 0.17 s | ~720k packets/s | 134 MB |
| search | 2.4 s | 0.19 s | ~680k packets/s | 227 MB |

About 1.5 µs per packet on a laptop CPU → light enough for an edge box. The model file is the
heavy part; fewer / shallower trees would shrink it if needed.

## 6.1 Reproducibility
- Same seed, re-trained → **identical predictions** on both paths.
- `python src/run_all.py` re-ran every stage from the raw CSV; every number in the docs matched
  the earlier runs exactly.

## Decision
NFR-2, NFR-4, NFR-5 are met. The importance results are used as evidence in `FINDINGS-AP.md` and
`results.html`.

## Sources
- [S5] Strobl et al., BMC Bioinformatics 2007.
- [S12] Breiman 2001 (permutation importance); scikit-learn docs, *Permutation feature importance*.
