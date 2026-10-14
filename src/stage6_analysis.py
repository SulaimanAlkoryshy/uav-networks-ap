"""
Stage 6 — interpretability + CPU cost + reproducibility check (AP), for BOTH paths.

Covers:
  6.2 Feature importance (NFR-4): impurity importance (fast, biased toward many-valued features)
      AND permutation importance (slower, more trustworthy). On the report path this doubles as
      a leakage check: do the time / IP columns dominate?
  6.3 CPU cost (NFR-2): training time, inference time + throughput, and model size.
  6.1 Reproducibility (NFR-5): train the SAME model twice with the fixed seed and check the
      predictions are identical.

Run:
    python src/stage6_analysis.py
"""

import gc
import pickle
import time

import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

SEED = 42
LABEL = "Class"
PATHS = ["report", "search"]
UNDER_CAP = 30000
SMOTE_FLOOR = 5000
PERM_SAMPLE = 10000   # permutation importance on a test subsample (speed + memory)


# ==========================================================================
# STEP 1 — make_pipeline()
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
# STEP 2 — main(): cost, importance, reproducibility per path
# ==========================================================================
def main():
    cost_rows = []
    for path in PATHS:
        print(f"\n################  PATH: {path}  ################")
        tr = pd.read_csv(f"data/processed/ap_{path}_train.csv", low_memory=False)
        te = pd.read_csv(f"data/processed/ap_{path}_test.csv", low_memory=False)
        X_train, y_train = tr.drop(columns=[LABEL]), tr[LABEL]
        X_test, y_test = te.drop(columns=[LABEL]), te[LABEL]

        # ---- 6.3 training time ----
        pipe = make_pipeline()
        t0 = time.perf_counter()
        pipe.fit(X_train, y_train)
        train_s = time.perf_counter() - t0

        # ---- 6.3 inference time + throughput ----
        t0 = time.perf_counter()
        pred = pipe.predict(X_test)
        infer_s = time.perf_counter() - t0
        per_sample_ms = infer_s / len(X_test) * 1000
        throughput = len(X_test) / infer_s

        # ---- 6.3 model size ----
        size_mb = len(pickle.dumps(pipe)) / 1e6

        print(f"[cost] train={train_s:.1f}s  inference={infer_s:.2f}s for {len(X_test)} rows "
              f"({per_sample_ms:.4f} ms/row, {throughput:,.0f} rows/s)  model={size_mb:.1f} MB")

        # ---- 6.2 impurity importance (top 10) ----
        rf = pipe.named_steps["rf"]
        imp = pd.Series(rf.feature_importances_, index=X_train.columns).sort_values(ascending=False)
        print("[impurity importance] top 10:")
        for name, val in imp.head(10).items():
            print(f"    {name:30s} {val:.4f}")

        # ---- 6.2 permutation importance (top 10, on a test subsample) ----
        Xs = X_test.sample(n=min(PERM_SAMPLE, len(X_test)), random_state=SEED)
        ys = y_test.loc[Xs.index]
        # n_jobs=1 on purpose: parallel workers would each copy the big model and blow up memory.
        perm = permutation_importance(pipe, Xs, ys, n_repeats=3, random_state=SEED,
                                      scoring="f1_macro", n_jobs=1)
        pimp = pd.Series(perm.importances_mean, index=X_test.columns).sort_values(ascending=False)
        print("[permutation importance] top 10 (drop in macro-F1 when shuffled):")
        for name, val in pimp.head(10).items():
            print(f"    {name:30s} {val:.4f}")

        pd.DataFrame({"feature": imp.index, "impurity": imp.values}).to_csv(
            f"data/processed/stage6_{path}_impurity.csv", index=False)
        pd.DataFrame({"feature": pimp.index, "perm_importance": pimp.values}).to_csv(
            f"data/processed/stage6_{path}_permutation.csv", index=False)

        # ---- 6.1 reproducibility: train again, predictions must match exactly ----
        pipe2 = make_pipeline().fit(X_train, y_train)
        identical = bool((pipe2.predict(X_test) == pred).all())
        print(f"[reproducibility] same seed -> identical predictions: {identical}")

        cost_rows.append({"path": path, "train (s)": round(train_s, 1),
                          f"inference (s, {len(X_test)} rows)": round(infer_s, 2),
                          "rows/sec": f"{throughput:,.0f}", "model size (MB)": round(size_mb, 0),
                          "reproducible": identical})

        # free memory before the next path (models are large)
        del pipe, pipe2, rf, X_train, X_test, tr, te
        gc.collect()

    pd.DataFrame(cost_rows).to_csv("data/processed/stage6_cost.csv", index=False)


if __name__ == "__main__":
    main()
