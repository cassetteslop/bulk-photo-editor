@echo off
REM ---------------------------------------------------------------------------
REM  Easiest way to run Bulk Photo Editor on Windows WITHOUT building an .exe:
REM  double-click this file. It sets up a private Python environment next to the app, installs what it
REM  needs, and puts a "Bulk Photo Editor" shortcut on your Desktop and in the Start menu.
REM  Needs Python 3.9+ from https://www.python.org/downloads/windows/ ("Add python.exe to PATH" ticked).
REM  Re-run it any time to update; run packaging\windows\uninstall_from_source.bat to remove the shortcuts.
REM ---------------------------------------------------------------------------
setlocal enableextensions
cd /d "%~dp0\..\.."
set ROOT=%CD%

where python >nul 2>nul || (echo Python was not found. Install it from https://www.python.org/downloads/windows/ and tick "Add python.exe to PATH". & pause & exit /b 1)
python -c "import tkinter" 2>nul || (echo This Python has no Tk. Re-run the Python installer, choose Modify, and tick "tcl/tk and IDLE". & pause & exit /b 1)

echo Creating environment...
python -m venv "%ROOT%\.venv" || (pause & exit /b 1)
"%ROOT%\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul
"%ROOT%\.venv\Scripts\python.exe" -m pip install -r "%ROOT%\requirements.txt" || (pause & exit /b 1)
if not exist "%ROOT%\packaging\windows\BulkPhotoEditor.ico" "%ROOT%\.venv\Scripts\python.exe" "%ROOT%\packaging\make_icon.py"

echo Creating shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\packaging\windows\create_shortcuts.ps1" -Root "%ROOT%"

echo.
echo Done. Start "Bulk Photo Editor" from your Desktop or Start menu.
echo Tip: drag a folder of photos onto the window - or onto the shortcut.
pause
endlocal
