"""
Stage 1 — preprocessing for the Access Point scenario (AP / Case 2), done TWO WAYS so we can
compare them later.

We carry two paths through the whole project:
    PATH "report"  = exactly what the GP report says.
    PATH "search"  = my own research-based version (may differ from the report).

For Stage 1 the two paths differ in TWO places (everything else is identical):

                          PATH report              PATH search
    id + time columns     encode & keep            drop them (shortcut leakage)
    feature ranking       ANOVA F-score top-25     RandomForest importance top-25
    train/test split      SAME stratified 80/20 in both  <- kept identical for a fair comparison
    PCC |corr|>0.85       SAME in both

Why AP is different from GSC (see docs/DATASET-AP.md):
  - AP is PACKET-level Wi-Fi data (radiotap / wlan / ip fields), not flow statistics.
  - The label column has no proper header: it is called "Normal". We rename it to "Class".
  - The column headers do not match their contents (shifted), and some cells hold IP addresses,
    hex values ("0x0000") or host names.
  - Time/order columns leak the answer: the capture timestamp ALONE gives macro-F1 ~0.92,
    because each attack was recorded in its own session. These are dropped in PATH search.
  - Rows with text cells can NOT be dropped: that would delete 100% of Evil Twin, MITM,
    Reconnaissance and Replay. So unparsable text is set to -1 instead.

Run it:
    python src/stage1_preprocess.py
(First make data/processed/ap_raw.csv once with:  python src/convert_ap_xlsx_to_csv.py)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

RAW_CSV = "data/processed/ap_raw.csv"
RAW_LABEL = "Normal"                              # the label column's (broken) header in the file
LABEL = "Class"                                   # what we rename it to
LABEL_FIXES = {"Ewil Twin": "Evil Twin"}          # typo in the source file

# columns that hold IP addresses (headers are shifted, so ip.proto / ip.ttl really hold IPs)
ID_COLS = ["ip.dst", "ip.proto", "ip.src", "ip.ttl"]
# columns that hold the capture time / packet order (headers shifted too — see DATASET-AP.md):
#   frame.number               = packet index in the capture
#   frame.time_relative        = really the epoch timestamp (alone -> macro-F1 0.92!)
#   radiotap.channel.flags.cck = really time since capture start
#   radiotap.rxflags           = really the radio's microsecond clock (TSF)
TIME_COLS = ["frame.number", "frame.time_relative", "radiotap.channel.flags.cck", "radiotap.rxflags"]
SHORTCUT_COLS = ID_COLS + TIME_COLS

SEED = 42
TEST_SIZE = 0.20
CORR_THRESHOLD = 0.85
TOP_K = 25
TEXT_VALUE = -1          # what an unparsable text cell becomes

# the two paths, described as simple settings
PATHS = {
    "report": {"drop_shortcuts": False, "ranker": "anova"},
    "search": {"drop_shortcuts": True,  "ranker": "tree"},
}
RANKER_SAMPLE = 150000   # for the tree ranker: fit importance on a stratified sample (speed)
SHORTCUT_SAMPLE = 150000 # rows used by the one-column shortcut check


# ---------- shared steps (same for both paths) -------------------------------------------

# ==========================================================================
# STEP 1 — load_ap()
# ==========================================================================
def load_ap(path=RAW_CSV):
    # read everything as text first: many columns mix numbers, hex and IPs
    return pd.read_csv(path, low_memory=False, dtype=str)


# ==========================================================================
# STEP 2 — to_number(): one column of text -> numbers
# ==========================================================================
def to_number(col):
    """'0x00a1' -> 161 (hex), '12.0' -> 12.0, anything else (IP, host name) -> NaN."""
    is_hex = col.str.match(r"^0x[0-9a-fA-F]+$", na=False)
    out = pd.to_numeric(col.where(~is_hex), errors="coerce")
    out[is_hex] = col[is_hex].apply(lambda v: int(v, 16))
    return out


# ==========================================================================
# STEP 3 — clean_common()
# ==========================================================================
def clean_common(df):
    """Clean that both paths share: fix label, make numeric, drop constant columns."""
    df = df.rename(columns={RAW_LABEL: LABEL})
    df[LABEL] = df[LABEL].astype(str).str.strip().replace(LABEL_FIXES)

    # make feature columns numeric, but leave the id columns alone for now (paths handle them)
    text_cells = 0
    for c in df.columns:
        if c != LABEL and c not in ID_COLS:
            num = to_number(df[c])
            text_cells += int(num.isna().sum())
            df[c] = num.replace([np.inf, -np.inf], np.nan).fillna(TEXT_VALUE)
    print(f"  text/unparsable cells set to {TEXT_VALUE}: {text_cells}")

    # drop constant numeric columns (one value = no information)
    numeric_feats = [c for c in df.columns if c not in ID_COLS + [LABEL]]
    constant = [c for c in numeric_feats if df[c].nunique() <= 1]
    print(f"  constant columns dropped: {constant}")
    return df.drop(columns=constant)


# ==========================================================================
# STEP 4 — pcc_columns_to_drop()
# ==========================================================================
def pcc_columns_to_drop(X_train, threshold=CORR_THRESHOLD):
    """Drop features that are near-copies of another (|corr| > threshold)."""
    corr = X_train.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    return [col for col in upper.columns if (upper[col] > threshold).any()]


# ---------- the parts that DIFFER between paths ------------------------------------------

# ==========================================================================
# STEP 5 — build_features()
# ==========================================================================
def build_features(df, drop_shortcuts):
    """Decide what to do with the id + time columns, then return X and y."""
    df = df.copy()
    if drop_shortcuts:
        X = df.drop(columns=[c for c in SHORTCUT_COLS if c in df.columns] + [LABEL])  # PATH search
    else:
        # PATH report: keep them; id columns hold IP text, so turn each value into a number
        for c in ID_COLS:
            df[c] = pd.factorize(df[c])[0]
        X = df.drop(columns=[LABEL])
    y = df[LABEL]
    return X, y


# ==========================================================================
# STEP 6 — rank_features()
# ==========================================================================
def rank_features(X_train, y_train, how, k=TOP_K):
    """Pick the top-k features the chosen way."""
    k = min(k, X_train.shape[1])
    if how == "anova":
        selector = SelectKBest(score_func=f_classif, k=k).fit(X_train, y_train)
        return list(X_train.columns[selector.get_support()])
    # how == "tree": train a small Random Forest and take the k most important features.
    # We fit on a stratified sample (not all 500k rows) just to rank features quickly.
    Xr, yr = X_train, y_train
    if len(X_train) > RANKER_SAMPLE:
        Xr, _, yr, _ = train_test_split(
            X_train, y_train, train_size=RANKER_SAMPLE, random_state=SEED, stratify=y_train
        )
    rf = RandomForestClassifier(
        n_estimators=100, random_state=SEED, n_jobs=-1, class_weight="balanced"
    )
    rf.fit(Xr, yr)
    importance = pd.Series(rf.feature_importances_, index=X_train.columns)
    return list(importance.sort_values(ascending=False).head(k).index)


# ---------- run one path end to end ------------------------------------------------------

# ==========================================================================
# STEP 7 — run_path()
# ==========================================================================
def run_path(name, cfg, df_clean):
    print(f"\n=== PATH '{name}'  ({cfg}) ===")
    X, y = build_features(df_clean, cfg["drop_shortcuts"])
    print(f"  features after id/time handling: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y
    )
    print(f"  split: train {len(X_train)} / test {len(X_test)}")

    drop_cols = pcc_columns_to_drop(X_train)
    X_train, X_test = X_train.drop(columns=drop_cols), X_test.drop(columns=drop_cols)
    print(f"  PCC dropped {len(drop_cols)} -> {X_train.shape[1]} left")

    selected = rank_features(X_train, y_train, cfg["ranker"])
    X_train, X_test = X_train[selected], X_test[selected]
    print(f"  {cfg['ranker']} kept {len(selected)} features")

    # save outputs for this path
    pd.Series(selected).to_csv(f"data/processed/ap_{name}_features.txt", index=False, header=False)
    tr = X_train.copy(); tr[LABEL] = y_train.values
    te = X_test.copy(); te[LABEL] = y_test.values
    tr.to_csv(f"data/processed/ap_{name}_train.csv", index=False)
    te.to_csv(f"data/processed/ap_{name}_test.csv", index=False)
    print(f"  saved ap_{name}_train.csv {tr.shape} / ap_{name}_test.csv {te.shape}")
    print(f"  classes present in test: {te[LABEL].nunique()} of {df_clean[LABEL].nunique()}")
    return set(selected)


# ==========================================================================
# STEP 8 — shortcut_check(): how well does ONE column alone predict the class?
# ==========================================================================
def shortcut_check(df_clean):
    """A plain decision tree on each single column (sample, train-part only). A behaviour feature
    alone should be weak; a column that alone gets a high macro-F1 is a suspected shortcut."""
    df = df_clean.sample(n=min(SHORTCUT_SAMPLE, len(df_clean)), random_state=SEED)
    y = df[LABEL]
    rows = []
    for c in df.columns:
        if c == LABEL:
            continue
        x = df[[c]].copy()
        if c in ID_COLS:
            x[c] = pd.factorize(x[c])[0]          # IP text -> number
        Xtr, Xte, ytr, yte = train_test_split(x, y, test_size=0.3, random_state=SEED, stratify=y)
        pred = DecisionTreeClassifier(random_state=SEED).fit(Xtr, ytr).predict(Xte)
        rows.append({"column": c, "macro_f1_alone": round(f1_score(yte, pred, average="macro"), 3),
                     "dropped_in_search": c in SHORTCUT_COLS})
    out = pd.DataFrame(rows).sort_values("macro_f1_alone", ascending=False)
    out.to_csv("data/processed/stage1_shortcut_check.csv", index=False)
    print("\nShortcut check (top 10 single columns):")
    print(out.head(10).to_string(index=False))


# ==========================================================================
# STEP 9 — main()
# ==========================================================================
def main():
    print("Loading + common clean ...")
    df = clean_common(load_ap())
    print(f"  clean shape: {df.shape}  | classes: {df[LABEL].nunique()}")
    print(df[LABEL].value_counts().to_string())

    shortcut_check(df)

    selected = {name: run_path(name, cfg, df) for name, cfg in PATHS.items()}

    both = selected["report"] & selected["search"]
    print(f"\nFeatures chosen by BOTH paths: {len(both)}")
    print(f"Only report: {sorted(selected['report'] - selected['search'])}")
    print(f"Only search: {sorted(selected['search'] - selected['report'])}")


if __name__ == "__main__":
    main()
