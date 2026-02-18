@echo off
chcp 65001 >nul
echo ========================================
echo 打包 狂犬病毒抗体检测报告 为 exe
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo 错误：依赖安装失败
    pause
    exit /b 1
)

REM 确保模板存在
if not exist "templates\templatepet.docx" (
    echo 警告：templates\templatepet.docx 不存在，请将模板放入后重新打包
    pause
)

REM 打包（排除 torch/scipy 等大型未用库以减小体积）
echo.
echo [2/3] 正在打包（约需 2-5 分钟）...
python -m PyInstaller --noconfirm --clean ^
    --exclude-module torch ^
    --exclude-module torchvision ^
    --exclude-module tensorflow ^
    --exclude-module keras ^
    --onedir ^
    --name "PetReport" ^
    --copy-metadata streamlit ^
    --copy-metadata docxtpl ^
    --collect-all streamlit ^
    --collect-all docxtpl ^
    --add-data "app.py;." ^
    --add-data "report;report" ^
    --add-data "templates;templates" ^
    --hidden-import streamlit ^
    --hidden-import docxtpl ^
    --hidden-import docxtpl.inline_image ^
    --hidden-import docx ^
    --hidden-import docx.shared ^
    --hidden-import PIL ^
    --hidden-import jinja2 ^
    --hidden-import docx2pdf ^
    launcher.py

if errorlevel 1 (
    echo.
    echo 错误：打包失败
    pause
    exit /b 1
)

echo.
echo [3/3] 完成！
echo.
echo 输出目录：dist\PetReport\
echo 运行方式：双击 dist\PetReport\PetReport.exe
echo.
echo 分发给他人时，请将整个 PetReport 文件夹一并复制。
echo.
echo 提示：若体积仍偏大，可用「 build_exe_minimal.bat 」在干净虚拟环境中打包（体积更小）。
echo.
pause
