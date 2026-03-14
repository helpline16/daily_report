@echo off
title Create Desktop Shortcut
color 0B

echo ========================================
echo   CREATE DESKTOP SHORTCUT
echo   Fraud Analysis Tool
echo ========================================
echo.

REM Get the current directory
set "SCRIPT_DIR=%~dp0"

REM Get the Desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

REM Create VBS script to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\Fraud Analysis Tool.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%launcher.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Fraud Analysis Tool - Gujarat Cyber Crime" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%%SystemRoot%%\System32\shell32.dll,13" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

REM Run the VBS script
cscript //nologo "%TEMP%\CreateShortcut.vbs"

REM Clean up
del "%TEMP%\CreateShortcut.vbs"

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Desktop shortcut created successfully!
echo.
echo You can now double-click the shortcut on
echo your desktop to launch the application.
echo.
echo Shortcut location:
echo %DESKTOP%\Fraud Analysis Tool.lnk
echo.
echo ========================================

pause
