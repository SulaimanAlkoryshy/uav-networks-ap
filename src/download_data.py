"""
Step 0 — download the UAV-NIDD dataset and keep only the Access Point file.

What it does:
    1. Downloads "UAV-NDD CSV.zip" (~302 MB) from Zenodo record 15125851.
    2. Takes "Access Point Case2 Label.xlsx" out of the zip into data/raw/.
If the files are already there, it skips that part.

Run it once:
    python src/download_data.py
Next step:
    python src/convert_ap_xlsx_to_csv.py
"""

import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://zenodo.org/api/records/15125851/files/UAV-NDD%20CSV.zip/content"
ZIP_PATH = Path("data/raw/UAV-NDD CSV.zip")
AP_NAME = "Access Point Case2 Label.xlsx"
AP_PATH = Path("data/raw") / AP_NAME


# ==========================================================================
# STEP 1 — download the zip (skip if we already have it)
# ==========================================================================
def download_zip():
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        print(f"already have {ZIP_PATH} ({ZIP_PATH.stat().st_size / 1e6:.0f} MB)")
        return
    print(f"downloading {URL}\n  -> {ZIP_PATH} (~302 MB, takes a few minutes) ...")
    with urllib.request.urlopen(URL) as response, open(ZIP_PATH, "wb") as f:
        shutil.copyfileobj(response, f)
    print(f"done ({ZIP_PATH.stat().st_size / 1e6:.0f} MB)")


# ==========================================================================
# STEP 2 — take only the Access Point file out of the zip
# ==========================================================================
def extract_ap():
    if AP_PATH.exists():
        print(f"already have {AP_PATH}")
        return
    with zipfile.ZipFile(ZIP_PATH) as z:
        member = [m for m in z.namelist() if m.endswith(AP_NAME)][0]
        with z.open(member) as src, open(AP_PATH, "wb") as dst:
            shutil.copyfileobj(src, dst)
    print(f"extracted {AP_PATH} ({AP_PATH.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    download_zip()
    extract_ap()
