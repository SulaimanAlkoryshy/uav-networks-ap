<div dir="rtl">

# دليل الفريق — Git و GitHub خطوة بخطوة

هذا شرح مختصر لطريقة شغلنا كفريق على المشروع. الأوامر جاهزة تنسخها وتلصقها (copy–paste)، وبدّل أي شي بين `<...>` ببياناتك.

> **القاعدة الأساسية:** لا ترفع على `main` مباشرة. الخطوات دايمًا: اسحب آخر تحديث، بعدين سوّ branch، اشتغل، ارفع، وافتح Pull Request.

---

## 0) مرة وحدة بس (Setup)

**١. ثبّت الأدوات:** Git و GitHub CLI و Python 3.12 و VS Code.

```bash
winget install Git.Git GitHub.cli Python.Python.3.12 Microsoft.VisualStudioCode
```

**٢. عرّف نفسك لـ git:**
```bash
git config --global user.name "<اسمك>"
git config --global user.email "<إيميلك في GitHub>"
```

**٣. سجّل دخولك في GitHub** (يفتح لك المتصفح، وتنسخ فيه الكود اللي يطلع لك):
```bash
gh auth login
```

**٤. انسخ المشروع لجهازك (clone) وافتحه في VS Code:**
```bash
gh repo clone SulaimanAlkoryshy/uav-networks-ap
cd uav-networks-ap
code .
```

**٥. جهّز بيئة Python:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**٦. الداتا** (مرة وحدة): الأمر الأول ينزّل الداتا من Zenodo، والثاني يحوّلها لـ CSV:
```bash
python src/download_data.py
python src/convert_ap_xlsx_to_csv.py
```

---

## 1) الروتين اليومي

**١. حدّث نسختك قبل أي شي:**
```bash
git checkout main
git pull
```

**٢. سوّ branch جديد باسم مهمتك:**
```bash
git checkout -b <اسم-المهمة>
```

**٣. اشتغل، وبعدها احفظ تغييراتك (commit):**
```bash
git add .
git commit -m "<وصف واضح للي سويته>"
```

**٤. ارفع الـ branch:**
```bash
git push -u origin <اسم-المهمة>
```

**٥. افتح Pull Request عشان صاحب الريبو يراجع شغلك:**
```bash
gh pr create --fill
```

---

## 2) أوامر تحتاجها كثير

```bash
git status            # وش الملفات اللي تغيّرت
git diff              # الفروقات بالتفصيل
git log --oneline     # سجل الـ commits باختصار
git pull              # نزّل آخر التحديثات
git branch            # الـ branches اللي عندك
git checkout <branch> # انتقل لـ branch ثاني
```

---

## 3) تشغيل المشروع

```bash
python src/run_all.py                 # يشغّل المراحل كلها ويطلع results.html
python src/stage4_multiclass.py       # أو مرحلة وحدة بس
```

- النتائج تنحفظ في `data/processed/` وفي `results.html`.
- المراحل الثقيلة تاخذ دقائق. **لا تشغّل** `permutation_importance` بـ `n_jobs=-1` (يستهلك الرام كلها).

---

## 4) قواعد الشغل

- **كود بسيط ومقروء:** ملف واحد لكل مرحلة، وكل خطوة لها عنوان `# ===== STEP n — ... =====`.
- **لا ترفع الداتا:** مجلد `data/` موجود في `.gitignore`.
- **أي رقم تكتبه في docs لازم يجي من تشغيل حقيقي**، وتسجّله في `docs/BUILD-LOG.md`.
- **قبل ما تبدأ اقرأ `docs/STATE.md`** عشان تعرف وين وقف الشغل.

</div>
