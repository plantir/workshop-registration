@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ============================================================
echo   This will PERMANENTLY delete:
echo     - registrations.db   (all test registrations)
echo     - uploads folder     (all uploaded CV files)
echo   This cannot be undone!
echo  ============================================================
echo.
choice /c YN /m "Are you sure? (Y = Yes, delete / N = No, cancel)"
if errorlevel 2 exit /b

if exist registrations.db del registrations.db
if exist uploads rmdir /s /q uploads

echo.
echo  Done! All test data removed. Start the site again and it
echo  will create a fresh empty database.
echo.
pause
