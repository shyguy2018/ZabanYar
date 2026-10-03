@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "%~dp0app.py" (
  echo.
  echo  ERROR: Please EXTRACT the zip file first, then run build.bat from the extracted folder.
  echo.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo  ERROR: Python is not installed, or "Add python.exe to PATH" was not ticked.
  echo         Install Python from https://www.python.org/downloads/ and tick
  echo         "Add python.exe to PATH" during setup. Then run build.bat again.
  echo.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)

echo.
echo   ZabanYar - Made by Behrooz Shayestepoor
echo.
echo === Step 1/3: Installing requirements ===
python -m pip install --upgrade -r requirements.txt pyinstaller
if errorlevel 1 goto failed

echo === Step 2/3: Preparing dictionaries and icon ===
python tools\make_wordlists.py
if errorlevel 1 goto failed
python tools\make_ico.py
if errorlevel 1 goto failed

echo === Step 3/3: Building ZabanYar.exe ===
python -m PyInstaller --noconfirm --noconsole --onefile --name ZabanYar --icon "assets\ZabanYar.ico" --version-file version_info.txt --add-data "data;data" --hidden-import pystray._win32 --collect-submodules pystray --hidden-import PIL._tkinter_finder app.py
if errorlevel 1 goto failed
if not exist "dist\ZabanYar.exe" goto failed

copy /y "dist\ZabanYar.exe" "%~dp0ZabanYar.exe" >nul
rmdir /s /q build >nul 2>nul
del /q ZabanYar.spec >nul 2>nul

echo.
echo  DONE!  ZabanYar.exe is now in this folder:
echo  %~dp0
echo.
explorer /select,"%~dp0ZabanYar.exe"
pause
exit /b 0

:failed
echo.
echo  BUILD FAILED. Please take a screenshot of this window and send it.
echo.
pause
exit /b 1
