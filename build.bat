@echo off
REM ============================================================
REM  Build Forza Horizon 6 Car Tracker into a single .exe
REM ============================================================
cd /d "%~dp0"

echo Installing / updating PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller

echo.
echo Building executable...
".venv\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "Forza Car Tracker" ^
  --icon "icon.ico" ^
  --add-data "cars.json;." ^
  --add-data "image.png;." ^
  --add-data "icon.ico;." ^
  forza_car_tracker.py

echo.
echo ============================================================
echo  Done! Your program is here:
echo     dist\Forza Car Tracker.exe
echo ============================================================
echo  (owned_cars.json and settings.json will be created next to
echo   the .exe when you run it - that is where your progress is saved.)
echo.
pause
