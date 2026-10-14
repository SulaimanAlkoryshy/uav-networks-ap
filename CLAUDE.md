# CLAUDE.md — UAV Networks (AP / Case 2)

## What this is
Graduation-project IDS on UAV-NIDD, **Access Point scenario only**, built in 6 stages.
**Read `docs/STATE.md` first**, then `docs/PLAN.md`.

## How we work
- **Basic student code**: simple functions, no frameworks, no clever abstractions.
- **One file per stage** (`src/stageN_<name>.py`), each step under a banner
  `# ===== STEP n — <what it does> =====`.
- Two paths everywhere: **report** (as the GP report says) vs **search** (honest, drops shortcuts).
- **Two-opinion rule**: for every step, record what the report says AND an independent opinion
  (research-based, allowed to disagree), the decision and the evidence, in `docs/STAGEn-DECISIONS.md`.
- Fit everything on **train only**; fixed `SEED = 42`; judge by **macro-F1**, never accuracy alone.
- Numbers go in the docs only from a real run, never guessed. Log decisions in `docs/BUILD-LOG.md`
  (append-only) and update `docs/STATE.md` at the end of a session.
- Show the work: `results.html` (`src/make_report.py`), `student_review.docx/.pdf` (Arabic + English
  ML terms, RTL — `src/make_student_review.py`), `REPORT.docx/.pdf` (`src/make_weekly_report.py`).

## AP-specific gotchas
- Label column header is `Normal` → renamed `Class`; `Ewil Twin` → `Evil Twin`.
- Column headers are shifted vs contents; columns hold hex / IPs / text → parse hex, text → -1.
  **Never drop rows with text**: it deletes 100% of Evil Twin, MITM, Reconnaissance, Replay.
- Time/order columns leak (timestamp alone = 0.92 macro-F1): `frame.number`,
  `frame.time_relative`, `radiotap.channel.flags.cck`, `radiotap.rxflags`.
- Normal capture is different (`frame.encap_type = 23`) → binary = 1.000 is an artifact.

## Compute safety
- Never `n_jobs=-1` on `permutation_importance` or anything that copies a big model; `n_jobs=1`.
- Data lives in `data/` (gitignored, ~1.3 GB).

## Commands
```bash
python src/convert_ap_xlsx_to_csv.py                              # once
python src/run_all.py                                             # everything + results.html + docs
powershell -File src/docx_to_pdf.ps1 student_review.docx REPORT.docx   # PDFs
```
