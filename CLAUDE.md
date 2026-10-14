# CLAUDE.md — UAV Networks (AP / Case 2)

## What this is
Graduation-project IDS on UAV-NIDD, **Access Point scenario only**. Same plan as the GSC repo
(github.com/OS-78/uav-networks), adapted to AP. Read `docs/FINDINGS-AP.md` first.

## Rules (carried over from the GSC project)
- **Basic student code**: simple functions, no frameworks, no clever abstractions.
- **One file per stage** (`src/stageN_<name>.py`), each step under a banner
  `# ===== STEP n — <what it does> =====`.
- Two paths everywhere: **report** (as the GP report says) vs **search** (honest, drops shortcuts).
- Fit everything on **train only**; fixed `SEED = 42`; judge by **macro-F1**, never accuracy alone.
- Results shown in self-contained `results.html` (built by `src/make_report.py` from the CSVs).
- Numbers go in the docs only from a real run, never guessed.

## AP-specific gotchas
- Label column header is `Normal` → renamed `Class`; `Ewil Twin` → `Evil Twin`.
- Column headers are shifted vs contents; columns hold hex / IPs / text → parse hex, text → -1.
  **Never drop rows with text**: it deletes 100% of Evil Twin, MITM, Reconnaissance, Replay.
- Time/order columns leak (timestamp alone = 0.92 macro-F1): `frame.number`,
  `frame.time_relative`, `radiotap.channel.flags.cck`, `radiotap.rxflags`.
- Normal capture is different (`frame.encap_type = 23`) → binary = 1.000 is an artifact.

## Compute safety
- Never `n_jobs=-1` on `permutation_importance` or anything that copies a big model; `n_jobs=1`.
- Data lives in `data/` (gitignored).

## Commands
```bash
python src/convert_ap_xlsx_to_csv.py   # once
python src/run_all.py                  # everything + results.html
```
