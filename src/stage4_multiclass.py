"""
Stage 4 — multi-class modeling (AP): identify WHICH of the 11 classes (10 attacks + Normal),
for BOTH paths.

Model: Random Forest + under_smote (our choices). Judged by 5-fold stratified CV (pooled
predictions) so every rare class is tested, and by the full per-class precision/recall/F1.
Fit on train only / inside each CV fold (see docs/ML-METHODOLOGY.md).

We keep all classes (dropping rare ones would just hide the problem). Reconnaissance has only
40 rows in the whole AP file (32 in train), so its score is flagged as unreliable.

Run:
    python src/stage4_multiclass.py
"""

import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

SEED = 42
LABEL = "Class"
PATHS = ["report", "search"]
UNDER_CAP = 30000
SMOTE_FLOOR = 5000


# ==========================================================================
# STEP 1 — load_xy()
# ==========================================================================
def load_xy(path_name, split):
    df = pd.read_csv(f"data/processed/ap_{path_name}_{split}.csv", low_memory=False)
    return df.drop(columns=[LABEL]), df[LABEL]


# ==========================================================================
# STEP 2 — make_pipeline() (sampling targets worked out per fold)
# ==========================================================================
def _under(y):
    c = pd.Series(y).value_counts()
    return {k: UNDER_CAP for k, n in c.items() if n > UNDER_CAP}


def _smote(y):
    c = pd.Series(y).value_counts()
    return {k: SMOTE_FLOOR for k, n in c.items() if n < SMOTE_FLOOR}


def make_pipeline():
    return ImbPipeline([
        ("under", RandomUnderSampler(sampling_strategy=_under, random_state=SEED)),
        ("smote", BorderlineSMOTE(sampling_strategy=_smote, random_state=SEED, k_neighbors=5)),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)),
    ])


# ==========================================================================
# STEP 3 — main(): 5-fold CV per path, summary + per-class table
# ==========================================================================
def main():
    summary = []
    per_class = {}
    for path in PATHS:
        X_train, y_train = load_xy(path, "train")
        print(f"[{path}] 5-fold CV (multi-class) ...", flush=True)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        pred = cross_val_predict(make_pipeline(), X_train, y_train, cv=cv, n_jobs=1)

        macro = f1_score(y_train, pred, average="macro")
        weighted = f1_score(y_train, pred, average="weighted")
        print(f"    macro-F1={macro:.4f}  weighted-F1={weighted:.4f}", flush=True)
        summary.append({"path": path, "cv_macroF1": round(macro, 4),
                        "cv_weightedF1": round(weighted, 4)})

        rep = classification_report(y_train, pred, output_dict=True, zero_division=0)
        per_class[path] = {c: {"f1": round(rep[c]["f1-score"], 3), "recall": round(rep[c]["recall"], 3),
                               "precision": round(rep[c]["precision"], 3), "support": int(rep[c]["support"])}
                           for c in sorted(y_train.unique())}

    summ = pd.DataFrame(summary)
    summ.to_csv("data/processed/stage4_multiclass_results.csv", index=False)
    print("\n===== STAGE 4 — MULTI-CLASS (5-fold CV) =====")
    print(summ.to_string(index=False))

    # tidy per-class F1 table (one row per class, a column per path)
    classes = sorted(per_class["report"].keys())
    f1tab = pd.DataFrame({
        "class": classes,
        "support": [per_class["report"][c]["support"] for c in classes],
        "report_f1": [per_class["report"][c]["f1"] for c in classes],
        "search_f1": [per_class["search"][c]["f1"] for c in classes],
        "search_recall": [per_class["search"][c]["recall"] for c in classes],
        "search_precision": [per_class["search"][c]["precision"] for c in classes],
    })
    f1tab.to_csv("data/processed/stage4_per_class_f1.csv", index=False)
    print("\n===== per-class F1 (report vs search) + search P/R =====")
    print(f1tab.to_string(index=False))


if __name__ == "__main__":
    main()
