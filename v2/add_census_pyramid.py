# -*- coding: utf-8 -*-
"""
يضيف الهرم السكاني التفصيلي (منطقة × جنسية × جنس × 21 فئة عمرية) إلى
categories.census_population.pyramid_detail في baseline.json و baseline_live.json.

المصدر: الهيئة العامة للإحصاء — تعداد السعودية 2022، «السكان حسب الفئات العمرية التفصيلية»
(منصة البيانات المفتوحة، المجموعة 7c1dfcdc). الإجمالي يطابق التعداد: 32,175,224.
التشغيل: python add_census_pyramid.py [مسار ملف xlsx]
"""
import glob
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
DEFAULT = glob.glob(str(Path.home() / "opendata_sync/files/general authority for statistics gastat/Population by detailed Age__7c1dfcdc/*.xlsx"))
REGION = {"Ar Riyadh": "الرياض", "Makkah Al Mukarramah": "مكة المكرمة", "Al Madinah Al Munawwarah": "المدينة المنورة", "Al Qaseem": "القصيم",
          "Eastern Region": "المنطقة الشرقية", "Aseer": "عسير", "Tabuk": "تبوك", "Hail": "حائل", "Northern Borders": "الحدود الشمالية",
          "Jazan": "جازان", "Najran": "نجران", "Al Bahah": "الباحة", "Al Jawf": "الجوف"}
AGES = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64",
        "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-99", "100+"]
NAT = {"Saudi": "saudi", "Non-Saudi": "non_saudi"}
SEX = {"Male": "m", "Female": "f"}

src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT[0]
df = pd.read_excel(src)
df.columns = [c.strip() for c in df.columns]
assert set(df["Region"]) == set(REGION) and set(df["Age Group"]) == set(AGES)
assert int(df["Population"].sum()) == 32175224, df["Population"].sum()


def block(d):
    g = d.groupby(["Nationality", "Gender", "Age Group"])["Population"].sum()
    return {NAT[n]: {SEX[s]: [int(g.get((n, s, a), 0)) for a in AGES] for s in SEX} for n in NAT}


detail = {"ages": AGES, "regions": {"المملكة": block(df)}}
for en, ar in REGION.items():
    detail["regions"][ar] = block(df[df["Region"] == en])

for name in ("baseline.json", "baseline_live.json"):
    p = ROOT / "data" / name
    d = json.loads(p.read_text(encoding="utf-8"))
    d["categories"]["census_population"]["pyramid_detail"] = detail
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(name, "ok")
