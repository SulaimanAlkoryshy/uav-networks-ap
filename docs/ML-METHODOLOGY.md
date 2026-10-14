# ML METHODOLOGY — how we keep the results honest

**Our real goal.** Not the highest accuracy number — the highest number we can *trust* to hold on
new, unseen UAV traffic. A model that scores 99.9% by cheating is worthless in the field. So every
step is judged by one question: **would this number still be true on data the model has never seen?**

This doc is the rulebook for the whole project. Both pipelines (PATH report, PATH search) must obey
it. It also explains *how* these ML/IDS projects are properly built and the three mistakes they work
hardest to avoid.

---

## How an ML intrusion-detection project is built (the honest pipeline)
A standard data-science flow (CRISP-DM style), and the order is not optional — it is what keeps the
result honest:

1. **Understand the problem & data** — what are we detecting, what do the features mean, how are the
   classes distributed. (We did this: `DATASET-GSC.md`.)
2. **Split FIRST** — set the test set aside *before* any cleaning/selection/scaling that learns from
   data. The test set must stay "unseen" until the very end.
3. **Preprocess & select features — fit on TRAIN only** — correlation filter, ANOVA/importance,
   scaling, and resampling all learn their settings from the training set, then are *applied* to the
   test set. Never the other way round.
4. **Train** the model on the (balanced) training set.
5. **Evaluate once** on the untouched test set, using honest metrics.
6. **Validate generalisation** — check on a *different* scenario/session (here: the report's FR-7
   cross-scenario test), because a held-out slice of the *same* capture can still be too easy.

---

## The 3 enemies and how we stop them

### 1) Data leakage — the test set (or the answer) sneaks into training
Leakage makes scores look great in testing and then collapse in the real world. Forms we guard against:
- **Test-into-train leakage.** Fitting a scaler / feature selector / SMOTE on the *whole* dataset
  lets information from the test rows shape the model. **Guard:** split first; fit everything on
  train only (steps 2–3 above). In code this is why `pcc_columns_to_drop`, `rank_features`, and
  (later) SMOTE all receive **only `X_train`**.
- **Identifier / shortcut leakage.** Features like **IP address, host id, and destination port** let
  a model memorise *which machine* sent traffic instead of *what the attack looks like*. Research
  shows this gives deceptively high scores (up to ~100%) that drop >90% on new data. We *saw this
  live*: Path report's ANOVA picked `uid`, `id.orig_h`, `id.resp_h` into its top-25. **Guard:** Path
  search **drops** all id/host columns; Path report keeps them *on purpose* so we can measure how much
  "cheating" they buy (and expose it at the cross-scenario stage).
- **Target leakage.** A feature that is basically a stand-in for the label. **Guard:** watch for any
  single feature that alone separates classes almost perfectly — treat it as a suspect.

### 2) Overfitting — the model memorises the training data instead of learning the pattern
It then does well on train and badly on test. **Guards:**
- A real held-out **test set** (never trained on, never tuned on).
- Watch the **train-vs-test gap**: a big gap = overfitting.
- Prefer models with sensible limits (Random Forest depth/estimators) and use **cross-validation**
  when tuning.
- **Never tune on the test set.** If we try thresholds/feature counts, we compare them with
  cross-validation on the *training* data, and the test set is spent only once at the end.
- Fewer, non-redundant features (our PCC + selection) also reduce overfitting.

### 3) Bias — the result is skewed by the data or the metric
- **Class-imbalance bias.** GSC is 5,103:1 (DoS vs Benign). A model can get ~99% accuracy by always
  saying "DoS" and still miss every rare attack. **Guards:** (a) judge with **macro-F1 and per-class
  recall**, never accuracy alone — macro-F1 weights every class equally; (b) resample (undersample +
  Borderline-SMOTE) **fit on train only** (never resample before the split — that leaks).
- **Selection bias.** Global feature rankers (ANOVA, mutual information) can under-weight features
  that only matter for rare attacks. **Guard:** compare rankers across paths (ANOVA vs tree
  importance) and judge by macro-F1, not by the ranker's own score.
- **Sampling bias.** The test set must reflect reality. **Guard:** stratified split keeps the class
  mix identical in train and test; cross-scenario validation checks we didn't overfit to one capture.

---

## Reproducibility (so the numbers are real and checkable)
- One **fixed seed** (`SEED = 42`) everywhere (split, SMOTE, model).
- Every reported number comes from an actual run that is saved; measurements go in `BUILD-LOG.md`,
  never guessed.
- The whole pipeline re-runs from one command.

## Red-flag checklist (if we see these, assume a mistake, not a miracle)
- Accuracy or F1 **≈ 99–100%** on a hard, imbalanced problem → suspect leakage.
- **Huge train-vs-test gap** → overfitting.
- A score that **collapses on the cross-scenario test** → the within-scenario score was leaking.
- **High accuracy but low macro-F1** → the model is ignoring rare classes (imbalance bias).
- One feature with suspiciously high importance that is an **id/port/address** → shortcut leakage.

---

## How the two paths serve this methodology
We run two pipelines to *measure*, not guess, the effect of these choices — and we judge the winner
only at Stage 3 (modeling) with macro-F1, and again at Stage 5 (cross-scenario):

| Choice | PATH report (report as-written) | PATH search (rigour-first) | which enemy it tests |
|--------|----------------------------------|----------------------------|----------------------|
| id/host columns | keep (encoded) | **drop** | identifier/shortcut leakage |
| feature ranking | ANOVA top-25 | tree-importance top-25 | selection bias under imbalance |
| split (within GSC) | stratified 80/20 | stratified 80/20 (same) | kept identical for a fair comparison |
| real leakage test | — | **cross-scenario at Stage 5** | the true generalisation check |

**Note on the split.** We first tried a host-based *group split* for Path search (the textbook
anti-leakage split). The data proved it infeasible here: GSC has only ~42 hosts, so an 80/20 group
split left a 5,311-row test missing 5 of 10 classes — you cannot compute a fair macro-F1 that way.
So we use the same stratified split for both paths (fair, all classes testable) and put the real
anti-leakage check at Stage 5 cross-scenario. This itself is the methodology working: we tested an
idea against the data and let the evidence correct it, instead of trusting the opinion.
