# -*- coding: utf-8 -*-
"""
يولّد v2/index.html بتصميم «تقرير مؤسسي رصين»:
  - هيكل جديد بالكامل (ترويسة، قائمة جانبية مجمّعة، خريطة، محتوى) بلا إيموجي ولا تدرجات.
  - يعيد استخدام منطق النسخة الأولى (العارضات الـ22 + الخريطة + التصدير + المقارنة) كما هو،
    مع إعادة تعريف مكوّنات العرض (البطاقات، الرسوم، الملاحظات، المصادر) بالشكل الجديد وتنقية الإيموجي.
  - الطبقة الحيّة: بطاقات المصدر، التعيير بالسكان، الترتيب، السلاسل الزمنية، مؤشر الفجوة، ملف المنطقة، المنهجية، سجل التغيّرات.
التشغيل: python make_ui.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
old = (ROOT.parent / "index.html").read_text(encoding="utf-8")
svg = re.search(r'<svg id="saudi-map".*?</svg>', old, re.S).group(0)
js = max(re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", old, re.S), key=len)

# --- منطق النسخة الأولى: نزيل محمّل البيانات القديم ونربط العارضات بالطبقة الحيّة
js = re.sub(r"// Load data - use embedded data or fetch.*?\n\}\n", "", js, count=1, flags=re.S)
js = js.replace("  if (renderers[cat]) {\n    renderers[cat](r);\n  }\n}", "  if (renderers[cat]) {\n    renderers[cat](r);\n    injectLive(cat, r);\n  }\n}")
js = js.replace("if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {",
                "if (['changes','methodology'].includes(selectedCategory)) { welcome.style.display = 'none'; content.style.display = 'block'; Object.values(charts).forEach(c => c.destroy()); charts = {}; ({changes: renderChanges, methodology: renderMethodology})[selectedCategory](); return; }\n  if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {")
assert "injectLive(cat, r)" in js and "renderMethodology" in js

NAV = [
    ("المؤشرات الحيّة", "g-live", [("population_housing", "السكان والإسكان"), ("education", "التعليم"), ("health", "الصحة"), ("disability", "ذوو الإعاقة"), ("labor", "سوق العمل والمنشآت"),
                         ("sports", "الرياضة"), ("nonprofit", "القطاع غير الربحي"), ("security", "الأمن والطوارئ"), ("infrastructure", "الخدمات البلدية"), ("tourism", "السياحة والضيافة"),
                         ("real_estate", "العقارات"), ("religious", "الشؤون الدينية"), ("commerce", "التجارة"), ("women", "المرأة")]),
    ("التحليل", "g-analysis", [("comparison", "مقارنة المناطق"), ("executive_summary", "الملخص التنفيذي")]),
    ("تعداد 2022", "g-census", [("census_population", "التركيبة السكانية"), ("census_nationality", "الجنسية"), ("census_marital", "الحالة الاجتماعية"), ("census_growth", "النمو السكاني"),
                    ("census_dependency", "الإعالة"), ("census_households", "تركيبة الأسر"), ("census_buildings", "المساكن"), ("census_units", "الوحدات السكنية")]),
    ("المرجع", "g-ref", [("methodology", "المنهجية والمصادر")]),
]
nav_html = "".join(
    f'<div class="nav-group {cls}"><div class="nav-title">{g}</div>' + "".join(
        f'<button class="cat-btn" data-cat="{k}" onclick="selectCategory(\'{k}\')"><i class="ic" data-ic="{k}"></i><span>{n}</span>'
        + (f'<span class="nav-count" id="chgCount"></span>' if k == "changes" else "") + '</button>' for k, n in items) + "</div>"
    for g, cls, items in NAV)

CSS = r"""
:root{--navy:#13315C;--navy-2:#1F4E9C;--gold:#B07D00;--teal:#0F9B8E;--brick:#A63D40;--violet:#6D5BB8;
--ink:#111827;--ink-2:#374151;--muted:#6B7280;--line:#E3E6EB;--line-2:#CBD2DB;--bg:#F4F5F7;--card:#FFFFFF;--tint:#EEF2F8;
--s1:#1F4E9C;--s2:#C28A00;--s3:#0F9B8E;--s4:#A63D40;--s5:#6D5BB8;--radius:8px}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:"IBM Plex Sans Arabic",system-ui,sans-serif;background:var(--bg);color:var(--ink);font-size:14.5px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--navy-2)}
button{font:inherit}
h1,h2,h3,h4{font-weight:600;line-height:1.3}
.num,.stat-v,.card-value,.kpi-value,.exec-kpi-value,td{font-variant-numeric:tabular-nums}

/* ترويسة */
.top{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50}
.top-in{max-width:1440px;margin:0 auto;padding:14px 28px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:14px}
.mark{width:40px;height:40px;border-radius:8px;background:var(--navy);position:relative;flex:none}
.mark::after{content:"";position:absolute;inset:12px 9px;border-top:2px solid #fff;border-bottom:2px solid var(--gold);opacity:.95}
.brand h1{font-size:19px;letter-spacing:-.2px}
.brand p{font-size:12.5px;color:var(--muted);margin-top:1px}
.brand p b{color:var(--ink-2);font-weight:600}
.top-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.btn{border:1px solid var(--line-2);background:var(--card);color:var(--ink-2);padding:7px 14px;border-radius:6px;cursor:pointer;font-size:13px}
.btn:hover{border-color:var(--navy-2);color:var(--navy-2)}
.btn.primary{background:var(--navy);border-color:var(--navy);color:#fff}
.region-badge{display:none;align-items:center;gap:8px;padding:6px 12px;border-radius:6px;background:var(--tint);color:var(--navy);font-weight:600;font-size:13px;border:1px solid #D6DFF0}
.region-badge.active{display:inline-flex}
.region-badge::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--gold)}
.reset-btn{display:none}.reset-btn.active{display:inline-block}
.year-wrap{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--muted)}
.year-wrap select{font:inherit;font-size:13px;padding:6px 10px;border:1px solid var(--line-2);border-radius:6px;background:var(--card);color:var(--ink)}

/* الهيكل */
.shell{max-width:1440px;margin:0 auto;display:grid;grid-template-columns:236px minmax(0,1fr);gap:28px;padding:24px 28px 60px}
.side{position:sticky;top:78px;align-self:start;max-height:calc(100vh - 100px);overflow:auto;padding-left:6px}
.nav-group{margin-bottom:18px}
.nav-title{font-size:11px;letter-spacing:.4px;color:var(--muted);font-weight:600;padding:0 10px 6px;text-transform:uppercase}
.cat-btn{display:flex;align-items:center;justify-content:space-between;width:100%;text-align:right;background:transparent;border:0;border-right:3px solid transparent;padding:7px 10px;border-radius:0 6px 6px 0;color:var(--ink-2);font-size:13.5px;cursor:pointer}
.cat-btn:hover{background:var(--card);color:var(--ink)}
.cat-btn.active{background:var(--card);color:var(--navy);font-weight:600;border-right-color:var(--gold)}
.nav-group{--g:var(--navy)}.g-analysis{--g:var(--gold)}.g-census{--g:var(--teal)}.g-ref{--g:#5B6B7F}
.nav-group .nav-title{color:var(--g);display:flex;align-items:center;gap:6px}
.nav-group .nav-title::before{content:"";width:8px;height:8px;border-radius:2px;background:var(--g)}
.nav-group .cat-btn{border-right-color:transparent}
.nav-group .cat-btn.active{border-right-color:var(--g);color:var(--g)}
.nav-group .cat-btn:hover{color:var(--g)}
.nav-count{font-size:11px;background:var(--tint);color:var(--navy);padding:0 7px;border-radius:9px;font-weight:600}
.content{min-width:0}
.ic{width:17px;height:17px;flex:none;display:inline-flex;color:var(--g,var(--navy-2));opacity:.85}
.ic svg{width:100%;height:100%;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.cat-btn{justify-content:flex-start;gap:9px}
.cat-btn .nav-count{margin-right:auto}
.search{position:relative;flex:1;min-width:260px;max-width:460px;display:flex;align-items:center;gap:8px;border:1px solid var(--line-2);border-radius:8px;padding:6px 10px;background:var(--bg)}
.search:focus-within{border-color:var(--navy-2);background:var(--card)}
.search svg{width:16px;height:16px;fill:none;stroke:var(--muted);stroke-width:2;stroke-linecap:round;flex:none}
.search input{border:0;background:transparent;font:inherit;font-size:13.5px;width:100%;outline:none;color:var(--ink)}
.q-res{position:absolute;top:calc(100% + 6px);right:0;left:0;background:var(--card);border:1px solid var(--line-2);border-radius:8px;box-shadow:0 12px 30px rgba(0,0,0,.12);max-height:380px;overflow:auto;z-index:60}
.q-res div{padding:8px 12px;font-size:13px;cursor:pointer;display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid var(--line)}
.q-res div:last-child{border-bottom:0}
.q-res div:hover,.q-res div.on{background:var(--tint)}
.q-res small{color:var(--muted)}
.kpi-wall{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;cursor:pointer;transition:border-color .15s,transform .15s;display:flex;flex-direction:column;gap:6px}
.tile:hover{border-color:var(--navy-2);transform:translateY(-2px)}
.tile .t-head{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12.5px}
.tile .t-head .ic{color:var(--navy-2)}
.tile .t-v{font-size:24px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;line-height:1.1}
.tile .t-l{font-size:12.5px;color:var(--ink-2)}
.tile .t-bars{display:flex;flex-direction:column;gap:3px;margin-top:4px}
.tile .t-bar{display:grid;grid-template-columns:72px 1fr 48px;align-items:center;gap:6px;font-size:11px;color:var(--muted)}
.tile .t-bar i{display:block;height:5px;border-radius:3px;background:var(--navy-2);opacity:.75}
.tile .t-bar b{font-weight:500;color:var(--ink-2);text-align:left;direction:ltr}
.crumb{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted);margin-bottom:6px;flex-wrap:wrap}
.crumb b{color:var(--ink-2);font-weight:500}
.crumb .ic{width:18px;height:18px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line-2);margin:4px 0 16px}
.tabs button{background:none;border:0;border-bottom:2px solid transparent;padding:8px 14px;font-size:13.5px;color:var(--muted);cursor:pointer;margin-bottom:-1px}
.tabs button.on{color:var(--navy);border-bottom-color:var(--gold);font-weight:600}
.tabs button span{font-size:11px;background:var(--tint);color:var(--navy);padding:0 6px;border-radius:9px;margin-right:6px}
#oldTab .summary-grid,#oldTab .kpi-section,#oldTab .insight-box,#oldTab .note,#oldTab .export-bar,#oldTab .source-box,#oldTab h2{display:none}
.src-list{display:flex;flex-direction:column;gap:10px}
.src-item{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;padding:10px 14px;border:1px solid var(--line);border-radius:8px;font-size:13px}
.src-item small{display:block;color:var(--muted);font-size:11.5px;margin-top:2px}
.grp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;margin-top:14px}
.grp-panel{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.grp-title{font-size:13px;font-weight:600;color:var(--navy);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.grp-row{display:grid;grid-template-columns:minmax(90px,1.2fr) 1fr 74px 36px;align-items:center;gap:8px;padding:5px 6px;border-radius:6px;cursor:pointer;font-size:12.5px}
.grp-row:hover{background:var(--bg)}
.grp-row.on{background:var(--tint);box-shadow:inset 0 0 0 1px var(--navy-2)}
.grp-l{color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.grp-bar{height:7px;background:var(--line);border-radius:4px;overflow:hidden}.grp-bar i{display:block;height:100%;background:var(--navy-2);border-radius:4px}
.grp-v{font-weight:600;color:var(--navy);text-align:left;direction:ltr;font-variant-numeric:tabular-nums}
.grp-s{color:var(--muted);text-align:left;direction:ltr;font-size:11px}
.grp-foot{font-size:11px;color:var(--muted);margin-top:6px}
.more-btn{margin:10px 0 4px}
.live-group{display:none}
.menu{position:relative}
.menu-list{position:absolute;top:calc(100% + 6px);left:0;min-width:260px;background:var(--card);border:1px solid var(--line-2);border-radius:8px;box-shadow:0 12px 30px rgba(0,0,0,.12);z-index:70;padding:4px}
.menu-list button{display:block;width:100%;text-align:right;background:none;border:0;padding:8px 12px;font-size:13px;color:var(--ink-2);cursor:pointer;border-radius:6px}
.menu-list button:hover{background:var(--tint);color:var(--navy)}
.dl{display:inline-flex;gap:4px;margin-right:8px}
.dl button{font-size:11px;padding:1px 8px;border:1px solid var(--line-2);border-radius:999px;background:var(--card);color:var(--ink-2);cursor:pointer}
.dl button:hover{border-color:var(--navy-2);color:var(--navy-2)}
@media print{.dl,.menu{display:none!important}}
.flash{animation:flash 1.6s ease}
@keyframes flash{0%{box-shadow:0 0 0 3px rgba(176,125,0,.6)}100%{box-shadow:0 0 0 3px rgba(176,125,0,0)}}

/* أقسام وبطاقات */
.panel{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px}
.sec-head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.sec-head h2{font-size:21px}
.sec-head .sub{font-size:12.5px;color:var(--muted)}
.eyebrow{font-size:11.5px;letter-spacing:.3px;color:var(--gold);font-weight:600;margin-bottom:4px}
.map-section{margin-bottom:22px}
.map-wrap{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;align-items:start}
.map-container{display:flex;justify-content:center;background:var(--card)}
#saudi-map{width:100%;max-width:680px;height:auto}
#saudi-map path{fill:#D5DEEC;stroke:#fff;stroke-width:1.4;cursor:pointer;transition:fill .2s}
#saudi-map path:hover{fill:#B9C8E0}
#saudi-map path.selected{fill:var(--navy);stroke:var(--gold);stroke-width:2}
.region-label{font-family:"IBM Plex Sans Arabic";font-weight:600;fill:var(--ink-2);pointer-events:none;text-anchor:middle;dominant-baseline:central}
#saudi-map path.selected + .region-label{fill:#fff}
.map-tooltip{position:fixed;background:var(--navy);color:#fff;padding:8px 14px;border-radius:6px;font-size:13px;pointer-events:none;z-index:1000;display:none;box-shadow:0 6px 20px rgba(0,0,0,.18)}
.map-side h3{font-size:14px;margin-bottom:10px}
.heatmap-bar{display:flex;flex-direction:column;gap:10px}
.heatmap-bar label{font-size:12.5px;color:var(--muted)}
.heatmap-bar select,.compare-selectors select{width:100%;font:inherit;font-size:13.5px;padding:8px 10px;border:1px solid var(--line-2);border-radius:6px;background:var(--card);color:var(--ink)}
.heatmap-legend{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
.heatmap-gradient{flex:1;height:8px;border-radius:4px;background:linear-gradient(90deg,#E3EAF5,#13315C)}
.heatmap-reset{align-self:flex-start;background:none;border:0;color:var(--brick);font-size:12.5px;cursor:pointer;padding:0}
.map-hint{font-size:12px;color:var(--muted)}
.region-list{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:12px}
.region-list button{text-align:right;background:none;border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:12.5px;color:var(--ink-2);cursor:pointer}
.region-list button:hover{border-color:var(--navy-2);color:var(--navy-2)}

.welcome-screen h2{font-size:21px;margin-bottom:6px}
.welcome-screen>p{color:var(--muted);font-size:13.5px;margin-bottom:16px}
.region-overview{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.region-overview-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px;cursor:pointer}
.region-overview-card:hover{border-color:var(--navy-2)}
.ro-name{font-weight:600;font-size:14px}.ro-pop{font-size:12px;color:var(--muted)}

.summary-grid,.kpi-grid,.exec-kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin-bottom:18px}
.stat,.summary-card,.kpi-card,.exec-kpi-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;position:relative;text-align:right}
.stat-v,.card-value,.kpi-value,.exec-kpi-value{font-size:26px;font-weight:600;color:var(--navy);letter-spacing:-.3px;line-height:1.15}
.stat-l,.card-label,.kpi-label,.exec-kpi-label{font-size:12.5px;color:var(--muted);margin-top:4px}
.kpi-desc{font-size:11.5px;color:var(--muted)}
.card-icon,.kpi-icon,.exec-kpi-icon{display:none}
.kpi-section{margin:18px 0}.kpi-section>h3{font-size:13px;color:var(--muted);font-weight:600;margin-bottom:10px}
.detail-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:16px;margin-bottom:18px}
.detail-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;min-width:0}
.detail-card h3{font-size:14.5px;margin-bottom:12px;color:var(--ink)}
.detail-card h3 small{color:var(--muted);font-weight:400}
.chart-container{position:relative;height:260px;width:100%}
.full-width{grid-column:1/-1}
.insight-box,.note{background:var(--tint);border-right:3px solid var(--gold);border-radius:6px;padding:12px 16px;margin-bottom:16px}
.insight-box h4,.note-t{font-size:12px;color:var(--gold);font-weight:600;margin-bottom:4px}
.insight-box p,.note p{font-size:13.5px;color:var(--ink-2)}
.source-box,.src{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:10px;margin-top:16px;display:flex;flex-direction:column;gap:4px}
.source-row{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.source-label{font-weight:600;color:var(--ink-2)}
.source-link{color:var(--navy-2);text-decoration:none;border-bottom:1px solid #C5D3EA;font-size:12px}
.source-publisher{color:var(--ink-2)}
.export-bar{display:flex;gap:8px;margin:12px 0}
.export-btn{background:var(--card);border:1px solid var(--line-2);color:var(--ink-2);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12.5px}
.export-btn:hover{border-color:var(--navy-2);color:var(--navy-2)}
.data-table,.rank-table,.compare-table{width:100%;border-collapse:collapse;font-size:13px}
.data-table th,.rank-table th,.compare-table th{text-align:right;font-weight:600;color:var(--muted);font-size:12px;padding:8px 10px;border-bottom:1px solid var(--line-2);background:transparent}
.data-table td,.rank-table td,.compare-table td{padding:8px 10px;border-bottom:1px solid var(--line);color:var(--ink-2)}
.data-table tr:hover td,.rank-table tr:hover td{background:#FAFBFD}
.rank-1 td{background:var(--tint)!important;font-weight:600}
.compare-table th.c1{color:var(--navy-2)}.compare-table th.c2{color:var(--gold)}
.compare-win{color:var(--teal);font-weight:600}
.compare-badge{font-size:11px;padding:1px 7px;border-radius:9px;background:var(--tint);color:var(--navy)}
.compare-selectors{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.gov-list{max-height:300px;overflow:auto}
.gov-item{display:flex;justify-content:space-between;padding:8px 4px;border-bottom:1px solid var(--line);font-size:13px}
.gov-name{color:var(--ink-2)}.gov-value{font-weight:600}
.gov-bar{height:4px;background:var(--line);border-radius:2px;margin-top:4px;overflow:hidden}.gov-bar-fill{height:100%;background:var(--navy-2)}
.stat-bar-container{margin-bottom:10px}.stat-bar-label{display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:3px}
.stat-bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden}.stat-bar-fill{height:100%;background:var(--navy-2)!important;border-radius:3px}
.filter-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.filter-bar label{font-size:12.5px;color:var(--muted)}
.filter-btn{padding:5px 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--card);color:var(--ink-2);font-size:12.5px;cursor:pointer}
.filter-btn.active{background:var(--navy);border-color:var(--navy);color:#fff}
.no-data{text-align:center;padding:36px;color:var(--muted);font-size:14px}
.fade-in{animation:fadeIn .25s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
#dataContent h2{font-size:21px;margin-bottom:14px!important}

/* الطبقة الحيّة */
.live-box{margin-bottom:10px}
.live-head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:12px;border-bottom:2px solid var(--navy);padding-bottom:8px}
.live-head h3{font-size:16px;color:var(--navy)}
.live-head span{font-size:12.5px;color:var(--muted)}
.live-group{font-size:12.5px;font-weight:600;color:var(--muted);margin:14px 0 8px;padding-right:10px;border-right:3px solid var(--line-2)}
.live-card{cursor:pointer}
.live-card.active{border-color:var(--navy);box-shadow:inset 0 0 0 1px var(--navy)}
.live-card .stat-l{color:var(--ink-2);font-weight:500;min-height:36px}
.live-card .stat-l small{color:var(--muted);font-weight:400}
.live-meta{font-size:11.5px;color:var(--muted);margin-top:8px;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.live-dot{width:7px;height:7px;border-radius:50%;background:var(--line-2);flex:none}
.live-dot.fresh{background:var(--teal)}.live-dot.year{background:var(--navy-2)}.live-dot.old{background:var(--gold)}
.rank-pill{position:absolute;top:10px;left:10px;font-size:10.5px;font-weight:600;padding:1px 8px;border-radius:9px;background:var(--bg);color:var(--muted);border:1px solid var(--line)}
.rank-pill.top{color:var(--teal);border-color:#BFE3DD}.rank-pill.low{color:var(--brick);border-color:#EBCACB}
.live-src{font-size:12px;color:var(--muted);margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:8px}
.live-divider{display:flex;align-items:center;gap:12px;margin:18px 0 16px;color:var(--muted);font-size:12.5px;font-weight:600}
.live-divider::before,.live-divider::after{content:"";flex:1;height:1px;background:var(--line-2)}
.profile-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.axis-row{display:grid;grid-template-columns:150px 1fr 52px;align-items:center;gap:10px;font-size:13px;padding:5px 0}
.axis-bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden}.axis-bar i{display:block;height:100%;background:var(--navy-2)}
footer{max-width:1440px;margin:0 auto;padding:0 28px 40px;font-size:12px;color:var(--muted)}

@media (max-width:900px){.search{min-width:0;max-width:none;order:9;flex-basis:100%}.shell{grid-template-columns:1fr;padding:16px}.side{position:static;max-height:none;display:flex;flex-wrap:wrap;gap:4px}.nav-group{display:contents}.nav-title{display:none}.cat-btn{width:auto;border:1px solid var(--line);border-radius:6px}.cat-btn.active{border-color:var(--navy)}.map-wrap{grid-template-columns:1fr}.detail-grid{grid-template-columns:1fr}.top-in{padding:12px 16px}}
@media print{.top-actions,.side,.map-section,.export-bar,.filter-bar,.no-print,.reset-btn{display:none!important}.shell{display:block;padding:0}.top{position:static;border:0}body{background:#fff}.panel,.detail-card,.stat{border-color:#ccc}.detail-card{break-inside:avoid}@page{size:A4;margin:12mm}}
"""

NEW_JS = r"""
// ===== نبض المناطق: الطبقة الجديدة فوق منطق النسخة الأولى =====
let LIVE = null, CHANGES = [], yearFilter = '';
const inYear = m => !yearFilter || String(m.period || '').includes(yearFilter);
const PALETTE = ['#1F4E9C', '#C28A00', '#0F9B8E', '#A63D40', '#6D5BB8', '#5B6B7F', '#8FA3C7', '#D9B55C'];
const EMOJI = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}\u{1F1E6}-\u{1F1FF}]/gu;
const strip = s => String(s ?? '').replace(EMOJI, '').replace(/^\s+/, '');
function deEmoji(root) { if (!root) return; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { if (EMOJI.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(EMOJI, ''); } }

Chart.defaults.font.family = '"IBM Plex Sans Arabic", system-ui, sans-serif';
Chart.defaults.font.size = 11.5;
Chart.defaults.color = '#6B7280';
Chart.defaults.plugins.legend.labels.boxWidth = 10;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.tooltip.rtl = true;
Chart.defaults.plugins.tooltip.backgroundColor = '#13315C';
Chart.defaults.elements.bar.borderRadius = 3;
Chart.defaults.elements.line.borderWidth = 2;
Chart.defaults.elements.point.radius = 2.5;
// إعادة تلوين كل الرسوم القديمة بلوحة واحدة: نحافظ على التمييز (مميّز/عادي) ونستبدل الأصباغ
function hueOf(c) { const m = String(c).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/); let r, g, b; if (m) [r, g, b] = [+m[1], +m[2], +m[3]]; else { const h = String(c).replace('#', ''); if (h.length !== 6) return null; r = parseInt(h.slice(0, 2), 16); g = parseInt(h.slice(2, 4), 16); b = parseInt(h.slice(4, 6), 16); } const mx = Math.max(r, g, b), mn = Math.min(r, g, b); if (mx === mn) return -1; let h; if (mx === r) h = (g - b) / (mx - mn); else if (mx === g) h = 2 + (b - r) / (mx - mn); else h = 4 + (r - g) / (mx - mn); h = Math.round(h * 60); return h < 0 ? h + 360 : h; }
function alphaOf(c) { const m = String(c).match(/rgba\([^)]*,\s*([\d.]+)\)/); return m ? +m[1] : 1; }
function recolor(c, i) { if (typeof c !== 'string') return c; const h = hueOf(c); const a = alphaOf(c); let p; if (h == null) return c; if (h < 0) p = '#5B6B7F'; else if (h < 20 || h >= 330) p = PALETTE[3]; else if (h < 60) p = PALETTE[1]; else if (h < 170) p = PALETTE[2]; else if (h < 260) p = PALETTE[0]; else p = PALETTE[4]; if (a < 0.75) { const r = parseInt(p.slice(1, 3), 16), g = parseInt(p.slice(3, 5), 16), b = parseInt(p.slice(5, 7), 16); return `rgba(${r},${g},${b},${Math.max(a, 0.45)})`; } return p; }
Chart.register({ id: 'nabdPalette', beforeInit(chart) { const t = chart.config.type; (chart.config.data.datasets || []).forEach((ds, i) => { if (t === 'doughnut' || t === 'pie') { ds.backgroundColor = (ds.data || []).map((_, k) => PALETTE[k % PALETTE.length]); ds.borderColor = '#fff'; ds.borderWidth = 2; return; } ['backgroundColor', 'borderColor'].forEach(k => { if (Array.isArray(ds[k])) ds[k] = ds[k].map(c => recolor(c, i)); else if (typeof ds[k] === 'string') ds[k] = recolor(ds[k], i); else if (ds[k] == null && k === 'backgroundColor') ds[k] = PALETTE[i % PALETTE.length]; }); if (t === 'line') { ds.backgroundColor = ds.borderColor; ds.fill = false; ds.tension = 0.25; } }); const o = chart.config.options || (chart.config.options = {}); o.plugins = o.plugins || {}; if (o.plugins.legend && o.plugins.legend.labels) { o.plugins.legend.labels.color = '#374151'; o.plugins.legend.labels.font = { family: '"IBM Plex Sans Arabic"', size: 11.5 }; } if (o.scales) Object.values(o.scales).forEach(s => { s.grid = Object.assign({}, s.grid, { color: '#EEF0F3' }); s.border = { display: false }; s.ticks = Object.assign({}, s.ticks, { color: '#6B7280', font: { family: '"IBM Plex Sans Arabic"', size: 11 } }); }); } });

// أرقام لاتينية موحّدة في كل الصفحة (القديمة كانت تعرض أرقاماً هندية)
function formatNum(n) { if (n === undefined || n === null || isNaN(n)) return '0'; return Math.round(n).toLocaleString('ar-SA-u-nu-latn'); }
// ----- أيقونات رسومية خطية -----
const ICONS = {
  population_housing: 'M3 10.5 12 3l9 7.5V21H3zM9 21v-6h6v6', education: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5V5.5A2.5 2.5 0 0 1 6.5 3H20v14M8 7h8M8 11h5',
  health: 'M20.8 7.6a5 5 0 0 0-8.8-2.4A5 5 0 0 0 3.2 7.6c0 5 8.8 11 8.8 11s8.8-6 8.8-11zM3 12h4l2-3 3 6 2-3h7', disability: 'M12 5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM4 9l8 1 8-1M12 10v5l-3 7M12 15l3 7',
  labor: 'M3 8h18v12H3zM8 8V5h8v3M3 13h18', sports: 'M7 4h10v5a5 5 0 0 1-10 0zM7 6H4v2a3 3 0 0 0 3 3M17 6h3v2a3 3 0 0 1-3 3M12 14v4M8 21h8',
  nonprofit: 'M12 21s-8-5-8-11a4 4 0 0 1 8-1 4 4 0 0 1 8 1c0 6-8 11-8 11z', security: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4',
  infrastructure: 'M12 3l6 8h-3l4 5H5l4-5H6zM12 16v5', tourism: 'M3 18V8h18v10M3 12h18M7 12V9h4v3', real_estate: 'M4 21V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v16M16 10h3a1 1 0 0 1 1 1v10M8 8h2M8 12h2M8 16h2M12 8h2M12 12h2M12 16h2',
  religious: 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z', commerce: 'M3 9l1.5-5h15L21 9M3 9h18v2a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0zM5 13v8h14v-8M10 21v-5h4v5',
  women: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0', comparison: 'M12 3v18M4 7h16M6 7l-3 7a3 3 0 0 0 6 0zM18 7l-3 7a3 3 0 0 0 6 0zM8 21h8',
  executive_summary: 'M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6', census_population: 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M16 3.5a4 4 0 0 1 0 7.5M22 21a7 7 0 0 0-5-6.7',
  census_nationality: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18', census_marital: 'M8 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM16 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z',
  census_growth: 'M3 17l6-6 4 4 8-8M15 7h6v6', census_dependency: 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M17 14a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM22 21a4.5 4.5 0 0 0-5-4.5',
  census_households: 'M3 10.5 12 3l9 7.5V21H3zM8 21v-8h8v8', census_buildings: 'M4 21V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v16M16 10h3a1 1 0 0 1 1 1v10M8 8h2M8 12h2M12 8h2M12 12h2',
  census_units: 'M3 21V7l9-4 9 4v14M9 21v-6h6v6M3 12h18', methodology: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01'
};
const ico = k => `<svg viewBox="0 0 24 24"><path d="${ICONS[k] || ICONS.methodology}"/></svg>`;
function paintIcons() { document.querySelectorAll('.ic[data-ic]').forEach(el => { if (!el.innerHTML) el.innerHTML = ico(el.dataset.ic); }); }
const CAT_NAME = {};

// ----- عدّاد متحرك للأرقام -----
function countUp(root) {
  root.querySelectorAll('.stat-v, .t-v').forEach(el => {
    if (el.dataset.done) return; el.dataset.done = 1;
    const txt = el.textContent.trim(); const num = parseFloat(txt.replace(/[^\d.]/g, '')); if (!isFinite(num) || num < 10) return;
    const dec = (txt.split('.')[1] || '').length; const t0 = performance.now(); const dur = 650;
    const step = now => { const k = Math.min(1, (now - t0) / dur); const e = 1 - Math.pow(1 - k, 3); el.textContent = (num * e).toLocaleString('ar-SA-u-nu-latn', { maximumFractionDigits: dec, minimumFractionDigits: dec }); if (k < 1) requestAnimationFrame(step); else el.textContent = txt; };
    requestAnimationFrame(step);
  });
}

// ----- مكوّنات العرض (تحل محل القديمة) -----
function summaryCard(icon, value, label) { return `<div class="stat"><div class="stat-v">${value}</div><div class="stat-l">${strip(label)}</div></div>`; }
function insightBox(text) { return `<div class="note"><div class="note-t">قراءة تحليلية</div><p>${strip(text)}</p></div>`; }
function kpiSection(kpis) { if (!kpis || !kpis.length) return ''; return `<div class="kpi-section"><h3>مؤشرات محسوبة</h3><div class="kpi-grid">` + kpis.map(k => `<div class="kpi-card"><div class="kpi-value">${k.value}</div><div class="kpi-label">${strip(k.label)}</div>${k.desc ? `<div class="kpi-desc">${strip(k.desc)}</div>` : ''}</div>`).join('') + '</div></div>'; }
function sourceBox(sources) { if (!sources || !sources.length) return ''; const list = Array.isArray(sources) ? sources : [sources]; return '<div class="source-box">' + list.map((s, i) => typeof s === 'string' ? `<div class="source-row">${i === 0 ? '<span class="source-label">المصدر:</span>' : ''}<span>${strip(s)}</span></div>` : `<div class="source-row">${i === 0 ? '<span class="source-label">المصدر:</span>' : ''}<span>${strip(s.name || '')}</span>${s.publisher ? `<span class="source-publisher">· ${strip(s.publisher)}</span>` : ''}${s.link ? `<a class="source-link" href="${s.link}" target="_blank" rel="noopener">رابط المصدر</a>` : ''}</div>`).join('') + '</div>'; }
function exportBar(k) { return `<div class="export-bar"><button class="export-btn" onclick="exportCSV('${k}')">تصدير CSV</button><button class="export-btn" onclick="exportJSON('${k}')">تصدير JSON</button></div>`; }

// ----- الخريطة: تدرج كحلي واحد + مؤشر الفجوة -----
applyHeatMap = function (indicator) {
  heatMapIndicator = indicator;
  const legend = document.getElementById('heatmapLegend'), resetBtn = document.getElementById('heatmapReset');
  if (!indicator) { resetHeatMap(); return; }
  const cfg = HEAT_CONFIGS[indicator]; if (!cfg) return;
  const values = DATA.regions.map(r => cfg.get(r)); const min = Math.min(...values), max = Math.max(...values);
  document.querySelectorAll('#saudi-map path').forEach(p => { const t = max > min ? (cfg.get(p.dataset.region) - min) / (max - min) : .5; const mix = (a, b) => Math.round(a + (b - a) * t); p.style.fill = `rgb(${mix(227, 19)},${mix(234, 49)},${mix(245, 92)})`; p.style.opacity = ''; });
  document.querySelectorAll('#saudi-map .region-label').forEach(t => { const v = cfg.get(t.dataset.label); t.style.fill = (max > min ? (v - min) / (max - min) : .5) > .55 ? '#fff' : '#374151'; });
  if (legend) legend.style.display = 'flex'; if (resetBtn) resetBtn.style.display = 'inline-block';
};
resetHeatMap = function () { heatMapIndicator = null; const s = document.getElementById('heatmapSelect'); if (s) s.value = ''; const l = document.getElementById('heatmapLegend'), b = document.getElementById('heatmapReset'); if (l) l.style.display = 'none'; if (b) b.style.display = 'none'; document.querySelectorAll('#saudi-map path').forEach(p => { p.style.fill = ''; p.style.opacity = ''; }); document.querySelectorAll('#saudi-map .region-label').forEach(t => t.style.fill = ''); };

// ----- المحتوى: نُنقّي الإيموجي بعد كل عرض -----
const _selectRegion = selectRegion, _resetSelection = resetSelection;
selectRegion = function (region) { _selectRegion(region); document.querySelectorAll('#saudi-map .region-label').forEach(t => t.style.fill = (t.dataset.label === region) ? '#fff' : (heatMapIndicator ? t.style.fill : '')); };
resetSelection = function () { _resetSelection(); document.querySelectorAll('#saudi-map .region-label').forEach(t => { if (!heatMapIndicator) t.style.fill = ''; }); };
const _renderContent = renderContent;
renderContent = function () { _renderContent(); deEmoji(document.getElementById('dataContent')); deEmoji(document.getElementById('welcomeScreen')); };

function dstr(s) { if (!s) return '—'; try { return new Date(s).toLocaleDateString('ar-SA-u-nu-latn', { year: 'numeric', month: 'long', day: 'numeric' }); } catch (e) { return s; } }
function freshClass(d) { if (!d) return 'static'; const days = (Date.now() - new Date(d)) / 864e5; return days <= 120 ? 'fresh' : days <= 400 ? 'year' : 'old'; }
function freshWord(d) { return { fresh: 'نُشر خلال 4 أشهر', year: 'نُشر خلال سنة', old: 'لم يُحدَّث عند المصدر منذ أكثر من سنة', static: 'ثابت' }[freshClass(d)]; }
function fmtv(m, v) { if (v == null) return '—'; if (m.key === 'repi' || m.agg === 'mean') return Number(v).toLocaleString('ar-SA-u-nu-latn', { maximumFractionDigits: 2 }); return Math.round(v).toLocaleString('ar-SA-u-nu-latn'); }
function mval(m, r) { return r ? m.values[r] : m.total; }

function liveHeader() {
  const rl = document.getElementById('regionList'); if (rl && DATA) rl.innerHTML = DATA.regions.map(r => `<button onclick="selectRegion('${r}')">${r}</button>`).join('');
  if (!LIVE) { paintIcons(); return; }
  const metrics = Object.values(LIVE.categories).flatMap(c => c.metrics);
  const checked = metrics.map(m => m.checked_at).filter(Boolean).sort().pop();
  const newest = metrics.map(m => m.source_date).filter(Boolean).sort().pop();
  document.querySelectorAll('.cat-btn').forEach(b => { const sp = b.querySelector('span'); CAT_NAME[b.dataset.cat] = (sp ? sp.textContent : b.textContent).trim(); });
  paintIcons(); buildWall(); buildSearch(); smartMap();
  const ys = new Set(); metrics.forEach(m => { const y = String(m.period || '').match(/20[1-3]\d/); if (y) ys.add(y[0]); });
  const sel = document.getElementById('yearSel'); if (sel && sel.options.length <= 1) [...ys].sort().reverse().forEach(y => { const o = document.createElement('option'); o.value = y; o.textContent = y; sel.appendChild(o); });
}

function liveCard(m, r, i, active) {
  const v = mval(m, r);
  return `<div class="stat live-card ${active ? 'active' : ''}" data-i="${i}"><div class="stat-v">${fmtv(m, v)}</div><div class="stat-l">${m.name}${(!r && m.agg === 'mean') ? ' <small>· متوسط المناطق</small>' : ''}</div><div class="live-meta"><span class="live-dot ${freshClass(m.source_date)}"></span>بيانات <b>${m.period || '—'}</b> · نُشر ${dstr(m.source_date)}</div></div>`;
}

function injectLive(cat, r) {
  if (!LIVE || !LIVE.categories[cat]) return;
  const c0 = LIVE.categories[cat]; const content = document.getElementById('dataContent');
  const c = { ...c0, metrics: c0.metrics.filter(inYear) };
  if (yearFilter && !c.metrics.length) { [...content.children].forEach(el => el.style.display = 'none'); content.insertAdjacentHTML('afterbegin', `<div class="live-box"><div class="crumb"><i class="ic" data-ic="${cat}"></i><b>${CAT_NAME[cat] || ''}</b> › <b>${yearFilter}</b></div><div class="live-head"><h3>أحدث البيانات</h3><span>لا مقاييس لسنة ${yearFilter} في هذا القسم</span></div></div>`); paintIcons(); return; }
  if (!c.metrics.length) { content.insertAdjacentHTML('afterbegin', `<div class="crumb"><i class="ic" data-ic="${cat}"></i><b>${CAT_NAME[cat] || ''}</b>${r ? ` › <b>${r}</b>` : ''}</div>`); paintIcons(); return; }
  const f = c.freshness || {};
  // محتوى النسخة الأولى → تبويب «تفاصيل المحافظات» (بلا بطاقاته المكررة)
  const oldNodes = [...content.children]; const oldTab = document.createElement('div'); oldTab.id = 'oldTab'; oldTab.style.display = 'none'; oldNodes.forEach(n => oldTab.appendChild(n)); content.appendChild(oldTab);
  const hasOld = cat !== 'real_estate' && (!!oldTab.querySelector('.gov-list') || /المحافظ|المدن|الأمانات/.test(oldTab.innerText || ''));
  if (!hasOld) oldTab.remove();
  const srcs = {}; c0.metrics.forEach(m => { const mf = (LIVE.manifest || {})[m.indicator] || {}; const k = m.indicator; if (!srcs[k]) srcs[k] = { src: m.source, file: mf.source_file ? decodeURIComponent(mf.source_file).replace(/_fixed_\d+$/, '') : '', url: m.source_url, date: m.source_date, metrics: [] }; srcs[k].metrics.push(m.name); });
  content.insertAdjacentHTML('afterbegin', `<div class="live-box fade-in">
    <div class="crumb"><i class="ic" data-ic="${cat}"></i><b>${CAT_NAME[cat] || ''}</b>${r ? ` › <b>${r}</b>` : ' › إجمالي المملكة'}${yearFilter ? ` › <b>${yearFilter}</b>` : ''}</div>
    <div class="tabs" id="liveTabs"><button class="on" data-t="live">المؤشرات <span>${c.metrics.length}</span></button>${hasOld ? '<button data-t="old">تفاصيل المحافظات</button>' : ''}<button data-t="src">المصادر <span>${Object.keys(srcs).length}</span></button></div>
    <div id="srcTab" style="display:none"><div class="src-list">${Object.values(srcs).map(x => `<div class="src-item"><div>${x.src}<small>${x.file || ''} · نُشر ${dstr(x.date)} · ${x.metrics.length} مقياساً</small></div>${x.url ? `<a class="btn" href="${x.url}" target="_blank" rel="noopener">الملف الأصلي</a>` : ''}</div>`).join('')}</div></div>
    <div id="liveTab">
    <div class="live-head"><h3>أحدث البيانات${r ? ' — ' + r : ' — إجمالي المملكة'}</h3><span>${c.metrics.length} مقياساً${yearFilter ? ' · سنة ' + yearFilter : ''} · أحدث نشر ${dstr(f.latest_source_date)} <span class="dl"><button onclick="exportCat('${cat}','csv')">CSV</button><button onclick="exportCat('${cat}','xlsx')">Excel</button></span></span></div>
    ${(() => {
      const main = [], groups = [];
      c.metrics.forEach((m, i) => { if (!m.group) main.push([m, i]); else { let G = groups.find(x => x.g === m.group); if (!G) { G = { g: m.group, items: [] }; groups.push(G); } G.items.push([m, i]); } });
      const LIM = 8; const extra = main.length > LIM ? main.slice(LIM) : [];
      let h = `<div id="liveCards"><div class="summary-grid">${main.slice(0, LIM).map(([m, i]) => liveCard(m, r, i, i === main[0][1])).join('')}</div>`;
      if (extra.length) h += `<div class="summary-grid more-cards" hidden>${extra.map(([m, i]) => liveCard(m, r, i, false)).join('')}</div><button class="btn more-btn" onclick="const g=this.previousElementSibling; g.hidden=!g.hidden; this.textContent=g.hidden?'عرض ${extra.length} مقاييس أخرى':'إخفاء'; if(!g.hidden) countUp(g);">عرض ${extra.length} مقاييس أخرى</button>`;
      if (groups.length) h += `<div class="grp-grid">` + groups.map(G => { const vals = G.items.map(([m]) => mval(m, r) || 0); const mx = Math.max(...vals, 1); const sum = vals.reduce((a, b) => a + b, 0);
        return `<div class="grp-panel"><div class="grp-title">${G.g}</div>${G.items.map(([m, i], k) => { const v = vals[k]; const share = sum && !m.agg ? (v / sum * 100) : null; const label = m.name.replace(/^[^:]+:\s*/, '').replace(/^(سعوديون|غير سعوديين|طلاب|كبار السن|إشراف|إعاقة|شدة|متزوجة\?|لديه إعاقة\?)\s*/, '');
          return `<div class="grp-row" data-i="${i}"><span class="grp-l" title="${m.name}">${label}</span><span class="grp-bar"><i style="width:${Math.max(2, v / mx * 100)}%"></i></span><b class="grp-v">${fmtv(m, v)}</b><small class="grp-s">${share != null ? share.toFixed(0) + '%' : ''}</small></div>`; }).join('')}<div class="grp-foot">بيانات ${G.items[0][0].period || ''} · اضغطي صفاً لعرضه حسب المناطق</div></div>`; }).join('') + `</div>`;
      return h + `</div>`; })()}
    <div class="detail-grid"><div class="detail-card full-width"><h3 id="liveChartTitle"></h3><div class="chart-container" style="height:360px"><canvas id="liveChart"></canvas></div><div class="live-src" id="liveSrc"></div></div>
    <div class="detail-card full-width" id="liveSeriesCard" style="display:none"><h3 id="liveSeriesTitle"></h3><div class="chart-container" style="height:280px"><canvas id="liveSeries"></canvas></div></div></div>
    </div></div>`);
  paintIcons(); countUp(content);
  document.getElementById('liveTabs').onclick = e => { const b = e.target.closest('button'); if (!b) return; document.querySelectorAll('#liveTabs button').forEach(x => x.classList.toggle('on', x === b)); document.getElementById('liveTab').style.display = b.dataset.t === 'live' ? '' : 'none'; const ot = document.getElementById('oldTab'); if (ot) ot.style.display = b.dataset.t === 'old' ? '' : 'none'; document.getElementById('srcTab').style.display = b.dataset.t === 'src' ? '' : 'none'; if (b.dataset.t === 'old') Object.values(charts).forEach(ch => { try { ch.resize(); } catch (e) {} }); };
  const draw = i => {
    const m = c.metrics[i]; const vals = m.values;
    document.querySelectorAll('#liveCards .live-card').forEach(x => x.classList.toggle('active', +x.dataset.i === i));
    document.querySelectorAll('#liveCards .grp-row').forEach(x => x.classList.toggle('on', +x.dataset.i === i));
    document.getElementById('liveChartTitle').innerHTML = `${m.name} حسب المناطق <small>· بيانات ${m.period || ''}</small>`;
    const mf = (LIVE.manifest || {})[m.indicator] || {};
    document.getElementById('liveSrc').innerHTML = `<span class="dl"><button onclick="exportMetric('${cat}',${i},'csv')">CSV</button><button onclick="exportMetric('${cat}',${i},'xlsx')">Excel</button></span><span>المصدر: ${m.source}</span><span>· الملف: ${mf.source_file ? decodeURIComponent(mf.source_file).replace(/_fixed_\d+$/, '') : '—'}</span>${m.ref ? `<span>· الموضع: ${m.ref}</span>` : ''}<span>· نُشر ${dstr(m.source_date)} (${freshWord(m.source_date)})</span>${m.source_url ? `<a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">الملف الأصلي</a>` : ''}`;
    const regs = [...LIVE.regions].sort((a, b) => (vals[b] || 0) - (vals[a] || 0));
    if (charts.liveChart) charts.liveChart.destroy();
    charts.liveChart = new Chart(document.getElementById('liveChart'), { type: 'bar', data: { labels: regs, datasets: [{ data: regs.map(x => vals[x] ?? null), backgroundColor: regs.map(x => x === r ? PALETTE[1] : PALETTE[0]), barThickness: 16 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: x => ' ' + fmtv(m, x.raw) } } }, scales: { x: { ticks: { callback: v => shortNum(v) } }, y: { grid: { display: false }, ticks: { font: { size: 12.5 } } } } } });
    const sc = document.getElementById('liveSeriesCard'); if (charts.liveSeries) { charts.liveSeries.destroy(); delete charts.liveSeries; }
    if (m.series) {
      sc.style.display = 'block'; const show = r ? [r] : ['الرياض', 'مكة المكرمة', 'المنطقة الشرقية', 'عسير']; const labels = (m.series[show[0]] || []).map(p => p.period).filter(l => !yearFilter || String(l).includes(yearFilter));
      document.getElementById('liveSeriesTitle').innerHTML = `${m.name} — السلسلة الزمنية${r ? ' — ' + r : ''} <small>· تُضاف الفترات الجديدة تلقائياً عند نشرها</small>`;
      charts.liveSeries = new Chart(document.getElementById('liveSeries'), { type: 'line', data: { labels, datasets: show.map((rg, i) => ({ label: rg, data: labels.map(l => { const p = (m.series[rg] || []).find(q => q.period === l); return p ? p.value : null; }), borderColor: PALETTE[i], backgroundColor: PALETTE[i] })) },
        options: { responsive: true, maintainAspectRatio: false, animation: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: show.length > 1, rtl: true } }, scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: v => shortNum(v) } } } } });
    } else sc.style.display = 'none';
  };
  document.getElementById('liveCards').onclick = e => { const el = e.target.closest('.live-card, .grp-row'); if (!el) return; draw(+el.dataset.i); document.querySelectorAll('.grp-row').forEach(x => x.classList.toggle('on', x === el)); };
  draw(0);
}

function renderMethodology() {
  const content = document.getElementById('dataContent'); const M = LIVE.methodology || [];
  let html = `<div class="fade-in"><div class="eyebrow">المرجع</div><h2>المنهجية والمصادر</h2>
  <div class="note"><div class="note-t">كيف تُجمع الأرقام</div><p>لكل مقياس مصدر رسمي واحد محدد بملفه وموضعه داخل الملف. برنامج جامع يفحص المصادر يومياً (هيئة الإحصاء ووزارة البلديات من السحابة، ومنصة سدايا من جهاز الموظف لأنها تمنع السحب الآلي الخارجي)، وينزّل الملف فقط إذا تغيّر تاريخ نشره أو محتواه، ثم تحوّله محلّلات مخصصة إلى قيم للمناطق الإدارية الثلاث عشرة. كل رقم يحمل سنة بياناته وتاريخ نشر الجهة له ورابط الملف الأصلي.</p><p style="margin-top:8px"><b>حدود:</b> تاريخ البيانات يتبع الجهة؛ بعض الجهات تنشر سنوياً بتأخر يصل عشرة أشهر. تعداد السكان ثابت حتى التعداد القادم. المقاييس الملفّية تُعدّ كما نشرتها الجهة دون تنقية.</p></div>
  <div class="note"><div class="note-t">حالة التحديث</div><p>آخر فحص آلي للمصادر: ${dstr(Object.values(LIVE.manifest || {}).map(m => m.checked_at).filter(Boolean).sort().pop())} · أحدث نشر عند الجهات: ${dstr(Object.values(LIVE.manifest || {}).map(m => m.source_date).filter(Boolean).sort().pop())}.</p></div>
  <div class="detail-card"><h3>سجل المقاييس <small>· ${M.length}</small></h3><table class="data-table"><tr><th>القسم</th><th>المقياس</th><th>الجهة</th><th>الملف</th><th>الموضع</th><th>بيانات</th><th>نشر المصدر</th><th>التحديث</th><th></th></tr>`;
  M.forEach(m => { html += `<tr><td>${m.category}</td><td>${m.metric}</td><td>${m.source}</td><td style="font-size:11px;direction:ltr;text-align:right">${m.file || '—'}</td><td style="font-size:11px">${m.ref || '—'}</td><td>${m.period || '—'}</td><td>${dstr(m.source_date)}</td><td>${m.runner === 'cloud' ? 'يومي آلي' : 'من الجهاز'}</td><td>${m.source_url ? `<a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">رابط</a>` : ''}</td></tr>`; });
  content.innerHTML = html + '</table></div></div>';
}

function renderChanges() {
  const content = document.getElementById('dataContent');
  let html = `<div class="fade-in"><div class="eyebrow">التحديث</div><h2>سجل التغيّرات</h2><p style="color:var(--muted);font-size:13px;margin-bottom:16px">كل يوم يفحص الجامع المصادر الرسمية؛ وكل رقم يتغيّر عند المصدر يُسجَّل هنا.</p>`;
  if (!CHANGES.length) html += `<div class="no-data">لا تغيّرات مرصودة بعد. النشر الأول كان ${dstr(LIVE && LIVE.built_at)}، ومن اليوم التالي تُقارن القيم يومياً.</div>`;
  else { html += '<div class="detail-card"><table class="data-table"><tr><th>التاريخ</th><th>القسم</th><th>المقياس</th><th>المناطق المتغيّرة</th><th>فترة البيانات</th><th>نشر المصدر</th></tr>' + CHANGES.slice(0, 200).map(c => `<tr><td>${dstr(c.at)}</td><td>${(LIVE.categories[c.category] || {}).name || c.category}</td><td>${c.name}</td><td>${c.regions_changed}</td><td>${c.period || '—'}</td><td>${dstr(c.source_date)}</td></tr>`).join('') + '</table></div>'; }
  if (LIVE && LIVE.manifest) { html += '<div class="detail-card" style="margin-top:16px"><h3>حالة المصادر</h3><table class="data-table"><tr><th>المؤشر</th><th>المصدر</th><th>آخر نشر عند المصدر</th><th>آخر فحص</th><th>الحالة</th></tr>' + Object.values(LIVE.manifest).map(m => `<tr><td>${m.name}</td><td>${(LIVE.sources[m.source] || {}).name || m.source}</td><td>${dstr(m.source_date)}</td><td>${dstr(m.checked_at)}</td><td>${{ updated: 'نُزّل جديد', unchanged: 'بلا تغيير', static: 'ثابت' }[m.status] || m.status}</td></tr>`).join('') + '</table></div>'; }
  content.innerHTML = html + '</div>';
}

// ----- جدار المؤشرات الرئيسية -----
function headline(cat) { const c = LIVE.categories[cat]; if (!c || !c.metrics.length) return null; return c.metrics.find(m => !m.group) || c.metrics[0]; }
function buildWall() {
  const wall = document.getElementById('kpiWall'); if (!wall) return;
  wall.innerHTML = Object.keys(LIVE.categories).map(cat => { const m = headline(cat); if (!m) return ''; const top = [...LIVE.regions].sort((a, b) => (m.values[b] || 0) - (m.values[a] || 0)).slice(0, 3); const mx = m.values[top[0]] || 1;
    return `<div class="tile" onclick="selectCategory('${cat}')"><div class="t-head"><i class="ic" data-ic="${cat}"></i>${CAT_NAME[cat] || cat}</div><div class="t-v">${fmtv(m, m.total)}</div><div class="t-l">${m.name} · ${m.period || ''}</div><div class="t-bars">${top.map(rg => `<div class="t-bar"><span>${rg}</span><i style="width:${Math.max(4, (m.values[rg] || 0) / mx * 100)}%"></i><b>${fmtv(m, m.values[rg])}</b></div>`).join('')}</div></div>`; }).join('');
  paintIcons(); countUp(wall);
}

// ----- البحث الفوري (Ctrl+K) -----
let QIDX = [], qSel = -1;
function buildSearch() {
  QIDX = [];
  DATA.regions.forEach(r => QIDX.push({ t: 'منطقة', l: r, go: () => selectRegion(r) }));
  Object.entries(CAT_NAME).forEach(([k, n]) => QIDX.push({ t: 'قسم', l: n, go: () => selectCategory(k) }));
  Object.entries(LIVE.categories).forEach(([k, c]) => c.metrics.forEach((m, i) => QIDX.push({ t: CAT_NAME[k] || k, l: m.name, sub: m.period || '', go: () => { selectCategory(k); setTimeout(() => { const el = document.querySelector(`#liveCards .live-card[data-i="${i}"]`); if (el) { el.click(); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 1700); } }, 250); } })));
  const q = document.getElementById('q'), res = document.getElementById('qRes'); if (!q) return;
  const norm = x => String(x).replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي').toLowerCase();
  const show = () => { const v = norm(q.value.trim()); if (!v) { res.hidden = true; return; } const hits = QIDX.filter(x => norm(x.l).includes(v) || norm(x.t).includes(v)).slice(0, 12); qSel = -1; res.innerHTML = hits.map((h, i) => `<div data-i="${i}"><span>${h.l}${h.sub ? ` <small>· ${h.sub}</small>` : ''}</span><small>${h.t}</small></div>`).join('') || '<div><small>لا نتائج</small></div>'; res.hidden = false; res._hits = hits; };
  q.oninput = show; q.onfocus = show;
  q.onkeydown = e => { const hits = res._hits || []; if (e.key === 'ArrowDown') { qSel = Math.min(hits.length - 1, qSel + 1); } else if (e.key === 'ArrowUp') { qSel = Math.max(0, qSel - 1); } else if (e.key === 'Enter') { const h = hits[Math.max(0, qSel)]; if (h) { h.go(); q.value = ''; res.hidden = true; q.blur(); } return; } else if (e.key === 'Escape') { res.hidden = true; q.blur(); return; } else return; e.preventDefault(); [...res.children].forEach((d, i) => d.classList.toggle('on', i === qSel)); };
  res.onmousedown = e => { const d = e.target.closest('div[data-i]'); if (!d) return; e.preventDefault(); const h = (res._hits || [])[+d.dataset.i]; if (h) { h.go(); q.value = ''; res.hidden = true; q.blur(); } };
  document.addEventListener('click', e => { if (!e.target.closest('#search')) res.hidden = true; });
  document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); q.focus(); q.select(); } });
}

// ----- خريطة ذكية: التلميح يعرض مؤشر القسم الحالي، والأسهم تتنقل بين المناطق -----
function smartMap() {
  const tip = document.getElementById('mapTooltip');
  document.querySelectorAll('#saudi-map path').forEach(p => p.addEventListener('mouseenter', () => {
    const r = p.dataset.region; const m = LIVE.categories[selectedCategory] ? headline(selectedCategory) : null;
    const pop = DATA.categories.population_housing && DATA.categories.population_housing.population[r];
    let lines = `<strong>${r}</strong>`; if (pop) lines += `<br>${formatNum(pop.total)} نسمة`; if (m) lines += `<br>${m.name}: ${fmtv(m, m.values[r])}`;
    if (heatMapIndicator && HEAT_CONFIGS[heatMapIndicator]) lines += `<br>${HEAT_CONFIGS[heatMapIndicator].label}: ${formatNum(HEAT_CONFIGS[heatMapIndicator].get(r))}`;
    tip.innerHTML = lines; }));
  document.addEventListener('keydown', e => { if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return; if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return; const i = DATA.regions.indexOf(selectedRegion); const n = (i < 0 ? 0 : i + (e.key === 'ArrowRight' ? -1 : 1) + DATA.regions.length) % DATA.regions.length; selectRegion(DATA.regions[n]); });
}

// ----- تنزيل البيانات: CSV / Excel -----
function catRows(cat) {
  const c = LIVE.categories[cat]; if (!c) return null;
  const head = ['المقياس', 'المجموعة', 'فترة البيانات', 'الإجمالي/المتوسط', ...LIVE.regions, 'المصدر', 'تاريخ النشر', 'رابط الملف'];
  const rows = c.metrics.map(m => [m.name, m.group || '', m.period || '', m.total, ...LIVE.regions.map(r => m.values[r] ?? ''), m.source || '', m.source_date || '', m.source_url || '']);
  return { name: CAT_NAME[cat] || cat, head, rows };
}
function metricRows(cat, i) {
  const m = LIVE.categories[cat].metrics[i];
  const head = ['المنطقة', m.name + (m.period ? ` (${m.period})` : '')];
  const rows = LIVE.regions.map(r => [r, m.values[r] ?? '']); rows.push(['الإجمالي/المتوسط', m.total]);
  if (m.series) { head.push('', 'الفترة', 'القيمة (' + (selectedRegion || 'الرياض') + ')'); const ser = m.series[selectedRegion || 'الرياض'] || []; ser.forEach((p, k) => { if (!rows[k]) rows[k] = ['', '']; rows[k][2] = ''; rows[k][3] = p.period; rows[k][4] = p.value; }); }
  return { name: m.name, head, rows };
}
function toCSV(head, rows) { const esc = v => { const t = String(v ?? ''); return /[",\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }; return '﻿' + [head, ...rows].map(r => r.map(esc).join(',')).join('\r\n'); }
function saveBlob(blob, name) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800); }
function stamp() { return new Date().toISOString().slice(0, 10); }
function withXLSX(fn) { if (window.XLSX) return fn(); const sc = document.createElement('script'); sc.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'; sc.onload = fn; sc.onerror = () => alert('تعذّر تحميل مكتبة Excel (يلزم اتصال بالإنترنت). استخدمي CSV.'); document.head.appendChild(sc); }
function sheetName(n) { return String(n).replace(/[\\/?*\[\]:]/g, ' ').slice(0, 31) || 'Sheet'; }
function exportCat(cat, fmt) {
  const d = catRows(cat); if (!d) { alert('اختاري قسماً من المؤشرات الحيّة أولاً'); return; }
  const fname = `${d.name} - ${stamp()}`;
  if (fmt === 'csv') return saveBlob(new Blob([toCSV(d.head, d.rows)], { type: 'text/csv;charset=utf-8' }), fname + '.csv');
  withXLSX(() => { const wb = XLSX.utils.book_new(); const ws = XLSX.utils.aoa_to_sheet([d.head, ...d.rows]); ws['!views'] = [{ RTL: true }]; XLSX.utils.book_append_sheet(wb, ws, sheetName(d.name)); XLSX.writeFile(wb, fname + '.xlsx'); });
}
function exportMetric(cat, i, fmt) {
  const d = metricRows(cat, i); const fname = `${d.name} - ${stamp()}`;
  if (fmt === 'csv') return saveBlob(new Blob([toCSV(d.head, d.rows)], { type: 'text/csv;charset=utf-8' }), fname + '.csv');
  withXLSX(() => { const wb = XLSX.utils.book_new(); const ws = XLSX.utils.aoa_to_sheet([d.head, ...d.rows]); ws['!views'] = [{ RTL: true }]; XLSX.utils.book_append_sheet(wb, ws, 'البيانات'); XLSX.writeFile(wb, fname + '.xlsx'); });
}
function exportAll(fmt) {
  document.querySelectorAll('.menu-list').forEach(m => m.hidden = true);
  const cats = Object.keys(LIVE.categories).map(catRows).filter(Boolean);
  const fname = `لوحة بيانات المملكة - كل المؤشرات - ${stamp()}`;
  if (fmt === 'csv') { const head = ['القسم', ...cats[0].head]; const rows = cats.flatMap(d => d.rows.map(r => [d.name, ...r])); return saveBlob(new Blob([toCSV(head, rows)], { type: 'text/csv;charset=utf-8' }), fname + '.csv'); }
  withXLSX(() => { const wb = XLSX.utils.book_new();
    cats.forEach(d => { const ws = XLSX.utils.aoa_to_sheet([d.head, ...d.rows]); ws['!views'] = [{ RTL: true }]; XLSX.utils.book_append_sheet(wb, ws, sheetName(d.name)); });
    const M = LIVE.methodology || []; const ws = XLSX.utils.aoa_to_sheet([['القسم', 'المقياس', 'الجهة', 'الملف', 'الموضع في الملف', 'فترة البيانات', 'تاريخ النشر', 'الرابط'], ...M.map(m => [m.category, m.metric, m.source, m.file || '', m.ref || '', m.period || '', m.source_date || '', m.source_url || ''])]); ws['!views'] = [{ RTL: true }]; XLSX.utils.book_append_sheet(wb, ws, 'المصادر');
    XLSX.writeFile(wb, fname + '.xlsx'); });
}
document.addEventListener('click', e => { if (!e.target.closest('.menu')) document.querySelectorAll('.menu-list').forEach(m => m.hidden = true); });

// ----- تحميل البيانات -----
Promise.all([
  fetch('data/baseline_live.json').then(r => r.ok ? r.json() : fetch('data/baseline.json').then(x => x.json())),
  fetch('data/dashboard.json').then(r => r.json()).catch(() => null),
  fetch('data/changes.json').then(r => r.ok ? r.json() : []).catch(() => [])
]).then(([base, live, ch]) => { DATA = base; LIVE = live; CHANGES = ch || []; init(); liveHeader(); deEmoji(document.getElementById('welcomeScreen')); })
  .catch(e => { document.getElementById('dataContent').innerHTML = '<div class="no-data">خطأ في تحميل البيانات</div>'; console.error(e); });
"""

HTML = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>لوحة بيانات المملكة العربية السعودية</title>
<meta name="description" content="مؤشرات مناطق المملكة الثلاث عشرة من مصادرها الرسمية، تُفحص آلياً كل يوم، وكل رقم يحمل تاريخ مصدره">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="brand"><div class="mark"></div><div><h1>لوحة بيانات المملكة العربية السعودية</h1><p>تحليل شامل لبيانات 13 منطقة إدارية</p></div></div>
  <div class="search" id="search"><svg viewBox="0 0 24 24"><path d="M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3"/></svg><input id="q" type="search" autocomplete="off" placeholder="ابحثي عن مؤشر أو منطقة أو قسم…  Ctrl+K"><div id="qRes" class="q-res" hidden></div></div>
  <div class="top-actions">
    <label class="year-wrap"><span>السنة</span><select id="yearSel" onchange="yearFilter=this.value;renderContent()"><option value="">الكل</option></select></label>
    <span id="regionBadge" class="region-badge"><span id="badgeIcon" hidden></span><span id="badgeName"></span></span>
    <button id="resetBtn" class="btn reset-btn" onclick="resetSelection()">إلغاء التحديد</button>
    <div class="menu"><button class="btn" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">تنزيل البيانات ▾</button><div class="menu-list" hidden>
      <button onclick="exportAll('xlsx')">كل المؤشرات — Excel (ورقة لكل قسم)</button>
      <button onclick="exportAll('csv')">كل المؤشرات — CSV</button>
      <button onclick="exportCat(selectedCategory,'xlsx')">القسم الحالي — Excel</button>
      <button onclick="exportCat(selectedCategory,'csv')">القسم الحالي — CSV</button>
    </div></div>
    <button class="btn" onclick="window.print()">طباعة</button>
  </div>
</div></header>
<div class="shell">
  <nav class="side">{nav_html}</nav>
  <main class="content">
    <section class="panel map-section">
      <div class="sec-head"><div><div class="eyebrow">المناطق الإدارية</div><h2>خريطة المملكة</h2></div><span class="map-hint">اختاري منطقة من الخريطة لعرض كل مؤشراتها</span></div>
      <div class="map-wrap">
        <div class="map-container">{svg}</div>
        <aside class="map-side">
          <h3>تلوين الخريطة بمؤشر</h3>
          <div class="heatmap-bar">
            <select id="heatmapSelect" onchange="applyHeatMap(this.value)">
              <option value="">بدون تلوين</option>
              <optgroup label="أعداد"><option value="population">السكان</option><option value="saudi">السكان السعوديون</option><option value="schools">المدارس</option><option value="hospitals">الزيارات الصحية</option><option value="workers">العاملون</option><option value="hotels">الفنادق</option><option value="mosques">المساجد</option></optgroup>
            </select>
            <div class="heatmap-legend" id="heatmapLegend" style="display:none"><span>أدنى</span><div class="heatmap-gradient"></div><span>أعلى</span></div>
            <button class="heatmap-reset" id="heatmapReset" style="display:none" onclick="resetHeatMap()">إزالة التلوين</button>
          </div>
          <h3 style="margin-top:18px">المناطق</h3>
          <div class="region-list" id="regionList"></div>
        </aside>
      </div>
      <div id="mapTooltip" class="map-tooltip"></div>
    </section>
    <div id="contentArea">
      <div id="welcomeScreen" class="welcome-screen fade-in">
        <div class="eyebrow">نظرة عامة</div><h2>المؤشرات الرئيسية</h2>
        <p>اضغطي على أي بطاقة للدخول إلى قسمها، أو اختاري منطقة من الخريطة.</p>
        <div class="kpi-wall" id="kpiWall"></div>
        <div class="eyebrow" style="margin-top:22px">المناطق</div>
        <div class="region-overview" id="regionOverview"></div>
      </div>
      <div id="dataContent" style="display:none;"></div>
    </div>
  </main>
</div>
<footer>لوحة بيانات المملكة العربية السعودية · البيانات من هيئة الإحصاء ووزارة البلديات والإسكان ومنصة سدايا للبيانات المفتوحة · تعداد السكان 2022 طبقة ثابتة · التفاصيل في صفحة المنهجية.</footer>
<script>{js}</script>
<script>{NEW_JS}</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(HTML, encoding="utf-8")
print("index.html:", len(HTML), "bytes")
