# REPORT-NOTES — the GP report, distilled for coding

**Source:** `Graduation project 1.pdf` — *"Towards Robust Cyber Threat Detection in UAV
Networks: A Data-Driven Classification Framework"* (King Saud University, May 2026).
This file holds everything we need to write code **without re-reading the 39-page PDF**.
When something here is not enough, open the PDF at the page noted in `()`.

> We build **based on this report**, one stage at a time, as **basic student code**.
> The report's choices (thresholds, methods) are the plan — but we still *test* them on the
> real data and record evidence, we don't just trust the numbers.

---

## 1. What the project is (p6–9, 23, 30)
A **software-only, classical Machine-Learning Intrusion Detection System (IDS)** for UAV
networks. It reads network-traffic records and classifies each one as:
- **Binary** — Normal vs Attack (FR-1).
- **Multi-class** — which of the 10 attacks, or Normal (FR-2).

No deep learning, no GPU, no live/on-drone deployment. Just load → preprocess → train →
evaluate, on a real recorded dataset.

## 2. The dataset — UAV-NIDD (p24–26)
Real-world UAV testbed capture (IEEE TNSE 2025, ref [1]). **Not simulated.**
- **~860,000 records, ~1.6 GB**, 10 attack types + Normal.
- **3 communication scenarios** = 3 files (our `data/raw/`):

  | Scenario | Meaning (who is compromised) | Features | File | key |
  |----------|------------------------------|----------|------|-----|
  | Case 1 — UAV-to-UAV   | a UAV launches a network-wide attack      | 45 | `UAV-Case1-Label.csv`            | u2u |
  | Case 2 — UAV-to-AP    | an access point intercepts traffic        | 51 | `Access Point Case2 Label.xlsx` | u2a |
  | Case 3 — UAV-to-GCS   | the ground station is fully taken over    | 85 | `GSC Case3 Label .csv`          | u2g |

  (Case 2 is **.xlsx** → needs `openpyxl`, not `read_csv`. Case 3 filename has a typo + trailing space.)

- **10 attacks + Normal** (p23, 27): Scanning, Reconnaissance, DoS, DDoS,
  GPS Jamming & Spoofing, MITM, Replay, Evil Twin, Brute-Force, Fake Landing Packet.
- **Severe class imbalance** (p24): most frequent **DDoS ≈ 193,171**, least frequent
  **Reconnaissance = 6** → ratio **32,195 : 1**. This is the central challenge.

## 3. The pipeline the report prescribes (p27–28, 31, 32) — our stage order
Flow: **load → split (80/20 stratified, fixed seed) → preprocess → balance → train → evaluate.**
Everything after the split is **fit on the training set only** (no test-set leakage).

### Stage 1 — Preprocessing & feature selection (FR-3, p27)
Two-stage feature selection to cut dimensionality:
1. **PCC (Pearson Correlation Coefficient)** — drop features with **|corr| > 0.85** (redundant). Eq (1): `φ(X,Y) = Cov(X,Y) / (σX·σY)`.
2. **ANOVA F-score** — rank remaining features, keep **top 25 per scenario**. Eq (2)(3): F = between-group var / within-group var.

*(Thresholds 0.85 and top-25 are the report's suggestion — we test they actually help.)*

### Stage 2 — Class imbalance (FR-4 / NFR-3, p28)
**Random Undersampling (reduce majority) → then Borderline-SMOTE (oversample minority).**
Borderline-SMOTE eq (4): `x_new = xi + λ·(xĵ − xi)`, λ∈[0,1], only *borderline* minority
samples (those surrounded by majority neighbours) are synthesised.
- Without resampling, macro-F1 is only **0.67–0.78** despite high accuracy (p29) — proof that
  balancing is required, not optional.

### Stage 3 & 4 — Modeling (FR-5, p28, 30, 32)
- **Random Forest = primary model** (accuracy + speed + interpretable, good for low-resource).
- Benchmark against: **XGBoost, Decision Tree (DT), SVM, Logistic Regression (LR)**.
- Do **binary first (Stage 3)**, then **multi-class 10 attacks (Stage 4)**.

### Stage 5 — Cross-scenario + benchmarking (FR-7, p28)
Run the whole pipeline on **all three scenarios (U2U / U2A / U2G)** and compare models.

### Stage 6 — Reproducibility / interpretability / cost (NFR-4,5,2)
Fixed seed reproduces every number; tree feature-importance report; CPU time check
(edge-deployability sanity — Raspberry-Pi-class, p33).

## 4. Evaluation (FR-6, p28) — how we judge every run
Metrics: **Accuracy, Precision, Recall, F1, AUC** (eq 5–8).
- **Macro-averaged F1 is the PRIMARY metric** — it weights every attack class equally, so rare
  attacks count as much as common ones. (Accuracy alone lies under imbalance.)
- `Accuracy=(TP+TN)/(TP+TN+FP+FN)`, `Precision=TP/(TP+FP)`, `Recall=TP/(TP+FN)`,
  `F1=2·P·R/(P+R)`.

## 5. Targets & numbers to compare against (p29, 30–31)
- **NFR-1 target: macro-F1 ≥ 0.90** on the primary scenario. ← our "done" bar.
- Prior work on this exact dataset (to compare, not copy):
  - Ensemble (RF+DT+XGBoost soft-voting), ref [3] Charfi: **macro-F1 ≈ 0.95, up to 0.964** with resampling.
  - XGBoost: **99.98% accuracy** on U2U, ref [4].
  - DT: **F1 ≈ 0.9638**, ref [3].
  - Undersample+SMOTE combo: **+0.18 macro-F1** vs imbalanced, **~+1pt** vs plain SMOTE (ref [3]).

## 6. Requirements checklist (p26–30) — what "done" means overall
FR-1 binary · FR-2 multi-class(10) · FR-3 preprocess+2-stage FS · FR-4 imbalance handling ·
FR-5 train RF + benchmark 4 others · FR-6 the 5 metrics, macro-F1 primary · FR-7 all 3 scenarios.
NFR-1 macro-F1≥0.90 · NFR-2 classical/CPU/lightweight · NFR-3 robust to imbalance ·
NFR-4 interpretable (tree importances) · NFR-5 reproducible (fixed seed, 80/20 stratified) ·
NFR-6 generalises across 3 scenarios · NFR-7 extensible to new data/features.

## 7. Context facts (nice to know, rarely needed in code) (p24–25)
Testbed: **PX4 Vision Dev Kit V1.5** (hub/AP) + **DJI Mavic Air** + **DJI Mini 3 Pro**, 5GHz
802.11n ad-hoc mesh. Protocols: **MAVLink, DJI SDK, UDP, HTTP, SFTP, Telnet**. Attacker:
Kali 2023.1 with Aircrack-ng, Nmap, Metasploit, Bettercap, DroneSploit, Hping3.
Authors: Osama Aldhayan + team; supervisor Dr. Mustafa Qamhan.

---
*Page numbers refer to `Graduation project 1.pdf`. Update this file if we learn the real column
names / exact label values when we first open the CSVs in Stage 1.*
