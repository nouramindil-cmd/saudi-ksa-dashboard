@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/3] سحب بيانات سدايا (يفتح كروم ويغلقه وحده)...
python collect.py --runner local
echo [2/3] بناء ملف الداشبورد...
python build.py
echo [3/3] رفع التحديث...
git add -A data
git commit -m "تحديث محلي (سدايا) %date%"
git push
echo تم. الرابط يتحدث خلال دقيقة.
pause
