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

# 3-أ) خيارات تلوين الخريطة بمؤشر الفجوة ومحاوره
src = src.replace('<option value="mosques">عدد المساجد</option>',
                  '<option value="mosques">عدد المساجد</option>\n<option value="gap">🧭 فجوة الخدمات (مركّب)</option><option value="gap_health">فجوة الصحة</option><option value="gap_education">فجوة التعليم</option><option value="gap_safety">فجوة الأمن والطوارئ</option><option value="gap_municipal">فجوة الخدمات البلدية</option><option value="gap_jobs">فجوة فرص العمل</option>')
# 3-ب) أزرار جديدة في القائمة: مؤشر الفجوة، ملف المنطقة، المنهجية
src = src.replace(
    """<button class="cat-btn" onclick="selectCategory('comparison')" data-cat="comparison">""",
    """<button class="cat-btn" onclick="selectCategory('gap')" data-cat="gap"> <span class="cat-icon">🧭</span> مؤشر فجوة الخدمات </button>
      <button class="cat-btn" onclick="selectCategory('profile')" data-cat="profile"> <span class="cat-icon">📍</span> ملف المنطقة (للطباعة) </button>
      <button class="cat-btn" onclick="selectCategory('methodology')" data-cat="methodology"> <span class="cat-icon">📐</span> المنهجية والمصادر </button>
      <button class="cat-btn" onclick="selectCategory('comparison')" data-cat="comparison">""")

# 3) زر «ما الذي تغيّر» في القائمة
src = src.replace(
    """<button class="cat-btn" onclick="selectCategory('executive_summary')" data-cat="executive_summary">""",
    """<button class="cat-btn" onclick="selectCategory('changes')" data-cat="changes"> <span class="cat-icon">🔔</span> ما الذي تغيّر <span id="chgCount" style="margin-right:auto;font-size:11px;background:rgba(14,122,74,0.15);color:var(--accent);padding:1px 8px;border-radius:10px"></span> </button>
      <button class="cat-btn" onclick="selectCategory('executive_summary')" data-cat="executive_summary">""")

# 4) معالجة القسم الجديد في renderContent
src = src.replace(
    "if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {",
    "if (['changes','gap','profile','methodology'].includes(selectedCategory)) { welcome.style.display = 'none'; content.style.display = 'block'; Object.values(charts).forEach(c => c.destroy()); charts = {}; ({changes: renderChanges, gap: renderGap, profile: renderProfile, methodology: renderMethodology})[selectedCategory](); return; }\n  if (selectedCategory === 'executive_summary' || selectedCategory === 'comparison') {")

# 4-ب) تلوين الخريطة بالفجوة: نعترض applyHeatMap للقيم التي تبدأ بـ gap
src = src.replace("function applyHeatMap(indicator) {\n  heatMapIndicator = indicator;",
                  "function applyHeatMap(indicator) {\n  if (indicator && indicator.startsWith('gap') && LIVE && LIVE.gap_index) { const ax = indicator === 'gap' ? null : indicator.slice(4); HEAT_CONFIGS[indicator] = { label: ax ? 'فجوة ' + LIVE.gap_index.axes[ax].name : 'فجوة الخدمات', get: r => { const g = LIVE.gap_index.regions[r]; if (!g) return 0; return ax ? Math.round(100 - (g.axes[ax] ?? 0)) : (g.gap ?? 0); } }; }\n  heatMapIndicator = indicator;")

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
  const hrs = checked ? Math.max(0, Math.round((Date.now() - new Date(checked)) / 36e5)) : null;
  const month = Object.values(LIVE.manifest || {}).filter(m => m.source_date && (Date.now() - new Date(m.source_date)) / 864e5 <= 30).length;
  if (el) el.innerHTML = `${metrics.length} مقياساً حيّاً من ${Object.keys(LIVE.manifest || {}).length} مصدراً رسمياً · آخر فحص آلي قبل <b>${hrs == null ? '—' : hrs < 24 ? hrs + ' ساعة' : Math.round(hrs / 24) + ' يوماً'}</b> · <b>${month}</b> مصادر نُشر لها جديد خلال 30 يوماً · أحدث نشر: <b>${dstr(newest)}</b>`;
  const c = document.getElementById('chgCount'); if (c) c.textContent = CHANGES.length || '';
}

let perCapita = false;  // وضع العرض: العدد أم لكل 10 آلاف نسمة
function mval(m, r) {  // قيمة المقياس بحسب الوضع
  if (perCapita && m.per_10k) { if (r) return m.per_10k[r]; const pop = LIVE.gap_index ? Object.values(LIVE.gap_index.population).reduce((a, b) => a + b, 0) : 0; return pop ? m.total / pop * 10000 : null; }
  return r ? m.values[r] : m.total;
}
function mfmt(m, v) { if (v == null) return '—'; if (m.key === 'repi' || (perCapita && m.per_10k)) return Number(v).toLocaleString('ar-SA', { maximumFractionDigits: v < 10 ? 2 : 1 }); return formatNum(v); }
function liveCard(m, r, i, active) {
  const v = mval(m, r);
  const rk = r ? ((perCapita && m.rank_per_10k) ? m.rank_per_10k[r] : (m.rank || {})[r]) : null;
  return `<div class="summary-card live-card ${active ? 'active' : ''}" data-i="${i}" title="اضغطي لعرض التوزيع حسب المناطق">
    ${rk ? `<span class="rank-pill ${rk <= 3 ? 'top' : rk >= 11 ? 'low' : ''}">الترتيب ${rk}/13</span>` : ''}
    <div class="card-value">${mfmt(m, v)}</div>
    <div class="card-label">${m.name}${perCapita && m.per_10k ? ' <small>لكل 10 آلاف نسمة</small>' : ''}</div>
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
    <div class="filter-bar"><label>العرض:</label>
      <button class="filter-btn ${perCapita ? '' : 'active'}" onclick="perCapita=false;renderContent()">العدد</button>
      <button class="filter-btn ${perCapita ? 'active' : ''}" onclick="perCapita=true;renderContent()">لكل 10 آلاف نسمة</button>
      <span style="font-size:11.5px;color:var(--text-muted)">التعيير بسكان تعداد 2022 يُظهر المناطق الصغيرة التي يخفيها العدد المطلق</span></div>
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
    const pc = perCapita && m.per_10k;
    const vals = pc ? m.per_10k : m.values;
    document.getElementById('liveChartTitle').innerHTML = `📊 ${m.name} حسب المناطق${pc ? ' — لكل 10 آلاف نسمة' : ''} <small style="font-weight:400;color:var(--text-muted)">· بيانات ${m.period || ''}</small>`;
    const mf = (LIVE.manifest || {})[m.indicator] || {};
    document.getElementById('liveSrc').innerHTML = `<span>📋 المصدر: ${m.source}</span> <span>· الملف: ${mf.source_file || '—'}</span> ${m.ref ? `<span>· الموضع: ${m.ref}</span>` : ''} <span>· نُشر ${dstr(m.source_date)} (${freshWord(m.source_date)})</span>${m.source_url ? ` · <a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">🔗 الملف الأصلي</a>` : ''}`;
    const regs = [...LIVE.regions].sort((a, b) => (vals[b] || 0) - (vals[a] || 0));
    if (charts.liveChart) charts.liveChart.destroy();
    charts.liveChart = new Chart(document.getElementById('liveChart'), {
      type: 'bar',
      data: { labels: regs, datasets: [{ data: regs.map(x => vals[x] ?? null), backgroundColor: regs.map(x => x === r ? '#d97706' : '#0e7a4a'), borderRadius: 6 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { rtl: true, callbacks: { label: x => ' ' + mfmt(m, x.raw) } } },
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

// ===== مؤشر فجوة الخدمات =====
const AXIS_COLORS = { health: '#dc2626', education: '#2563eb', safety: '#d97706', municipal: '#059669', jobs: '#7c3aed' };
function renderGap() {
  const content = document.getElementById('dataContent');
  const G = LIVE && LIVE.gap_index; if (!G) { content.innerHTML = '<div class="no-data">المؤشر غير متاح</div>'; return; }
  const regs = Object.entries(G.regions).filter(([, v]) => v.score != null).sort((a, b) => a[1].score - b[1].score); // الأكبر فجوة أولاً
  const r = selectedRegion;
  let html = `<div class="fade-in"><h2 style="font-size:20px;margin-bottom:6px;">🧭 مؤشر فجوة الخدمات${r ? ' — ' + r : ''}</h2>
    <p style="color:var(--text-muted);font-size:13px;margin-bottom:16px">${G.method}</p>`;
  if (r && G.regions[r]) {
    const g = G.regions[r];
    html += '<div class="summary-grid">' + summaryCard('🧭', g.gap + ' / 100', 'الفجوة الكلية') + summaryCard('🏅', g.rank + ' من 13', 'ترتيب المنطقة (1 = الأفضل تغطية)') +
      Object.entries(G.axes).map(([ak, ax]) => summaryCard(ax.icon, (g.axes[ak] ?? 0).toFixed(0) + ' / 100', `تغطية ${ax.name} (الترتيب ${g.axis_rank[ak]})`)).join('') + '</div>';
    const weakest = Object.entries(g.axes).sort((a, b) => a[1] - b[1]).slice(0, 3);
    html += insightBox(`أكبر ثلاث فجوات في ${r}: ` + weakest.map(([ak, v]) => `<b>${G.axes[ak].name}</b> (تغطية ${v.toFixed(0)}/100، الترتيب ${g.axis_rank[ak]} من 13)`).join('، ') + '.');
  }
  html += `<div class="detail-grid"><div class="detail-card full-width"><h3>📊 تغطية الخدمات حسب المنطقة والمحور (0 = أدنى منطقة، 100 = أعلى منطقة)</h3><div class="chart-container" style="height:420px"><canvas id="gapChart"></canvas></div></div></div>`;
  html += '<div class="detail-card"><h3>🏅 ترتيب المناطق (الأكبر فجوة أولاً)</h3><table class="rank-table"><tr><th>#</th><th>المنطقة</th><th>الفجوة</th>' + Object.values(G.axes).map(a => `<th>${a.icon} ${a.name}</th>`).join('') + '<th>السكان</th></tr>';
  regs.forEach(([rg, g], i) => { html += `<tr class="${rg === r ? 'rank-1' : ''}"><td>${i + 1}</td><td><a href="#" onclick="selectRegion('${rg}');return false;">${rg}</a></td><td><b>${g.gap}</b></td>` + Object.keys(G.axes).map(ak => `<td>${(g.axes[ak] ?? 0).toFixed(0)}</td>`).join('') + `<td>${formatNum(G.population[rg])}</td></tr>`; });
  html += '</table></div>';
  html += '<div class="detail-card" style="margin-top:16px"><h3>🧩 مكوّنات كل محور</h3>' + Object.entries(G.axes).map(([ak, a]) => `<p style="font-size:13px;margin:6px 0"><b>${a.icon} ${a.name}:</b> ${a.metrics.map(m => m.name + (m.period ? ` (${m.period})` : '')).join(' · ')}</p>`).join('') + '</div></div>';
  content.innerHTML = html;
  const labels = regs.map(x => x[0]);
  makeBarChart('gapChart', labels, Object.entries(G.axes).map(([ak, a]) => ({ label: a.name, data: regs.map(([, g]) => g.axes[ak] ?? 0), backgroundColor: AXIS_COLORS[ak], borderRadius: 3 })), { chartOptions: { indexAxis: 'y', scales: { x: { stacked: false, max: 100 }, y: {} } } });
}

// ===== ملف المنطقة للطباعة =====
function renderProfile() {
  const content = document.getElementById('dataContent');
  const r = selectedRegion;
  if (!r) { content.innerHTML = `<div class="fade-in"><h2 style="font-size:20px;margin-bottom:10px">📍 ملف المنطقة</h2><p style="color:var(--text-muted);font-size:14px;margin-bottom:16px">اختاري منطقة من الخريطة أو من القائمة التالية، ثم اضغطي «طباعة / PDF». الملف صفحتان: المؤشرات معيّرة بالسكان، ترتيب المنطقة، وأبرز الفجوات.</p><div class="region-overview">` + DATA.regions.map(x => `<div class="region-overview-card" onclick="selectRegion('${x}')"><div class="ro-name">${x}</div></div>`).join('') + '</div></div>'; return; }
  const G = LIVE.gap_index, g = G.regions[r], pop = G.population[r];
  let html = `<div class="fade-in profile-print"><div class="profile-head"><div><h2 style="font-size:24px;margin:0">📍 ملف منطقة ${r}</h2><div style="color:var(--text-muted);font-size:13px">نبض المناطق · أُعدّ آلياً في ${dstr(new Date().toISOString())} · السكان ${formatNum(pop)} نسمة (تعداد 2022)</div></div>
    <button class="print-btn no-print" onclick="window.print()">🖨️ طباعة / PDF</button></div>`;
  html += '<div class="summary-grid">' + summaryCard('🧭', g.gap + ' / 100', 'فجوة الخدمات الكلية') + summaryCard('🏅', g.rank + ' من 13', 'الترتيب بين المناطق') +
    Object.entries(G.axes).map(([ak, ax]) => summaryCard(ax.icon, (g.axes[ak] ?? 0).toFixed(0), `تغطية ${ax.name} · الترتيب ${g.axis_rank[ak]}`)).join('') + '</div>';
  const weakest = Object.entries(g.axes).sort((a, b) => a[1] - b[1]).slice(0, 3);
  html += insightBox(`<b>أبرز ثلاث فجوات:</b> ` + weakest.map(([ak, v]) => `${G.axes[ak].name} (${v.toFixed(0)}/100، الترتيب ${g.axis_rank[ak]} من 13)`).join('، ') + '. الدرجة نسبية بين المناطق الثلاث عشرة بعد التعيير بالسكان.');
  // أدنى المقاييس ترتيباً لكل نسمة
  const all = Object.entries(LIVE.categories).flatMap(([ck, c]) => c.metrics.filter(m => m.per_10k && m.rank_per_10k).map(m => ({ ...m, cat: c.name })));
  const worst = all.filter(m => m.rank_per_10k[r] >= 11).sort((a, b) => b.rank_per_10k[r] - a.rank_per_10k[r]).slice(0, 6);
  if (worst.length) html += '<div class="detail-card" style="margin-bottom:16px"><h3>🔻 مقاييس تقع فيها المنطقة ضمن الثلاث الأدنى لكل نسمة</h3><table class="data-table"><tr><th>القسم</th><th>المقياس</th><th>لكل 10 آلاف نسمة</th><th>الترتيب</th><th>بيانات</th></tr>' + worst.map(m => `<tr><td>${m.cat}</td><td>${m.name}</td><td>${m.per_10k[r].toLocaleString('ar-SA', { maximumFractionDigits: 2 })}</td><td>${m.rank_per_10k[r]} / 13</td><td>${m.period || ''}</td></tr>`).join('') + '</table></div>';
  html += '<div class="detail-card"><h3>📋 كل المؤشرات الحيّة للمنطقة</h3><table class="data-table"><tr><th>القسم</th><th>المقياس</th><th>العدد</th><th>لكل 10 آلاف نسمة</th><th>الترتيب</th><th>بيانات</th><th>نشر المصدر</th></tr>';
  Object.entries(LIVE.categories).forEach(([ck, c]) => c.metrics.forEach(m => { const v = m.values[r]; html += `<tr><td>${c.name}</td><td>${m.name}</td><td>${v == null ? '—' : (m.key === 'repi' ? v : formatNum(v))}</td><td>${m.per_10k ? m.per_10k[r].toLocaleString('ar-SA', { maximumFractionDigits: 2 }) : '—'}</td><td>${(m.rank_per_10k || m.rank || {})[r] || '—'} / 13</td><td>${m.period || ''}</td><td>${dstr(m.source_date)}</td></tr>`; }));
  html += '</table></div><p style="font-size:11px;color:var(--text-muted);margin-top:10px">المصادر: ' + Object.values(LIVE.sources).map(s => s.name).join(' · ') + '. التعيير بسكان تعداد 2022. التفاصيل في صفحة المنهجية.</p></div>';
  content.innerHTML = html;
}

// ===== المنهجية والمصادر =====
function renderMethodology() {
  const content = document.getElementById('dataContent');
  const M = LIVE.methodology || [];
  let html = `<div class="fade-in"><h2 style="font-size:20px;margin-bottom:8px">📐 المنهجية والمصادر</h2>
  <div class="insight-box"><h4>كيف تُجمع الأرقام</h4><p>لكل مقياس مصدر رسمي واحد محدد بملفه وموضعه داخل الملف. برنامج جامع يفحص المصادر يومياً (هيئة الإحصاء ووزارة البلديات من السحابة، ومنصة سدايا من جهاز الموظف لأنها تمنع السحب الآلي الخارجي)، وينزّل الملف فقط إذا تغيّر تاريخ نشره أو محتواه، ثم تحوّله محلّلات مخصصة إلى قيم للمناطق الإدارية الثلاث عشرة. كل رقم يحمل سنة بياناته وتاريخ نشر الجهة له ورابط الملف الأصلي.</p>
  <p style="margin-top:8px"><b>التعيير:</b> القيم «لكل 10 آلاف نسمة» تُقسم على سكان المنطقة في تعداد 2022. <b>مؤشر الفجوة:</b> ${LIVE.gap_index ? LIVE.gap_index.method : ''}</p>
  <p style="margin-top:8px"><b>حدود:</b> تاريخ البيانات يتبع الجهة؛ بعض الجهات تنشر سنوياً بتأخر يصل عشرة أشهر. تعداد السكان ثابت حتى التعداد القادم. المقاييس الملفّية (سجل لكل منشأة) تُعدّ كما نشرتها الجهة دون تنقية.</p></div>
  <div class="detail-card"><h3>📋 سجل المقاييس (${M.length})</h3><table class="data-table"><tr><th>القسم</th><th>المقياس</th><th>الجهة</th><th>الملف</th><th>الموضع في الملف</th><th>بيانات</th><th>نشر المصدر</th><th>التحديث</th><th>رابط</th></tr>`;
  M.forEach(m => { html += `<tr><td>${m.category}</td><td>${m.metric}</td><td>${m.source}</td><td style="font-size:11px;direction:ltr;text-align:right">${m.file || '—'}</td><td style="font-size:11px">${m.ref || '—'}</td><td>${m.period || '—'}</td><td>${dstr(m.source_date)}</td><td>${m.runner === 'cloud' ? 'يومي آلي' : 'من الجهاز'}</td><td>${m.source_url ? `<a class="source-link" href="${m.source_url}" target="_blank" rel="noopener">🔗</a>` : ''}</td></tr>`; });
  html += '</table></div></div>';
  content.innerHTML = html;
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
.rank-pill { position: absolute; top: 10px; left: 10px; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 10px; background: rgba(100,116,139,0.12); color: var(--text-secondary); }
.rank-pill.top { background: rgba(5,150,105,0.14); color: var(--green); } .rank-pill.low { background: rgba(220,38,38,0.12); color: var(--red); }
.profile-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
@media print {
  .no-print, .live-box .filter-bar { display: none !important; }
  .profile-print .summary-grid { grid-template-columns: repeat(4, 1fr) !important; }
  .profile-print .data-table { font-size: 10.5px; }
  .profile-print .detail-card { break-inside: avoid; }
  @page { size: A4; margin: 12mm; }
}
"""
src = src.replace("</style>", live_css + "</style>", 1)
src = src.replace("<h1>لوحة بيانات المملكة العربية السعودية</h1>", "<h1>لوحة بيانات المملكة العربية السعودية</h1>", 1)
(ROOT / "index.html").write_text(src, encoding="utf-8")
print("index.html:", len(src), "bytes; live hooks:", src.count("injectLive("), "loader:", "data/baseline.json" in src)
