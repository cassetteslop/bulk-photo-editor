@echo off
REM Removes the shortcuts made by install_from_source.bat (and the private environment). Your photos are never touched.
setlocal
cd /d "%~dp0\..\.."
powershell -NoProfile -Command "foreach($d in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs'))){ Remove-Item (Join-Path $d 'Bulk Photo Editor.lnk') -ErrorAction SilentlyContinue }"
if exist .venv rmdir /s /q .venv
echo Removed.
pause
endlocal
