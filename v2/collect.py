"""
جامع بيانات المؤشرات — يكتشف أحدث ملف لكل مؤشر من مصدره، ينزّله إن تغيّر، ويحدّث data/manifest.json.

الاستخدام:
  python collect.py --runner cloud      # الهيئة + وزارة البلديات (يعمل من GitHub Actions)
  python collect.py --runner local      # منصة سدايا (كروم ظاهر على الجهاز)
  python collect.py --list-momah        # طباعة كل عناوين وزارة البلديات (لضبط الأنماط)
  python collect.py --dry-run           # اكتشاف بلا تنزيل
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import requests

try:  # شهادات ويندوز/الشركات: يحل خطأ CERTIFICATE_VERIFY_FAILED محلياً، ولا يلزم على GitHub Actions
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ksa-indicators-collector/1.0"}
GASTAT = "https://www.stats.gov.sa"
MOMAH = "https://momah.gov.sa"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(*a):
    print(*a, flush=True)


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"generated_at": None, "indicators": {}}


def save_manifest(m):
    m["generated_at"] = now()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def get(url, **kw):
    headers = {**UA, **kw.pop("headers", {})}
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=90, **kw)
            if r.status_code == 200:
                return r
            log(f"  http {r.status_code} {url[:90]}")
        except requests.RequestException as e:
            log(f"  retry {i + 1}: {e}")
        time.sleep(3 * (i + 1))
    return None


# ---------------- الهيئة العامة للإحصاء ----------------
def gastat_files(category_id):
    """ملفات Excel المنشورة تحت تصنيف معيّن. تاريخ المصدر من معلمة t= (ملي ثانية)."""
    r = get(f"{GASTAT}/ar/statistics-tabs", params={"tab": "436312", "category": category_id})
    if not r:
        return []
    h = html.unescape(r.text)
    # صندوق «أحدث النشرات» أعلى الصفحة يعرض نشرة مميزة من أي قسم (غالباً السياحة) — نستبعده ونقرأ القائمة فقط
    h = re.sub(r'<div id="latest-publication-container">.*?(?=publications-list-accordion)', "", h, count=1, flags=re.S)
    out, seen = [], set()
    for href in re.findall(r'href="(/documents/[^"]+\.(?:xlsx|xls|csv)[^"]*)"', h):
        if href in seen:
            continue
        seen.add(href)
        name = href.split("/")[4]
        t = re.search(r"[?&]t=(\d+)", href)
        sdate = datetime.fromtimestamp(int(t.group(1)) / 1000, timezone.utc).strftime("%Y-%m-%d") if t else None
        out.append({"url": GASTAT + href, "name": name, "source_date": sdate})
    return out


def gastat_taxonomy(parent_id):
    """الأقسام الفرعية لتصنيف معيّن عبر واجهة Liferay المفتوحة (JSON)."""
    r = get(
        f"{GASTAT}/o/headless-admin-taxonomy/v1.0/taxonomy-categories/{parent_id}/taxonomy-categories",
        params={"pageSize": 100, "fields": "id,name"},
        headers={"Accept": "application/json"},
    )
    return r.json().get("items", []) if r else []


# ---------------- وزارة البلديات والإسكان ----------------
_momah_cache = None


def momah_listing():
    """كل صفوف جدول البيانات المفتوحة: العنوان، تاريخ الإنشاء، روابط CSV/XLSX."""
    global _momah_cache
    if _momah_cache is not None:
        return _momah_cache
    rows, page = [], 1
    while True:
        r = get(f"{MOMAH}/ar/open-data", params={"title": "", "sort_bef_combine": "changed_DESC", "pageNumber": page})
        if not r:
            break
        h = html.unescape(r.text)
        found = 0
        for tr in re.findall(r"<tr>(.*?)</tr>", h, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(tds) < 4:
                continue
            title = re.sub(r"<[^>]+>", "", tds[0]).strip()
            dt = re.search(r'datetime="([^"]+)"', tds[2])
            links = re.findall(r'href="([^"]+\.(csv|xlsx|xls))"', tds[3])
            if not title or not links:
                continue
            found += 1
            if any(x["files"].get(links[0][1]) == links[0][0] for x in rows):
                continue  # الصفحة تكرر الصف نفسه ثلاث مرات (نسخ للجوال)
            rows.append({"title": title, "created": dt.group(1)[:10] if dt else None,
                         "files": {ext: url for url, ext in links}})
        log(f"  momah page {page}: {found} rows")
        if found == 0 or page >= 80:
            break
        page += 1
    _momah_cache = rows
    return rows


# ---------------- التنزيل والبصمة ----------------
def download(ind_id, url, name):
    d = RAW / ind_id
    d.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"\.(xlsx|xls|csv)_fixed_\d+$", r".\1", name)  # الهيئة تلحق _fixed_NNN بعد الامتداد أحياناً
    name = unquote(name).replace("+", " ")
    name = re.sub(r"\(\d+\)", "", name)  # (1) (2) نسخ متكررة من الرفع
    safe = re.sub(r"[^\w.\-؀-ۿ]+", "_", name).strip("_")[:120]
    for old in d.glob("*"):  # ملف واحد لكل مؤشر: الأحدث فقط
        if old.name != safe:
            old.unlink()
    path = d / safe
    r = get(url)
    if not r:
        return None, None
    path.write_bytes(r.content)
    return path, hashlib.sha256(r.content).hexdigest()


def pick_latest(cands, pattern):
    rx = re.compile(pattern)
    m = [c for c in cands if rx.search(c.get("name") or c.get("title") or "")]
    if not m:
        return None

    def period_key(c):
        """أحدث فترة بيانات في اسم الملف (سنة + ربع إن وُجد) ثم تاريخ النشر — فلا يفوز إصدار قديم أُعيد رفعه لاحقاً."""
        name = c.get("name") or c.get("title") or ""
        years = [int(y) for y in re.findall(r"(20[1-3]\d)", name)]
        q = re.search(r"Q([1-4])", name)
        return (max(years) if years else 0, int(q.group(1)) if q else 0, c.get("source_date") or c.get("created") or "")
    return max(m, key=period_key)


# ---------------- التشغيل ----------------
def run(runner, only=None, dry=False):
    reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    man = load_manifest()
    for ind_id, ind in reg["indicators"].items():
        if only and ind_id not in only:
            continue
        src = ind["source"]
        if reg["sources"][src]["runner"] != runner:
            continue
        entry = man["indicators"].setdefault(ind_id, {})
        entry.update({"name": ind["name"], "category": ind["category"], "source": src, "checked_at": now()})
        log(f"\n[{ind_id}] {ind['name']}")
        try:
            if src == "gastat_pub":
                best = pick_latest(gastat_files(ind["category_id"]), ind["match"])
                if not best:
                    entry["status"] = "no_match"
                    log("  لا يوجد ملف مطابق")
                    continue
                url, name, sdate = best["url"], best["name"], best["source_date"]
            elif src == "momah":
                best = pick_latest(momah_listing(), ind["match"])
                if not best:
                    entry["status"] = "no_match"
                    log("  لا يوجد عنوان مطابق")
                    continue
                url = best["files"].get("csv") or best["files"].get("xlsx") or best["files"].get("xls")
                name, sdate = best["title"] + "." + url.rsplit(".", 1)[-1], best["created"]
            elif src == "odp":
                from collectors.odp import latest as odp_latest  # يحتاج كروم ظاهر على الجهاز
                best = odp_latest({**ind, "_id": ind_id})
                if not best:
                    entry["status"] = "no_match"
                    continue
                url, name, sdate = best["url"], best["name"], best["source_date"]
            else:
                entry["status"] = "static"
                continue
            log(f"  أحدث ملف: {name}  (تاريخ المصدر {sdate})")
            if entry.get("source_url") == url and entry.get("source_date") == sdate and entry.get("sha256"):
                entry["status"] = "unchanged"
                log("  لم يتغيّر")
                continue
            if dry:
                entry["status"] = "would_download"
                continue
            if src == "odp":
                path, sha = Path(best["path"]), best["sha256"]
            else:
                path, sha = download(ind_id, url, name)
            if not path:
                entry["status"] = "download_failed"
                continue
            changed = sha != entry.get("sha256")
            entry.update({
                "source_url": url, "source_file": name, "source_date": sdate, "sha256": sha,
                "local_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "fetched_at": now(), "status": "updated" if changed else "unchanged",
            })
            if changed:
                entry["last_change_at"] = now()
            log("  ✔ نُزّل" + (" (محتوى جديد)" if changed else " (نفس المحتوى)"))
        except Exception as e:  # noqa: BLE001
            entry["status"] = f"error: {e}"
            log("  خطأ:", e)
        save_manifest(man)
    save_manifest(man)
    log("\nتم. الحالة:", json.dumps({k: v.get("status") for k, v in man["indicators"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", default="cloud", choices=["cloud", "local"])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-momah", action="store_true")
    a = ap.parse_args()
    if a.list_momah:
        for r in momah_listing():
            print(r["created"], "|", r["title"], "|", ",".join(r["files"]))
        sys.exit()
    run(a.runner, a.only, a.dry_run)
