@echo off
title Fraud Analysis Tool - Gujarat Cyber Crime
color 0A

echo ========================================
echo   FRAUD ANALYSIS TOOL
echo   Gujarat State Cyber Crime Police
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
echo      Python found!

echo.
echo [2/3] Checking Streamlit installation...
python -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo      Streamlit not found. Installing...
    pip install streamlit pandas openpyxl
) else (
    echo      Streamlit found!
)

echo.
echo [3/3] Starting application...
echo.
echo ========================================
echo   APPLICATION RUNNING
echo   Browser will open automatically
echo   URL: http://localhost:8501
echo.
echo   Keep this window OPEN
echo   Close this window to STOP the app
echo ========================================
echo.

REM Wait 2 seconds then open browser
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8501"

REM Start Streamlit
python -m streamlit run src/app.py --server.headless true --server.port 8501

pause
