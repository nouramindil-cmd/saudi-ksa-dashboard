@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    رفع تحديث بيانات الداشبورد
echo ========================================
echo.

git add dashboard_data.json
git commit -m "تحديث بيانات الداشبورد %date%"
git push

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo    تم الرفع بنجاح!
    echo    الداشبورد سيتحدث خلال دقيقة
    echo    https://nouramindil-cmd.github.io/saudi-ksa-dashboard/
    echo ========================================
) else (
    echo.
    echo خطأ في الرفع - تأكد من إعدادات Git
)

echo.
pause
