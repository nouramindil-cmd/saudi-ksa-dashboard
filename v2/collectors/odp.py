"""
جامع منصة البيانات المفتوحة (سدايا) — يعمل محلياً فقط لأن المنصة تحجب أي طلب بلا كروم ظاهر.

يعتمد على أداة opendata_sync الموجودة:
  1) `odp_sync.py sync` يحدّث كتالوج SQLite (updated_at لكل مجموعة) تفاضلياً من قمة القائمة.
  2) نقرأ من الكتالوج المجموعة المطلوبة (بالمعرّف أو بجزء من العنوان) وأحدث مورد Excel/CSV لها.
  3) ننزّل عبر Portal.download (كروم ظاهر يحل تحدي Radware) إلى data/raw/<indicator>/.
"""
import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ODP_DIR = Path(r"C:\Users\lenovo\opendata_sync")
CATALOG = ODP_DIR / "catalog.db"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

_portal = None
_synced = False


def _sync_catalog():
    """تحديث تفاضلي للكتالوج مرة واحدة لكل تشغيل."""
    global _synced
    if _synced:
        return
    # --no-download: نحدّث الكتالوج فقط؛ التنزيل هنا يقتصر على مجموعات هذا المشروع
    subprocess.run([sys.executable, str(ODP_DIR / "odp_sync.py"), "sync", "--no-download"], cwd=ODP_DIR, check=False)
    _synced = True


def _portal_open():
    global _portal
    if _portal is None:
        sys.path.insert(0, str(ODP_DIR))
        from odp_sync import Portal  # noqa: E402
        _portal = Portal(headless=False).__enter__()
    return _portal


def _resolve(ind):
    con = sqlite3.connect(CATALOG)
    con.row_factory = sqlite3.Row
    if ind.get("dataset_id"):
        rows = con.execute("select * from datasets where dataset_id like ? order by updated_at desc",
                           (ind["dataset_id"] + "%",)).fetchall()
    else:
        rows = con.execute("select * from datasets where title_ar like ? order by updated_at desc",
                           ("%" + ind["title_like"] + "%",)).fetchall()
    if not rows:
        return None, None
    ds = rows[0]
    res = con.execute("select * from resources where dataset_id=? order by format", (ds["dataset_id"],)).fetchall()
    pref = [r for r in res if (r["format"] or "").upper() in ("XLSX", "CSV", "XLS")]
    pref.sort(key=lambda r: {"XLSX": 0, "CSV": 1, "XLS": 2}[(r["format"] or "").upper()])
    return ds, (pref[0] if pref else None)


def latest(ind):
    """يرجّع {url, name, source_date, path, sha256} لأحدث ملف، أو None.
    مع all_matching=true ينزّل كل المجموعات المطابقة للعنوان (مثل 13 ملفاً إقليمياً) ويرجّع ملخصاً واحداً."""
    _sync_catalog()
    if ind.get("all_matching"):
        con = sqlite3.connect(CATALOG)
        con.row_factory = sqlite3.Row
        rows = con.execute("select * from datasets where title_ar like ? order by updated_at desc",
                           ("%" + ind["title_like"] + "%",)).fetchall()
        ind_id = ind.get("_id")
        d = RAW / ind_id
        d.mkdir(parents=True, exist_ok=True)
        shas, newest = [], ""
        portal = _portal_open()
        for ds in rows:
            res = con.execute("select * from resources where dataset_id=? and upper(format) in ('XLSX','CSV','XLS')",
                              (ds["dataset_id"],)).fetchall()
            if not res:
                continue
            res = sorted(res, key=lambda r: {"XLSX": 0, "CSV": 1, "XLS": 2}[(r["format"] or "").upper()])[0]
            dest = d / (re.sub(r"[^\w.\-؀-ۿ]+", "_", ds["dataset_id"][:8] + "_" + Path(res["url"]).name)[:120])
            portal.download(res["url"], str(dest))
            shas.append(hashlib.sha256(dest.read_bytes()).hexdigest())
            newest = max(newest, (ds["updated_at"] or "")[:10])
        if not shas:
            return None
        return {"url": "https://open.data.gov.sa/ar/datasets?searchValue=" + ind["title_like"],
                "name": f"{len(shas)} ملفات: {ind['title_like']}", "source_date": newest, "path": str(d),
                "sha256": hashlib.sha256("".join(sorted(shas)).encode()).hexdigest()}
    ds, res = _resolve(ind)
    if not ds or not res:
        return None
    ind_id = ind.get("_id") or re.sub(r"\W+", "_", ind["name"])[:40]
    name = Path(res["url"]).name
    dest = RAW / ind_id / re.sub(r"[^\w.\-\u0600-\u06FF]+", "_", name)[:120]
    dest.parent.mkdir(parents=True, exist_ok=True)
    portal = _portal_open()
    portal.download(res["url"], str(dest))
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    return {"url": "https://open.data.gov.sa/ar/datasets/view/" + ds["dataset_id"],
            "name": name, "source_date": (ds["updated_at"] or "")[:10], "path": str(dest), "sha256": sha,
            "title": ds["title_ar"], "publisher": ds["publisher_ar"]}
