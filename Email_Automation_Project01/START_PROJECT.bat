@echo off
title Email Automation System
cd /d "%~dp0"
color 0B

echo ============================================================
echo               EMAIL AUTOMATION SYSTEM
echo                  Auto Setup + Start
echo ============================================================
echo.

REM ---------- Step 1 : Python dhoondo ----------
set "PYCMD="

where py >nul 2>&1
if %errorlevel% equ 0 (set "PYCMD=py" & goto :found)

where python >nul 2>&1
if %errorlevel% equ 0 (set "PYCMD=python" & goto :found)

where python3 >nul 2>&1
if %errorlevel% equ 0 (set "PYCMD=python3" & goto :found)

goto :nopython

:found
echo [1/3]  Python mil gaya!  Command: %PYCMD%
%PYCMD% --version
echo.

REM ---------- Step 2 : Packages install ----------
echo [2/3]  Required packages install ho rahe hai...
echo        (pehli baar 1-2 minute lag sakta hai, internet on rakho)
echo.
%PYCMD% -m pip install --upgrade pip
%PYCMD% -m pip install flask pandas jinja2 schedule openpyxl
echo.

if %errorlevel% neq 0 (
    color 0C
    echo ============================================================
    echo  [ERROR] Packages install nahi ho paye.
    echo  Internet connection check karo aur dobara try karo.
    echo ============================================================
    pause
    exit /b 1
)

REM ---------- Step 3 : App start ----------
echo [3/3]  Application start ho raha hai...
echo.
echo ============================================================
echo   Browser me kholo  --^>  http://127.0.0.1:5000
echo   Band karne ke liye is window me  Ctrl + C  dabao
echo ============================================================
echo.

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5000
%PYCMD% app.py

pause
exit /b 0

REM ---------- Python hi nahi mila ----------
:nopython
color 0C
echo ============================================================
echo   [ERROR]  Python aapke computer par install nahi hai
echo            (ya PATH me add nahi hua hai)
echo ============================================================
echo.
echo   SOLUTION:
echo.
echo   1. Jao      https://www.python.org/downloads/
echo   2. "Download Python 3.x" par click karke installer chalao
echo   3. IMPORTANT: Sabse niche wala checkbox
echo                 [x] Add python.exe to PATH
echo                 ZAROOR tick karo, phir "Install Now"
echo   4. Install hone ke baad computer RESTART karo
echo   5. Ye file (START_PROJECT.bat) dobara double-click karo
echo.
echo ============================================================
pause
exit /b 1
