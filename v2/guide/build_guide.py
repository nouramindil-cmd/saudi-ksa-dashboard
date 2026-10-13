# -*- coding: utf-8 -*-
"""يولّد «دليل لوحة بيانات المملكة» (ملف HTML واحد) من بيانات اللوحة في saudi-ksa-dashboard/v2/data/dashboard.json"""
import json, re, datetime
from pathlib import Path

V2 = Path(r"C:/Users/lenovo/saudi-ksa-dashboard/v2")
OUT = Path(r"C:/Users/lenovo/Downloads/دليل لوحة بيانات المملكة.html")
d = json.load(open(V2 / "data/dashboard.json", encoding="utf-8"))

BUILT = d["built_at"][:10]
built_dt = datetime.date.fromisoformat(BUILT)
AR_MONTHS = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
def ar_date(s):
    if not s: return ""
    y, m, dd = s[:10].split("-")
    return f"{int(dd)} {AR_MONTHS[int(m)-1]} {y}"

NAV = [("population_housing","السكان والإسكان"),("education","التعليم"),("health","الصحة"),("disability","ذوو الإعاقة"),("labor","سوق العمل والمنشآت"),
       ("sports","الرياضة"),("nonprofit","القطاع غير الربحي"),("security","الأمن والطوارئ"),("infrastructure","الخدمات البلدية"),("tourism","السياحة والضيافة"),
       ("real_estate","العقارات"),("religious","الشؤون الدينية"),("commerce","التجارة"),("women","المرأة")]
CAT_NAME = dict(NAV)
CAT_ORDER = [k for k, _ in NAV]

ENTITY = {"gastat_pub": "الهيئة العامة للإحصاء", "gastat_api": "الهيئة العامة للإحصاء", "momah": "وزارة البلديات والإسكان", "odp": "منصة البيانات المفتوحة (سدايا)", "census_tableau": "الهيئة العامة للإحصاء – تعداد 2022"}
ENTITY_SHORT = {"الهيئة العامة للإحصاء": "الهيئة", "وزارة البلديات والإسكان": "البلديات", "منصة البيانات المفتوحة (سدايا)": "سدايا"}
def entity_of_source_name(s):
    if "سدايا" in s: return "منصة البيانات المفتوحة (سدايا)"
    if "البلديات" in s: return "وزارة البلديات والإسكان"
    return "الهيئة العامة للإحصاء"

manifest = d["manifest"]
# metric key -> category key + extra (group, agg)
meta = {}
for ck, cv in d["categories"].items():
    for m in cv.get("metrics", []):
        meta[m["key"]] = (ck, m)

records = []
for i, m in enumerate(d["methodology"], 1):
    ck, mm = meta[m["key"]]
    ent = entity_of_source_name(m["source"])
    sd = m.get("source_date") or ""
    age = (built_dt - datetime.date.fromisoformat(sd[:10])).days if sd else None
    if age is None: fresh = "غير محدد"
    elif age <= 90: fresh = "خلال 3 أشهر"
    elif age <= 365: fresh = "3 – 12 شهراً"
    else: fresh = "أكثر من سنة"
    period = m.get("period") or ""
    year = re.match(r"\d{4}", period).group(0) if re.match(r"\d{4}", period) else "غير محدد"
    ind = mm.get("indicator") or m.get("indicator") or ""; ds = manifest.get(ind, {})
    records.append({
        "id": f"M{i:03d}", "n": i,
        "cat": ck, "cat_name": CAT_NAME[ck],
        "name": m["metric"], "group": mm.get("group") or "المقاييس الرئيسية",
        "entity": ent, "source_full": m["source"],
        "ds_key": ind, "ds": ds.get("name") or ind,
        "file": m.get("file") or "", "ref": m.get("ref") or "",
        "period": period, "year": year,
        "source_date": sd[:10], "source_date_ar": ar_date(sd), "age": age, "fresh": fresh,
        "url": m.get("source_url") or "",
        "agg": "متوسط المناطق" if mm.get("agg") == "mean" else "مجموع المناطق",
        "total": mm.get("total"),
    })

# sources register
src_rows = []
for k, v in manifest.items():
    ent = ENTITY.get(v.get("source"), v.get("source"))
    n = sum(1 for r in records if r["ds_key"] == k)
    cats = sorted({r["cat_name"] for r in records if r["ds_key"] == k}, key=lambda x: CAT_ORDER.index([kk for kk, nn in NAV if nn == x][0]))
    st = v.get("status")
    status = {"updated": "تغيّر منذ آخر سحب", "unchanged": "بلا تغيير", "static": "لقطة ثابتة"}.get(st, st or "")
    sd = v.get("source_date") or ""
    src_rows.append({"key": k, "name": v.get("name"), "entity": ent, "entity_short": ENTITY_SHORT.get(ent, "الهيئة"), "cats": cats or (["تعداد 2022"] if k == "census_2022" else []),
                     "metrics": n, "status": status, "source_date": sd[:10], "source_date_ar": ar_date(sd) if sd else "—",
                     "file": v.get("source_file") or "", "url": v.get("source_url") or "", "runner": "آلي يومي" if v.get("source") in ("gastat_pub", "momah") else "دوري عبر فريق العمل"})

# census glossary
census = d["census"]
k = census["census_population"]["kpis"]; kn = census["census_nationality"]["kpis"]; km = census["census_marital"]["kpis"]; kg = census["census_growth"]["kpis"]
kd = census["census_dependency"]["kpis"]; kh = census["census_households"]["kpis"]; kb = census["census_buildings"]["kpis"]; ku = census["census_units"]["kpis"]
fmt = lambda x: f"{int(round(x)):,}"
CENSUS = [
    {"key": "census_population", "name": "التركيبة السكانية", "what": "الهرم السكاني للمملكة ولكل منطقة، الفئات العمرية العريضة، والتوزيع بين الذكور والإناث.",
     "kpis": [("إجمالي السكان", fmt(k["total_population"])), ("في سن العمل", fmt(k["working_age"])), ("العمر الوسيط", f'{k["median_age"]:.0f} سنة')]},
    {"key": "census_nationality", "name": "الجنسية", "what": "السعوديون وغير السعوديين بالجنس، وأكبر الجنسيات غير السعودية عدداً.",
     "kpis": [("غير السعوديين", f'{kn["non_saudi_pct"]}%'), ("السعوديون", fmt(kn["saudi_total"])), ("أكبر جنسية وافدة", f'{kn["largest_non_saudi"]} ({fmt(kn["largest_count"])})')]},
    {"key": "census_marital", "name": "الحالة الاجتماعية", "what": "المتزوجون والمطلقون لمن هم 15 سنة فأكثر، بالمنطقة والجنس والجنسية والفئة العمرية.",
     "kpis": [("نسبة المتزوجين", f'{km["married_pct"]}%'), ("أعلى منطقة", f'{km["highest_married_region"]} ({km["highest_married_pct"]}%)'), ("نسبة المطلقين", f'{km["divorced_pct"]}%')]},
    {"key": "census_growth", "name": "النمو السكاني", "what": "السلسلة الزمنية للسكان ومعدل النمو السنوي للسعوديين وغير السعوديين، ومقارنة النمو بين المناطق.",
     "kpis": [("نمو إجمالي", f'{kg["total_growth_pct"]}%'), ("نمو السعوديين", f'{kg["saudi_growth_pct"]}%'), ("أعلى منطقة نمواً", f'{kg["highest_region"]} ({kg["highest_pct"]}%)')]},
    {"key": "census_dependency", "name": "الإعالة", "what": "نسبة الإعالة (المعالون إلى من هم في سن العمل) بالمنطقة، وتوزيع الأسر أحادية ومتعددة المعيلين.",
     "kpis": [("نسبة الإعالة", f'{kd["total_ratio"]}%'), ("أعلى منطقة", f'{kd["highest_region"]} ({kd["highest_value"]}%)'), ("أدنى منطقة", f'{kd["lowest_region"]} ({kd["lowest_value"]}%)')]},
    {"key": "census_households", "name": "تركيبة الأسر", "what": "عدد الأسر السعودية وغير السعودية، وتوزيع الأسر بحجمها (عدد الأفراد) لكل منطقة.",
     "kpis": [("إجمالي الأسر", fmt(kh["total"])), ("أسر سعودية", f'{kh["saudi_pct"]}%'), ("الحجم الأكثر شيوعاً", f'{kh["largest_size"]} ({kh["largest_size_pct"]}%)')]},
    {"key": "census_buildings", "name": "المساكن", "what": "المباني السكنية وغير السكنية (تجارية، إسكان عام، مخيمات عمل) بالمنطقة ونوع المبنى.",
     "kpis": [("إجمالي المباني", fmt(kb["total"])), ("سكنية", f'{kb["residential_pct"]}%'), ("غير سكنية", f'{kb["non_residential_pct"]}%')]},
    {"key": "census_units", "name": "الوحدات السكنية", "what": "نوع الوحدة (شقة، فيلا، دور…)، مادة البناء، ومتوسط أفراد الأسرة بنوع الوحدة.",
     "kpis": [("الوحدات المشغولة", fmt(ku["total"])), ("النوع الأكثر", f'{ku["top_type"]} ({ku["top_type_pct"]}%)'), ("مادة البناء الأكثر", f'{ku["top_material"]} ({ku["top_material_pct"]}%)')]},
]

ent_counts = {}
for r in records: ent_counts[r["entity"]] = ent_counts.get(r["entity"], 0) + 1
latest_pub = max(r["source_date"] for r in records)
recent90 = sum(1 for r in records if r["age"] is not None and r["age"] <= 90)

DATA = {
    "meta": {"built": BUILT, "built_ar": ar_date(BUILT), "latest_pub": latest_pub, "latest_pub_ar": ar_date(latest_pub), "recent90": recent90,
             "regions": d["regions"], "n_sources": len(manifest), "n_cats": len(NAV), "n_census": len(CENSUS),
             "doc_version": "1.0", "doc_date": "2026-10-13", "doc_date_ar": ar_date("2026-10-13"),
             "colors": {"الهيئة العامة للإحصاء": "#028BAF", "منصة البيانات المفتوحة (سدايا)": "#15A890", "وزارة البلديات والإسكان": "#DD861F",
                        "fresh": {"خلال 3 أشهر": "#028BAF", "3 – 12 شهراً": "#8FC6D6", "أكثر من سنة": "#DD861F", "غير محدد": "#CFD8DC"},
                        "agg": {"مجموع المناطق": "#028BAF", "متوسط المناطق": "#106263"}},
             "orders": {"cat": [CAT_NAME[c] for c in CAT_ORDER], "fresh": ["خلال 3 أشهر", "3 – 12 شهراً", "أكثر من سنة", "غير محدد"],
                        "entity": ["الهيئة العامة للإحصاء", "منصة البيانات المفتوحة (سدايا)", "وزارة البلديات والإسكان"]}},
    "records": records,
}

tpl = open(Path(__file__).parent / "guide_template.html", encoding="utf-8").read()
MAP_SRC = re.search(r'<svg id="saudi-map".*?</svg>', (V2 / "index.html").read_text(encoding="utf-8"), re.S).group(0)
MAP = "".join(f'<path class="m{" on" if reg == "الرياض" else ""}" d="{dd}"/>' for _, reg, dd in re.findall(r'<path id="([^"]+)" data-region="([^"]+)" d="([^"]+)"', MAP_SRC))
html = tpl.replace("/*__DATA__*/", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/")).replace("<!--__MAP__-->", MAP)
OUT.write_text(html, encoding="utf-8")
print("written", OUT, len(html), "bytes;", len(records), "records;", len(src_rows), "sources; recent90", recent90, "latest", latest_pub)
