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


S = lambda ind, sheet, cols: ("services_sum", ind, dict(sheet=sheet, cols=cols))  # noqa: E731
T = lambda ind, sheet, cols: ("region_table", ind, dict(sheet=sheet, cols=cols))  # noqa: E731
M = lambda ind, cols: ("momah_csv", ind, dict(cols=cols))  # noqa: E731
R = lambda ind, label, key, name, sum_label=None, period=None: ("records_by_region", ind, dict(region_label=label, key=key, name=name, sum_label=sum_label, period=period))  # noqa: E731

# ---------------- خريطة الأقسام → المقاييس ----------------
METRICS = {
    "education": [
        S("services_statistics", "1-2", {"*مدارس": ("schools_public_boys", "مدارس حكومية (بنين)"), "*فصول": ("classes_public_boys", "فصول حكومية (بنين)")}),
        S("services_statistics", "1-4", {"*مدارس": ("schools_public_girls", "مدارس حكومية (بنات)"), "*فصول": ("classes_public_girls", "فصول حكومية (بنات)")}),
        S("services_statistics", "1-3", {"*مدارس": ("schools_private_boys", "مدارس أهلية (بنين)")}),
        S("services_statistics", "1-5", {"*مدارس": ("schools_private_girls", "مدارس أهلية (بنات)")}),
        S("services_statistics", "1-1", {"*مدارس": ("kindergartens", "رياض الأطفال")}),
        S("services_statistics", "1-6", {"المعاهد الحكومية": ("tvtc_public", "معاهد التدريب التقني الحكومية"), "المعاهد الاهلية": ("tvtc_private", "معاهد التدريب التقني الأهلية")}),
        ("students_directorates", "odp_students_directorates", {}),
        ("schools_by_directorate", "odp_schools_public", dict(key="schools_public_2025", name="مدارس التعليم العام الحكومي (مدرسة×مرحلة)")),
        ("schools_by_directorate", "odp_schools_private", dict(key="schools_private_2025", name="مدارس التعليم الأهلي (مدرسة×مرحلة)")),
    ],
    "health": [
        T("health_establishments", "1", {"الإجمالي": ("hospitals", "المستشفيات"), "حكومي": ("hospitals_gov", "مستشفيات حكومية"), "خاص": ("hospitals_private", "مستشفيات خاصة")}),
        T("health_establishments", "4", {"الإجمالي": ("beds", "أسرّة المستشفيات")}),
        T("health_establishments", "9", {"الإجمالي": ("phc_centers", "مراكز الرعاية الأولية والمجمعات الطبية")}),
        T("health_establishments", "11", {"صيدليات": ("pharmacies", "صيدليات القطاع الخاص")}),
        ("health_clusters", "odp_health_visits", {}),
    ],
    "disability": [
        R("odp_disability", "المنطقة", "pwd", "الأشخاص ذوو الإعاقة", "العدد", "2025 الربع الأول"),
        R("odp_disability_elderly", "المنطقة", "pwd_elderly", "كبار السن من ذوي الإعاقة", "العدد", "2025 الربع الأول"),
    ],
    "labor": [
        T("labor_registry", "3-4", {3: ("gosi_saudi", "مشتركو التأمينات السعوديون"), 6: ("gosi_nonsaudi", "مشتركو التأمينات غير السعوديين"), 9: ("gosi_total", "المشتركون على رأس العمل (التأمينات)")}),
        T("labor_registry", "4-4", {9: ("civil_service", "العاملون في الخدمة المدنية")}),
        T("labor_registry", "5-4", {9: ("gosi_new", "المشتركون الجدد خلال الربع")}),
        R("odp_qurra", "المنطقة", "qurra_children", "أطفال مستفيدون من دعم قرة", "عدد الأطفال", "2025 الربع الرابع"),
    ],
    "sports": [
        R("odp_sports_centers", "المنطقة", "licensed_centers", "الصالات والمراكز الرياضية المرخصة", None, "2026"),
        R("odp_sports_facilities", "المنطقة", "facilities", "مرافق المنشآت الرياضية (وزارة الرياضة)", None, "2026"),
        S("services_statistics", "5-5", {"المدن والاستادات": ("stadiums", "المدن والاستادات الرياضية"), "الأندية": ("clubs", "الأندية الرياضية"), "بيوت الشباب": ("youth_hostels", "بيوت الشباب")}),
        M("momah_fields", {"العدد": ("municipal_fields", "الملاعب البلدية")}),
    ],
    "nonprofit": [("nonprofit_dir", "odp_nonprofit", {})],
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
        elif fn == "repi_series":
            out = repi_series(path)
        else:
            return ind_id, None, "unknown_fn"
        return ind_id, out, "ok"
    except Exception as e:  # noqa: BLE001
        return ind_id, None, f"error: {e}"


def merge_education_years(live_base, years, stages):
    """يضيف سنوات الطلاب الجديدة إلى categories.education.data[region].by_year في نسخة baseline الحيّة."""
    edu = live_base["categories"].get("education")
    if not edu:
        return
    yrs = set(edu.get("available_years", []))
    for y, regs in years.items():
        for reg_, total in regs.items():
            node = edu["data"].setdefault(reg_, {"by_year": {}})
            by = node.setdefault("by_year", {})
            cur = by.setdefault(y, {"schools": 0, "students": 0, "teachers": 0, "admins": 0, "classes": 0, "by_stage": {}})
            cur["students"] = int(round(total))
            cur.setdefault("by_stage", {})
            for st, v in stages.get(y, {}).get(reg_, {}).items():
                cur["by_stage"].setdefault(st, {"schools": 0, "students": 0, "teachers": 0})["students"] = int(round(v))
            cur["_live"] = True
        yrs.add(y)
    edu["available_years"] = sorted(yrs)


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
        if ck.startswith("census_") or ck == "population_housing":
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
                if "_years" in met:  # دمج السنوات الجديدة في بيانات النسخة الأولى حتى تتحدث رسومها القديمة (مقارنة الطلاب حسب السنة...)
                    merge_education_years(live_base, met.pop("_years"), met.pop("_stages"))
                    edu = live_base["categories"]["education"]["data"]  # السلسلة = سنوات النسخة الأولى + السنوات الحيّة
                    met["series"] = {r: [{"period": y, "value": edu[r]["by_year"][y]["students"]}
                                         for y in sorted(edu.get(r, {}).get("by_year", {})) if edu[r]["by_year"][y].get("students")]
                                     for r in P.REGIONS}
                met = {**met, "indicator": ind_id, "source": reg["sources"][reg["indicators"][ind_id]["source"]]["name"],
                       "source_url": m.get("source_url"), "source_date": m.get("source_date"), "checked_at": m.get("checked_at"),
                       "runner": reg["sources"][reg["indicators"][ind_id]["source"]]["runner"]}
                met["values"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in met["values"].items() if v is not None}
                met["total"] = round(sum(v for v in met["values"].values() if isinstance(v, (int, float))), 2)
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
