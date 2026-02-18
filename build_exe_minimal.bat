@echo off
chcp 65001 >nul
echo ========================================
echo Build PetReport (Python 3.8, Win7+)
echo ========================================
echo.

if exist ".venv_build" (
    echo Removing old venv...
    rmdir /s /q .venv_build
)

echo [1/4] Creating venv with Python 3.8...
py -3.8 -m venv .venv_build
call .venv_build\Scripts\activate.bat

echo [2/4] Installing deps...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
python -m pip install pyinstaller -q

echo.
echo [3/4] Building (exclude heavy libs to reduce size)...
python -m PyInstaller --noconfirm --clean --onedir --name PetReport --exclude-module torch --exclude-module torchvision --exclude-module tensorflow --exclude-module keras --exclude-module scipy --exclude-module sklearn --exclude-module matplotlib --exclude-module cv2 --exclude-module IPython --exclude-module jupyter --exclude-module pytest --copy-metadata streamlit --copy-metadata docxtpl --collect-all streamlit --collect-all docxtpl --add-data "app.py;." --add-data "report;report" --add-data "templates;templates" --hidden-import streamlit --hidden-import docxtpl --hidden-import docxtpl.inline_image --hidden-import docx --hidden-import docx.shared --hidden-import PIL --hidden-import jinja2 --hidden-import docx2pdf launcher.py

call deactivate 2>nul
echo.
echo [4/4] Done. Output: dist\PetReport\
pause
