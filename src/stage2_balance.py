"""
Stage 2 — class balancing (AP), compared fairly, for BOTH paths.

The question: does fixing the class imbalance actually help, and which way is best?
We answer it with numbers (not opinion), judged by macro-F1 and per-class recall on the
UNTOUCHED test set. All balancing is fit on the TRAIN set only (fitting it on the test set,
or before the split, would leak and inflate the score — see docs/ML-METHODOLOGY.md).

Three strategies are compared for each path:
    none          - train on the imbalanced data as-is          (report's baseline, step 2.1)
    under_smote   - RandomUnderSampler -> BorderlineSMOTE        (report's method, FR-4 / eq.4)
    class_weight  - cost-sensitive Random Forest, no resampling  (my research-based option)

AP imbalance: Brute-Force ~172k vs Reconnaissance 40 (≈ 4,300:1). We undersample big classes
down to a cap and lift tiny ones to a floor (full balance would be ~1.9M rows, and SMOTE from
32 Reconnaissance samples up to 172k would be pure invention).

Run it:
    python src/stage2_balance.py
Needs the Stage-1 outputs: data/processed/ap_<path>_train.csv and _test.csv.
"""

import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score

SEED = 42
LABEL = "Class"
PATHS = ["report", "search"]
STRATEGIES = ["none", "under_smote", "class_weight"]

UNDER_CAP = 30000    # undersample any class bigger than this down to this many rows
SMOTE_FLOOR = 5000   # oversample any class smaller than this up to this many rows


# ==========================================================================
# STEP 1 — load_xy()
# ==========================================================================
def load_xy(path_name, split):
    df = pd.read_csv(f"data/processed/ap_{path_name}_{split}.csv", low_memory=False)
    return df.drop(columns=[LABEL]), df[LABEL]


# ==========================================================================
# STEP 2 — make_rf()
# ==========================================================================
def make_rf(class_weight=None):
    return RandomForestClassifier(
        n_estimators=100, random_state=SEED, n_jobs=-1, class_weight=class_weight
    )


# ==========================================================================
# STEP 3 — under_targets() / smote_targets()
# ==========================================================================
def under_targets(y):
    """Classes bigger than the cap get reduced to the cap; others untouched."""
    return {c: UNDER_CAP for c, n in y.value_counts().items() if n > UNDER_CAP}


def smote_targets(y):
    """Classes smaller than the floor get raised to the floor; others untouched."""
    return {c: SMOTE_FLOOR for c, n in y.value_counts().items() if n < SMOTE_FLOOR}


# ==========================================================================
# STEP 4 — build_model()
# ==========================================================================
def build_model(strategy, y_train):
    if strategy == "none":
        return make_rf()
    if strategy == "class_weight":
        return make_rf(class_weight="balanced_subsample")
    if strategy == "under_smote":
        return ImbPipeline([
            ("under", RandomUnderSampler(sampling_strategy=under_targets(y_train), random_state=SEED)),
            ("smote", BorderlineSMOTE(sampling_strategy=smote_targets(y_train), random_state=SEED, k_neighbors=5)),
            ("rf", make_rf()),
        ])
    raise ValueError(strategy)


# ==========================================================================
# STEP 5 — main(): train every (path, strategy), score on the test set
# ==========================================================================
def main():
    rows = []
    recall_rows = []
    for path in PATHS:
        X_train, y_train = load_xy(path, "train")
        X_test, y_test = load_xy(path, "test")
        classes = sorted(y_test.unique())
        for strat in STRATEGIES:
            print(f"[{path} / {strat}] training ...", flush=True)
            model = build_model(strat, y_train)
            model.fit(X_train, y_train)
            pred = model.predict(X_test)

            macro = f1_score(y_test, pred, average="macro")
            weighted = f1_score(y_test, pred, average="weighted")
            acc = accuracy_score(y_test, pred)
            rows.append({"path": path, "strategy": strat,
                         "macro_f1": round(macro, 4), "weighted_f1": round(weighted, 4),
                         "accuracy": round(acc, 4)})
            print(f"    macro-F1={macro:.4f}  weighted-F1={weighted:.4f}  acc={acc:.4f}", flush=True)

            # per-class recall (did we actually catch the rare attacks?)
            rec = recall_score(y_test, pred, average=None, labels=classes, zero_division=0)
            row = {"path": path, "strategy": strat}
            row.update({c: round(r, 3) for c, r in zip(classes, rec)})
            recall_rows.append(row)

    results = pd.DataFrame(rows)
    recalls = pd.DataFrame(recall_rows)
    results.to_csv("data/processed/stage2_results.csv", index=False)
    recalls.to_csv("data/processed/stage2_recall_per_class.csv", index=False)

    print("\n===== STAGE 2 RESULTS (macro-F1 is what matters) =====")
    print(results.to_string(index=False))
    print("\n===== per-class recall =====")
    print(recalls.to_string(index=False))


if __name__ == "__main__":
    main()
