"""
Stage 3 — binary modeling (AP): Normal vs Attack, for BOTH paths.

Model: Random Forest (the report's primary model).
Balancing: under_smote (our Stage-2 choice), fit on train only / inside each CV fold.

Difference from GSC: in AP, "Normal" is NOT rare (~129k rows, ~20%). So the binary task is
much less imbalanced (about 4 Attack : 1 Normal). Undersampling brings both sides to the cap;
SMOTE has nothing to do here (no class is below the floor).

We still report 5-fold stratified CV as the MAIN number and the held-out test as a check, and
compare against the trivial "always Attack" baseline. Metrics: macro-F1, Normal precision/recall,
MCC and balanced accuracy. See docs/ML-METHODOLOGY.md.

Run:
    python src/stage3_binary.py
Needs Stage-1 outputs: data/processed/ap_<path>_train.csv and _test.csv.
"""

import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (balanced_accuracy_score, classification_report,
                             f1_score, matthews_corrcoef)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.tree import DecisionTreeClassifier

SEED = 42
LABEL = "Class"
NORMAL = "Normal"
PATHS = ["report", "search"]
UNDER_CAP = 30000     # undersample any side bigger than this
SMOTE_FLOOR = 5000    # oversample any side smaller than this


# ==========================================================================
# STEP 1 — to_binary() + load_xy()
# ==========================================================================
def to_binary(y):
    """Everything that is not Normal becomes 'Attack'."""
    return y.where(y == NORMAL, "Attack")


def load_xy(path_name, split):
    df = pd.read_csv(f"data/processed/ap_{path_name}_{split}.csv", low_memory=False)
    return df.drop(columns=[LABEL]), to_binary(df[LABEL])


# ==========================================================================
# STEP 2 — make_pipeline(): under_smote + Random Forest
# ==========================================================================
def _under(y):
    c = pd.Series(y).value_counts()
    return {k: UNDER_CAP for k, n in c.items() if n > UNDER_CAP}


def _smote(y):
    c = pd.Series(y).value_counts()
    return {k: SMOTE_FLOOR for k, n in c.items() if n < SMOTE_FLOOR}


def make_pipeline():
    """Samplers act on training data only (targets are worked out per fold)."""
    return ImbPipeline([
        ("under", RandomUnderSampler(sampling_strategy=_under, random_state=SEED)),
        ("smote", BorderlineSMOTE(sampling_strategy=_smote, random_state=SEED, k_neighbors=5)),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)),
    ])


# ==========================================================================
# STEP 3 — normal_scores()
# ==========================================================================
def normal_scores(y_true, y_pred):
    """Precision/recall/F1 for the Normal class."""
    rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    b = rep.get(NORMAL, {"precision": 0, "recall": 0, "f1-score": 0})
    return b["precision"], b["recall"], b["f1-score"]


# ==========================================================================
# STEP 4 — capture_check(): is the perfect binary score real or a capture artifact?
# ==========================================================================
def capture_check():
    """Binary scores 1.000 even on the honest path -> a red flag (ML-METHODOLOGY.md).
    (a) score each single column with a depth-3 tree; (b) drop the strongest columns one group
    at a time and re-train RF. If the score stays ~1.0, Normal is separable by HOW it was
    captured (all Normal packets have frame.encap_type = 23, no attack packet does), not by a
    single removable column."""
    X_train, y_train = load_xy("search", "train")
    X_test, y_test = load_xy("search", "test")
    Xs, _, ys, _ = train_test_split(X_train, y_train, train_size=150000,
                                    random_state=SEED, stratify=y_train)

    # (a) one column alone
    single = []
    for c in Xs.columns:
        Xa, Xb, ya, yb = train_test_split(Xs[[c]], ys, test_size=0.3, random_state=SEED, stratify=ys)
        p = DecisionTreeClassifier(max_depth=3, random_state=SEED).fit(Xa, ya).predict(Xb)
        single.append((c, f1_score(yb, p, average="macro")))
    single = sorted(single, key=lambda t: -t[1])
    print("\n[capture check] binary macro-F1 using ONE column (top 5):")
    for c, f in single[:5]:
        print(f"    {c:30s} {f:.3f}")

    # (b) drop the top 0 / 1 / 4 / 6 columns and re-train
    rows = []
    for n in [0, 1, 4, 6]:
        drop = [c for c, _ in single[:n]]
        rf = RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
        rf.fit(Xs.drop(columns=drop), ys)
        f = f1_score(y_test, rf.predict(X_test.drop(columns=drop)), average="macro")
        rows.append({"columns_dropped": n, "which": ", ".join(drop) or "-", "test_macroF1": round(f, 4)})
        print(f"    drop top-{n}: test macro-F1 = {f:.4f}")
    pd.DataFrame(rows).to_csv("data/processed/stage3_capture_check.csv", index=False)


# ==========================================================================
# STEP 5 — main(): CV + held-out test + trivial baseline, per path
# ==========================================================================
def main():
    rows = []
    for path in PATHS:
        X_train, y_train = load_xy(path, "train")
        X_test, y_test = load_xy(path, "test")
        print(f"\n[{path}] Normal in train={int((y_train == NORMAL).sum())}, "
              f"test={int((y_test == NORMAL).sum())}", flush=True)

        # ---- main estimate: 5-fold stratified CV on train ----
        print(f"[{path}] 5-fold CV ...", flush=True)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        cv_pred = cross_val_predict(make_pipeline(), X_train, y_train, cv=cv, n_jobs=1)
        cv_macro = f1_score(y_train, cv_pred, average="macro")
        cv_np, cv_nr, cv_nf = normal_scores(y_train, cv_pred)
        cv_mcc = matthews_corrcoef(y_train, cv_pred)
        cv_bal = balanced_accuracy_score(y_train, cv_pred)

        # ---- secondary: held-out test ----
        print(f"[{path}] held-out test ...", flush=True)
        model = make_pipeline().fit(X_train, y_train)
        pred = model.predict(X_test)
        t_macro = f1_score(y_test, pred, average="macro")
        t_np, t_nr, t_nf = normal_scores(y_test, pred)
        t_mcc = matthews_corrcoef(y_test, pred)

        # ---- trivial baseline: always "Attack" ----
        base_pred = pd.Series(["Attack"] * len(y_test), index=y_test.index)
        base_macro = f1_score(y_test, base_pred, average="macro")
        base_acc = (base_pred.values == y_test.values).mean()

        rows.append({
            "path": path,
            "cv_macroF1": round(cv_macro, 4), "cv_normal_recall": round(cv_nr, 3),
            "cv_normal_prec": round(cv_np, 3), "cv_MCC": round(cv_mcc, 3), "cv_balAcc": round(cv_bal, 3),
            "test_macroF1": round(t_macro, 4), "test_normal_recall": round(t_nr, 3),
            "test_normal_prec": round(t_np, 3), "test_MCC": round(t_mcc, 3),
            "baseline_allAttack_macroF1": round(base_macro, 4), "baseline_acc": round(base_acc, 4),
        })
        print(f"    CV macro-F1={cv_macro:.4f} (Normal recall {cv_nr:.2f})  "
              f"test macro-F1={t_macro:.4f} (Normal recall {t_nr:.2f})  "
              f"baseline macro-F1={base_macro:.4f} (acc {base_acc:.4f})", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("data/processed/stage3_binary_results.csv", index=False)
    print("\n===== STAGE 3 — BINARY (Normal vs Attack) =====")
    print(out.to_string(index=False))

    capture_check()


if __name__ == "__main__":
    main()
