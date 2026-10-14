# ML METHODOLOGY — how we keep the AP results honest

**The goal.** Not the biggest number, but the biggest number we can **trust** on traffic the model
has never seen. A model that scores 99% by reading the clock is useless on a real drone network.
Every step is judged by one question: **would this number still hold on new, unseen UAV traffic?**

This is the rulebook for every stage. Both paths (report, search) obey it.

---

## The order of work (and why the order matters)
1. **Look at the data first** — what each column really holds, the class counts, the junk.
   (`DATASET-AP.md`.) In AP this step found the shifted headers and the timestamp leak.
2. **Split first** — put the test set aside before anything learns from the data.
3. **Fit on train only** — PCC, ANOVA / tree ranking, scaling and resampling all learn from the
   training rows and are then *applied* to the test rows. Inside cross-validation, the samplers
   sit in an `imblearn` Pipeline so they only ever see the training folds.
4. **Train** on the (balanced) training set.
5. **Evaluate once** on the untouched test set (plus 5-fold CV where classes are small).
6. **Question any great score** before believing it (red-flag list below).

---

## The 3 enemies

### 1) Data leakage — the answer sneaks into the features
- **Test-into-train leakage.** Fitting a selector / scaler / SMOTE on all rows lets test rows shape
  the model. **Guard:** split first; fit on train only.
- **Shortcut (identifier / session) leakage.** Features that say *where* or *when* a packet was
  captured instead of *what it does*. In AP these are real and strong:
  - **time / order columns** — the capture timestamp alone gives macro-F1 **0.92**, because each
    attack was recorded in its own session;
  - **IP address columns** — memorise hosts, not behaviour.
  **Guard:** PATH search drops them; PATH report keeps them on purpose so we can *measure* the
  inflation. A one-column-at-a-time check (`stage1_shortcut_check.csv`) finds such columns.
- **Capture-setup leakage.** If one class is recorded with different equipment or settings, the
  model can learn the setup. In AP, every Normal packet has `frame.encap_type = 23` and no attack
  packet does. This cannot be fixed by dropping one column, so we **report it** instead of
  claiming the binary score as real skill.

### 2) Overfitting — memorising instead of learning
- Keep a real held-out test set; never tune on it.
- Use cross-validation when comparing settings.
- Watch for a big train-vs-test gap.
- Fewer, non-redundant features (PCC + top-25) help.

### 3) Bias — the metric or the data skews the result
- **Imbalance bias.** AP is ≈ 4,300 : 1 (Brute-Force vs Reconnaissance). Accuracy hides the rare
  classes, so the main metric is **macro-F1** plus **per-class recall/F1**.
- **Selection bias.** A global ranker (ANOVA) favours whatever separates the big classes — in AP it
  happily picked the timestamp. We compare rankers by the model's macro-F1, not by their own score.
- **Tiny-class bias.** Reconnaissance has 40 rows; its score is reported but flagged as unreliable.

---

## Reproducibility
- One fixed seed, `SEED = 42`, in the split, the samplers and every model.
- Every number in the docs comes from a saved run (`data/processed/*.csv`), never typed by guess.
- `python src/run_all.py` re-runs everything; Stage 6 re-trains and checks the predictions are identical.

## Red-flag checklist (assume a mistake, not a miracle)
- Macro-F1 ≈ 1.00 on a hard, imbalanced problem → look for leakage (we did: AP binary).
- One column with huge importance that is a time / id / address → shortcut.
- High accuracy, low macro-F1 → the model ignores rare classes.
- Big train-vs-test gap → overfitting.

## How the two paths serve this
| choice | PATH report (as written) | PATH search (honest) | enemy tested |
|---|---|---|---|
| time/order + IP columns | keep (IPs encoded) | **drop** | shortcut leakage |
| feature ranking | ANOVA top-25 | RF-importance top-25 | selection bias |
| split | stratified 80/20 | same split | kept equal for a fair comparison |
| balancing | under + Borderline-SMOTE | same | imbalance bias |

**Known limit.** The split is random within one capture file, so packets from the same session sit
on both sides. A **time-based split** (train on earlier packets, test on later ones, per class) is
the stronger test and is the main open item (see `PLAN.md`).
