"""
يبني data/dashboard.json للواجهة من:
  - data/baseline.json  : بيانات الداشبورد القديمة كاملة (لا يسقط أي قسم) + التعداد الثابت
  - data/raw/*          : أحدث الملفات من المصادر، تُحلَّل إلى مقاييس بالمناطق عبر parsers.py
  - data/manifest.json  : تواريخ المصدر والفحص لكل مؤشر
ويحفظ سجل التغيّرات في data/changes.json بمقارنة القيم مع البناء السابق.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import parsers as P

ROOT = Path(__file__).parent
DATA = ROOT / "data"
reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
man = json.loads((DATA / "manifest.json").read_text(encoding="utf-8")) if (DATA / "manifest.json").exists() else {"indicators": {}}
base = json.loads((DATA / "baseline.json").read_text(encoding="utf-8"))


def raw_path(ind_id):
    m = man["indicators"].get(ind_id, {})
    p = m.get("local_path")
    if not p:
        d = DATA / "raw" / ind_id
        files = sorted(d.glob("*")) if d.exists() else []
        return files[0] if files else None
    return ROOT / p


CLUSTER_REGION = [("Riyadh", "الرياض"), ("Makkah", "مكة المكرمة"), ("Jeddah", "مكة المكرمة"), ("Taif", "مكة المكرمة"),
                  ("Madinah", "المدينة المنورة"), ("Qassim", "القصيم"), ("Eastern", "المنطقة الشرقية"), ("Ahsa", "المنطقة الشرقية"),
                  ("Hafr", "المنطقة الشرقية"), ("Aseer", "عسير"), ("Asir", "عسير"), ("Bisha", "عسير"), ("Tabuk", "تبوك"),
                  ("Hail", "حائل"), ("Northern", "الحدود الشمالية"), ("Jazan", "جازان"), ("Najran", "نجران"),
                  ("Baha", "الباحة"), ("Jouf", "الجوف"), ("Qurayyat", "الجوف")]
DIRECTORATE_REGION = {"الاحساء": "المنطقة الشرقية", "الأحساء": "المنطقة الشرقية", "الشرقية": "المنطقة الشرقية",
                      "الطائف": "مكة المكرمة", "جدة": "مكة المكرمة"}


def health_clusters(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))
    wb.close()
    hdr = [str(c).strip() if c else "" for c in rows[0]]
    tj = hdr.index("Total") if "Total" in hdr else len(hdr) - 2
    cj = len(hdr) - 1
    vals = {r: 0.0 for r in P.REGIONS}
    for r in rows[1:]:
        name = str(r[cj] or "")
        reg_ = next((v for k, v in CLUSTER_REGION if k.lower() in name.lower()), None)
        v = P.num(r[tj])
        if reg_ and v is not None:
            vals[reg_] += v
    return [{"key": "phc_visits", "name": "زيارات الرعاية الصحية الأولية (وزارة الصحة)", "values": vals, "period": "2024"}]


def schools_by_directorate(path, key, name):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    vals = {r: 0.0 for r in P.REGIONS}
    seen, period = set(), None
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        d = str(r[2] or "").strip()
        reg_ = DIRECTORATE_REGION.get(d) or P.norm_region(d)
        if not reg_:
            continue
        period = period or str(r[1])
        k = (r[3], r[6])  # الرقم الوزاري + المرحلة = مدرسة-مرحلة
        if k in seen:
            continue
        seen.add(k)
        vals[reg_] += 1
    wb.close()
    return [{"key": key, "name": name, "values": vals, "period": period}]


EN_REGION = {"riyadh": "الرياض", "makkah": "مكة المكرمة", "madinah": "المدينة المنورة", "qassim": "القصيم", "eastern": "المنطقة الشرقية",
             "asir": "عسير", "aseer": "عسير", "tabuk": "تبوك", "hail": "حائل", "northern": "الحدود الشمالية", "jazan": "جازان",
             "najran": "نجران", "baha": "الباحة", "jouf": "الجوف"}


def nonprofit_dir(dirpath):
    """13 ملفاً إقليمياً (المركز الوطني لتنمية القطاع غير الربحي): صف لكل كيان. المنطقة من اسم الورقة أو اسم الملف."""
    import openpyxl
    vals, filled = {r: 0.0 for r in P.REGIONS}, {}
    for f in sorted(Path(dirpath).glob("*")):
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        fn_reg = next((v for k, v in EN_REGION.items() if k in f.name.lower()), None)
        best = None
        for sn in wb.sheetnames:
            rows = list(wb[sn].iter_rows(values_only=True))
            hi = next((i for i, r in enumerate(rows) if r and any("اسم الكيان" in str(c) for c in r if c)), None)
            if hi is None:
                continue
            nj = next(j for j, c in enumerate(rows[hi]) if c and "اسم الكيان" in str(c))
            n = sum(1 for r in rows[hi + 1:] if len(r) > nj and r[nj] and str(r[nj]).strip())
            reg_ = P.norm_region(sn) or P.norm_region(sn.replace("مكة", "مكة المكرمة")) or fn_reg
            if reg_ and (best is None or n > best[1]):
                best = (reg_, n, sn)
        wb.close()
        if best and best[1] > filled.get(best[0], 0):  # ملفان لنفس المنطقة: الأكبر فقط
            filled[best[0]] = best[1]
    vals.update(filled)
    return [{"key": "entities", "name": "الكيانات غير الربحية المسجّلة", "values": vals, "period": "2026"}]


STAGE_NAMES = {"رياض الأطفال": "رياض الأطفال", "المرحلة الإبتدائية": "المرحلة الإبتدائية", "المرحلة الابتدائية": "المرحلة الإبتدائية",
               "المرحلة المتوسطة": "المرحلة المتوسطة", "المرحلة الثانوية": "المرحلة الثانوية"}


def students_directorates(dirpath):
    """ملفات وزارة التعليم (ملف لكل إدارة تعليمية × سنة): سنة، إدارة، مرحلة، سلطة، جنس، سعودي، غير سعودي، إجمالي.
    يرجّع مقياس الطلاب لأحدث سنة + سلسلة سنوية لكل منطقة + تفصيل المراحل لكل سنة (لدمجه في رسوم النسخة الأولى)."""
    import openpyxl
    years = {}   # year -> region -> total
    stages = {}  # year -> region -> stage -> total
    for f in sorted(Path(dirpath).glob("*")):
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            rows = list(wb[sn].iter_rows(values_only=True))
            hi = next((i for i, r in enumerate(rows) if r and any("الإدارة" in str(c) for c in r if c)), None)
            if hi is None:
                continue
            hdr = [str(c).strip() if c else "" for c in rows[hi]]
            try:
                yj = next(j for j, h in enumerate(hdr) if "ميلادي" in h)
                dj = next(j for j, h in enumerate(hdr) if "الإدارة" in h)
                sj = next(j for j, h in enumerate(hdr) if "المرحلة" in h)
                tj = next(j for j, h in enumerate(hdr) if "الإجمالي" in h)
            except StopIteration:
                continue
            for r in rows[hi + 1:]:
                if not r or r[yj] is None:
                    continue
                y = str(P.num(r[yj]) and int(P.num(r[yj])))
                d = str(r[dj] or "").strip()
                reg_ = DIRECTORATE_REGION.get(d) or P.norm_region(d)
                v = P.num(r[tj])
                if not reg_ or v is None:
                    continue
                years.setdefault(y, {}).setdefault(reg_, 0.0)
                years[y][reg_] += v
                st = STAGE_NAMES.get(str(r[sj] or "").strip())
                if st:
                    stages.setdefault(y, {}).setdefault(reg_, {}).setdefault(st, 0.0)
                    stages[y][reg_][st] += v
        wb.close()
    if not years:
        return []
    latest = max(years)
    vals = {r: years[latest].get(r, 0.0) for r in P.REGIONS}
    series = {r: [{"period": y, "value": years[y][r]} for y in sorted(years) if r in years[y]] for r in P.REGIONS}
    return [{"key": "students", "name": "طلاب التعليم العام (كل المراحل والقطاعات)", "values": vals, "period": latest,
             "series": series, "_years": years, "_stages": stages}]


def schools_lists(dirpath):
    """قوائم المدارس (حكومي/أهلي/عالمي) — صف لكل مدرسة×مرحلة: سنة، إدارة، رقم وزاري، مرحلة.
    نعدّ (رقم وزاري، مرحلة) الفريدة لكل سنة ومنطقة ومرحلة، وهو تعريف «عدد المدارس» في النسخة الأولى (مجموع المراحل)."""
    import openpyxl
    seen = {}  # year -> region -> stage -> set(ids)
    for f in sorted(Path(dirpath).glob("*")):
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            rows = wb[sn].iter_rows(values_only=True)
            hdr = None
            for r in rows:
                cells = [str(c).strip() if c is not None else "" for c in r]
                if hdr is None:
                    if any("الإدارة" in c for c in cells) and any("المرحلة" in c for c in cells):
                        hdr = cells
                        yj = next((j for j, c in enumerate(hdr) if "ميلادي" in c), None)
                        dj = next(j for j, c in enumerate(hdr) if "الإدارة" in c)
                        ij = next((j for j, c in enumerate(hdr) if "الرقم الوزاري" in c), None)
                        sj = next(j for j, c in enumerate(hdr) if "المرحلة" in c)
                    continue
                reg_ = DIRECTORATE_REGION.get(cells[dj]) or P.norm_region(cells[dj])
                st = STAGE_NAMES.get(cells[sj])
                if not reg_ or not st:
                    continue
                y = str(int(P.num(cells[yj]))) if yj is not None and P.num(cells[yj]) else "0"
                sid = cells[ij] if ij is not None else cells[dj] + "|" + str(r)
                seen.setdefault(y, {}).setdefault(reg_, {}).setdefault(st, set()).add(sid)
        wb.close()
    seen.pop("0", None)
    if not seen:
        return []
    years = {y: {r: sum(len(s) for s in st.values()) for r, st in regs.items()} for y, regs in seen.items()}
    stages = {y: {r: {k: len(s) for k, s in st.items()} for r, st in regs.items()} for y, regs in seen.items()}
    latest = max(years)
    vals = {r: float(years[latest].get(r, 0)) for r in P.REGIONS}
    return [{"key": "schools", "name": "المدارس (مدرسة×مرحلة، كل القطاعات)", "values": vals, "period": latest,
             "_years_schools": years, "_stages_schools": stages}]


def records_breakdown(path, region_label, dim_label, group, key_prefix, name_prefix, sum_label=None, period=None, top=None, filt=None, sheet=None, files=None):
    """ملف سجلّي: يفكّك العدّ/الجمع حسب عمود المنطقة × عمود بُعد (نوع/جنس/حالة...). يرجّع مقياساً لكل قيمة للبُعد.
    files: مجلد بملفات متعددة (مثل غير الربحي) — تُقرأ كلها."""
    import openpyxl
    paths = sorted(Path(path).glob("*")) if files else [Path(path)]
    per_sheet = []  # [(region_total_by_region, agg)] لكل ورقة؛ عند تعدد الأوراق لنفس المنطقة نأخذ الأكبر فقط (ملفات مكررة)
    for f in paths:
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            if sheet and sn != sheet:
                continue
            agg = {}  # dim value -> region -> number
            hdr, rj, dj, sj, fj = None, None, None, None, None
            file_region = None
            for r in wb[sn].iter_rows(values_only=True):
                cells = [str(c).strip() if c is not None else "" for c in r]
                if hdr is None:
                    if any(dim_label == c or dim_label in c for c in cells) and (region_label is None or any(region_label in c for c in cells)):
                        hdr = cells
                        dj = next(j for j, c in enumerate(cells) if dim_label == c or dim_label in c)
                        rj = next((j for j, c in enumerate(cells) if region_label and region_label in c), None)
                        sj = next((j for j, c in enumerate(cells) if sum_label and sum_label in c), None)
                        fj = next((j for j, c in enumerate(cells) if filt and filt[0] in c), None)
                        if rj is None:  # المنطقة من اسم الورقة/الملف (ملفات إقليمية)
                            file_region = P.norm_region(sn) or P.norm_region(sn.replace("مكة", "مكة المكرمة")) or next((v for k, v in EN_REGION.items() if k in f.name.lower()), None)
                    continue
                reg_ = P.norm_region(cells[rj]) if rj is not None and rj < len(cells) else file_region
                if not reg_ or dj >= len(cells):
                    continue
                if fj is not None and (fj >= len(cells) or cells[fj] != filt[1]):
                    continue
                dim = re.sub(r"\s+", " ", cells[dj]).strip()
                if not dim:
                    continue
                v = 1.0 if sj is None else (P.num(cells[sj]) if sj < len(cells) else None)
                if v is None:
                    continue
                agg.setdefault(dim, {}).setdefault(reg_, 0.0)
                agg[dim][reg_] += v
            if agg:
                totals = {}
                for dim, regs in agg.items():
                    for rg, v in regs.items():
                        totals[rg] = totals.get(rg, 0.0) + v
                per_sheet.append((totals, agg))
        wb.close()
    # دمج الأوراق: لكل منطقة نأخذ الورقة التي تحوي أكبر مجموع لها (يمنع تكرار ملفين لنفس المنطقة)
    best_sheet = {}
    for i, (totals, _) in enumerate(per_sheet):
        for rg, t in totals.items():
            if t > best_sheet.get(rg, (0, -1))[0]:
                best_sheet[rg] = (t, i)
    agg = {}
    for rg, (_, i) in best_sheet.items():
        for dim, regs in per_sheet[i][1].items():
            if rg in regs:
                agg.setdefault(dim, {})[rg] = regs[rg]
    items = sorted(agg.items(), key=lambda kv: -sum(kv[1].values()))
    if top:
        items = items[:top]
    out = []
    for dim, regs in items:
        vals = {r: regs.get(r, 0.0) for r in P.REGIONS}
        out.append({"key": f"{key_prefix}_{re.sub(r'\\W+', '_', dim)[:30]}", "name": f"{name_prefix}{dim}", "values": vals, "period": period, "group": group})
    return out


BRANCH_REGION = CLUSTER_REGION + [("Holy Capital", "مكة المكرمة"), ("Ahsa", "المنطقة الشرقية"), ("Hafr", "المنطقة الشرقية"), ("Bisha", "عسير"),
                                  ("Qunfudah", "مكة المكرمة"), ("Qurayyat", "الجوف"), ("Northern", "الحدود الشمالية")]


def births_branches(path):
    """المواليد الأحياء (وزارة الصحة): صف لكل فرع/مكتب بالإنجليزية في العمود الأخير؛ نجمع الفروع إلى مناطق."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))
    wb.close()
    h1 = [str(c).strip() if c else "" for c in rows[0]]
    h2 = [str(c).strip() if c else "" for c in rows[1]]
    hdr = [(a + " " + b).strip() for a, b in zip(h1, h2)]
    bj = next(j for j, h in enumerate(hdr) if "Branch" in h)
    spec = {"Type of Delivery Total": ("births", "المواليد الأحياء"), "Type of Delivery C.S.": ("births_cs", "ولادات قيصرية"), "Type of Delivery Normal": ("births_normal", "ولادات طبيعية"),
            "Gender Male": ("births_male", "مواليد ذكور"), "Gender Female": ("births_female", "مواليد إناث"), "Nationality Saudi": ("births_saudi", "مواليد سعوديون"), "Nationality Non-Saudi": ("births_nonsaudi", "مواليد غير سعوديين")}
    out = []
    for label, (key, name) in spec.items():
        j = next((j for j, h in enumerate(hdr) if h.startswith(label)), None)
        if j is None:
            continue
        vals = {r: 0.0 for r in P.REGIONS}
        for r in rows[2:]:
            name_en = str(r[bj] or "") if bj < len(r) else ""
            reg_ = next((v for k, v in BRANCH_REGION if k.lower() in name_en.lower()), None)
            v = P.num(r[j]) if j < len(r) else None
            if reg_ and v is not None:
                vals[reg_] += v
        out.append({"key": key, "name": name, "values": vals, "period": "2024", "group": "المواليد الأحياء (وزارة الصحة)"})
    return out


def gender_sheet(path, sheet, region_col, cols, group, period):
    """جداول النوع الاجتماعي: المنطقة بالعربية في عمود محدد، والقيم في أعمدة محددة."""
    rows = P._rows(path, sheet)
    out = {}
    for sel, (key, name) in cols.items():
        vals = {}
        for r in rows:
            if len(r) <= max(sel, region_col):
                continue
            reg_ = P.norm_region(re.sub(r"ـ+", "", str(r[region_col] or "")))
            v = P.num(r[sel])
            if reg_ and v is not None:
                vals[reg_] = round(v, 2)
        if vals:
            out[key] = {"key": key, "name": name, "values": vals, "period": period, "group": group, "agg": "mean"}
    return list(out.values())


S = lambda ind, sheet, cols: ("services_sum", ind, dict(sheet=sheet, cols=cols))  # noqa: E731
T = lambda ind, sheet, cols: ("region_table", ind, dict(sheet=sheet, cols=cols))  # noqa: E731
M = lambda ind, cols: ("momah_csv", ind, dict(cols=cols))  # noqa: E731
R = lambda ind, label, key, name, sum_label=None, period=None: ("records_by_region", ind, dict(region_label=label, key=key, name=name, sum_label=sum_label, period=period))  # noqa: E731

# ---------------- خريطة الأقسام → المقاييس ----------------
METRICS = {
    "population_housing": [
        ("region_table", "housing_bulletin", dict(sheet="1", cols={"الجملة": ("housing_units", "المساكن المشغولة بأسر سعودية"), "فيلا": ("housing_villa", "فلل"), "شقة": ("housing_apartment", "شقق"), "منزل شعبي": ("housing_traditional", "منازل شعبية"), "دور": ("housing_floor", "أدوار")})),
        ("region_table", "housing_bulletin", dict(sheet="3", cols={"6+": ("hh_6plus", "مساكن تسكنها أسر من 6 أفراد فأكثر"), "1": ("hh_1", "مساكن يسكنها فرد واحد")})),
        ("births_branches", "odp_births", {}),
    ],
    "education": [
        S("services_statistics", "1-2", {"*مدارس": ("schools_public_boys", "مدارس حكومية (بنين)"), "*فصول": ("classes_public_boys", "فصول حكومية (بنين)")}),
        S("services_statistics", "1-4", {"*مدارس": ("schools_public_girls", "مدارس حكومية (بنات)"), "*فصول": ("classes_public_girls", "فصول حكومية (بنات)")}),
        S("services_statistics", "1-3", {"*مدارس": ("schools_private_boys", "مدارس أهلية (بنين)")}),
        S("services_statistics", "1-5", {"*مدارس": ("schools_private_girls", "مدارس أهلية (بنات)")}),
        S("services_statistics", "1-1", {"*مدارس": ("kindergartens", "رياض الأطفال")}),
        S("services_statistics", "1-6", {"المعاهد الحكومية": ("tvtc_public", "معاهد التدريب التقني الحكومية"), "المعاهد الاهلية": ("tvtc_private", "معاهد التدريب التقني الأهلية")}),
        ("students_directorates", "odp_students_directorates", {}),
        ("records_breakdown", "odp_students_directorates", dict(region_label="الإدارة العامة", dim_label="جنس الطالب", sum_label="الإجمالي الكلي", group="الطلاب حسب الجنس (2025)", key_prefix="stu_sex", name_prefix="طلاب: ", period="2025", files=True, filt=("السنة ميلادي", "2025"))),
        ("records_breakdown", "odp_students_directorates", dict(region_label="الإدارة العامة", dim_label="السلطة", sum_label="الإجمالي الكلي", group="الطلاب حسب القطاع (2025)", key_prefix="stu_sector", name_prefix="طلاب: ", period="2025", files=True, filt=("السنة ميلادي", "2025"))),
        ("records_breakdown", "odp_students_directorates", dict(region_label="الإدارة العامة", dim_label="المرحلة", sum_label="سعودي", group="الطلاب السعوديون حسب المرحلة (2025)", key_prefix="stu_saudi", name_prefix="سعوديون: ", period="2025", files=True, filt=("السنة ميلادي", "2025"))),
        ("records_breakdown", "odp_students_directorates", dict(region_label="الإدارة العامة", dim_label="المرحلة", sum_label="غير سعودي", group="الطلاب غير السعوديين حسب المرحلة (2025)", key_prefix="stu_nonsaudi", name_prefix="غير سعوديين: ", period="2025", files=True, filt=("السنة ميلادي", "2025"))),
        ("schools_lists", "odp_schools_lists", {}),
    ],
    "health": [
        T("health_establishments", "1", {"الإجمالي": ("hospitals", "المستشفيات"), "حكومي": ("hospitals_gov", "مستشفيات حكومية"), "خاص": ("hospitals_private", "مستشفيات خاصة")}),
        T("health_establishments", "4", {"الإجمالي": ("beds", "أسرّة المستشفيات")}),
        T("health_establishments", "9", {"الإجمالي": ("phc_centers", "مراكز الرعاية الأولية والمجمعات الطبية")}),
        T("health_establishments", "11", {"صيدليات": ("pharmacies", "صيدليات القطاع الخاص")}),
        ("health_clusters", "odp_health_visits", {}),
        ("gender_sheet", "health_care", dict(sheet="11", region_col=0, cols={3: ("child_visits_rate", "معدل زيارات الأطفال (<15) لمقدم رعاية صحية خلال 12 شهراً"), 1: ("child_visits_rate_m", "معدل الزيارات – ذكور"), 2: ("child_visits_rate_f", "معدل الزيارات – إناث")}, group="مسح الرعاية الصحية: الأطفال", period="2025")),
        ("gender_sheet", "health_care", dict(sheet="15", region_col=0, cols={3: ("child_satisfaction", "نسبة الأطفال الراضين عن وقت الطبيب في الاستشارة %")}, group="مسح الرعاية الصحية: الأطفال", period="2025")),
        ("gender_sheet", "health_care", dict(sheet="19", region_col=0, cols={3: ("child_dentist", "نسبة الأطفال الذين تلقوا استشارة طبيب أسنان %")}, group="مسح الرعاية الصحية: الأطفال", period="2025")),
    ],
    "disability": [
        R("odp_disability", "المنطقة", "pwd", "الأشخاص ذوو الإعاقة", "العدد", "2025 الربع الأول"),
        ("records_breakdown", "odp_disability", dict(region_label="المنطقة", dim_label="تصنيف الإعاقة", sum_label="العدد", group="ذوو الإعاقة حسب نوع الإعاقة", key_prefix="pwd_type", name_prefix="إعاقة ", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability", dict(region_label="المنطقة", dim_label="شدة الإعاقة", sum_label="العدد", group="ذوو الإعاقة حسب الشدة", key_prefix="pwd_sev", name_prefix="شدة ", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability", dict(region_label="المنطقة", dim_label="الحالة المهنية", sum_label="العدد", group="ذوو الإعاقة حسب الحالة المهنية", key_prefix="pwd_job", name_prefix="", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability", dict(region_label="المنطقة", dim_label="الجنس", sum_label="العدد", group="ذوو الإعاقة حسب الجنس", key_prefix="pwd_sex", name_prefix="", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability", dict(region_label="المنطقة", dim_label="الحالة التعليمية", sum_label="العدد", group="ذوو الإعاقة حسب الحالة التعليمية", key_prefix="pwd_edu", name_prefix="", period="2025 الربع الأول", top=6)),
        R("odp_disability_elderly", "المنطقة", "pwd_elderly", "كبار السن من ذوي الإعاقة", "العدد", "2025 الربع الأول"),
        ("records_breakdown", "odp_disability_elderly", dict(region_label="المنطقة", dim_label="الجنس", sum_label="العدد", group="كبار السن من ذوي الإعاقة حسب الجنس", key_prefix="eld_sex", name_prefix="كبار السن: ", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability_elderly", dict(region_label="المنطقة", dim_label="الحالة الاجتماعية", sum_label="العدد", group="كبار السن من ذوي الإعاقة حسب الحالة الاجتماعية", key_prefix="eld_mar", name_prefix="كبار السن: ", period="2025 الربع الأول")),
        ("records_breakdown", "odp_disability_elderly", dict(region_label="المنطقة", dim_label="الحالة المهنية", sum_label="العدد", group="كبار السن من ذوي الإعاقة حسب الحالة المهنية", key_prefix="eld_job", name_prefix="كبار السن: ", period="2025 الربع الأول")),
    ],
    "labor": [
        T("labor_registry", "3-4", {3: ("gosi_saudi", "مشتركو التأمينات السعوديون"), 6: ("gosi_nonsaudi", "مشتركو التأمينات غير السعوديين"), 9: ("gosi_total", "المشتركون على رأس العمل (التأمينات)")}),
        T("labor_registry", "4-4", {9: ("civil_service", "العاملون في الخدمة المدنية")}),
        T("labor_registry", "5-4", {9: ("gosi_new", "المشتركون الجدد خلال الربع")}),
        R("odp_qurra", "المنطقة", "qurra_children", "أطفال مستفيدون من دعم قرة", "عدد الأطفال", "2025 الربع الرابع"),
        R("odp_qurra", "المنطقة", "qurra_mothers", "أمهات مستفيدات من دعم قرة (طلبات)", None, "2025 الربع الرابع"),
        ("records_breakdown", "odp_qurra", dict(region_label="المنطقة", dim_label="متزوج", sum_label="عدد الأطفال", group="أطفال قرة حسب الحالة الاجتماعية للأم", key_prefix="qurra_mar", name_prefix="متزوجة؟ ", period="2025 الربع الرابع")),
        ("records_breakdown", "odp_qurra", dict(region_label="المنطقة", dim_label="لديه إعاقة", sum_label="عدد الأطفال", group="أطفال قرة حسب وجود إعاقة", key_prefix="qurra_dis", name_prefix="لديه إعاقة؟ ", period="2025 الربع الرابع")),
    ],
    "women": [
        T("labor_registry", "3-4", {2: ("gosi_f_saudi", "مشتركات التأمينات السعوديات"), 5: ("gosi_f_nonsaudi", "مشتركات التأمينات غير السعوديات"), 8: ("gosi_f_total", "إجمالي المشتركات في التأمينات"), 9: ("gosi_all_total", "إجمالي المشتركين ذكوراً وإناثاً (للمقارنة)")}),
        T("labor_registry", "4-4", {2: ("civil_f_saudi", "موظفات الخدمة المدنية السعوديات"), 8: ("civil_f_total", "إجمالي موظفات الخدمة المدنية")}),
        T("labor_registry", "5-4", {8: ("gosi_new_f", "المشتركات الجدد خلال الربع")}),
        ("gender_sheet", "women_gender", dict(sheet="3.2", region_col=3, cols={1: ("tfr_saudi", "معدل الخصوبة الكلية للسعوديات"), 2: ("teen_fertility", "خصوبة النساء 15–19 سنة (لكل ألف)")}, group="الخصوبة (مسح النوع الاجتماعي)", period="2018")),
        ("gender_sheet", "women_gender", dict(sheet="(4.7)", region_col=4, cols={2: ("employed_female_share", "نسبة الإناث من المشتغلين السعوديين %"), 1: ("gender_gap_employment", "فجوة النوع في التشغيل (نقطة مئوية)")}, group="المشتغلون حسب الجنس (مسح النوع الاجتماعي)", period="2018")),
        ("gender_sheet", "women_gender", dict(sheet="(6.1)", region_col=7, cols={5: ("income_female_head", "متوسط الدخل الشهري لأسرة ترأسها امرأة (ريال)"), 6: ("income_male_head", "متوسط الدخل الشهري لأسرة يرأسها رجل (ريال)")}, group="دخل الأسرة حسب جنس رئيسها (مسح النوع الاجتماعي)", period="2018")),
    ],
    "sports": [
        R("odp_sports_centers", "المنطقة", "licensed_centers", "الصالات والمراكز الرياضية المرخصة", None, "2026"),
        R("odp_sports_facilities", "المنطقة", "facilities", "مرافق المنشآت الرياضية (وزارة الرياضة)", None, "2026"),
        S("services_statistics", "5-5", {"المدن والاستادات": ("stadiums", "المدن والاستادات الرياضية"), "الأندية": ("clubs", "الأندية الرياضية"), "بيوت الشباب": ("youth_hostels", "بيوت الشباب")}),
        M("momah_fields", {"العدد": ("municipal_fields", "الملاعب البلدية")}),
    ],
    "nonprofit": [
        ("nonprofit_dir", "odp_nonprofit", {}),
        ("records_breakdown", "odp_nonprofit", dict(region_label=None, dim_label="نوع الكيان", group="الكيانات غير الربحية حسب النوع", key_prefix="np_type", name_prefix="", period="2026", files=True)),
        ("records_breakdown", "odp_nonprofit", dict(region_label=None, dim_label="جهة الإشراف", group="الكيانات غير الربحية حسب جهة الإشراف (الأكثر)", key_prefix="np_sup", name_prefix="إشراف: ", period="2026", files=True, top=6)),
        ("records_breakdown", "odp_nonprofit", dict(region_label=None, dim_label="التصنيف الفرعي الا", group="الكيانات غير الربحية حسب مجال النشاط (الأكثر)", key_prefix="np_field", name_prefix="", period="2026", files=True, top=8)),
    ],
    "security": [
        S("services_statistics", "2-1", {"عدد مراكز الدفاع": ("civil_defense_centers", "مراكز الدفاع المدني")}),
        S("services_statistics", "2-2", {"عدد مراكز إسعاف": ("ambulance_centers", "مراكز إسعاف الهلال الأحمر"), "عدد المسعفين": ("paramedics", "المسعفون"), "عدد الحالات": ("ambulance_cases", "الحالات الإسعافية")}),
    ],
    "infrastructure": [
        M("momah_parks", {"عدد الحدائق": ("parks", "الحدائق والمنتزهات"), "مساحة  الحدائق": ("parks_area", "مساحة الحدائق (م²)"), "المسطحات": ("green_area", "مساحة المسطحات الخضراء (م²)")}),
        M("momah_plazas", {"عدد الساحات": ("plazas", "الساحات البلدية")}),
        M("momah_trees", {"الاشجار": ("trees", "الأشجار المزروعة"), "الزهور": ("flowers", "الزهور المزروعة")}),
        M("momah_urban_centers", {"عدد المراكز": ("urban_centers", "المراكز الحضرية")}),
        M("momah_service_offices", {"عدد مكاتب": ("service_offices", "مكاتب الخدمات البلدية"), "البلديات الفرعية": ("sub_municipalities", "البلديات الفرعية")}),
        ("amanah_xlsx", "odp_municipalities", dict(cols={"الإجمالي": ("municipalities", "البلديات (كل الفئات)")})),
        S("services_statistics", "6-2", {"الامانات": ("amanahs", "الأمانات"), "البلديات الفرعية": ("sub_municipalities_gastat", "البلديات الفرعية (الهيئة)")}),
    ],
    "tourism": [
        T("tourism_establishments", "2.1", {3: ("hotels", "الفنادق المرخصة"), 2: ("serviced_apartments", "الشقق المخدومة ومرافق الضيافة الأخرى")}),
        S("services_statistics", "5-1", {"عدد الفنادق": ("hotels_2024", "الفنادق"), "عدد الغرف": ("hotel_rooms", "غرف الفنادق")}),
        S("services_statistics", "5-2", {"عدد الشقق": ("apartments_2024", "الشقق المخدومة"), "عدد الوحدات": ("apartment_units", "وحدات الشقق المخدومة")}),
    ],
    "real_estate": [],
    "religious": [S("services_statistics", "3-5", {"الجوامع": ("jamie", "الجوامع"), "المساجد": ("mosques", "المساجد"), "مصليات": ("eid", "مصليات العيد")})],
    "commerce": [
        S("services_statistics", "4-1", {"عدد الغرف": ("chambers", "الغرف التجارية"), "عدد اللجان الفرعية": ("subcommittees", "اللجان الفرعية"), "عدد اللجان": ("committees", "اللجان")}),
        S("services_statistics", "4-2", {"*البنوك": ("bank_branches", "فروع البنوك"), "*الصرف": ("atms", "أجهزة الصرف الآلي")}),
        S("services_statistics", "4-5", {"*المدن": ("industrial_cities", "المدن الصناعية"), "*المصانع": ("factories", "المصانع المنتجة")}),
    ],
}


def repi_series(path):
    """السلاسل الزمنية للرقم القياسي لأسعار العقارات حسب المنطقة (ورقة 3): العمود المؤشر لكل منطقة."""
    rows = P._rows(path, "3")
    hdr_i = next(i for i, r in enumerate(rows) if r and any(P.norm_region(c) for c in r if c))
    hdr = rows[hdr_i]
    cols = {}
    for j, c in enumerate(hdr):
        rg = P.norm_region(c)
        if rg:
            cols[rg] = j
    series = {rg: [] for rg in cols}
    year = None
    for r in rows[hdr_i + 3:]:
        if not r or (r[0] is None and r[1] is None):
            continue
        if r[0] is not None and P.num(r[0]):
            year = int(P.num(r[0]))
        q = str(r[1] or "").strip()
        if not year or not q:
            continue
        for rg, j in cols.items():
            v = P.num(r[j]) if j < len(r) else None
            if v is not None:
                series[rg].append({"period": f"{year} {q}", "value": round(v, 2)})
    latest = {rg: (s[-1]["value"] if s else None) for rg, s in series.items()}
    last_period = next((s[-1]["period"] for s in series.values() if s), None)
    return [{"key": "repi", "name": "الرقم القياسي لأسعار العقارات (2023=100)", "values": latest, "period": last_period, "series": series}]


def run_metric(spec):
    fn, ind_id, kw = spec
    path = raw_path(ind_id)
    if not path or not Path(path).exists():
        return ind_id, None, "no_file"
    try:
        if fn == "services_sum":
            out = P.services_sum(path, **kw)
        elif fn == "region_table":
            out = P.region_table(path, **kw)
        elif fn == "momah_csv":
            out = P.momah_csv(path, **kw)
        elif fn == "records_by_region":
            out = P.records_by_region(path, **kw)
        elif fn == "amanah_xlsx":
            out = P.amanah_xlsx(path, **kw)
        elif fn == "health_clusters":
            out = health_clusters(path)
        elif fn == "schools_by_directorate":
            out = schools_by_directorate(path, **kw)
        elif fn == "nonprofit_dir":
            out = nonprofit_dir(path)
        elif fn == "students_directorates":
            out = students_directorates(path)
        elif fn == "schools_lists":
            out = schools_lists(path)
        elif fn == "records_breakdown":
            out = records_breakdown(path, **kw)
        elif fn == "gender_sheet":
            out = gender_sheet(path, **kw)
        elif fn == "births_branches":
            out = births_branches(path)
        elif fn == "repi_series":
            out = repi_series(path)
        else:
            return ind_id, None, "unknown_fn"
        return ind_id, out, "ok"
    except Exception as e:  # noqa: BLE001
        return ind_id, None, f"error: {e}"


def merge_education_years(live_base, years, stages, field="students"):
    """يضيف سنوات (الطلاب أو المدارس) الجديدة إلى categories.education.data[region].by_year في نسخة baseline الحيّة."""
    edu = live_base["categories"].get("education")
    if not edu:
        return
    yrs = set(edu.get("available_years", []))
    for y, regs in years.items():
        for reg_, total in regs.items():
            node = edu["data"].setdefault(reg_, {"by_year": {}})
            by = node.setdefault("by_year", {})
            cur = by.setdefault(y, {"schools": 0, "students": 0, "teachers": 0, "admins": 0, "classes": 0, "by_stage": {}})
            cur[field] = int(round(total))
            cur.setdefault("by_stage", {})
            for st, v in stages.get(y, {}).get(reg_, {}).items():
                cur["by_stage"].setdefault(st, {"schools": 0, "students": 0, "teachers": 0})[field] = int(round(v))
            cur["_live"] = True
        yrs.add(y)
    edu["available_years"] = sorted(yrs)


# ---------------- التعيير بالسكان + مؤشر فجوة الخدمات ----------------
NON_COUNT = {"repi", "parks_area", "green_area"}  # مؤشرات/مساحات لا تُعيَّر بالسكان
PER = 10000
GAP_AXES = {  # المحور → المقاييس المكوّنة له (قسم.مقياس)؛ كلها معيّرة بالسكان ثم min-max إلى 0–100
    "health": {"name": "الصحة", "icon": "🏥", "metrics": ["health.hospitals", "health.beds", "health.phc_centers", "health.pharmacies"]},
    "education": {"name": "التعليم", "icon": "📚", "metrics": ["education.schools", "education.kindergartens", "education.tvtc_public", "education.classes_public_boys", "education.classes_public_girls"]},
    "safety": {"name": "الأمن والطوارئ", "icon": "🚨", "metrics": ["security.civil_defense_centers", "security.ambulance_centers", "security.paramedics"]},
    "municipal": {"name": "الخدمات البلدية", "icon": "🌳", "metrics": ["infrastructure.parks", "infrastructure.plazas", "infrastructure.service_offices", "infrastructure.urban_centers", "sports.municipal_fields"]},
    "jobs": {"name": "فرص العمل", "icon": "💼", "metrics": ["labor.gosi_total", "labor.gosi_new", "labor.civil_service", "commerce.bank_branches"]},
}
REFS = {  # كيف يصل الباحث للرقم في الملف الأصلي
    "services_sum": "ورقة {sheet} — جمع صفوف المنطقة الإدارية",
    "region_table": "ورقة {sheet} — صف المنطقة",
    "momah_csv": "ملف CSV — جمع صفوف الأمانات التابعة للمنطقة",
    "records_by_region": "ملف سجلّي — عدّ/جمع الصفوف حسب عمود المنطقة",
    "amanah_xlsx": "جدول الأمانات — جمع الأمانات التابعة للمنطقة",
    "health_clusters": "عمود Total — تجميع التجمعات الصحية إلى مناطق",
    "nonprofit_dir": "13 ملفاً إقليمياً — عدّ الكيانات",
    "students_directorates": "16 ملفاً — جمع عمود الإجمالي الكلي حسب الإدارة التعليمية",
    "schools_lists": "3 قوائم — عدّ (الرقم الوزاري × المرحلة) حسب الإدارة التعليمية",
    "repi_series": "ورقة 3 — السلاسل الزمنية حسب المنطقة",
    "records_breakdown": "ملف سجلّي — تفكيك حسب عمود المنطقة × عمود البُعد",
    "gender_sheet": "ورقة {sheet} — صف المنطقة",
}


def population():
    pop = base["categories"]["population_housing"]["population"]
    return {r: float(pop[r]["total"]) for r in P.REGIONS if r in pop and pop[r].get("total")}


def normalize(out):
    """لكل مقياس عددي: القيمة لكل 10 آلاف نسمة + ترتيب المنطقة (1 = الأعلى لكل نسمة)."""
    pop = population()
    for ck, c in out["categories"].items():
        for m in c["metrics"]:
            if m["key"] in NON_COUNT:
                m["rank"] = _rank(m["values"])
                continue
            per = {r: round(v / pop[r] * PER, 3) for r, v in m["values"].items() if r in pop and pop[r] and v is not None}
            m["per_10k"] = per
            m["rank"] = _rank(m["values"])
            m["rank_per_10k"] = _rank(per)


def _rank(vals):
    order = sorted([r for r in vals if vals[r] is not None], key=lambda r: -vals[r])
    return {r: i + 1 for i, r in enumerate(order)}


def gap_index(out):
    """درجة 0–100 لكل منطقة في كل محور (متوسط مقاييسه المعيّرة بعد min-max)، والدرجة الكلية متوسط المحاور، والفجوة = 100 − الدرجة."""
    lookup = {}
    for ck, c in out["categories"].items():
        for m in c["metrics"]:
            if m.get("per_10k"):
                lookup[f"{ck}.{m['key']}"] = m
    axes_out, used = {}, {}
    for ak, ax in GAP_AXES.items():
        scores = {r: [] for r in P.REGIONS}
        used[ak] = []
        for mk in ax["metrics"]:
            m = lookup.get(mk)
            if not m:
                continue
            used[ak].append({"metric": mk, "name": m["name"], "period": m.get("period")})
            rk = m["rank_per_10k"]  # درجة رتبية: الأولى لكل نسمة = 100، الأخيرة = 0 (أقل حساسية للقيم الشاذة من min-max)
            n = len(rk)
            for r in P.REGIONS:
                if r in rk and n > 1:
                    scores[r].append((n - rk[r]) / (n - 1) * 100)
        axes_out[ak] = {r: round(sum(s) / len(s), 1) for r, s in scores.items() if s}
    regions = {}
    for r in P.REGIONS:
        ax = {ak: axes_out[ak].get(r) for ak in GAP_AXES if r in axes_out.get(ak, {})}
        score = round(sum(ax.values()) / len(ax), 1) if ax else None
        regions[r] = {"axes": ax, "score": score, "gap": round(100 - score, 1) if score is not None else None}
    rank = _rank({r: v["score"] for r, v in regions.items() if v["score"] is not None})
    for r in regions:
        regions[r]["rank"] = rank.get(r)
        regions[r]["axis_rank"] = {ak: _rank(axes_out[ak]).get(r) for ak in axes_out}
    out["gap_index"] = {"axes": {ak: {"name": a["name"], "icon": a["icon"], "metrics": used[ak]} for ak, a in GAP_AXES.items()},
                        "regions": regions, "population": population(),
                        "method": "كل مقياس يُقسَم على سكان المنطقة (تعداد 2022) لكل 10 آلاف نسمة، ثم تُرتَّب المناطق فيه وتُحوَّل الرتبة إلى درجة (الأولى = 100، الأخيرة = 0)، ودرجة المحور متوسط مقاييسه، والدرجة الكلية متوسط المحاور الخمسة، والفجوة = 100 − الدرجة. الدرجة نسبية بين المناطق الثلاث عشرة ولا تقيس كفاية مطلقة."}


def methodology(out):
    rows = []
    for ck, c in out["categories"].items():
        for m in c["metrics"]:
            rows.append({"category": c["name"], "metric": m["name"], "key": m["key"], "source": m.get("source"), "file": (out["manifest"].get(m["indicator"]) or {}).get("source_file"),
                         "ref": m.get("ref"), "period": m.get("period"), "source_date": m.get("source_date"), "source_url": m.get("source_url"),
                         "runner": m.get("runner")})
    out["methodology"] = rows


def main():
    global live_base
    live_base = json.loads(json.dumps(base))  # نسخة من بيانات النسخة الأولى تُحقن فيها السنوات الجديدة
    prev_path = DATA / "dashboard.json"
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else None
    prev_vals = {}
    if prev:
        for ck, c in prev.get("categories", {}).items():
            for m in c.get("metrics", []):
                prev_vals[(ck, m["key"])] = m["values"]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {"built_at": now, "regions": P.REGIONS, "categories": {}, "census": {}, "sources": reg["sources"], "log": []}
    METRICS["real_estate"] = [("repi_series", "real_estate_repi", {})]
    changes = []
    for ck, cat in base["categories"].items():
        if ck.startswith("census_"):
            out["census"][ck] = cat
            continue
        entry = {"name": cat.get("name", ck), "icon": cat.get("icon", ""), "baseline": {k: v for k, v in cat.items() if k not in ("name", "icon")},
                 "metrics": []}
        prev_metrics = {m["key"]: m for m in (prev or {}).get("categories", {}).get(ck, {}).get("metrics", [])} if prev else {}
        for spec in METRICS.get(ck, []):
            ind_id, metrics, status = run_metric(spec)
            m = man["indicators"].get(ind_id, {})
            out["log"].append({"category": ck, "indicator": ind_id, "status": status})
            if not metrics:
                # أمان: لا نُسقط مقياساً كان موجوداً في البناء السابق لمجرد تعثّر ملف اليوم — نُبقي القيم السابقة ونعلّمها
                for pm in prev_metrics.values():
                    if pm.get("indicator") == ind_id and pm["key"] not in {x["key"] for x in entry["metrics"]}:
                        entry["metrics"].append({**pm, "parse_status": status})
                continue
            for met in metrics:
                if not met.get("period"):  # سنة البيانات من اسم الملف عند غيابها داخل الجدول (مثل نشرة المساكن 2025)
                    yrs = re.findall(r"(20[1-3]\d)", Path(raw_path(ind_id) or "").name)
                    met["period"] = max(yrs) if yrs else None
                if "_years_schools" in met:  # عدد المدارس بالسنوات → by_year[y].schools و by_stage
                    merge_education_years(live_base, met.pop("_years_schools"), met.pop("_stages_schools"), field="schools")
                    edu = live_base["categories"]["education"]["data"]
                    met["series"] = {r: [{"period": y, "value": edu[r]["by_year"][y]["schools"]}
                                         for y in sorted(edu.get(r, {}).get("by_year", {})) if edu[r]["by_year"][y].get("schools")]
                                     for r in P.REGIONS}
                if "_years" in met:  # دمج السنوات الجديدة في بيانات النسخة الأولى حتى تتحدث رسومها القديمة (مقارنة الطلاب حسب السنة...)
                    merge_education_years(live_base, met.pop("_years"), met.pop("_stages"))
                    edu = live_base["categories"]["education"]["data"]  # السلسلة = سنوات النسخة الأولى + السنوات الحيّة
                    met["series"] = {r: [{"period": y, "value": edu[r]["by_year"][y]["students"]}
                                         for y in sorted(edu.get(r, {}).get("by_year", {})) if edu[r]["by_year"][y].get("students")]
                                     for r in P.REGIONS}
                met = {**met, "indicator": ind_id, "ref": REFS.get(spec[0], "").format(sheet=spec[2].get("sheet", "")), "source": reg["sources"][reg["indicators"][ind_id]["source"]]["name"],
                       "source_url": m.get("source_url"), "source_date": m.get("source_date"), "checked_at": m.get("checked_at"),
                       "runner": reg["sources"][reg["indicators"][ind_id]["source"]]["runner"]}
                met["values"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in met["values"].items() if v is not None}
                nums = [v for v in met["values"].values() if isinstance(v, (int, float))]
                met["total"] = round((sum(nums) / len(nums)) if met.get("agg") == "mean" and nums else sum(nums), 2)
                old = prev_vals.get((ck, met["key"]))
                if old is not None and old != met["values"]:
                    diff = [r for r in met["values"] if old.get(r) != met["values"][r]]
                    changes.append({"at": now, "category": ck, "metric": met["key"], "name": met["name"], "regions_changed": len(diff),
                                    "period": met.get("period"), "source_date": met.get("source_date")})
                entry["metrics"].append(met)
        dates = [m["source_date"] for m in entry["metrics"] if m.get("source_date")]
        entry["freshness"] = {"latest_source_date": max(dates) if dates else None, "metrics": len(entry["metrics"]),
                              "last_checked": max((m.get("checked_at") or "" for m in entry["metrics"]), default=None)}
        out["categories"][ck] = entry
    out["census_note"] = "تعداد السعودية 2022 — لقطة ثابتة من لوحات الهيئة حتى صدور التعداد القادم"
    out["manifest"] = {k: {kk: v.get(kk) for kk in ("name", "source", "status", "source_date", "checked_at", "last_change_at", "source_url", "source_file")}
                       for k, v in man["indicators"].items()}
    methodology(out)
    (DATA / "dashboard.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    (DATA / "baseline_live.json").write_text(json.dumps(live_base, ensure_ascii=False), encoding="utf-8")
    ch_path = DATA / "changes.json"
    allch = json.loads(ch_path.read_text(encoding="utf-8-sig")) if ch_path.exists() else []
    allch = (changes + allch)[:500]
    ch_path.write_text(json.dumps(allch, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for x in out["log"] if x["status"] == "ok")
    print(f"dashboard.json: {len(out['categories'])} أقسام، {sum(len(c['metrics']) for c in out['categories'].values())} مقياساً، {ok}/{len(out['log'])} محلّل نجح، {len(changes)} تغيّر")
    for x in out["log"]:
        if x["status"] != "ok":
            print("  !", x)
    # status.json للواجهة والفحص
    (DATA / "status.json").write_text(json.dumps({"built_at": now, "manifest": out["manifest"], "log": out["log"]}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
