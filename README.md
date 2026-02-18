# 狂犬病毒抗体检测报告生成器

本地运行的最小可用项目（MVP），实现：**表单填写 + 插入采样照片 + 根据 Word 模板生成排版稳定的报告 + 导出 PDF**。

## 功能

- 本地 Streamlit 界面，填写/选择字段
- 上传 1 张采样照片（jpg/png），可选
- 将数据填充到 Word 模板，保持排版与模板一致
- 导出 `filled_docx` 与 `output_pdf`，文件名为报告编号

## 环境要求

- Python 3.10+（建议 3.11）
- Windows：生成 PDF 需安装 **Microsoft Word**（通过 docx2pdf）或 **LibreOffice**
- macOS/Linux：生成 PDF 需安装 **LibreOffice**

## 从零开始运行

### 1. 安装依赖

```bash
cd autopetprint
pip install -r requirements.txt
```

### 2. 放置模板

将 `templatepet.docx` 放入 `templates/` 目录（当前使用此模板以保持格式排版）：

```
autopetprint/
  templates/
    templatepet.docx   <-- 放这里
  ...
```

模板中需使用 Jinja2 占位符（双花括号 `{{ 变量名 }}`）。templatepet.docx 已适配以下占位符：

| 占位符 | 说明 |
|--------|------|
| `{{report_no}}` | 报告编号（自动） |
| `{{sample_name}}` | 样品名称 |
| `{{client_name}}` | 客户姓名 |
| `{{client_address}}` | 客户地址 |
| `{{pet_gender}}` | 宠物性别 |
| `{{pet_age}}` | 宠物年龄 |
| `{{sender_name}}` | 送样者 |
| `{{recv_date}}` | 收样日期 YYYY-MM-DD |
| `{{antibody_value}}` | 抗体滴度数值 |
| `{{test_date}}` | 检验日期（同 recv_date） |
| `{{conclusion_text}}` | 检验结论 |
| `{{sampling_photo}}` | 采样照片插入点 |
| `{{sampling_note}}` | 采样备注 |

### 3. 启动 Streamlit

```bash
streamlit run app.py
```

浏览器会打开 `http://localhost:8501`。

### 4. 填写表单并生成报告

1. 填写基本信息、宠物信息、检验信息
2. 可选上传 1 张采样照片
3. 点击「生成报告」
4. 成功后下载 DOCX 和 PDF

输出文件保存在 `outputs/` 目录，文件名格式：`LS20251101-4827-W-1.docx` / `.pdf`。

## 项目结构

```
autopetprint/
  app.py              # Streamlit 入口
  report/
    __init__.py
    config.py         # 下拉配置、常量
    generator.py      # 模板填充、PDF 导出
  templates/
    templatepet.docx   # 用户提供的模板（格式排版版）
    placeholder.png   # 未上传照片时的占位图（自动生成）
  outputs/            # 生成的 docx、pdf（自动创建）
  data/               # 每次提交的数据 CSV（按日期命名）+ 照片（data/{日期}/photos/）
  requirements.txt
  README.md
```

## PDF 转换说明

### Windows

- **推荐**：安装 Microsoft Word，使用 `docx2pdf` 调用 Word 转换
- **备选**：安装 [LibreOffice](https://www.libreoffice.org/)，程序会尝试使用 `C:\Program Files\LibreOffice\program\soffice.exe`

### macOS

- 安装 LibreOffice：`brew install --cask libreoffice`
- 或使用本机 Word（若已安装）

### Linux

- 安装 LibreOffice：`sudo apt install libreoffice`（Ubuntu/Debian）

## 常见错误排查

### 1. 模板不存在

**现象**：提示「模板文件不存在」

**处理**：确认 `templates/templatepet.docx` 存在，且文件名、路径正确。

### 2. PDF 转换失败

**现象**：提示「未安装 docx2pdf 或 LibreOffice」

**处理**：
- Windows：安装 Word 或 LibreOffice
- macOS/Linux：安装 LibreOffice：`brew install --cask libreoffice` 或 `apt install libreoffice`
- 确认 LibreOffice 路径为 `C:\Program Files\LibreOffice\program\soffice.exe`（Windows）

### 3. docx2pdf 报错「Word 未安装」

**处理**：本机需安装正版 Microsoft Word，docx2pdf 通过 COM 调用 Word。

### 4. 图片插入异常

**处理**：确保上传为 jpg/png，且文件未损坏。未上传时使用自动生成的占位图。

### 5. 占位符未被替换

**处理**：检查模板中占位符为 `{{name}}` 格式（双花括号、无多余空格），与 `config.py` / `generator.py` 中的 key 一致。

## 打包为 exe（分发给他人使用）

将项目打包为 exe，他人无需安装 Python 即可运行：

### 1. 打包步骤

```bash
# 在项目目录下执行
build_exe.bat
```

或手动执行：

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onedir --name "狂犬病毒抗体检测报告" ^
  --copy-metadata streamlit --collect-all streamlit ^
  --add-data "app.py;." --add-data "report;report" --add-data "templates;templates" ^
  launcher.py
```

### 2. 输出位置

打包完成后，在 `dist/PetReport/` 目录下会生成：

- `PetReport.exe`：主程序
- `_internal/`：依赖文件（templates、report、streamlit 等）

### 3. 分发给他人

将整个 `dist/PetReport` 文件夹打包（如 ZIP），发给他人。对方解压后：

1. 双击 `PetReport.exe`
2. 等待几秒，浏览器会自动打开
3. 在页面中填写表单并生成报告

**注意**：
- 生成 PDF 仍需本机安装 **Word** 或 **LibreOffice**
- 报告和 CSV 数据会保存在 exe 所在目录下的 `outputs/`、`data/` 文件夹

**体积优化**：若打包后体积过大（如含 PyTorch 时可达 1GB+），可执行 `build_exe_minimal.bat` 在干净虚拟环境中打包，体积可降至约 80–150MB。

---

## 配置

在 `report/config.py` 中可修改：

- `SAMPLE_NAME_OPTIONS`：样品名称下拉选项
- 宠物主人姓名：即送样者，直接填写
- `SAMPLING_PHOTO_WIDTH_CM`：插入图片宽度（cm）
