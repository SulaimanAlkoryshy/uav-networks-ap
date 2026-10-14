# DATASET — AP (Case 2), what we are working on

This file describes the **Access Point scenario** of UAV-NIDD and what our cleaning does.
For the general report plan see `REPORT-NOTES.md`; for the honesty rules see `ML-METHODOLOGY.md`.

## What AP is
AP = **Case 2 = UAV-to-Access-Point** traffic: the capture taken when the **access point is the
compromised point** of the network (it intercepts the traffic).

- Source file: `data/raw/Access Point Case2 Label.xlsx` (inside `UAV-NDD CSV.zip`, Zenodo 15125851).
- Converted once to `data/processed/ap_raw.csv` by `src/convert_ap_xlsx_to_csv.py`
  → **631,356 rows × 51 columns** (50 features + label).

## AP at a glance
| | AP (Case 2) |
|---|---|
| level | **packet** fields (radiotap / 802.11 / IP / UDP / HTTP), like the AWID Wi-Fi datasets |
| rows | 631,356 |
| features | 50 |
| label column | **`Normal`** (header lost) → renamed `Class` |
| normal class | `Normal`, 129,541 rows (~20%) — not rare |
| rarest class | **Reconnaissance, 40 rows** |
| classes | **10 attacks + Normal** |

## Data-quality problems found (and what we do)
1. **Label header is broken** — the label column is called `Normal`. Renamed to `Class`.
2. **Typo in a class name** — `Ewil Twin` → fixed to `Evil Twin`.
3. **Column headers are shifted against their contents.** Examples (checked on real rows):
   - `frame.time_relative` holds the **epoch timestamp** (e.g. 1507828733.8).
   - `radiotap.channel.flags.cck` holds **time since capture start**.
   - `radiotap.datarate` holds the **channel frequency** (2437 / 2412 MHz).
   - `radiotap.rxflags` holds the radio's **microsecond clock** (TSF).
   - `ip.proto` / `ip.ttl` / `ip.dst` hold **IP addresses** in many rows.
   So column names are not trustworthy; we judge columns by their contents.
4. **Mixed text in numeric columns** — hex (`0x0000`) is parsed to a number; other text (IPs,
   host names, raw payload hex) becomes **-1**.
   *Why not just drop those rows?* Because it would delete **100%** of Evil Twin, MITM,
   Reconnaissance and Replay (and 67% of DoS). Measured, not assumed.
5. **One constant column** — `wlan.fc.protected` → dropped.
6. **117 duplicate rows** — kept (tiny; packet captures repeat legitimately).

## Classes (after cleaning)
| Class | Rows |
|---|---:|
| Brute-Force | 172,509 |
| De-authentication | 155,564 |
| Normal | 129,541 |
| Scanning | 70,319 |
| DDoS | 31,612 |
| Fake Landing | 24,584 |
| DoS | 23,612 |
| Evil Twin | 10,034 |
| Replay | 8,525 |
| MITM | 5,016 |
| Reconnaissance | **40** |

Imbalance ≈ **4,300 : 1** (Brute-Force vs Reconnaissance).

## Leakage found in AP (the important part)
### 1) Time / order columns (removed in PATH search)
A decision tree using **one column only** (`stage1_shortcut_check.csv`):

| column (really holds) | macro-F1 alone |
|---|---:|
| `frame.time_relative` (epoch timestamp) | **0.923** |
| `radiotap.channel.flags.cck` (time since start) | 0.614 |
| `radiotap.rxflags` (radio clock) | 0.344 |
| `frame.number` (packet index) | 0.279 |

Each attack was captured in its own session, so **the time says which attack it is**. PATH search drops these 4 + the 4 `ip.*` columns.
PATH report's ANOVA selected **7 of the 8** (the 8th was removed by PCC as a near-copy).

### 2) Normal was captured differently (cannot be removed by dropping a column)
`frame.encap_type = 23` on **every** Normal packet and on **no** attack packet; attack packets
have 0 / 1 / 20. The Normal traffic was recorded with a different capture setup. Dropping the 6
strongest columns still leaves binary macro-F1 = 0.93 (`stage3_capture_check.csv`), so the
difference runs through the whole Normal capture. **Consequence: the AP binary score (≈1.000)
measures "which capture is this", not real normal-vs-attack detection.** Reported honestly, not hidden.
