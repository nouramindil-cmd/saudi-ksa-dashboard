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
    ("التحليل", "g-analysis", [("comparison", "مقارنة المناطق"), ("executive_summary", "الملخص التنفيذي"), ("changes", "سجل التغيّرات")]),
    ("تعداد 2022", "g-census", [("census_population", "التركيبة السكانية"), ("census_nationality", "الجنسية"), ("census_marital", "الحالة الاجتماعية"), ("census_growth", "النمو السكاني"),
                    ("census_dependency", "الإعالة"), ("census_households", "تركيبة الأسر"), ("census_buildings", "المساكن"), ("census_units", "الوحدات السكنية")]),
    ("المرجع", "g-ref", [("methodology", "المنهجية والمصادر")]),
]
nav_html = "".join(
    f'<div class="nav-group {cls}"><div class="nav-title">{g}</div>' + "".join(
        f'<button class="cat-btn" data-cat="{k}" onclick="selectCategory(\'{k}\')">{n}'
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

@media (max-width:900px){.shell{grid-template-columns:1fr;padding:16px}.side{position:static;max-height:none;display:flex;flex-wrap:wrap;gap:4px}.nav-group{display:contents}.nav-title{display:none}.cat-btn{width:auto;border:1px solid var(--line);border-radius:6px}.cat-btn.active{border-color:var(--navy)}.map-wrap{grid-template-columns:1fr}.detail-grid{grid-template-columns:1fr}.top-in{padding:12px 16px}}
@media print{.top-actions,.side,.map-section,.export-bar,.filter-bar,.no-print,.reset-btn{display:none!important}.shell{display:block;padding:0}.top{position:static;border:0}body{background:#fff}.panel,.detail-card,.stat{border-color:#ccc}.detail-card{break-inside:avoid}@page{size:A4;margin:12mm}}
"""

NEW_JS = r"""
// ===== نبض المناطق: الطبقة الجديدة فوق منطق النسخة الأولى =====
let LIVE = null, CHANGES = [];
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
  if (!LIVE) { const el = document.getElementById('liveStatus'); if (el) el.textContent = 'تعذّر تحميل الطبقة الحيّة — تُعرض بيانات النسخة الأولى'; return; }
  const metrics = Object.values(LIVE.categories).flatMap(c => c.metrics);
  const checked = metrics.map(m => m.checked_at).filter(Boolean).sort().pop();
  const newest = metrics.map(m => m.source_date).filter(Boolean).sort().pop();
  const hrs = checked ? Math.max(0, Math.round((Date.now() - new Date(checked)) / 36e5)) : null;
  const month = Object.values(LIVE.manifest || {}).filter(m => m.source_date && (Date.now() - new Date(m.source_date)) / 864e5 <= 30).length;
  const el = document.getElementById('liveStatus');
  if (el) el.innerHTML = `${metrics.length} مقياساً من ${Object.keys(LIVE.manifest || {}).length} مصدراً رسمياً · آخر فحص آلي قبل <b>${hrs == null ? '—' : hrs < 24 ? hrs + ' ساعة' : Math.round(hrs / 24) + ' يوماً'}</b> · <b>${month}</b> مصادر نُشر لها جديد خلال 30 يوماً · أحدث نشر: <b>${dstr(newest)}</b>`;
  const c = document.getElementById('chgCount'); if (c) c.textContent = CHANGES.length || '';
}

function liveCard(m, r, i, active) {
  const v = mval(m, r);
  return `<div class="stat live-card ${active ? 'active' : ''}" data-i="${i}"><div class="stat-v">${fmtv(m, v)}</div><div class="stat-l">${m.name}${(!r && m.agg === 'mean') ? ' <small>· متوسط المناطق</small>' : ''}</div><div class="live-meta"><span class="live-dot ${freshClass(m.source_date)}"></span>بيانات <b>${m.period || '—'}</b> · نُشر ${dstr(m.source_date)}</div></div>`;
}

function injectLive(cat, r) {
  if (!LIVE || !LIVE.categories[cat]) return;
  const c = LIVE.categories[cat]; const content = document.getElementById('dataContent');
  if (!c.metrics.length) { content.insertAdjacentHTML('afterbegin', `<div class="live-box"><div class="live-head"><h3>أحدث البيانات من المصدر</h3><span>لا مصدر آلي لهذا القسم بعد — البيانات أدناه من النسخة الأولى</span></div></div>`); return; }
  const f = c.freshness || {};
  content.insertAdjacentHTML('afterbegin', `<div class="live-box fade-in">
    <div class="live-head"><h3>أحدث البيانات من المصدر${r ? ' — ' + r : ' — إجمالي المملكة'}</h3><span>${c.metrics.length} مقياساً · أحدث نشر ${dstr(f.latest_source_date)} · آخر فحص ${dstr(f.last_checked)}</span></div>
    ${(() => { const groups = []; c.metrics.forEach((m, i) => { const g = m.group || ''; let G = groups.find(x => x.g === g); if (!G) { G = { g, items: [] }; groups.push(G); } G.items.push([m, i]); }); return `<div id="liveCards">` + groups.map(G => `${G.g ? `<div class="live-group">${G.g}</div>` : ''}<div class="summary-grid">${G.items.map(([m, i]) => liveCard(m, r, i, i === 0)).join('')}</div>`).join('') + `</div>`; })()}
    <div class="detail-grid"><div class="detail-card full-width"><h3 id="liveChartTitle"></h3><div class="chart-container" style="height:360px"><canvas id="liveChart"></canvas></div><div class="live-src" id="liveSrc"></div></div>
    <div class="detail-card full-width" id="liveSeriesCard" style="display:none"><h3 id="liveSeriesTitle"></h3><div class="chart-container" style="height:280px"><canvas id="liveSeries"></canvas></div></div></div>
    <div class="live-divider"><span>بيانات النسخة الأولى (كما كانت)</span></div></div>`);
  const draw = i => {
    const m = c.metrics[i]; const vals = m.values;
    document.querySelectorAll('#liveCards .live-card').forEach(x => x.classList.toggle('active', +x.dataset.i === i));
    document.getElementById('liveChartTitle').innerHTML = `${m.name} حسب المناطق <small>· بيانات ${m.period || ''}</small>`;
    const mf = (LIVE.manifest || {})[m.indicator] || {};
    document.getElementById('liveSrc').innerHTML = `<span>المصدر: ${m.source}</span><span>· الملف: ${mf.source_file ? decodeURIComponent(mf.source_file).replace(/_fixed_\d+$/, '') : '—'}</span>${m.ref ? `<span>· الموضع: ${m.ref}</span>` : ''}<span>· نُشر ${dstr(m.source_date)} (${freshWord(m.source_date)})</span>${m.source_url ? `<a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">الملف الأصلي</a>` : ''}`;
    const regs = [...LIVE.regions].sort((a, b) => (vals[b] || 0) - (vals[a] || 0));
    if (charts.liveChart) charts.liveChart.destroy();
    charts.liveChart = new Chart(document.getElementById('liveChart'), { type: 'bar', data: { labels: regs, datasets: [{ data: regs.map(x => vals[x] ?? null), backgroundColor: regs.map(x => x === r ? PALETTE[1] : PALETTE[0]), barThickness: 16 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: x => ' ' + fmtv(m, x.raw) } } }, scales: { x: { ticks: { callback: v => shortNum(v) } }, y: { grid: { display: false }, ticks: { font: { size: 12.5 } } } } } });
    const sc = document.getElementById('liveSeriesCard'); if (charts.liveSeries) { charts.liveSeries.destroy(); delete charts.liveSeries; }
    if (m.series) {
      sc.style.display = 'block'; const show = r ? [r] : ['الرياض', 'مكة المكرمة', 'المنطقة الشرقية', 'عسير']; const labels = (m.series[show[0]] || []).map(p => p.period);
      document.getElementById('liveSeriesTitle').innerHTML = `${m.name} — السلسلة الزمنية${r ? ' — ' + r : ''} <small>· تُضاف الفترات الجديدة تلقائياً عند نشرها</small>`;
      charts.liveSeries = new Chart(document.getElementById('liveSeries'), { type: 'line', data: { labels, datasets: show.map((rg, i) => ({ label: rg, data: labels.map(l => { const p = (m.series[rg] || []).find(q => q.period === l); return p ? p.value : null; }), borderColor: PALETTE[i], backgroundColor: PALETTE[i] })) },
        options: { responsive: true, maintainAspectRatio: false, animation: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: show.length > 1, rtl: true } }, scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: v => shortNum(v) } } } } });
    } else sc.style.display = 'none';
  };
  document.getElementById('liveCards').onclick = e => { const el = e.target.closest('.live-card'); if (el) draw(+el.dataset.i); };
  draw(0);
}

function renderMethodology() {
  const content = document.getElementById('dataContent'); const M = LIVE.methodology || [];
  let html = `<div class="fade-in"><div class="eyebrow">المرجع</div><h2>المنهجية والمصادر</h2>
  <div class="note"><div class="note-t">كيف تُجمع الأرقام</div><p>لكل مقياس مصدر رسمي واحد محدد بملفه وموضعه داخل الملف. برنامج جامع يفحص المصادر يومياً (هيئة الإحصاء ووزارة البلديات من السحابة، ومنصة سدايا من جهاز الموظف لأنها تمنع السحب الآلي الخارجي)، وينزّل الملف فقط إذا تغيّر تاريخ نشره أو محتواه، ثم تحوّله محلّلات مخصصة إلى قيم للمناطق الإدارية الثلاث عشرة. كل رقم يحمل سنة بياناته وتاريخ نشر الجهة له ورابط الملف الأصلي.</p><p style="margin-top:8px"><b>حدود:</b> تاريخ البيانات يتبع الجهة؛ بعض الجهات تنشر سنوياً بتأخر يصل عشرة أشهر. تعداد السكان ثابت حتى التعداد القادم. المقاييس الملفّية تُعدّ كما نشرتها الجهة دون تنقية.</p></div>
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
<title>نبض المناطق — مؤشرات مناطق المملكة</title>
<meta name="description" content="مؤشرات مناطق المملكة الثلاث عشرة من مصادرها الرسمية، تُفحص آلياً كل يوم، وكل رقم يحمل تاريخ مصدره">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="brand"><div class="mark"></div><div><h1>نبض المناطق</h1><p id="liveStatus">مؤشرات مناطق المملكة من مصادرها الرسمية · يُفحص آلياً كل يوم</p></div></div>
  <div class="top-actions">
    <span id="regionBadge" class="region-badge"><span id="badgeIcon" hidden></span><span id="badgeName"></span></span>
    <button id="resetBtn" class="btn reset-btn" onclick="resetSelection()">إلغاء التحديد</button>
    <button class="btn" onclick="exportAllData()">تصدير البيانات</button>
    <button class="btn" onclick="window.print()">طباعة</button>
  </div>
</div></header>
<div class="shell">
  <nav class="side">{nav_html}</nav>
  <main class="content">
    <section class="panel map-section">
      <div class="sec-head"><div><div class="eyebrow">المناطق الإدارية</div><h2>خريطة المملكة</h2></div><span class="map-hint">اختاري منطقة لعرض بياناتها في كل الأقسام</span></div>
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
        <div class="eyebrow">نظرة عامة</div><h2>اختاري منطقة أو قسماً</h2>
        <p>المؤشرات الحيّة في القائمة الجانبية تُحدَّث من مصادرها الرسمية، وكل رقم يحمل سنة بياناته وتاريخ نشره ورابط ملفه الأصلي.</p>
        <div class="region-overview" id="regionOverview"></div>
      </div>
      <div id="dataContent" style="display:none;"></div>
    </div>
  </main>
</div>
<footer>نبض المناطق · البيانات من هيئة الإحصاء ووزارة البلديات والإسكان ومنصة سدايا للبيانات المفتوحة · تعداد السكان 2022 طبقة ثابتة · التفاصيل في صفحة المنهجية.</footer>
<script>{js}</script>
<script>{NEW_JS}</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(HTML, encoding="utf-8")
print("index.html:", len(HTML), "bytes")
