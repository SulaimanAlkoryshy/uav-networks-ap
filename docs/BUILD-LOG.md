# BUILD-LOG — what was decided and why (append-only)

Every entry: date · what · why · the measured evidence. Newest at the bottom.

---

## 2026-10-14 · Data in
- Downloaded `UAV-NDD CSV.zip` (302,353,406 bytes) from Zenodo 15125851. Contains the 3 scenario
  files; this project uses only `Access Point Case2 Label.xlsx` (130 MB).
- Converted once, streaming, to `data/processed/ap_raw.csv`: **631,356 rows × 51 columns**.

## 2026-10-14 · Stage 1 — first look at the AP data
- Label header is `Normal` (lost header) → renamed `Class`. `Ewil Twin` → `Evil Twin`. 11 classes.
- Class counts: Brute-Force 172,509 · De-authentication 155,564 · Normal 129,541 · Scanning 70,319 ·
  DDoS 31,612 · Fake Landing 24,584 · DoS 23,612 · Evil Twin 10,034 · Replay 8,525 · MITM 5,016 ·
  Reconnaissance 40. Imbalance ≈ 4,300 : 1.
- Headers are shifted vs contents (e.g. `frame.time_relative` = epoch time, `radiotap.datarate` =
  channel frequency, `ip.proto` / `ip.ttl` hold IP addresses).
- **Decision: text → -1, keep all rows.** Evidence: 72,030 rows hold text, and they are 100% of
  Evil Twin, MITM, Reconnaissance, Replay (67% of DoS). 102,414 cells set to -1.
- Constant column dropped: `wlan.fc.protected`.

## 2026-10-14 · Stage 1 — shortcut check
- One-column decision tree, 150k sample: `frame.time_relative` **0.923** macro-F1 alone;
  `radiotap.channel.flags.cck` 0.614; `frame.len` 0.422; `radiotap.rxflags` 0.344.
- **Decision:** PATH search drops `frame.number`, `frame.time_relative`,
  `radiotap.channel.flags.cck`, `radiotap.rxflags`, `ip.dst`, `ip.proto`, `ip.src`, `ip.ttl`.
  PATH report keeps them (IPs factorised) to measure the inflation.

## 2026-10-14 · Stage 1 — split + selection
- Split 80/20 stratified, seed 42: train 505,084 / test 126,272; 11/11 classes in test.
- report: 49 → PCC −12 → 37 → ANOVA top-25. search: 41 → PCC −11 → 30 → RF top-25.
- ANOVA kept 7 of the 8 time/IP columns. 18 features shared by both paths.

## 2026-10-14 · Stage 2 — balancing
- Test macro-F1 — report: none 0.9586 / under_smote 0.9691 / class_weight 0.9595;
  search: none 0.8860 / under_smote 0.8853 / class_weight 0.8834.
- Report's +0.18 did not reproduce. **Chose under_smote** (lifts DDoS/MITM/Replay recall,
  smaller training set ≈ 208,693 rows). Honest note: a tie on the search path.

## 2026-10-14 · Stage 3 — binary
- CV macro-F1 1.000 on both paths; always-Attack baseline 0.443 (accuracy 0.795).
- Investigated: `frame.encap_type` = 23 on all Normal packets, none of the attacks.
  Dropping top 1 / 4 / 6 separators → 0.9999 / 0.9998 / 0.9299.
- **Decision:** document as a capture-setup artifact; do not claim the binary score as detection skill.

## 2026-10-14 · Stage 4 — multi-class
- 5-fold CV macro-F1: report 0.9742 / search 0.8846.
- Honest weak classes: DDoS 0.549, Replay 0.697, MITM 0.718. Reconnaissance 1.000 on 32 rows.
- **Decision:** keep all 11 classes; flag Reconnaissance as unreliable.

## 2026-10-14 · Stage 5 — benchmark
- Test macro-F1 (report / search): XGBoost 0.9795 / 0.8975 · RF 0.9691 / 0.8853 ·
  DT 0.9747 / 0.8723 · LR 0.9092 / 0.6828 · LinearSVM 0.9059 / 0.6801.
- **Decision:** RF stays primary (simple, explainable, 0.012 behind); XGBoost noted as best honest.

## 2026-10-14 · Stage 6 — importance, cost, reproducibility
- Permutation top-3 — report: radiotap.rxflags, frame.time_relative, frame.number (all time);
  search: frame.encap_type, wlan_radio.data_rate, udp.dstport.
- RF cost: train 2.4–2.5 s; ~680–720k packets/s; model 134 MB (report) / 227 MB (search).
- Same-seed re-train → identical predictions (both paths).

## 2026-10-14 · Reproduce everything
- `python src/run_all.py` from `ap_raw.csv` → every number above reproduced exactly.
- `results.html` built from the CSVs by `src/make_report.py`.

## 2026-10-14 · Show the work
- Added `student_review.docx/.pdf` (Arabic, RTL, Stage → steps) via `src/make_student_review.py`,
  `REPORT.docx/.pdf` (weekly report) via `src/make_weekly_report.py`, `TEAM-GUIDE.md`, per-stage
  decisions docs, PLAN / STATE / BUILD-LOG.
