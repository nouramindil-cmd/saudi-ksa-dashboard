"""
محلّلات الملفات الخام → أرقام بالمناطق الإدارية الثلاث عشرة.
كل محلّل يرجّع قائمة «مقاييس»: {key, name, unit, values:{region:number}, period}
"""
import csv
import re
import warnings
from pathlib import Path

import openpyxl

warnings.filterwarnings("ignore")

REGIONS = ["الرياض", "مكة المكرمة", "المدينة المنورة", "القصيم", "المنطقة الشرقية", "عسير", "تبوك", "حائل",
           "الحدود الشمالية", "جازان", "نجران", "الباحة", "الجوف"]

_ALIASES = {
    "المدينة المنوره": "المدينة المنورة", "المدينه المنوره": "المدينة المنورة", "المدينة": "المدينة المنورة",
    "الشرقية": "المنطقة الشرقية", "الشرقيه": "المنطقة الشرقية", "مكة": "مكة المكرمة", "مكه المكرمه": "مكة المكرمة",
    "مكة المكرّمة": "مكة المكرمة", "الحدود الشماليه": "الحدود الشمالية", "الباحه": "الباحة", "جيزان": "جازان",
    "منطقة الرياض": "الرياض", "منطقة مكة المكرمة": "مكة المكرمة", "منطقة المدينة المنورة": "المدينة المنورة",
    "منطقة القصيم": "القصيم", "المنطقة الشرقيه": "المنطقة الشرقية", "منطقة عسير": "عسير", "منطقة تبوك": "تبوك",
    "منطقة حائل": "حائل", "منطقة الحدود الشمالية": "الحدود الشمالية", "منطقة جازان": "جازان",
    "منطقة نجران": "نجران", "منطقة الباحة": "الباحة", "منطقة الجوف": "الجوف",
}

# أمانات وزارة البلديات → المنطقة الإدارية
AMANAH_TO_REGION = {
    "العاصمة المقدسة": "مكة المكرمة", "جده": "مكة المكرمة", "جدة": "مكة المكرمة", "الطائف": "مكة المكرمة",
    "المدينة المنوره": "المدينة المنورة", "المدينة المنورة": "المدينة المنورة",
    "الرياض": "الرياض", "القصيم": "القصيم", "الشرقية": "المنطقة الشرقية", "الاحساء": "المنطقة الشرقية",
    "الأحساء": "المنطقة الشرقية", "عسير": "عسير", "تبوك": "تبوك", "حائل": "حائل", "الحدود الشمالية": "الحدود الشمالية",
    "جازان": "جازان", "نجران": "نجران", "الباحة": "الباحة", "الجوف": "الجوف",
}


def norm_region(s):
    if s is None:
        return None
    t = re.sub(r"\s+", " ", str(s)).strip().replace("ـ", "")
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا") if False else t
    if t in REGIONS:
        return t
    if t in _ALIASES:
        return _ALIASES[t]
    for k, v in _ALIASES.items():
        if t.replace("ة", "ه") == k.replace("ة", "ه"):
            return v
    return None


def amanah_region(name):
    t = re.sub(r"\s+", " ", str(name or "")).strip()
    if not t.startswith("أمانة") and not t.startswith("امانة"):
        return None
    t = re.sub(r"^(أمانة|امانة)\s+(منطقة|محافظة)?\s*", "", t)
    for k, v in AMANAH_TO_REGION.items():
        if t.startswith(k):
            return v
    return None


def num(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("٬", "").strip()
    s = s.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    try:
        return float(s)
    except ValueError:
        return None


def _rows(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        alt = [s for s in wb.sheetnames if s.strip() == sheet.strip()]
        if not alt:
            wb.close()
            raise KeyError(f"sheet {sheet} not in {path}")
        sheet = alt[0]
    rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    wb.close()
    return rows


def _period_from_rows(rows, fallback=None):
    txt = " ".join(str(c) for r in rows[:8] for c in r if c)
    q = re.search(r"الربع (الأول|الثاني|الثالث|الرابع)\D{0,20}(20\d\d)", txt)
    if q:
        return f"{q.group(2)} {('الربع ' + q.group(1))}"
    y = re.search(r"(20\d\d)", txt)
    return y.group(1) if y else fallback


# ---------- 1) جداول «على مستوى المسمى السكاني» (إحصاءات الخدمات): نجمع كل الصفوف لكل منطقة ----------
def services_sum(path, sheet, cols, period=None):
    """cols: {اسم العمود كما في الترويسة (جزء منه): (key, name)} ; يجمع القيم لكل منطقة."""
    rows = _rows(path, sheet)
    hdr_i = next(i for i, r in enumerate(rows) if r and any(str(c).strip() == "المنطقة الإدارية" for c in r if c))
    # الترويسة قد تمتد على صفّين (مرحلة / مدارس-فصول)
    h1 = [str(c).strip() if c else "" for c in rows[hdr_i]]
    h2 = [str(c).strip() if c else "" for c in rows[hdr_i + 1]] if hdr_i + 1 < len(rows) else []
    merged, last = [], ""
    for j in range(max(len(h1), len(h2))):
        a = h1[j] if j < len(h1) else ""
        b = h2[j] if j < len(h2) else ""
        if a:
            last = a
        merged.append((last + " " + b).strip() if b and num(b) is None else (a or last))
    two_row = any(h2) and all(num(x) is None for x in h2 if x) and sum(1 for x in h2 if x) > 2
    data_start = hdr_i + (2 if two_row else 1)
    out = {}
    for label, (key, name) in cols.items():
        if label.startswith("*"):  # اجمع كل الأعمدة التي تحوي النص (مثل كل أعمدة «مدارس» عبر المراحل)
            js = [j for j, h in enumerate(merged) if label[1:] in h]
        else:
            j = next((j for j, h in enumerate(merged) if label in h), None)
            js = [j] if j is not None else []
        if not js:
            continue
        vals = {r: 0.0 for r in REGIONS}
        for r in rows[data_start:]:
            reg = norm_region(r[1]) if len(r) > 1 else None
            if not reg:
                continue
            for j in js:
                v = num(r[j]) if j < len(r) else None
                if v is not None:
                    vals[reg] += v
        out[key] = {"key": key, "name": name, "values": vals, "period": period or _period_from_rows(rows)}
    return list(out.values())


# ---------- 4) ملفات سجلّية (صف لكل منشأة/مستفيد): عدّ أو جمع حسب عمود المنطقة ----------
def records_by_region(path, region_label, key, name, sum_label=None, period=None, sheet=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    hdr = None
    vals = {r: 0.0 for r in REGIONS}
    for r in rows:
        cells = [str(c).strip() if c is not None else "" for c in r]
        if hdr is None:
            if any(region_label == c or region_label in c for c in cells):
                hdr = cells
                rj = next(j for j, c in enumerate(cells) if region_label == c or region_label in c)
                sj = next((j for j, c in enumerate(cells) if sum_label and sum_label in c), None)
            continue
        reg = norm_region(cells[rj]) if rj < len(cells) else None
        if not reg:
            continue
        if sj is None:
            vals[reg] += 1
        else:
            v = num(cells[sj]) if sj < len(cells) else None
            if v is not None:
                vals[reg] += v
    wb.close()
    return [{"key": key, "name": name, "values": vals, "period": period}]


# ---------- 5) جداول الأمانات في Excel (سدايا/البلديات) ----------
def amanah_xlsx(path, cols, period=None, sheet=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    rows = [[str(c).strip() if c is not None else "" for c in r] for r in ws.iter_rows(values_only=True)]
    wb.close()
    hdr_i = next(i for i, r in enumerate(rows) if any("الجهة" in c for c in r))
    hdr = rows[hdr_i]
    name_col = next(j for j, h in enumerate(hdr) if "الجهة" in h)
    yr = re.search(r"(20\d\d)", " ".join(rows[0]))
    out = {}
    for label, (key, name) in cols.items():
        j = next((j for j, h in enumerate(hdr) if label in h), None)
        if j is None:
            continue
        vals = {r: 0.0 for r in REGIONS}
        for r in rows[hdr_i + 1:]:
            if len(r) <= max(j, name_col):
                continue
            reg = amanah_region(r[name_col])
            if not reg:
                continue
            v = num(r[j])
            if v is not None:
                vals[reg] += v
        out[key] = {"key": key, "name": name, "values": vals, "period": period or (yr.group(1) if yr else None)}
    return list(out.values())


# ---------- 2) جدول بسيط: المنطقة في العمود الأول وأعمدة رقمية ----------
def region_table(path, sheet, cols, region_col=0, period=None):
    """cols: {رقم العمود أو جزء من اسم الترويسة: (key, name)}"""
    rows = _rows(path, sheet)
    hdr_i = next((i for i, r in enumerate(rows) if r and any(norm_region(c) for c in r[:2])), None)
    if hdr_i is None:
        return []
    # ترويسة = آخر صف نصي قبل أول منطقة (قد تكون سطرين)
    header_rows = [[str(c).strip() if c else "" for c in r] for r in rows[max(0, hdr_i - 3):hdr_i]]
    out = {}
    for sel, (key, name) in cols.items():
        if isinstance(sel, int):
            j = sel
        else:
            j = None
            for hr in header_rows:
                for jj, h in enumerate(hr):
                    if sel in h:
                        j = jj
            if j is None:
                continue
        vals = {}
        for r in rows[hdr_i:]:
            reg = norm_region(r[region_col]) if len(r) > region_col else None
            if not reg and region_col == 0 and len(r) > 1:
                reg = norm_region(r[1])
            if not reg:
                continue
            v = num(r[j]) if j < len(r) else None
            if v is not None:
                vals[reg] = v
        out[key] = {"key": key, "name": name, "values": vals, "period": period or _period_from_rows(rows)}
    return list(out.values())


# ---------- 3) ملفات وزارة البلديات (CSV بفاصلة منقوطة، صفوف الأمانات) ----------
def momah_csv(path, cols, period=None):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1256", "utf-16"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(txt.splitlines(), delimiter=";"))
    title = rows[0][0] if rows and rows[0] else ""
    yr = re.search(r"(20\d\d)", title)
    period = period or (yr.group(1) if yr else None)
    hdr_i = next(i for i, r in enumerate(rows) if any("الجهة" in c for c in r))
    hdr = [re.sub(r"\s+", " ", c).strip() for c in rows[hdr_i]]
    name_col = next(j for j, h in enumerate(hdr) if "الجهة" in h)
    out = {}
    for label, (key, name) in cols.items():
        j = next((j for j, h in enumerate(hdr) if label in h), None)
        if j is None:
            continue
        vals = {r: 0.0 for r in REGIONS}
        for r in rows[hdr_i + 1:]:
            if len(r) <= max(j, name_col):
                continue
            reg = amanah_region(r[name_col])
            if not reg:
                continue
            v = num(r[j])
            if v is not None:
                vals[reg] += v
        out[key] = {"key": key, "name": name, "values": vals, "period": period}
    return list(out.values())
