# -*- coding: utf-8 -*-
"""
يولّد v2/index.html من واجهة الداشبورد الأولى (../index.html) بنفس التصميم تماماً، مضيفاً:
  - تحميل data/baseline.json (بيانات النسخة الأولى كاملة) + data/dashboard.json (المقاييس الحيّة) + data/changes.json
  - كتلة «أحدث البيانات من المصدر» أعلى كل قسم: بطاقات بنفس تصميم summary-card مع سنة البيانات وتاريخ النشر عند المصدر، ورسم بالمناطق، ومصادر حقيقية
  - زر «ما الذي تغيّر» في القائمة الجانبية، وسطر حالة التحديث في الترويسة
التشغيل: python make_ui.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
src = (ROOT.parent / "index.html").read_text(encoding="utf-8")

# 1) العنوان والوصف
src = src.replace("<title>", "<title>نبض المناطق — ", 1) if "<title>نبض" not in src else src
src = src.replace("<p>تحليل شامل لبيانات 13 منطقة إدارية</p>",
                  '<p id="liveStatus">تحليل شامل لبيانات 13 منطقة إدارية · يُفحص آلياً كل يوم</p>')

# 2) تحميل البيانات
old_loader = re.search(r"// Load data - use embedded data or fetch.*?\n\}\n", src, re.S).group(0)
new_loader = """// Load data: baseline (النسخة الأولى كاملة) + live (المقاييس الحيّة) + changes
let LIVE = null, CHANGES = [];
Promise.all([
  fetch('data/baseline_live.json').then(r => r.ok ? r.json() : fetch('data/baseline.json').then(x => x.json())),
  fetch('data/dashboard.json').then(r => r.json()).catch(() => null),
  fetch('data/changes.json').then(r => r.ok ? r.json() : []).catch(() => [])
]).then(([base, live, ch]) => { DATA = base; LIVE = live; CHANGES = ch || []; init(); liveHeader(); })
  .catch(e => { document.getElementById('dataContent').innerHTML = '<div class="no-data">خطأ في تحميل البيانات</div>'; });
"""
src = src.replace(old_loader, new_loader)

# 3) زر «ما الذي تغيّر» في القائمة
src = src.replace(
    """<button class="cat-btn" onclick="selectCategory('executive_summary')" data-cat="executive_summary">""",
    """<button class="cat-btn" onclick="selectCategory('changes')" data-cat="changes"> <span class="cat-icon">🔔</span> ما الذي تغيّر <span id="chgCount" style="margin-right:auto;font-size:11px;background:rgba(14,122,74,0.15);color:var(--accent);padding:1px 8px;border-radius:10px"></span> </button>
      <button class="cat-btn" onclick="selectCategory('executive_summary')" data-cat="executive_summary">""")

# 4) معالجة القسم الجديد في renderContent
src = src.replace(
    "if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {",
    "if (selectedCategory === 'changes') { welcome.style.display = 'none'; content.style.display = 'block'; Object.values(charts).forEach(c => c.destroy()); charts = {}; renderChanges(); return; }\n  if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {")

# 5) حقن الكتلة الحيّة بعد كل عارض
src = src.replace(
    "  if (renderers[cat]) {\n    renderers[cat](r);\n  }\n}",
    "  if (renderers[cat]) {\n    renderers[cat](r);\n    injectLive(cat, r);\n  }\n}")

# 6) الدوال الجديدة + CSS
live_js = r"""
// ===== LIVE LAYER (نبض المناطق) =====
function dstr(s) { if (!s) return '—'; try { return new Date(s).toLocaleDateString('ar-SA-u-nu-latn', { year: 'numeric', month: 'long', day: 'numeric' }); } catch (e) { return s; } }
function freshClass(d) { if (!d) return 'static'; const days = (Date.now() - new Date(d)) / 864e5; return days <= 120 ? 'fresh' : days <= 400 ? 'year' : 'old'; }
function freshWord(d) { return { fresh: 'نُشر خلال 4 أشهر', year: 'نُشر خلال سنة', old: 'لم يُحدَّث عند المصدر منذ أكثر من سنة', static: 'ثابت' }[freshClass(d)]; }

function liveHeader() {
  if (!LIVE) return;
  const metrics = Object.values(LIVE.categories).flatMap(c => c.metrics);
  const checked = metrics.map(m => m.checked_at).filter(Boolean).sort().pop();
  const newest = metrics.map(m => m.source_date).filter(Boolean).sort().pop();
  const el = document.getElementById('liveStatus');
  if (el) el.innerHTML = `${metrics.length} مقياساً حيّاً من المصادر الرسمية · آخر فحص آلي: <b>${dstr(checked)}</b> · أحدث نشر عند المصدر: <b>${dstr(newest)}</b>`;
  const c = document.getElementById('chgCount'); if (c) c.textContent = CHANGES.length || '';
}

function liveCard(m, r, i, active) {
  const v = r ? m.values[r] : m.total;
  const val = (v == null) ? '—' : (m.key === 'repi' ? Number(v).toLocaleString('ar-SA', { maximumFractionDigits: 2 }) : formatNum(v));
  return `<div class="summary-card live-card ${active ? 'active' : ''}" data-i="${i}" title="اضغطي لعرض التوزيع حسب المناطق">
    <div class="card-value">${val}</div>
    <div class="card-label">${m.name}</div>
    <div class="live-meta"><span class="live-dot ${freshClass(m.source_date)}"></span> بيانات <b>${m.period || '—'}</b> · نُشر عند المصدر ${dstr(m.source_date)}</div>
  </div>`;
}

function injectLive(cat, r) {
  if (!LIVE || !LIVE.categories[cat]) return;
  const c = LIVE.categories[cat];
  const content = document.getElementById('dataContent');
  if (!c.metrics.length) {
    content.insertAdjacentHTML('afterbegin', `<div class="live-box"><div class="live-head"><h3>🔄 أحدث البيانات من المصدر</h3><span>لا مصدر آلي لهذا القسم بعد — البيانات أدناه من النسخة الأولى</span></div></div>`);
    return;
  }
  const f = c.freshness || {};
  let html = `<div class="live-box fade-in">
    <div class="live-head"><h3>🔄 أحدث البيانات من المصدر${r ? ' — ' + r : ' — إجمالي المملكة'}</h3>
      <span>${c.metrics.length} مقياساً · أحدث نشر: ${dstr(f.latest_source_date)} · آخر فحص آلي: ${dstr(f.last_checked)}</span></div>
    <div class="summary-grid" id="liveCards">${c.metrics.map((m, i) => liveCard(m, r, i, i === 0)).join('')}</div>
    <div class="detail-grid"><div class="detail-card full-width">
      <h3 id="liveChartTitle"></h3><div class="chart-container" style="height:360px"><canvas id="liveChart"></canvas></div>
      <div class="live-src" id="liveSrc"></div>
    </div>
    <div class="detail-card full-width" id="liveSeriesCard" style="display:none"><h3 id="liveSeriesTitle"></h3><div class="chart-container" style="height:280px"><canvas id="liveSeries"></canvas></div></div>
    </div>
    <div class="live-divider"><span>📁 بيانات النسخة الأولى (كما كانت)</span></div>
  </div>`;
  content.insertAdjacentHTML('afterbegin', html);
  const draw = i => {
    const m = c.metrics[i];
    document.querySelectorAll('#liveCards .live-card').forEach(x => x.classList.toggle('active', +x.dataset.i === i));
    document.getElementById('liveChartTitle').innerHTML = `📊 ${m.name} حسب المناطق <small style="font-weight:400;color:var(--text-muted)">· بيانات ${m.period || ''}</small>`;
    document.getElementById('liveSrc').innerHTML = `<span>📋 المصدر: ${m.source}</span> <span>· نُشر ${dstr(m.source_date)} (${freshWord(m.source_date)})</span>${m.source_url ? ` · <a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">🔗 الملف الأصلي</a>` : ''}`;
    const regs = [...LIVE.regions].sort((a, b) => (m.values[b] || 0) - (m.values[a] || 0));
    if (charts.liveChart) charts.liveChart.destroy();
    charts.liveChart = new Chart(document.getElementById('liveChart'), {
      type: 'bar',
      data: { labels: regs, datasets: [{ data: regs.map(x => m.values[x] ?? null), backgroundColor: regs.map(x => x === r ? '#d97706' : '#0e7a4a'), borderRadius: 6 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { rtl: true, callbacks: { label: x => ' ' + (m.key === 'repi' ? x.raw : formatNum(x.raw)) } } },
        scales: { x: { ticks: { color: '#475569', font: { family: 'Tajawal', size: 10 }, callback: v => shortNum(v) }, grid: { color: 'rgba(0,0,0,0.06)' } }, y: { ticks: { color: '#475569', font: { family: 'Tajawal', size: 12 } }, grid: { display: false } } } }
    });
    const sc = document.getElementById('liveSeriesCard');
    if (charts.liveSeries) { charts.liveSeries.destroy(); delete charts.liveSeries; }
    if (m.series) {
      sc.style.display = 'block';
      const show = r ? [r] : ['الرياض', 'مكة المكرمة', 'المنطقة الشرقية', 'عسير'];
      const cols = ['#0e7a4a', '#1d5db5', '#d97706', '#7c3aed'];
      const labels = (m.series[show[0]] || []).map(p => p.period);
      document.getElementById('liveSeriesTitle').innerHTML = `📈 ${m.name} — السلسلة الزمنية${r ? ' — ' + r : ''} <small style="font-weight:400;color:var(--text-muted)">· تُضاف الفترات الجديدة تلقائياً عند نشرها</small>`;
      charts.liveSeries = new Chart(document.getElementById('liveSeries'), {
        type: 'line',
        data: { labels, datasets: show.map((rg, i) => ({ label: rg, data: labels.map(l => { const p = (m.series[rg] || []).find(q => q.period === l); return p ? p.value : null; }), borderColor: cols[i], backgroundColor: cols[i], borderWidth: 2, pointRadius: 3, tension: 0.25 })) },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: show.length > 1, rtl: true, labels: { color: '#475569', font: { family: 'Tajawal', size: 11 } } }, tooltip: { rtl: true } },
          scales: { x: { ticks: { color: '#475569', font: { family: 'Tajawal', size: 10 }, maxTicksLimit: 12 }, grid: { display: false } }, y: { ticks: { color: '#475569', font: { family: 'Tajawal', size: 10 }, callback: v => shortNum(v) }, grid: { color: 'rgba(0,0,0,0.06)' } } } }
      });
    } else sc.style.display = 'none';
  };
  document.getElementById('liveCards').onclick = e => { const el = e.target.closest('.live-card'); if (el) draw(+el.dataset.i); };
  draw(0);
}

function renderChanges() {
  const content = document.getElementById('dataContent');
  let html = `<div class="fade-in"><h2 style="font-size:20px;margin-bottom:8px;">🔔 ما الذي تغيّر</h2>
    <p style="color:var(--text-muted);font-size:13px;margin-bottom:20px">كل يوم يفحص الجامع المصادر الرسمية؛ وكل رقم يتغيّر عند المصدر يُسجَّل هنا.</p>`;
  if (!CHANGES.length) html += `<div class="no-data">لا تغيّرات مرصودة بعد. النشر الأول كان ${dstr(LIVE && LIVE.built_at)}، ومن اليوم التالي تُقارن القيم يومياً.</div>`;
  else {
    html += '<div class="detail-card"><table class="data-table"><tr><th>التاريخ</th><th>القسم</th><th>المقياس</th><th>المناطق المتغيّرة</th><th>فترة البيانات</th><th>نشر المصدر</th></tr>';
    CHANGES.slice(0, 200).forEach(c => { html += `<tr><td>${dstr(c.at)}</td><td>${(LIVE.categories[c.category] || {}).name || c.category}</td><td>${c.name}</td><td>${c.regions_changed}</td><td>${c.period || '—'}</td><td>${dstr(c.source_date)}</td></tr>`; });
    html += '</table></div>';
  }
  // حالة كل مصدر
  if (LIVE && LIVE.manifest) {
    html += '<h3 style="margin:24px 0 10px;font-size:15px">🗂️ حالة المصادر</h3><div class="detail-card"><table class="data-table"><tr><th>المؤشر</th><th>المصدر</th><th>آخر نشر عند المصدر</th><th>آخر فحص</th><th>الحالة</th></tr>';
    Object.values(LIVE.manifest).forEach(m => { html += `<tr><td>${m.name}</td><td>${(LIVE.sources[m.source] || {}).name || m.source}</td><td>${dstr(m.source_date)}</td><td>${dstr(m.checked_at)}</td><td>${{ updated: '✅ نُزّل جديد', unchanged: '✅ بلا تغيير', static: '⏸ ثابت' }[m.status] || m.status}</td></tr>`; });
    html += '</table></div>';
  }
  content.innerHTML = html + '</div>';
}
"""
src = src.replace("function init() {", live_js + "\nfunction init() {", 1)

live_css = """
/* ===== live layer ===== */
.live-box { margin-bottom: 8px; }
.live-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.live-head h3 { font-size: 17px; font-weight: 800; color: var(--accent); }
.live-head span { font-size: 12px; color: var(--text-muted); }
.live-card { cursor: pointer; }
.live-card.active { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(14,122,74,0.25); }
.live-card .card-label { font-size: 13px; color: var(--text-primary); font-weight: 600; min-height: 36px; }
.live-meta { font-size: 11px; color: var(--text-muted); margin-top: 8px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; display: inline-block; }
.live-dot.fresh { background: var(--green); } .live-dot.year { background: var(--blue); } .live-dot.old { background: var(--gold); }
.live-src { font-size: 12px; color: var(--text-muted); margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.live-divider { display: flex; align-items: center; gap: 12px; margin: 10px 0 18px; color: var(--text-muted); font-size: 13px; font-weight: 700; }
.live-divider::before, .live-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
"""
src = src.replace("</style>", live_css + "</style>", 1)
src = src.replace("<h1>لوحة بيانات المملكة العربية السعودية</h1>", "<h1>لوحة بيانات المملكة العربية السعودية</h1>", 1)
(ROOT / "index.html").write_text(src, encoding="utf-8")
print("index.html:", len(src), "bytes; live hooks:", src.count("injectLive("), "loader:", "data/baseline.json" in src)
