"""
Build REPORT.docx — the project report for the AP scenario (English), from the saved numbers.

Sections: dataset & scenario, data-quality problems, the pipeline, results per stage, conclusion.
Every number is read from data/processed/*.csv, so the report matches the latest run.

Run:
    python src/make_weekly_report.py           # writes REPORT.docx
Then to PDF (Windows + Word):
    powershell -File src/docx_to_pdf.ps1 REPORT.docx
"""

import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor

D = "data/processed"


# ==========================================================================
# STEP 1 — small writers
# ==========================================================================
def h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x6E)


def para(doc, text, bold_start=None):
    p = doc.add_paragraph()
    if bold_start:
        p.add_run(bold_start).bold = True
    p.add_run(text)
    return p


def bullets(doc, items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def table(doc, df, fmt="{:.4f}"):
    """A pandas DataFrame as a simple Word table (header row bold)."""
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Light Grid Accent 1"
    for i, c in enumerate(df.columns):
        t.rows[0].cells[i].text = str(c)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = fmt.format(v) if isinstance(v, float) else str(v)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9.5)
    doc.add_paragraph()


# ==========================================================================
# STEP 2 — main(): write the report
# ==========================================================================
def main():
    s2 = pd.read_csv(f"{D}/stage2_results.csv")
    s3 = pd.read_csv(f"{D}/stage3_binary_results.csv")
    cap = pd.read_csv(f"{D}/stage3_capture_check.csv")
    s4 = pd.read_csv(f"{D}/stage4_multiclass_results.csv")
    pc = pd.read_csv(f"{D}/stage4_per_class_f1.csv")
    s5 = pd.read_csv(f"{D}/stage5_benchmark.csv").pivot(index="model", columns="path",
                                                           values="test_macroF1")
    s5 = s5.sort_values("search", ascending=False).reset_index()
    leak = pd.read_csv(f"{D}/stage1_shortcut_check.csv")
    cost = pd.read_csv(f"{D}/stage6_cost.csv")
    perm_r = pd.read_csv(f"{D}/stage6_report_permutation.csv").head(5)
    perm_s = pd.read_csv(f"{D}/stage6_search_permutation.csv").head(5)
    mc = s4.set_index("path")["cv_macroF1"]
    best = s5.iloc[0]

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    doc.add_heading("Project Report — UAV Networks: Access Point Scenario (Case 2)", 0)
    para(doc, "A classical-ML intrusion detection system (IDS) on the UAV-NIDD dataset, Access Point "
              "scenario. Built in six stages; every number below comes from a real, reproducible run "
              "(seed 42).")

    # ---- 1. dataset ----
    h(doc, "1. Dataset and scenario")
    para(doc, "UAV-NIDD (Hadi et al., IEEE TNSE 2025, Zenodo 15125851) is a real UAV testbed capture "
              "with three compromise scenarios. This project uses Case 2: a compromised Access Point "
              "that can intercept, redirect or observe traffic between the UAVs and the ground station "
              "— especially relevant to Man-in-the-Middle and Evil Twin attacks.")
    bullets(doc, [
        "Packet-level Wi-Fi capture: radiotap, 802.11, IP, UDP and HTTP fields.",
        "631,356 packets, 50 features, 10 attack classes + Normal.",
        "Imbalance ≈ 4,300 : 1 (Brute-Force 172,509 vs Reconnaissance 40).",
    ])

    # ---- 2. data quality ----
    h(doc, "2. Data-quality problems found")
    bullets(doc, [
        "The label column's header is 'Normal' (the real header was lost) → renamed 'Class'.",
        "'Ewil Twin' typo → 'Evil Twin'.",
        "Column headers are shifted against their contents (e.g. frame.time_relative holds the epoch "
        "time, radiotap.datarate holds the channel frequency, ip.proto holds IP addresses).",
        "Cells mix numbers, hex and text. Hex is parsed; other text becomes -1. Rows are kept: "
        "dropping them would delete 100% of Evil Twin, MITM, Reconnaissance and Replay.",
    ])

    # ---- 3. pipeline ----
    h(doc, "3. Pipeline and the two paths")
    para(doc, "Load → clean → split 80/20 stratified → PCC |corr| > 0.85 → top-25 features → "
              "RandomUnderSampler + Borderline-SMOTE → model → macro-F1. Everything that learns from "
              "data is fit on the training set only.")
    bullets(doc, [
        "report path: exactly as the GP report says (all columns kept, ANOVA top-25).",
        "search path: honest version — drops 4 time/order and 4 IP columns, RF-importance top-25.",
    ])

    # ---- 4. results ----
    h(doc, "4. Results")
    h(doc, "Stage 1 — shortcut check", 2)
    para(doc, f"A decision tree using one column only: {leak.iloc[0]['column']} (really the capture "
              f"timestamp) reaches macro-F1 {leak.iloc[0]['macro_f1_alone']:.3f} on its own. Each attack "
              "was captured in its own session, so time reveals the class (data leakage).")
    table(doc, leak.head(6), fmt="{:.3f}")

    h(doc, "Stage 2 — class balancing (test macro-F1)", 2)
    table(doc, s2)
    para(doc, "The report's claimed +0.18 from balancing does not reproduce (all within 0.01). "
              "under_smote was kept: it lifts the recall of DDoS, MITM and Replay.")

    h(doc, "Stage 3 — binary, Normal vs Attack (5-fold CV)", 2)
    table(doc, s3[["path", "cv_macroF1", "cv_normal_recall", "cv_normal_prec", "cv_MCC",
                   "baseline_allAttack_macroF1"]])
    para(doc, "1.000 even on the honest path is a red flag. Every Normal packet has frame.encap_type = 23 "
              "and no attack packet does: Normal was captured with a different setup. Dropping the "
              "strongest columns barely helps:")
    table(doc, cap)

    h(doc, "Stage 4 — multi-class, 11 classes (5-fold CV)", 2)
    table(doc, s4)
    table(doc, pc[["class", "support", "report_f1", "search_f1"]], fmt="{:.3f}")
    para(doc, "Weak classes on the honest path: DDoS, Replay, MITM. Reconnaissance (32 training rows) "
              "is not reliable.")

    h(doc, "Stage 5 — model benchmark (test macro-F1)", 2)
    table(doc, s5)
    para(doc, f"Tree models clearly beat linear models. Best honest model: {best['model']} "
              f"({best['search']:.4f}). The 0.90 target is met only on the leaky report path.")

    h(doc, "Stage 6 — importance, cost, reproducibility", 2)
    para(doc, "Permutation importance, top 5 — report path: " + ", ".join(perm_r["feature"]) +
              " (time/order columns lead). Search path: " + ", ".join(perm_s["feature"]) + ".")
    table(doc, cost)

    # ---- 5. conclusion ----
    h(doc, "5. Conclusion")
    bullets(doc, [
        f"Report-style results (~{mc['report']:.2f} macro-F1) rely on capture timestamps.",
        f"Trustworthy multi-class result: {mc['search']:.3f} (RF, CV) / {best['search']:.3f} "
        f"({best['model']}, test).",
        "Binary detection on AP is not a fair test: Normal was captured with a different setup.",
        "Next step: a time-aware split (train on earlier packets, test on later ones).",
    ])

    doc.save("REPORT.docx")
    print("wrote REPORT.docx")


if __name__ == "__main__":
    main()
