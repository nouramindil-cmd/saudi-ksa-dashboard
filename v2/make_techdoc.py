# -*- coding: utf-8 -*-
"""الدليل التقني الكامل للوحة بيانات المملكة — للقراءة قبل الاجتماع مع فريق التحول الرقمي.
المخرجات: Downloads\\الدليل التقني للوحة بيانات المملكة.html"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
man = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))["indicators"]
dash = json.loads((ROOT / "data" / "dashboard.json").read_text(encoding="utf-8"))
n_metrics = sum(len(c["metrics"]) for c in dash["categories"].values())

SRC_NAME = {"gastat_pub": "هيئة الإحصاء (نشرات Excel)", "momah": "وزارة البلديات والإسكان (بيانات مفتوحة)", "odp": "منصة البيانات المفتوحة (سدايا)", "census_tableau": "تعداد 2022 (ثابت)"}
RUNNER = {"cloud": "سحابي يومي", "local": "من جهاز الموظف"}
rows = []
for k, v in reg["indicators"].items():
    m = man.get(k, {})
    rows.append(f"<tr><td>{v['name']}</td><td>{SRC_NAME[v['source']]}</td><td>{RUNNER[reg['sources'][v['source']]['runner']] if v['source'] != 'census_tableau' else 'ثابت'}</td><td>{(m.get('source_date') or '—')[:10]}</td></tr>")
sources_table = "".join(rows)

HTML = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>الدليل التقني للوحة بيانات المملكة</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--navy:#13315C;--navy-2:#1F4E9C;--gold:#B07D00;--ink:#111827;--ink-2:#374151;--muted:#6B7280;--line:#E3E6EB;--bg:#F4F5F7;--card:#fff;--tint:#EEF2F8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"IBM Plex Sans Arabic",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.85;font-size:15px}}
.top{{background:var(--navy);color:#fff;padding:34px 24px}}
.top-in{{max-width:1080px;margin:0 auto}}
.top .eyebrow{{color:#D9B55C;font-size:12.5px;font-weight:600;letter-spacing:.3px}}
.top h1{{font-size:clamp(24px,3.4vw,34px);font-weight:700;margin-top:6px;line-height:1.3}}
.top p{{color:rgba(255,255,255,.8);margin-top:8px;max-width:70ch}}
.layout{{max-width:1080px;margin:0 auto;display:grid;grid-template-columns:220px minmax(0,1fr);gap:28px;padding:28px 24px 60px}}
nav{{position:sticky;top:16px;align-self:start;font-size:13px}}
nav a{{display:block;color:var(--ink-2);text-decoration:none;padding:5px 10px;border-right:2px solid transparent}}
nav a:hover{{color:var(--navy-2);border-right-color:var(--gold)}}
main{{min-width:0}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:22px 26px;margin-bottom:18px}}
h2{{font-size:20px;color:var(--navy);margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
h3{{font-size:15.5px;margin:16px 0 6px;color:var(--ink)}}
p{{margin-bottom:8px;color:var(--ink-2)}}
ul,ol{{padding-right:22px;margin-bottom:8px;color:var(--ink-2)}}
li{{margin-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}}
th{{text-align:right;color:var(--muted);font-weight:600;font-size:12.5px;padding:7px 9px;border-bottom:1px solid #CBD2DB}}
td{{padding:7px 9px;border-bottom:1px solid var(--line);color:var(--ink-2);vertical-align:top}}
code{{font-family:Consolas,monospace;font-size:12.5px;background:var(--tint);padding:1px 6px;border-radius:4px;direction:ltr;display:inline-block}}
.note{{background:var(--tint);border-right:3px solid var(--gold);border-radius:6px;padding:10px 14px;margin:10px 0;font-size:14px}}
.flow{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}}
.step{{background:var(--tint);border-radius:8px;padding:12px;font-size:13.5px;position:relative}}
.step b{{display:block;color:var(--navy);margin-bottom:4px}}
.step::after{{content:"←";position:absolute;left:-14px;top:40%;color:var(--navy-2);font-size:18px}}
.step:last-child::after{{content:""}}
.kv{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:10px 0}}
.kv div{{background:var(--tint);border-radius:8px;padding:10px 12px}}
.kv b{{display:block;font-size:22px;color:var(--navy);font-variant-numeric:tabular-nums}}
.kv span{{font-size:12.5px;color:var(--muted)}}
.q{{font-weight:600;color:var(--ink);margin-top:10px}}
footer{{max-width:1080px;margin:0 auto;padding:0 24px 40px;font-size:12.5px;color:var(--muted)}}
@media (max-width:820px){{.layout{{grid-template-columns:1fr}}nav{{position:static;display:flex;flex-wrap:wrap;gap:4px}}.flow{{grid-template-columns:1fr}}.step::after{{content:""}}}}
@media print{{nav{{display:none}}.layout{{display:block}}section{{break-inside:avoid;border:0;padding:0 0 14px}}@page{{size:A4;margin:14mm}}}}
</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="eyebrow">دليل تقني للنقاش مع فريق التحول الرقمي</div>
  <h1>لوحة بيانات المملكة العربية السعودية: كيف بُنيت وكيف تعمل وما تحتاجه</h1>
  <p>شرح كامل لبنية النظام وطريقة الربط بالجهات وآلية التحديث والتشغيل الحالي، ومتطلبات نقله إلى بيئة مؤسسية.</p>
</div></header>

<div class="layout">
<nav>
  <a href="#s1">1. الخلاصة</a><a href="#s2">2. ما كان قبل</a><a href="#s3">3. مكوّنات النظام</a><a href="#s4">4. الربط بكل جهة</a><a href="#s5">5. كشف التحديث</a><a href="#s6">6. المحلّلات</a><a href="#s7">7. الواجهة</a><a href="#s8">8. التشغيل الحالي</a><a href="#s9">9. الملفات والحجم</a><a href="#s10">10. المصادر</a><a href="#s11">11. القيود</a><a href="#s12">12. متطلبات الخادم</a><a href="#s13">13. خطة النقل</a><a href="#s14">14. أسئلة متوقعة</a><a href="#s15">15. مسرد</a>
</nav>
<main>

<section id="s1"><h2>1. الخلاصة</h2>
<div class="kv"><div><b>29</b><span>مصدراً رسمياً مربوطاً</span></div><div><b>{n_metrics}</b><span>مقياساً على مستوى المناطق</span></div><div><b>13</b><span>منطقة إدارية</span></div><div><b>22</b><span>قسماً (14 يتحدث من مصدره + 8 تعداد)</span></div><div><b>يومي</b><span>تشغيل تلقائي منذ 4 أكتوبر 2026</span></div></div>
<p>اللوحة نظام من ثلاث طبقات: <b>جامع</b> يزور المصادر الرسمية ويسحب الإصدارات الجديدة، <b>محلّلات</b> تحوّل الملفات إلى أرقام موحّدة بالمناطق، و<b>واجهة ويب</b> تعرضها. كل رقم يحمل سنة بياناته وتاريخ نشر الجهة ورابط ملفه الأصلي. النظام يعمل حالياً على استضافة عامة مجانية، وجزء منه على جهاز الموظف، وهذا ما نريد نقله إلى بيئة مؤسسية.</p>
</section>

<section id="s2"><h2>2. ما كان قبل</h2>
<p>الإصدار الأول كان صفحة ويب تعرض ملف أرقام واحداً أُدخل يدوياً من ملفات Excel. لم يكن هناك أي اتصال بالجهات: كل تحديث يعني أن يفتح أحدهم موقع الجهة، ينزّل الملف، يعدّل الأرقام بيده، ويرفعها. النتيجة: توقفت الأرقام عند أبريل 2026، ومصدر التعليم القديم اختفى من الإنترنت، واختلطت بيانات تعداد 2022 مع أرقام 2024 بلا تمييز.</p>
</section>

<section id="s3"><h2>3. مكوّنات النظام</h2>
<div class="flow">
  <div class="step"><b>1. سجل المصادر</b>ملف نصي (JSON) يصف كل مؤشر: الجهة، القسم في موقعها، نمط اسم الملف أو رقم المجموعة، وأي جدول يُقرأ.</div>
  <div class="step"><b>2. الجامع</b>برنامج بايثون يزور كل مصدر، يقارن تاريخ النشر وبصمة الملف بما لدينا، وينزّل الجديد فقط إلى مجلد الملفات الخام.</div>
  <div class="step"><b>3. المحلّلات</b>لكل نوع ملف قارئ يعرف شكله (الورقة، الأعمدة، الصفوف) ويحوّله إلى قيم للمناطق الثلاث عشرة في ملف أرقام موحّد.</div>
  <div class="step"><b>4. الواجهة</b>صفحة ويب واحدة تقرأ ملف الأرقام وتعرضه: خريطة، بطاقات، رسوم، بحث، فلتر سنة، تنزيل Excel.</div>
</div>
<p>لا توجد قاعدة بيانات ولا خادم تطبيقات. المخرجات ملفات: ملف الأرقام الموحّد، ملف التتبع، والملفات الخام. الصفحة ثابتة (HTML) تقرأ هذه الملفات عند فتحها.</p>
<h3>حجم الكود</h3>
<p>نحو 1,900 سطر بايثون موزعة على خمسة ملفات: <code>collect.py</code> الجامع، <code>parsers.py</code> و<code>build.py</code> المحلّلات والبناء، <code>collectors/odp.py</code> جزء سدايا، <code>make_ui.py</code> مولّد الواجهة. المكتبات المستخدمة قياسية: requests لطلبات الويب، openpyxl لقراءة Excel، playwright لتشغيل المتصفح في جزء سدايا.</p>
</section>

<section id="s4"><h2>4. طريقة الربط بكل جهة</h2>
<h3>هيئة الإحصاء (www.stats.gov.sa)</h3>
<p>الموقع مبني على منصة Liferay ويقبل الطلبات المباشرة بلا حساب ولا مفتاح. لكل قسم إحصائي رقم تصنيف، وصفحة القسم تعرض النشرات كملفات Excel بروابط ثابتة تحمل في نهايتها طابع وقت التعديل بالملّي ثانية. الجامع:</p>
<ol><li>يطلب صفحة القسم: <code>/ar/statistics-tabs?tab=436312&category=رقم_القسم</code>.</li><li>يستخرج روابط ملفات Excel، ويتجاهل صندوق «أحدث النشرات» أعلى الصفحة لأنه يعرض نشرة من قسم آخر.</li><li>يطابق اسم الملف بنمط المؤشر (مثل Register-based Labour Market) ويختار أحدث سنة وربع في الاسم، ثم أحدث تاريخ رفع.</li><li>ينزّل الملف إن كان أحدث مما لدينا.</li></ol>
<p>أرقام الأقسام المستخدمة: سوق العمل السجلي 124074، مسح القوى العاملة 417515، المنشآت السياحية 124304، مؤشر أسعار العقارات 121920، إحصاءات الخدمات 124988، المنشآت الصحية 2968800، الرعاية الصحية 123812، إحصاءات المساكن 3175009، النوع الاجتماعي 123614. شجرة الأقسام نفسها تُقرأ من واجهة JSON مفتوحة في الموقع.</p>
<div class="note">للهيئة أيضاً واجهة API رسمية على <code>api.stats.gov.sa</code> تتطلب مفتاحاً من بوابة المطوّرين <code>dp.stats.gov.sa</code> بعد تسجيل تطبيق. لم تُستخدم بعد لأن النشرات تكفي للمؤشرات الحالية، وهي الخطوة المناسبة لإضافة مؤشرات وطنية (التضخم، البطالة، الناتج) لاحقاً.</div>
<h3>وزارة البلديات والإسكان (momah.gov.sa)</h3>
<p>صفحة البيانات المفتوحة جدول HTML عادي في 34 صفحة، كل صف فيه اسم المجموعة وتاريخ الإنشاء وروابط CSV وExcel وPDF. الجامع يقرأ الصفحات كلها، يزيل التكرار (كل صف مكرر ثلاث مرات لنسخ الجوال)، يطابق العنوان، ويختار الأحدث. الملفات بفاصلة منقوطة وعلى مستوى الأمانات السبع عشرة، فتُجمع إلى المناطق حسب تبعية كل أمانة.</p>
<h3>منصة البيانات المفتوحة الوطنية (open.data.gov.sa)</h3>
<p>المنصة محمية بنظام حماية من الروبوتات (Radware) يرفض أي طلب لا يأتي من متصفح حقيقي، ويرفض حتى المتصفحات المخفية. لذلك هذا الجزء يعمل بطريقة مختلفة:</p>
<ol><li>يفتح متصفح كروم فعلياً على الجهاز ليجتاز التحقق.</li><li>يحدّث فهرساً محلياً لكل مجموعات المنصة (نحو 17,900 مجموعة) من واجهة القائمة <code>/api/datasets/list</code> بترتيب تاريخ التحديث، ويتوقف عند أول مجموعة لم تتغير.</li><li>يبحث في الفهرس عن المجموعات المطلوبة بالرقم أو بجزء من العنوان (مثل «البيانات التعليمية الخاصة بالطلاب بالإدارة العامة للتعليم»، فيلتقط 16 ملفاً لكل الإدارات، ويلتقط إصدار 2026 تلقائياً حين يُنشر بنفس العنوان).</li><li>ينزّل الملفات عبر المتصفح تسلسلياً بتريّث، لأن التنزيل المتوازي يؤدي إلى حجب مؤقت.</li></ol>
<div class="note">هذا الجزء هو الوحيد الذي يحتاج جهازاً عليه متصفح، وهو ما نريد نقله إلى الخادم.</div>
<h3>تعداد 2022</h3>
<p>بيانات التعداد ثابتة ولا تُسحب دورياً، وتُعرض كطبقة مستقلة معلّمة بسنتها.</p>
</section>

<section id="s5"><h2>5. كيف يُكتشف التحديث</h2>
<p>لكل مؤشر سجل في ملف التتبع يحفظ: رابط آخر ملف، تاريخ نشره عند الجهة، بصمته الرقمية (SHA-256)، وتاريخ آخر فحص. عند كل تشغيل:</p>
<ol><li>إن لم يتغير الرابط ولا تاريخ النشر، يُسجَّل «بلا تغيير» ولا يُنزَّل شيء.</li><li>إن تغيّر أحدهما، يُنزَّل الملف وتُحسب بصمته؛ إن اختلفت عن السابقة يُعلَّم «محتوى جديد».</li><li>يُعاد بناء ملف الأرقام من كل الملفات الخام، وإن تغيّرت قيمة أي مقياس يُسجَّل في سجل التغيّرات.</li></ol>
<p><b>صمام أمان:</b> إن تعطل ملف عند جهة أو تغيّر شكله فجأة، لا تختفي أرقامه، بل تبقى القيم السابقة ظاهرة مع علامة، ويُصحَّح المحلّل يدوياً.</p>
</section>

<section id="s6"><h2>6. المحلّلات: من ملف الجهة إلى رقم المنطقة</h2>
<p>الجهات تنشر بأشكال مختلفة، وهذه الأنماط الخمسة تغطيها كلها:</p>
<table><tr><th>النمط</th><th>مثال</th><th>ما يفعله المحلّل</th></tr>
<tr><td>جدول على مستوى القرية والمركز</td><td>نشرة إحصاءات الخدمات: الدفاع المدني، المساجد، الغرف التجارية، الفنادق</td><td>يجد صف الترويسة، ويجمع آلاف الصفوف صعوداً إلى المنطقة الإدارية</td></tr>
<tr><td>جدول بسيط: المنطقة في العمود الأول</td><td>المستشفيات والأسرّة، الفنادق ربعياً، مشتركو التأمينات</td><td>يقرأ الأعمدة المطلوبة بالاسم أو بالرقم لكل صف منطقة</td></tr>
<tr><td>ملف سجلّي: صف لكل منشأة أو مستفيد</td><td>ذوو الإعاقة (30 ألف صف)، المنشآت الرياضية، مستفيدو قرة</td><td>يعدّ أو يجمع حسب عمود المنطقة، ويفكّك حسب أي بُعد (نوع الإعاقة، الجنس، الحالة المهنية)</td></tr>
<tr><td>ملفات متعددة لنفس المؤشر</td><td>16 ملفاً للطلاب بالإدارات التعليمية، 13 ملفاً للكيانات غير الربحية</td><td>يقرأها كلها، يطابق الإدارة أو الورقة بمنطقتها، ويمنع تكرار منطقة وردت في ملفين</td></tr>
<tr><td>وحدات إدارية مختلفة</td><td>أمانات الوزارة، فروع وزارة الصحة بالإنجليزية، الإدارات التعليمية</td><td>جداول مطابقة ثابتة: جدة والطائف إلى مكة، الأحساء وحفر الباطن إلى الشرقية، وهكذا</td></tr></table>
<p>المخرج موحّد لكل مقياس: الاسم، فترة البيانات (سنة أو ربع)، القيمة لكل منطقة من الثلاث عشرة، المصدر وتاريخ نشره ورابطه وموضع الجدول في الملف. المعدلات والنسب تُعلَّم لتُعرض كمتوسط لا كمجموع.</p>
<h3>السلاسل الزمنية</h3>
<p>مقاييس مثل الطلاب والمدارس ومؤشر أسعار العقارات تُبنى من إصدارات متعاقبة: السنوات القديمة من الإصدار الأول، والجديدة من الملفات المسحوبة، فتظهر 2026 في الرسوم نفسها يوم نشرها.</p>
</section>

<section id="s7"><h2>7. الواجهة</h2>
<ul><li>صفحة HTML واحدة بتصميم مؤسسي، بلا إطار عمل ثقيل؛ مكتبة الرسوم الوحيدة Chart.js، ومكتبة Excel تُحمَّل عند الطلب.</li><li>خريطة المناطق تفاعلية: اختيار منطقة يعيد عرض كل الأقسام لها، وتلوين بأي مؤشر.</li><li>بحث فوري (Ctrl+K) في كل المقاييس والمناطق والأقسام.</li><li>في كل قسم: بطاقات للمقاييس الرئيسية، لوحات تفكيك للمجموعات، رسم بالمناطق، وتبويبات: المؤشرات، تفاصيل المحافظات، المصادر.</li><li>فلتر سنة، سلاسل زمنية، تنزيل CSV وExcel للقسم أو المقياس أو كل شيء.</li><li>تعمل على الجوال، وتُطبع، ولها نسخة ملف واحد ببيانات مضمّنة للإرسال بالبريد.</li></ul>
</section>

<section id="s8"><h2>8. التشغيل الحالي</h2>
<table><tr><th>المسار</th><th>أين يعمل</th><th>متى</th><th>ما يغطيه</th></tr>
<tr><td>السحابي</td><td>GitHub Actions (خوادم GitHub)</td><td>يومياً 05:17 صباحاً بتوقيت الرياض</td><td>هيئة الإحصاء ووزارة البلديات: 15 مصدراً</td></tr>
<tr><td>المحلي</td><td>جهاز الموظف، بضغطة على ملف تشغيل</td><td>عند الحاجة (المصادر سنوية وربعية)</td><td>منصة سدايا: 11 مصدراً</td></tr></table>
<p>الكود والبيانات في مستودع Git عام على GitHub، والصفحة تُنشر منه عبر GitHub Pages. التشغيل اليومي يسحب المستودع، يشغّل الجامع ثم البناء، ويرفع ما تغيّر بنفسه. عمل بلا انقطاع منذ 4 أكتوبر 2026، ومدة التشغيل من 3 إلى 12 دقيقة.</p>
</section>

<section id="s9"><h2>9. الملفات والحجم</h2>
<table><tr><th>المجلد أو الملف</th><th>المحتوى</th><th>الحجم</th></tr>
<tr><td><code>registry.json</code></td><td>سجل المصادر</td><td>صغير</td></tr>
<tr><td><code>data/raw/</code></td><td>آخر ملف خام لكل مؤشر (Excel/CSV كما نشرته الجهة)</td><td>نحو 32 ميجا</td></tr>
<tr><td><code>data/manifest.json</code></td><td>تتبع كل مؤشر: الرابط، تاريخ النشر، البصمة، آخر فحص</td><td>صغير</td></tr>
<tr><td><code>data/dashboard.json</code></td><td>ملف الأرقام الموحّد الذي تقرأه الواجهة</td><td>نحو 0.6 ميجا</td></tr>
<tr><td><code>data/baseline_live.json</code></td><td>بيانات الإصدار الأول مع السنوات الجديدة مدمجة</td><td>نحو 0.3 ميجا</td></tr>
<tr><td><code>index.html</code></td><td>الواجهة</td><td>نحو 0.2 ميجا</td></tr></table>
<p>المشروع كله أقل من 50 ميجا. لا متطلبات خاصة للتخزين.</p>
</section>

<section id="s10"><h2>10. المصادر المربوطة</h2>
<table><tr><th>المؤشر</th><th>الجهة</th><th>طريقة التحديث</th><th>آخر نشر</th></tr>{sources_table}</table>
</section>

<section id="s11"><h2>11. القيود والمخاطر الحالية</h2>
<ul><li><b>استضافة عامة:</b> الكود والبيانات في مستودع عام على خدمة خارجية، مناسب للتجربة لا للاعتماد المؤسسي.</li><li><b>الاعتماد على GitHub:</b> التشغيل اليومي مرهون بحدود الخدمة المجانية وسياساتها.</li><li><b>جزء سدايا على جهاز شخصي:</b> إن تعطل الجهاز أو غاب الموظف توقف تحديث 11 مصدراً.</li><li><b>بلا صلاحيات:</b> الرابط عام، لا تسجيل دخول ولا سجل وصول.</li><li><b>هشاشة الشكل:</b> إن غيّرت جهة شكل ملفها يحتاج محلّلها تعديلاً يدوياً صغيراً (الأرقام السابقة تبقى ولا تختفي).</li><li><b>تواتر الجهات:</b> التحديث مرهون بالنشر؛ وزارة البلديات مثلاً آخر ما نشرته بيانات 2023.</li></ul>
</section>

<section id="s12"><h2>12. متطلبات الخادم المقترح</h2>
<table><tr><th>البند</th><th>المطلوب</th><th>لماذا</th></tr>
<tr><td>نظام التشغيل</td><td>لينكس (Ubuntu 22.04 أو أحدث)</td><td>نفس بيئة التشغيل السحابي الحالية</td></tr>
<tr><td>المواصفات</td><td>2 معالج، 4 جيجا ذاكرة، 20 جيجا تخزين</td><td>الحمل خفيف: دقائق يومياً</td></tr>
<tr><td>البرمجيات</td><td>بايثون 3.12، Git، متصفح كروم (أو Chromium) مع Xvfb</td><td>كروم لجزء سدايا حتى ينتقل عن جهاز الموظف</td></tr>
<tr><td>الوصول للإنترنت</td><td>الخادم يصل إلى: stats.gov.sa، momah.gov.sa، open.data.gov.sa (مع odp-public)</td><td><b>الشرط الأهم:</b> بلا هذا الوصول لا يوجد تحديث</td></tr>
<tr><td>الجدولة</td><td>cron يومي</td><td>بديل GitHub Actions</td></tr>
<tr><td>النشر</td><td>خادم ويب بسيط (nginx) يخدم مجلداً ثابتاً</td><td>الصفحة ملفات ثابتة لا تحتاج تطبيقاً</td></tr>
<tr><td>الصلاحيات</td><td>ربط الصفحة بالدخول الموحد أو حصرها على الشبكة الداخلية</td><td>بدل الرابط العام</td></tr>
<tr><td>الكود</td><td>مستودع Git داخلي</td><td>بدل المستودع العام</td></tr></table>
<div class="note">السؤال الذي يحسم الأمر: هل يُسمح للخادم بالوصول إلى هذه المواقع الثلاثة؟ كثير من الخوادم الحكومية مقفلة على الإنترنت الخارجي. إن كان الوصول ممنوعاً، البديل: خادم خارج الشبكة الداخلية يسحب ويدفع النتائج إلى الداخل، أو إبقاء السحب كما هو ونقل العرض فقط.</div>
</section>

<section id="s13"><h2>13. خطة النقل</h2>
<ol><li><b>التجهيز (يوم):</b> تثبيت بايثون والمكتبات وكروم، ونسخ المستودع.</li><li><b>التحقق من الوصول (ساعة):</b> تجربة طلب واحد لكل موقع من الخادم.</li><li><b>التشغيل التجريبي (أسبوع):</b> تشغيل الجامع يومياً على الخادم بالتوازي مع GitHub ومقارنة النتائج.</li><li><b>نقل جزء سدايا:</b> تشغيل جزء المتصفح على الخادم بدل جهاز الموظف.</li><li><b>النشر الداخلي:</b> خدمة مجلد الواجهة من خادم الويب الداخلي، وربط الدخول.</li><li><b>الإغلاق:</b> إيقاف التشغيل على GitHub وجعل المستودع خاصاً أو حذفه.</li></ol>
</section>

<section id="s14"><h2>14. أسئلة متوقعة وأجوبتها</h2>
<p class="q">لماذا لا توجد قاعدة بيانات؟</p><p>حجم البيانات صغير (163 مقياساً × 13 منطقة) وملف واحد يكفي ويسهّل النقل. البيانات منظمة ويمكن تحميلها إلى أي قاعدة لو أرادوا ربطها بأنظمتهم.</p>
<p class="q">هل فيه API؟</p><p>المخرجات ملفات JSON منظمة؛ تقديمها كواجهة API من الخادم أمر مباشر. وللهيئة API رسمي يمكن ربطه بمفتاح مؤسسي.</p>
<p class="q">ماذا لو غيّرت الجهة شكل ملفها؟</p><p>يتعطل محلّل ذلك المؤشر فقط، وتبقى أرقامه السابقة ظاهرة. التصحيح تعديل صغير في المحلّل.</p>
<p class="q">من يصون النظام؟</p><p>بايثون قياسية بمكتبات شائعة، والكود مقسّم ومعلّق عليه بالعربية. أي مطور بايثون يستطيع صيانته.</p>
<p class="q">هل السحب من هذه المواقع مسموح؟</p><p>كلها بيانات منشورة للعموم، تُسحب بالطريقة نفسها التي يفتحها بها أي متصفح، وبتريّث لا يحمّل المواقع. ولا تُستخدم أي بيانات شخصية.</p>
<p class="q">كم يكلف؟</p><p>لا تراخيص ولا اشتراكات. التكلفة خادم صغير فقط.</p>
<p class="q">كيف نضيف مؤشراً جديداً؟</p><p>سطر في سجل المصادر يحدد الجهة والملف والجدول، ومحلّل من الأنماط الخمسة الجاهزة. معظم الإضافات الأخيرة استغرقت دقائق.</p>
</section>

<section id="s15"><h2>15. مسرد</h2>
<table><tr><th>المصطلح</th><th>المعنى</th></tr>
<tr><td>GitHub</td><td>خدمة لاستضافة الكود ومتابعة تغييراته؛ تُستخدم حالياً للكود والبيانات والنشر والتشغيل اليومي</td></tr>
<tr><td>GitHub Actions</td><td>خدمة تشغيل مهام مجدولة على خوادم GitHub؛ تشغّل الجامع كل صباح</td></tr>
<tr><td>GitHub Pages</td><td>نشر صفحة ويب ثابتة من المستودع؛ هو الرابط الحالي</td></tr>
<tr><td>JSON</td><td>صيغة ملف نصي منظم لتبادل البيانات؛ كل مخرجات النظام بها</td></tr>
<tr><td>Radware</td><td>نظام حماية من الروبوتات تستخدمه منصة سدايا؛ سبب الحاجة إلى متصفح حقيقي</td></tr>
<tr><td>SHA-256</td><td>بصمة رقمية للملف تتغير إن تغيّر أي جزء من محتواه؛ تُستخدم لكشف التحديث</td></tr>
<tr><td>cron</td><td>مجدول المهام في لينكس؛ بديل GitHub Actions على الخادم</td></tr>
<tr><td>Playwright</td><td>مكتبة تشغّل المتصفح برمجياً؛ تُستخدم لجزء سدايا</td></tr></table>
</section>

</main></div>
<footer>أُعدّ للنقاش الداخلي · {date.today().strftime('%Y/%m/%d')}</footer>
</body></html>
"""
out = Path.home() / "Downloads" / "الدليل التقني للوحة بيانات المملكة.html"
out.write_text(HTML, encoding="utf-8")
print(out, f"{out.stat().st_size / 1e3:.0f} KB")
