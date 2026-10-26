@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm cinema.spec
copy /y "cinema_app\config.example.ini" "dist\config.ini" >nul
echo.
echo Готово: dist\Cinema.exe
pause
