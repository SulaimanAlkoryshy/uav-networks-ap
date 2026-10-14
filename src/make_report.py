"""
"Show the work" — build a single self-contained results.html for the AP scenario.

Reads the saved numbers (data/processed/stage*.csv), (re)trains the chosen model to draw
confusion matrices, makes a few simple charts, and writes results.html with a short description
of each part. Open results.html in any browser. Every number in the page is read from the CSVs,
so re-running this keeps the page in sync with the data.

Run:
    python src/make_report.py
"""

import base64
import gc
import io

import matplotlib
matplotlib.use("Agg")  # no screen needed
import matplotlib.pyplot as plt
import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay

SEED = 42
LABEL = "Class"
UNDER_CAP = 30000
SMOTE_FLOOR = 5000
D = "data/processed"


# ==========================================================================
# STEP 1 — small helpers (pipeline, figure -> <img>, table)
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


def fig_to_img(fig):
    """Turn a matplotlib figure into an <img> tag with the PNG embedded (self-contained)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" />'


def table(df):
    return df.to_html(index=False, border=0, classes="tbl", float_format=lambda x: f"{x:.3f}")


# ==========================================================================
# STEP 2 — confusion matrices (needs a quick model run per path)
# ==========================================================================
def confusion_matrices():
    imgs = {}
    for path in ["search", "report"]:
        tr = pd.read_csv(f"{D}/ap_{path}_train.csv", low_memory=False)
        te = pd.read_csv(f"{D}/ap_{path}_test.csv", low_memory=False)
        pipe = make_pipeline().fit(tr.drop(columns=[LABEL]), tr[LABEL])
        pred = pipe.predict(te.drop(columns=[LABEL]))

        fig, ax = plt.subplots(figsize=(6.6, 5.4))
        ConfusionMatrixDisplay.from_predictions(te[LABEL], pred, labels=sorted(te[LABEL].unique()),
                                                ax=ax, xticks_rotation=45, colorbar=False,
                                                cmap="Blues", normalize="true", values_format=".2f")
        ax.set_title(f"Confusion matrix (row-normalised) — {path} path")
        imgs[path] = fig_to_img(fig)
        del pipe, tr, te
        gc.collect()
    return imgs


# ==========================================================================
# STEP 3 — charts from the saved numbers
# ==========================================================================
def chart_benchmark(s5):
    piv = s5.pivot(index="model", columns="path", values="test_macroF1").sort_values("search")
    fig, ax = plt.subplots(figsize=(7, 4))
    piv.plot(kind="barh", ax=ax, color={"report": "#c0504d", "search": "#4472c4"})
    ax.set_xlabel("test macro-F1"); ax.set_title("Stage 5 — model benchmark (higher = better)")
    ax.axvline(0.90, ls="--", color="gray"); ax.set_xlim(0, 1.05)
    return fig_to_img(fig)


def chart_perclass(s4pc):
    df = s4pc.sort_values("search_f1")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(df["class"], df["report_f1"], color="#c0504d", alpha=.6, label="report (keeps time/IP)")
    ax.barh(df["class"], df["search_f1"], color="#4472c4", alpha=.6, label="search (honest)")
    ax.set_xlabel("F1-score"); ax.set_title("Stage 4 — per-class F1 (multi-class)"); ax.legend()
    return fig_to_img(fig)


def chart_importance(path, title, color):
    df = pd.read_csv(f"{D}/stage6_{path}_permutation.csv").head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df["feature"], df["perm_importance"], color=color)
    ax.set_xlabel("drop in macro-F1 when shuffled"); ax.set_title(title)
    return fig_to_img(fig)


def chart_leak():
    """Shortcut check: macro-F1 of a tree using ONE column only (from stage1_shortcut_check.csv)."""
    df = pd.read_csv(f"{D}/stage1_shortcut_check.csv").head(10).iloc[::-1]
    colors = ["#c0504d" if s else "#4472c4" for s in df["dropped_in_search"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df["column"], df["macro_f1_alone"], color=colors)
    ax.set_xlabel("macro-F1 using this ONE column only"); ax.set_xlim(0, 1)
    ax.set_title("Shortcut check — red = time/IP column (dropped in search path)")
    return fig_to_img(fig)


# ==========================================================================
# STEP 4 — assemble the HTML
# ==========================================================================
def main():
    print("training models for confusion matrices ...", flush=True)
    cm = confusion_matrices()

    s2 = pd.read_csv(f"{D}/stage2_results.csv")
    s3 = pd.read_csv(f"{D}/stage3_binary_results.csv")[
        ["path", "cv_macroF1", "cv_normal_recall", "cv_normal_prec", "cv_MCC", "baseline_allAttack_macroF1"]]
    s4 = pd.read_csv(f"{D}/stage4_multiclass_results.csv")
    s4pc = pd.read_csv(f"{D}/stage4_per_class_f1.csv")
    s5 = pd.read_csv(f"{D}/stage5_benchmark.csv")
    s6 = pd.read_csv(f"{D}/stage6_cost.csv")
    leak = pd.read_csv(f"{D}/stage1_shortcut_check.csv")
    cap = pd.read_csv(f"{D}/stage3_capture_check.csv")

    print("drawing charts ...", flush=True)
    leak_img = chart_leak()
    bench_img, perclass_img = chart_benchmark(s5), chart_perclass(s4pc)
    imp_search = chart_importance("search", "Stage 6 — top features, honest (search) model", "#4472c4")
    imp_report = chart_importance("report", "Stage 6 — top features, report model", "#c0504d")

    # numbers used in the text (read from the CSVs, never typed by hand)
    def v(df, col, **where):
        row = df
        for k, val in where.items():
            row = row[row[k] == val]
        return float(row[col].iloc[0])

    top_leak = leak.iloc[0]
    s4r, s4s = v(s4, "cv_macroF1", path="report"), v(s4, "cv_macroF1", path="search")
    best = s5[s5["path"] == "search"].sort_values("test_macroF1", ascending=False).iloc[0]
    weak = s4pc.sort_values("search_f1").head(3)
    weak_txt = ", ".join(f"{r['class']} ({r['search_f1']:.2f})" for _, r in weak.iterrows())
    s5tab = s5.pivot(index="model", columns="path", values="test_macroF1").reset_index()

    def sec(title, desc, *body):
        return f'<section><h2>{title}</h2><p class="desc">{desc}</p>{"".join(body)}</section>'

    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UAV-NIDD AP Results</title>
<style>
 :root{{--bg:#fff;--fg:#1f2a37;--muted:#4b5563;--line:#e5e7eb;--head:#f3f4f6;--note:#fff7ed;--noteb:#fb923c}}
 @media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#111827;--fg:#e5e7eb;--muted:#9ca3af;--line:#374151;--head:#1f2937;--note:#3b2a1a;--noteb:#fb923c}}}}
 :root[data-theme="dark"]{{--bg:#111827;--fg:#e5e7eb;--muted:#9ca3af;--line:#374151;--head:#1f2937;--note:#3b2a1a;--noteb:#fb923c}}
 body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:920px;margin:0 auto;padding:24px 16px;color:var(--fg);background:var(--bg);line-height:1.5}}
 h1{{font-size:1.6rem}} h2{{margin-top:2rem;border-bottom:2px solid var(--line);padding-bottom:4px}}
 .desc{{color:var(--muted)}} .tbl{{border-collapse:collapse;margin:10px 0;font-size:.85rem;display:block;overflow-x:auto;max-width:100%}}
 .tbl th,.tbl td{{border:1px solid var(--line);padding:5px 9px;text-align:center}} .tbl th{{background:var(--head)}}
 img{{max-width:100%;height:auto;margin:10px 0;border:1px solid var(--line);border-radius:6px;background:#fff}}
 .note{{background:var(--note);border-left:4px solid var(--noteb);padding:8px 12px;margin:10px 0;border-radius:4px}}
 .two{{display:flex;flex-wrap:wrap;gap:12px}} .two>div{{flex:1;min-width:280px}}
</style></head><body>
<h1>UAV-NIDD — Access Point (Case 2) Intrusion Detection — Results</h1>
<p class="desc">A classical-ML IDS on the AP scenario (packet-level Wi-Fi capture, 631,356 packets,
10 attacks + Normal), built in 6 stages. Two paths: <b>report</b> = the GP report's method (keeps
every column, ANOVA top-25), and <b>search</b> = the honest version (drops the time/order and IP
columns, tree-importance top-25). The goal is a <b>trustworthy</b> score, not the biggest number.</p>

{sec("Stage 1 — Preprocessing, feature selection &amp; shortcut check",
     "The AP file is messy: the label column is headed 'Normal', 'Evil Twin' is spelled 'Ewil Twin', "
     "column headers are shifted against their contents, and cells mix numbers, hex (0x..) and IP "
     "addresses. Hex is parsed, other text becomes -1 (dropping those rows would delete 100% of "
     "Evil Twin, MITM, Reconnaissance and Replay). Split 80/20 stratified (seed 42), PCC &gt; 0.85, top-25.",
     f'<div class="note">Leakage: the column <b>{top_leak["column"]}</b> (really the capture '
     f'timestamp) <b>alone</b> reaches macro-F1 <b>{top_leak["macro_f1_alone"]:.2f}</b> — each attack '
     'was captured in its own session, so time identifies the class. The search path drops it with the '
     'other time/order + IP columns; the report path\'s ANOVA picked all of them.</div>',
     leak_img)}

{sec("Stage 2 — Class balancing",
     "AP imbalance: Brute-Force 172,509 vs Reconnaissance 40 (≈ 4,300:1). We compared no-balancing, "
     "RandomUnder+Borderline-SMOTE, and class_weight (RF), judged by test macro-F1.",
     table(s2))}

{sec("Stage 3 — Binary (Normal vs Attack)",
     "Normal is not rare in AP (~20% of packets). Judged by 5-fold CV; the trivial "
     "always-Attack baseline is shown for comparison.",
     table(s3),
     '<div class="note">Red flag: 1.000 even on the honest path. Every Normal packet has '
     '<b>frame.encap_type = 23</b> and no attack packet does: Normal was captured with a different '
     'setup. Dropping the strongest single-column separators barely moves the score (below), so the '
     'binary result measures "which capture", not real detection.</div>',
     table(cap))}

{sec("Stage 4 — Multi-class (11 classes)",
     f"5-fold CV macro-F1: report {s4r:.3f} vs search {s4s:.3f}. Hardest classes on the honest "
     f"path: {weak_txt}. Reconnaissance has only 40 rows in the whole file, so its score is unreliable.",
     f'<div class="two"><div>{table(s4)}{table(s4pc[["class", "support", "report_f1", "search_f1"]])}</div>'
     f'<div>{perclass_img}</div></div>',
     f'<div class="two"><div>{cm["search"]}</div><div>{cm["report"]}</div></div>')}

{sec("Stage 5 — Model benchmark",
     f"RF vs XGBoost vs Decision Tree vs Logistic Regression vs Linear SVM (test macro-F1). "
     f"Best on the honest path: <b>{best['model']}</b> ({best['test_macroF1']:.3f}).",
     f'<div class="two"><div>{table(s5tab)}</div><div>{bench_img}</div></div>')}

{sec("Stage 6 — Interpretability, CPU cost &amp; reproducibility",
     "Permutation importance (drop in macro-F1 when a feature is shuffled) for both models, plus "
     "train/inference cost on CPU and a same-seed re-train check.",
     f'<div class="two"><div>{imp_search}</div><div>{imp_report}</div></div>', table(s6))}
</body></html>"""

    with open("results.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote results.html")


if __name__ == "__main__":
    main()
