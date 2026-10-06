# -*- coding: utf-8 -*-
"""
يصنع نسخة ملف واحد من الداشبورد (البيانات مضمّنة داخله) للإرسال بالبريد أو فتحها بلا خادم.
المخرجات: Downloads\\نبض المناطق.html — يحتاج إنترنت فقط لمكتبة الرسوم والخط.
التشغيل: python make_single.py
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
html = (ROOT / "index.html").read_text(encoding="utf-8")
base = (ROOT / "data" / "baseline_live.json").read_text(encoding="utf-8")
live = (ROOT / "data" / "dashboard.json").read_text(encoding="utf-8")
changes = (ROOT / "data" / "changes.json").read_text(encoding="utf-8-sig")

loader_start = html.index("// ----- تحميل البيانات -----")
loader_end = html.index("</script>", loader_start)
inline = ("// ----- البيانات مضمّنة (نسخة ملف واحد) -----\n"
          "(function(){ const base = JSON.parse(document.getElementById('d-base').textContent); const live = JSON.parse(document.getElementById('d-live').textContent); const ch = JSON.parse(document.getElementById('d-ch').textContent);"
          " DATA = base; LIVE = live; CHANGES = ch || []; init(); liveHeader(); deEmoji(document.getElementById('welcomeScreen')); })();\n")
html = html[:loader_start] + inline + html[loader_end:]
esc = lambda s: s.replace("</script", "<\\/script")
data_tags = (f'<script type="application/json" id="d-base">{esc(base)}</script>\n'
             f'<script type="application/json" id="d-live">{esc(live)}</script>\n'
             f'<script type="application/json" id="d-ch">{esc(changes)}</script>\n')
html = html.replace("<footer>", data_tags + "<footer>", 1)
stamp = datetime.now().strftime("%Y-%m-%d")
html = html.replace("</footer>", f" · نسخة ملف واحد بتاريخ {stamp}</footer>", 1)
out = Path.home() / "Downloads" / "لوحة بيانات المملكة.html"
out.write_text(html, encoding="utf-8")
print(out, f"{out.stat().st_size / 1e6:.1f} MB")
