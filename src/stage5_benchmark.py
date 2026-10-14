"""
Stage 5 — model benchmarking (AP), for BOTH paths.

Models (the report's list): Random Forest, XGBoost, Decision Tree, Logistic Regression, SVM.
Full-kernel SVM is far too slow on 500k rows, so we use LinearSVC (a linear SVM).
All use under_smote (fit on train only). Tree models need no scaling; LR and SVM get a
StandardScaler. Judged by macro-F1 on the untouched test set.

Goal: see which model is best (FR-5) and whether we reach macro-F1 >= 0.90 (NFR-1) — honestly.

Run:
    python src/stage5_benchmark.py
"""

import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

SEED = 42
LABEL = "Class"
PATHS = ["report", "search"]
MODELS = ["RandomForest", "XGBoost", "DecisionTree", "LogisticRegression", "LinearSVM"]
UNDER_CAP = 30000
SMOTE_FLOOR = 5000


# ==========================================================================
# STEP 1 — sampling targets
# ==========================================================================
def _under(y):
    c = pd.Series(y).value_counts()
    return {k: UNDER_CAP for k, n in c.items() if n > UNDER_CAP}


def _smote(y):
    c = pd.Series(y).value_counts()
    return {k: SMOTE_FLOOR for k, n in c.items() if n < SMOTE_FLOOR}


# ==========================================================================
# STEP 2 — make_model(): returns (model, needs_scaling)
# ==========================================================================
def make_model(name):
    if name == "RandomForest":
        return RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1), False
    if name == "XGBoost":
        return XGBClassifier(n_estimators=200, max_depth=6, random_state=SEED,
                             n_jobs=-1, tree_method="hist", eval_metric="mlogloss"), False
    if name == "DecisionTree":
        return DecisionTreeClassifier(random_state=SEED), False
    if name == "LogisticRegression":
        return LogisticRegression(max_iter=1000), True   # needs scaling
    if name == "LinearSVM":
        return LinearSVC(random_state=SEED), True        # needs scaling
    raise ValueError(name)


# ==========================================================================
# STEP 3 — build_pipeline()
# ==========================================================================
def build_pipeline(name):
    model, needs_scaling = make_model(name)
    steps = [
        ("under", RandomUnderSampler(sampling_strategy=_under, random_state=SEED)),
        ("smote", BorderlineSMOTE(sampling_strategy=_smote, random_state=SEED, k_neighbors=5)),
    ]
    if needs_scaling:
        steps.append(("scale", StandardScaler()))
    steps.append(("model", model))
    return ImbPipeline(steps)


# ==========================================================================
# STEP 4 — main(): every model on both paths, test macro-F1
# ==========================================================================
def main():
    rows = []
    for path in PATHS:
        tr = pd.read_csv(f"data/processed/ap_{path}_train.csv", low_memory=False)
        te = pd.read_csv(f"data/processed/ap_{path}_test.csv", low_memory=False)
        X_train, y_train = tr.drop(columns=[LABEL]), tr[LABEL]
        X_test, y_test = te.drop(columns=[LABEL]), te[LABEL]

        # numeric labels (XGBoost needs them; harmless for the rest)
        le = LabelEncoder().fit(y_train)
        y_tr, y_te = le.transform(y_train), le.transform(y_test)

        for name in MODELS:
            print(f"[{path} / {name}] training ...", flush=True)
            pipe = build_pipeline(name)
            pipe.fit(X_train, y_tr)
            pred = pipe.predict(X_test)
            macro = f1_score(y_te, pred, average="macro")
            rows.append({"path": path, "model": name, "test_macroF1": round(macro, 4)})
            print(f"    macro-F1={macro:.4f}", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("data/processed/stage5_benchmark.csv", index=False)
    print("\n===== STAGE 5 — MODEL BENCHMARK (test macro-F1) =====")
    print(out.pivot(index="model", columns="path", values="test_macroF1").to_string())
    print("\n(target NFR-1: macro-F1 >= 0.90)")


if __name__ == "__main__":
    main()
