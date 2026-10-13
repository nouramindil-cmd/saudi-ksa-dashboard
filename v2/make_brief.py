# -*- coding: utf-8 -*-
"""صفحة تعريفية بما الجديد في لوحة بيانات المملكة (الإصدار الثاني) — بهوية مركز الدراسات والأبحاث / وزارة البلديات والإسكان.
المخرجات: Downloads\\ما الجديد في لوحة بيانات المملكة.html"""
import base64
from datetime import date
from pathlib import Path

logo = base64.b64encode(Path(r"C:\Users\lenovo\dashboard_hub\momah-logo-white.png").read_bytes()).decode()

ADDED = [
    ("التعليم", ["الفصول الدراسية (حكومي، بنين وبنات)", "معاهد التدريب التقني الحكومية والأهلية", "الطلاب حسب القطاع: حكومي، أهلي، عالمي وأجنبي", "الطلاب السعوديون وغير السعوديين بكل مرحلة"]),
    ("الصحة", ["المستشفيات حكومي وخاص", "أسرّة المستشفيات", "مراكز الرعاية الصحية الأولية والمجمعات الطبية", "صيدليات القطاع الخاص", "معدل زيارات الأطفال لمقدمي الرعاية", "رضا الأطفال عن وقت الاستشارة", "زيارات طبيب الأسنان للأطفال"]),
    ("ذوو الإعاقة", ["الحالة المهنية: على رأس العمل، قادر، باحث", "الحالة التعليمية", "كبار السن من ذوي الإعاقة", "كبار السن حسب الجنس والحالة الاجتماعية والمهنية"]),
    ("سوق العمل", ["مشتركو التأمينات: سعوديون وغير سعوديين", "العاملون في الخدمة المدنية", "المشتركون الجدد كل ربع", "الأمهات المستفيدات من دعم قرة", "أطفال قرة حسب الحالة الاجتماعية للأم ووجود إعاقة"]),
    ("المرأة", ["المشتركات في التأمينات سعوديات وغير سعوديات", "موظفات الخدمة المدنية", "المشتركات الجدد كل ربع", "نسبة الإناث من المشتغلين السعوديين", "متوسط دخل الأسرة حسب جنس رئيسها", "خصوبة النساء 15–19 سنة"]),
    ("السكان والإسكان", ["المساكن حسب النوع: فلل، شقق، أدوار، شعبي", "المساكن حسب حجم الأسرة", "المواليد الأحياء: الإجمالي", "المواليد حسب نوع الولادة والجنس والجنسية"]),
    ("القطاع غير الربحي", ["الكيانات حسب جهة الإشراف", "الكيانات حسب مجال النشاط"]),
    ("التجارة", ["فروع البنوك", "أجهزة الصراف الآلي", "المدن الصناعية", "المصانع المنتجة", "اللجان الفرعية للغرف التجارية"]),
    ("الرياضة", ["المدن والاستادات الرياضية", "الأندية الرياضية", "بيوت الشباب"]),
    ("الخدمات البلدية", ["توزيع البلديات حسب فئاتها", "مساحة المسطحات الخضراء"]),
]

sections_html = "".join(
    f'<div class="sec"><div class="sec-h"><span class="n">{len(items)}</span><h3>{name}</h3></div><ul>'
    + "".join(f"<li>{it}</li>" for it in items) + "</ul></div>"
    for name, items in ADDED)
total_added = sum(len(i) for _, i in ADDED)

HTML = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ما الجديد في لوحة بيانات المملكة</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--teal-900:#003A37;--teal-700:#006C67;--teal-500:#009A93;--lime:#9BC73E;--ground:#F3F6F5;--card:#FFFFFF;--ink:#17201F;--ink-2:#3C4A48;--muted:#6B7A78;--line:#D9E2E0;--tint:#E6F1F0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{color-scheme:light}}
body{{font-family:"IBM Plex Sans Arabic",system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--ground);color:var(--ink);line-height:1.7;font-size:15px;-webkit-font-smoothing:antialiased}}
.num{{font-variant-numeric:tabular-nums}}
h1,h2,h3{{line-height:1.3;font-weight:600;text-wrap:balance}}

/* الشريط العلوي */
.band{{background:var(--teal-900);color:#fff;position:relative;overflow:hidden}}
.band::after{{content:"";position:absolute;inset:auto -10% -60% auto;width:52%;height:140%;background:radial-gradient(closest-side,rgba(0,154,147,.35),transparent 70%);pointer-events:none}}
.band-in{{max-width:1100px;margin:0 auto;padding:28px 24px 34px;position:relative}}
.band-top{{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}}
.band img{{height:58px;width:auto}}
.center{{text-align:left;font-size:13px;color:rgba(255,255,255,.78);line-height:1.5}}
.center b{{display:block;color:#fff;font-weight:600;font-size:15px}}
.eyebrow{{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;letter-spacing:.3px;color:var(--lime);font-weight:600;margin-top:28px}}
.eyebrow::before{{content:"";width:22px;height:2px;background:var(--lime)}}
.band h1{{font-size:clamp(26px,3.6vw,38px);margin-top:8px;max-width:22ch}}
.band p.lead{{max-width:62ch;color:rgba(255,255,255,.82);margin-top:10px;font-size:15.5px}}

.wrap{{max-width:1100px;margin:0 auto;padding:0 24px 48px}}

/* المقارنة */
.compare{{display:grid;grid-template-columns:1fr auto 1fr;gap:20px;align-items:stretch;margin-top:-26px}}
.big{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 24px;box-shadow:0 10px 30px rgba(0,58,55,.08)}}
.big .l{{font-size:13px;color:var(--muted);font-weight:500}}
.big .v{{font-size:clamp(44px,6vw,64px);font-weight:700;line-height:1;margin:6px 0 4px;color:var(--teal-900)}}
.big.after .v{{color:var(--teal-500)}}
.big .s{{font-size:13.5px;color:var(--ink-2)}}
.arrow{{display:flex;align-items:center;justify-content:center;color:var(--teal-500);font-size:34px;font-weight:300}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-top:18px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.stat .v{{font-size:26px;font-weight:600;color:var(--teal-900);line-height:1.15}}
.stat .l{{font-size:12.5px;color:var(--muted);margin-top:2px}}

/* الأقسام */
section{{margin-top:44px}}
.sh{{display:flex;align-items:baseline;gap:14px;margin-bottom:16px}}
.sh h2{{font-size:22px;color:var(--teal-900)}}
.sh span{{font-size:13px;color:var(--muted)}}
.sh::after{{content:"";flex:1;height:1px;background:var(--line);align-self:center}}

.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 18px 16px;position:relative}}
.tile::before{{content:"";position:absolute;top:0;right:0;left:0;height:3px;border-radius:12px 12px 0 0;background:var(--teal-500)}}
.tile .ic{{width:36px;height:36px;border-radius:9px;background:var(--tint);display:flex;align-items:center;justify-content:center;margin-bottom:12px}}
.tile .ic svg{{width:20px;height:20px;fill:none;stroke:var(--teal-700);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.tile h3{{font-size:15.5px;margin-bottom:6px}}
.tile p{{font-size:13.5px;color:var(--ink-2)}}

.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.sec{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.sec-h{{display:flex;align-items:center;gap:10px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
.sec-h h3{{font-size:15.5px;color:var(--teal-900)}}
.sec-h .n{{font-size:12px;font-weight:600;color:var(--teal-700);background:var(--tint);border-radius:999px;padding:1px 9px;min-width:26px;text-align:center}}
.sec ul{{list-style:none;display:flex;flex-direction:column;gap:5px}}
.sec li{{font-size:13.5px;color:var(--ink-2);padding-right:16px;position:relative}}
.sec li::before{{content:"";position:absolute;right:0;top:.72em;width:7px;height:7px;border-radius:2px;background:var(--lime)}}

.note{{background:var(--tint);border-right:3px solid var(--teal-500);border-radius:8px;padding:12px 16px;font-size:13.5px;color:var(--ink-2);margin-top:14px}}
footer{{max-width:1100px;margin:0 auto;padding:18px 24px 40px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line)}}

@media (max-width:720px){{.compare{{grid-template-columns:1fr}}.arrow{{transform:rotate(90deg);font-size:28px}}.band-top{{flex-direction:column;align-items:flex-start}}.center{{text-align:right}}}}
@media print{{body{{background:#fff}}.band{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}.big,.stat,.tile,.sec{{box-shadow:none;break-inside:avoid}}section{{margin-top:26px}}@page{{size:A4;margin:12mm}}}}
</style>
</head>
<body>
<header class="band"><div class="band-in">
  <div class="band-top">
    <img src="data:image/png;base64,{logo}" alt="وزارة البلديات والإسكان">
    <div class="center"><b>مركز الدراسات والأبحاث</b>وزارة البلديات والإسكان</div>
  </div>
  <div class="eyebrow">الإصدار الثاني</div>
  <h1>ما الجديد في لوحة بيانات المملكة العربية السعودية</h1>
  <p class="lead">تحليل شامل لبيانات 13 منطقة إدارية، بمصادر رسمية موثّقة وآلية تحديث ومتابعة مستمرة.</p>
</div></header>

<main class="wrap">
  <div class="compare">
    <div class="big before"><div class="l">الإصدار الأول</div><div class="v num">75</div><div class="s">مقياساً على مستوى المناطق، تُحدَّث يدوياً</div></div>
    <div class="arrow">←</div>
    <div class="big after"><div class="l">الإصدار الثاني</div><div class="v num">163</div><div class="s">مقياساً على مستوى المناطق، من مصادر رسمية موثّقة</div></div>
  </div>
  <div class="stats">
    <div class="stat"><div class="v num">88</div><div class="l">مقياساً مضافاً لم يكن موجوداً</div></div>
    <div class="stat"><div class="v num">29</div><div class="l">مصدراً رسمياً مربوطاً</div></div>
    <div class="stat"><div class="v num">14</div><div class="l">قسماً يتحدث من مصدره</div></div>
    <div class="stat"><div class="v num">13</div><div class="l">منطقة إدارية</div></div>
  </div>

  <section>
    <div class="sh"><h2>التحديث والمتابعة</h2><span>ما تغيّر في طريقة العمل</span></div>
    <div class="tiles">
      <div class="tile"><div class="ic"><svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-3-6.7M21 3v6h-6"/></svg></div><h3>تحديث دوري من قبل فريق العمل</h3><p>فحص المصادر الرسمية بشكل دوري، وسحب الإصدارات الجديدة فور نشرها من هيئة الإحصاء ووزارة البلديات والإسكان ومنصة البيانات المفتوحة.</p></div>
      <div class="tile"><div class="ic"><svg viewBox="0 0 24 24"><path d="M3 17l6-6 4 4 8-8M15 7h6v6"/></svg></div><h3>متابعة إصدارات الجهات</h3><p>متابعة ما يصدر ربعياً وسنوياً، وإضافة السنوات والأرباع الجديدة إلى السلاسل الزمنية في موضعها.</p></div>
      <div class="tile"><div class="ic"><svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6"/></svg></div><h3>توثيق كل رقم</h3><p>كل مقياس يحمل سنة بياناته وتاريخ نشر الجهة ورابط الملف الأصلي والجدول الذي أُخذ منه.</p></div>
      <div class="tile"><div class="ic"><svg viewBox="0 0 24 24"><path d="M12 3v12M8 11l4 4 4-4M4 17v3h16v-3"/></svg></div><h3>تنزيل البيانات</h3><p>أي قسم أو مقياس أو كل المؤشرات بصيغة Excel أو CSV، مع ورقة للمصادر.</p></div>
    </div>
  </section>

  <section>
    <div class="sh"><h2>البيانات المضافة</h2><span>{total_added} بنداً جديداً في عشرة أقسام</span></div>
    <div class="grid">{sections_html}</div>
    <div class="note">بقية المقاييس من الإصدار الأول ما زالت موجودة وتحدّثت إلى أحدث إصدار منشور، وبيانات تعداد السكان 2022 ثابتة حتى صدور التعداد القادم.</div>
  </section>
</main>
<footer><span>مركز الدراسات والأبحاث · وزارة البلديات والإسكان</span><span>{date.today().strftime('%Y/%m/%d')}</span></footer>
</body>
</html>
"""
out = Path.home() / "Downloads" / "ما الجديد في لوحة بيانات المملكة.html"
out.write_text(HTML, encoding="utf-8")
print(out, f"{out.stat().st_size / 1e3:.0f} KB", "| added:", total_added)
