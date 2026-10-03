@echo off
cd /d "%~dp0"
python -m pip install --quiet -r requirements.txt
if not exist "data\en.txt" python tools\make_wordlists.py
start "" pythonw "%~dp0app.py"
