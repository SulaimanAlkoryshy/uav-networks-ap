# STAGE 1 — Preprocessing & feature selection: two opinions per step

**The rule (CLAUDE.md).** For every step we write down TWO opinions:
- **Report** = what the GP report says to do.
- **Independent** = what is best according to research + reasoning, on purpose *not* anchored to
  the report (it may disagree).

Then the **Decision** (what we did) and any **Open concern**. Sources are at the bottom.
Code: `src/convert_ap_xlsx_to_csv.py`, `src/stage1_preprocess.py`.

> Bottom line: the two opinions agree on cleaning, PCC and top-25. They **disagree** on the
> time/IP columns (report keeps them, independent drops them) and on what to do with text cells.
> The data decided both: the timestamp alone scores 0.92, and dropping text rows would delete four
> attack classes completely.

---

## Step 1.1 — Load the file
- **Report:** load each scenario file; Case 2 is `.xlsx`.
- **Independent:** an Excel sheet of 631k rows is slow and memory-heavy to read every run.
  Convert it **once** to CSV by streaming rows, then always read the CSV. Read every column as
  text first, because the AP columns mix numbers, hex and IPs — letting pandas guess types would
  silently turn mixed columns into strings or NaN.
- **Decision:** `convert_ap_xlsx_to_csv.py` (python-calamine, row by row) → `ap_raw.csv`
  (631,356 × 51). Stage 1 reads it with `dtype=str`. ✅ agree, with a speed fix.

## Step 1.2 — Fix the label
- **Report:** label = Normal + 10 attacks.
- **Independent:** always print the raw label values before trusting them; header and spelling
  mistakes create fake columns or fake classes.
- **Decision:** the label column's header is literally `Normal` (the real header was lost) →
  renamed to `Class`. `Ewil Twin` → `Evil Twin`. Trimmed spaces. Result: 11 real classes.
  ✅ agree.

## Step 1.3 — Make columns numeric  ← opinions DIFFER
- **Report (FR-3):** handle NaN/inf, encode non-numeric fields.
- **Independent:** the AP headers are **shifted against their contents** (e.g. `radiotap.datarate`
  holds 2437/2412 = channel frequency; `ip.proto` holds IP addresses). So "encode text" blindly
  would invent meaning. Parse what is really a number (incl. hex `0x…`), and mark anything else
  with one sentinel value. Before dropping rows, **measure which classes they belong to**.
- **Evidence:** 72,030 rows contain some text. They are **100%** of Evil Twin, MITM,
  Reconnaissance and Replay, and 67% of DoS. Dropping them (the usual "drop the few bad rows")
  would delete four attack classes.
- **Decision:** hex → number, other text → **-1**, keep all rows. 102,414 cells were set to -1.
  ✅ followed the independent opinion.
- **Open concern:** -1 means "this field held text here", which partly reflects packet type. It is
  a legitimate signal of packet structure, but it comes from a messy export, not a clean field.

## Step 1.4 — Drop constant columns
- **Report / Independent:** zero-variance columns carry no information → drop. Agree.
- **Decision:** dropped `wlan.fc.protected`. ✅

## Step 1.5 — Time / order and IP columns  ← independent goes BEYOND the report
- **Report:** does not mention them; only PCC + ANOVA. So all columns stay.
- **Independent:** identifier and time columns are classic shortcut features in intrusion
  datasets: when each attack is captured in its own session, *when* a packet was captured tells
  the class, and the model never learns *what* the attack looks like [S1][S2][S8]. Test it: train
  a tree on **one column at a time**; a behaviour feature alone should be weak.
- **Evidence (`stage1_shortcut_check.csv`):** `frame.time_relative` (really the epoch timestamp)
  alone → macro-F1 **0.923**; `radiotap.channel.flags.cck` (time since start) 0.614;
  `radiotap.rxflags` (radio clock) 0.344; `frame.number` (packet index) 0.279. IP columns 0.11–0.33.
- **Decision:** two paths.
  PATH report keeps them (IPs factorised to numbers) — to measure the inflation.
  PATH search drops the 4 time/order + 4 `ip.*` columns. ✅ both kept on purpose.

## Step 1.6 — Train/test split  ← independent has a concern
- **Report (NFR-5):** 80/20 random stratified split, fixed seed.
- **Independent:** a random split inside one capture puts neighbouring packets of the same session
  on both sides, which can still flatter the score. A **time-aware split** is the stronger test
  [S1][S9].
- **Decision:** report's split (80/20 stratified, seed 42) for both paths → train 505,084 / test
  126,272, all 11 classes in test (Reconnaissance: 32 / 8).
- **Open concern:** time-aware split = the main open item in `PLAN.md`.

## Step 1.7 — PCC filter |corr| > 0.85
- **Report (eq. 1):** drop one of each pair with |Pearson| > 0.85.
- **Independent:** fine as a cheap redundancy filter for trees; the exact threshold matters little.
  Must be computed on train only.
- **Decision:** on train only. report: 49 → 37 (12 dropped); search: 41 → 30 (11 dropped). ✅

## Step 1.8 — Rank and keep top-25  ← opinions DIFFER
- **Report (eq. 2–3):** ANOVA F-score top-25.
- **Independent:** ANOVA scores each feature by how much class *means* differ — it rewards any
  column that shifts between sessions (like a clock) and is weak for non-linear, rare-class
  signals. Tree importance (from a balanced RF) matches the model we actually use [S5].
- **Evidence:** ANOVA's top-25 contains **7 of the 8** time/IP columns (the 8th was removed by
  PCC). 18 features are shared by both paths.
- **Decision:** report = ANOVA top-25; search = RF-importance top-25 (fit on a 150k stratified
  sample of train). Winner judged by macro-F1 in Stages 3–5, not here. ✅

---

## Sources
- [S1] Arp et al., *Dos and Don'ts of Machine Learning in Computer Security*, USENIX Security 2022 — spurious correlations, data snooping, sampling bias.
- [S2] Kaufman et al., *Leakage in Data Mining: Formulation, Detection, and Avoidance*, ACM TKDD 2012.
- [S5] Strobl et al., *Bias in random forest variable importance measures*, BMC Bioinformatics 2007.
- [S8] Engelen, Rimmer, Joosen, *Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study*, IEEE S&P Workshops 2021.
- [S9] Pendlebury et al., *TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time*, USENIX Security 2019.
- [S11] Hadi et al., UAV-NIDD dataset, IEEE TNSE 2025, DOI 10.1109/TNSE.2025.3553442.
