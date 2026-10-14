# STATE — 2026-10-14 · UAV Networks (AP / Case 2)

Step:     ALL 6 STAGES DONE for the AP scenario (Case 2). Pipeline re-run end to end with
          `python src/run_all.py` → identical numbers. results.html, student_review.docx/.pdf and
          REPORT.docx/.pdf generated from the saved numbers.
Results:  Multi-class 5-fold CV macro-F1: report 0.974 / search 0.885.
          Best honest model XGBoost 0.898 (RF 0.885). Target 0.90: met only via leakage.
          Binary 1.000 on both paths = capture-setup artifact (frame.encap_type = 23 only on Normal).
          Weak classes (honest): DDoS 0.55, Replay 0.70, MITM 0.72. Reconnaissance 1.000 on 32 rows.
Leakage:  timestamp column alone = macro-F1 0.92 → time/order + IP columns dropped in PATH search.
Broken:   Nothing.
Next:     Optional Stage 7: time-aware split (PLAN.md). Otherwise the project is complete.
Gotchas:  - AP label header is "Normal" → renamed "Class"; "Ewil Twin" → "Evil Twin".
          - Column headers are shifted vs contents — never trust a column by its name.
          - Never drop rows that hold text: it deletes 100% of Evil Twin, MITM, Reconnaissance, Replay.
          - permutation_importance with n_jobs=1 only (big model, RAM).
          - data/ is gitignored (1.3 GB); re-download from Zenodo 15125851.
Where:    numbers  → docs/STAGE1..6-DECISIONS.md, docs/FINDINGS-AP.md, data/processed/*.csv
          history  → docs/BUILD-LOG.md
