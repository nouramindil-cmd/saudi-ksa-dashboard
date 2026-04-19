"""
أداة تحديث بيانات داشبورد المناطق
====================================
الاستخدام:
    python update_data.py

الأداة تقرأ ملف dashboard_data.json الحالي وتتيح تحديث أي قسم فيه.
بعد التحديث، ترفع التغييرات على GitHub تلقائياً.
"""

import json
import subprocess
import sys
import os

DATA_FILE = "dashboard_data.json"

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ تم حفظ البيانات في {DATA_FILE}")

def show_categories(data):
    print("\n📋 الأقسام المتاحة:")
    print("-" * 40)
    cats = data["categories"]
    for i, (key, val) in enumerate(cats.items(), 1):
        icon = val.get("icon", "")
        name = val.get("name", key)
        sub_keys = [k for k in val.keys() if k not in ("name", "icon")]
        print(f"  {i}. {icon} {name} ({key})")
        print(f"     البيانات الفرعية: {', '.join(sub_keys)}")
    return list(cats.keys())

def show_regions(data):
    print("\n🗺️  المناطق:")
    for i, r in enumerate(data["regions"], 1):
        print(f"  {i}. {r}")

def update_value_interactive(data):
    """تحديث قيمة محددة بشكل تفاعلي"""
    cat_keys = show_categories(data)

    choice = input("\nاختر رقم القسم (أو 0 للخروج): ").strip()
    if choice == "0":
        return False

    try:
        cat_key = cat_keys[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ اختيار غير صحيح")
        return False

    cat = data["categories"][cat_key]
    sub_keys = [k for k in cat.keys() if k not in ("name", "icon")]

    print(f"\n📂 البيانات الفرعية في '{cat.get('name', cat_key)}':")
    for i, k in enumerate(sub_keys, 1):
        print(f"  {i}. {k}")

    sub_choice = input("\nاختر رقم البيانات الفرعية: ").strip()
    try:
        sub_key = sub_keys[int(sub_choice) - 1]
    except (ValueError, IndexError):
        print("❌ اختيار غير صحيح")
        return False

    sub_data = cat[sub_key]
    print(f"\n📊 محتوى '{sub_key}':")
    print(json.dumps(sub_data, ensure_ascii=False, indent=2)[:2000])
    if len(json.dumps(sub_data)) > 2000:
        print("... (البيانات مختصرة)")

    print("\n💡 لتحديث هذا القسم، عدّل ملف dashboard_data.json مباشرة")
    print(f"   المسار: categories > {cat_key} > {sub_key}")
    return False

def git_push():
    """رفع التغييرات على GitHub"""
    try:
        subprocess.run(["git", "add", DATA_FILE], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"تحديث بيانات الداشبورد"],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
        print("\n🚀 تم رفع التحديث على GitHub!")
        print("   الداشبورد سيتحدث خلال دقيقة على:")
        print("   https://nouramindil-cmd.github.io/saudi-ksa-dashboard/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ خطأ في رفع البيانات: {e}")
        print("   تأكد من إعدادات Git")
        return False

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 50)
    print("  🏛️  أداة تحديث داشبورد المناطق")
    print("=" * 50)

    data = load_data()
    show_regions(data)

    while True:
        print("\n" + "=" * 50)
        print("  الخيارات:")
        print("  1. عرض الأقسام والبيانات")
        print("  2. رفع التغييرات على GitHub")
        print("  3. خروج")
        print("=" * 50)

        choice = input("\nاختيارك: ").strip()

        if choice == "1":
            update_value_interactive(data)
        elif choice == "2":
            git_push()
        elif choice == "3":
            print("\n👋 مع السلامة!")
            break
        else:
            print("❌ اختيار غير صحيح")

if __name__ == "__main__":
    main()
