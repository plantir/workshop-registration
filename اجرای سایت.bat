@echo off
cd /d "%~dp0"
set "PYCMD="

rem ---- 1) py launcher ----
where py >nul 2>nul && set "PYCMD=py"
if not "%PYCMD%"=="" goto :ready

rem ---- 2) python on PATH (skip the fake Microsoft Store stub) ----
where python >nul 2>nul && set "PYCMD=python"
if "%PYCMD%"=="" goto :try3
%PYCMD% -c "print(1)" >nul 2>nul || set "PYCMD="
if not "%PYCMD%"=="" goto :ready

:try3
where python3 >nul 2>nul && set "PYCMD=python3"
if "%PYCMD%"=="" goto :search
%PYCMD% -c "print(1)" >nul 2>nul || set "PYCMD="
if not "%PYCMD%"=="" goto :ready

rem ---- 3) search common installation folders ----
:search
call :findpy "%LOCALAPPDATA%\Programs\Python"
call :findpy "C:\Program Files"
call :findpy "C:\Program Files (x86)"
call :findpy "%USERPROFILE%\anaconda3"
call :findpy "%USERPROFILE%\miniconda3"
for /d %%D in ("C:\Python*") do if exist "%%D\python.exe" (
    set "PYCMD=%%D\python.exe"
    goto :ready
)
if not "%PYCMD%"=="" goto :ready

echo.
echo  ==========================================================
echo   Python was NOT found in common locations.
echo   Your Python may be installed in a custom folder.
echo   Reinstall from https://www.python.org/downloads/
echo   and tick "Add python.exe to PATH" during install.
echo  ==========================================================
echo.
pause
exit /b

:ready
echo Using Python: %PYCMD%
echo.

rem ---- first run: install required libraries ----
%PYCMD% -c "import flask, openpyxl" 2>nul || %PYCMD% -m pip install -r requirements.txt

rem ---- open browser automatically after 3 seconds ----
start "" /min cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

rem ---- run the site ----
%PYCMD% app.py

echo.
echo  The site stopped. Send a screenshot of this window for support.
pause
exit /b

:findpy
for /d %%D in ("%~1\Python*") do if exist "%%D\python.exe" (
    set "PYCMD=%%D\python.exe"
    goto :eof
)
if exist "%~1\python.exe" set "PYCMD=%~1\python.exe"
goto :eof
