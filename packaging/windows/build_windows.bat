@echo off
REM ---------------------------------------------------------------------------
REM  Build "Bulk Photo Editor" for Windows.
REM    packaging\windows\build_windows.bat            -> dist\BulkPhotoEditor\BulkPhotoEditor.exe (+ .zip)
REM    and, if Inno Setup 6 is installed             -> dist\BulkPhotoEditor-Setup-<version>.exe
REM  Needs: Python 3.9+ from python.org (tick "Add python.exe to PATH" and keep "tcl/tk" selected).
REM ---------------------------------------------------------------------------
setlocal enableextensions
cd /d "%~dp0\..\.."

where python >nul 2>nul || (echo Python was not found on PATH. Install it from https://www.python.org/downloads/windows/ & exit /b 1)
python -c "import tkinter" 2>nul || (echo This Python has no Tk. Re-run the Python installer, choose Modify, and tick "tcl/tk and IDLE". & exit /b 1)

for /f "delims=" %%v in ('python packaging\windows\get_version.py') do set VERSION=%%v
echo === Bulk Photo Editor %VERSION% ===

echo --- creating virtual environment (.build-venv)
python -m venv .build-venv || exit /b 1
call .build-venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements-windows.txt || exit /b 1

echo --- icon
if not exist packaging\windows\BulkPhotoEditor.ico python packaging\make_icon.py

echo --- PyInstaller
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --noconfirm --clean packaging\windows\BulkPhotoEditor.spec || exit /b 1

echo --- portable zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\BulkPhotoEditor' -DestinationPath 'dist\BulkPhotoEditor-%VERSION%-portable.zip' -Force"

echo --- installer (Inno Setup)
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if defined ISCC (
    "%ISCC%" /DAppVersion=%VERSION% packaging\windows\installer.iss || exit /b 1
    echo.
    echo Installer: dist\BulkPhotoEditor-Setup-%VERSION%.exe
) else (
    echo Inno Setup 6 not found - skipped. Get it free from https://jrsoftware.org/isdl.php to also build Setup.exe.
)
echo.
echo Done.  App folder: dist\BulkPhotoEditor\BulkPhotoEditor.exe
endlocal
