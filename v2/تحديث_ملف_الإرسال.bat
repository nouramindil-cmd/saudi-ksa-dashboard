@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/2] جلب آخر تحديث آلي من GitHub...
git pull --rebase -q origin master
echo [2/2] توليد ملف الإرسال في مجلد التنزيلات...
python make_single.py
echo.
echo تم. الملف: %USERPROFILE%\Downloads\لوحة بيانات المملكة.html
pause
