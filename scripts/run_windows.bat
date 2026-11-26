@echo off
REM Run straight from source (needs Python + "pip install -r requirements.txt").  Drag a folder onto this file to open it.
cd /d "%~dp0\.."
python run.py %*
