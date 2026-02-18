# report/generator.py
"""报告生成：模板填充、图片插入、PDF 导出"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm

from report.config import (
    COUNTER_FILE,
    ORG_ABBREV,
    ORG_NAME,
    OUTPUT_DIR,
    SAMPLING_PHOTO_WIDTH_CM,
    TEMPLATE_PATH,
)


def make_report_no() -> str:
    """生成报告编号：LS{机构首字母}{YYYYMMDD}-W-{序号}，如 LSZZCW20260218-W-01"""
    today: str = date.today().strftime("%Y%m%d")

    # 读取并递增序号（持久化）
    try:
        if COUNTER_FILE.exists():
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("count", 0)
        else:
            count = 0
    except (json.JSONDecodeError, OSError):
        count = 0

    count += 1

    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"count": count}, f, ensure_ascii=False)
    except OSError:
        pass  # 仍使用当前 count 生成编号

    seq = str(count).zfill(2) if count < 100 else str(count)
    return f"LS{ORG_ABBREV}{today}-W-{seq}"


def format_issue_date_cn(d: date) -> str:
    """格式化日期为中文：YYYY年M月D日"""
    return f"{d.year}年{d.month}月{d.day}日"


def build_test_result_text(antibody_value: float | int) -> str:
    """根据 antibody_value 生成检验结果文本"""
    return f"血清抗体滴度为{antibody_value} IU/ml"


def build_conclusion_text(sample_name: str, protection_level: str = "未达到") -> str:
    """根据 sample_name 与 protection_level（达到/未达到）拼接检验结论"""
    name_for_text: str = (
        sample_name.replace("血清", "的血清") if "血清" in sample_name else f"{sample_name}的"
    )
    return f"对 {name_for_text} 样本进行狂犬病抗体ELISA检测，抗体{protection_level}保护水平。"


def _ensure_docx_compatible_image(image_path: Path) -> Path:
    """
    确保图片可被 python-docx 识别（修复损坏头、转换为 PNG）。
    若转换失败则返回占位图路径。
    """
    try:
        from PIL import Image

        img = Image.open(image_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            img.save(out.name, format="PNG")
            return Path(out.name)
    except Exception:
        placeholder = Path(__file__).parent.parent / "templates" / "placeholder.png"
        if not placeholder.exists():
            _create_placeholder_image(placeholder)
        return placeholder


def _prepare_context(
    doc: DocxTemplate,
    data_dict: dict[str, Any],
    photo_path: Path | None,
) -> tuple[dict[str, Any], Path | None]:
    """
    构建 docxtpl 渲染上下文，doc 用于 InlineImage。
    返回 (ctx, temp_image_path) 便于渲染后删除临时转换的图片。
    """
    ctx: dict[str, Any] = dict(data_dict)
    temp_img: Path | None = None

    if photo_path is not None and photo_path.exists():
        img_path = _ensure_docx_compatible_image(photo_path)
        if str(img_path).startswith(tempfile.gettempdir()):
            temp_img = img_path
        ctx["sampling_photo"] = InlineImage(
            doc,
            str(img_path),
            width=Cm(SAMPLING_PHOTO_WIDTH_CM),
        )
    else:
        placeholder = Path(__file__).parent.parent / "templates" / "placeholder.png"
        if not placeholder.exists():
            _create_placeholder_image(placeholder)
        ctx["sampling_photo"] = InlineImage(
            doc,
            str(placeholder),
            width=Cm(SAMPLING_PHOTO_WIDTH_CM),
        )
    return ctx, temp_img


def _create_placeholder_image(out_path: Path) -> None:
    """创建“未提供照片”占位图"""
    from PIL import Image, ImageDraw, ImageFont

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (400, 150), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("msyh.ttc", 24)  # 微软雅黑
    except OSError:
        font = ImageFont.load_default()
    text = "（未提供照片）"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((400 - w) // 2, (150 - h) // 2), text, fill=(150, 150, 150), font=font)
    img.save(out_path)


def _patch_template_xml(template_path: Path) -> Path:
    """
    修复模板中导致 Jinja2 解析失败的字符（如 {{{ 应为 {{），
    返回修复后的临时模板路径。
    """
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    with ZipFile(template_path, "r") as zin:
        names = zin.namelist()
        with ZipFile(tmp_path, "w", ZIP_DEFLATED) as zout:
            for name in names:
                data = zin.read(name)
                if name == "word/document.xml":
                    xml = data.decode("utf-8")
                    # 修复 {{{ 为 {{（模板中多余花括号会导致 Jinja2 报错）
                    xml = xml.replace("{{{", "{{").replace("}}}", "}}")
                    data = xml.encode("utf-8")
                zout.writestr(name, data)
    return tmp_path


def render_docx(
    data_dict: dict[str, Any],
    template_path: Path,
    out_docx_path: Path,
    photo_path: Path | None = None,
) -> None:
    """
    使用 data_dict 填充 Word 模板，插入图片（若有），输出 docx。

    Args:
        data_dict: 占位符 → 值的字典
        template_path: 模板 docx 路径
        out_docx_path: 输出 docx 路径
        photo_path: 采样照片路径，None 表示未上传
    """
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_path}")

    out_docx_path.parent.mkdir(parents=True, exist_ok=True)

    patched = _patch_template_xml(template_path)
    temp_img: Path | None = None
    try:
        doc = DocxTemplate(str(patched))
        ctx, temp_img = _prepare_context(doc, data_dict, photo_path)
        doc.render(ctx)
        doc.save(str(out_docx_path))
    finally:
        patched.unlink(missing_ok=True)
        if temp_img is not None and temp_img.exists():
            temp_img.unlink(missing_ok=True)


def convert_to_pdf(in_docx_path: Path, out_pdf_path: Path) -> None:
    """
    将 docx 转为 PDF。
    Windows 优先使用 docx2pdf（调用本机 Word），否则尝试 LibreOffice。
    Linux/macOS 仅使用 LibreOffice（docx2pdf 依赖 Word，仅支持 Windows）。
    """
    if not in_docx_path.exists():
        raise FileNotFoundError(f"源 docx 不存在: {in_docx_path}")

    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    import platform
    import subprocess

    # 1. 仅在 Windows 上尝试 docx2pdf（依赖本机 Word；Linux/macOS 会直接报错）
    if platform.system() == "Windows":
        try:
            from docx2pdf import convert as docx2pdf_convert
            docx2pdf_convert(str(in_docx_path), str(out_pdf_path))
            return
        except ImportError:
            pass
        except Exception as e:
            pass  # 失败则 fallback 到 LibreOffice

    # 2. 使用 LibreOffice（Windows/macOS/Linux 通用，云端已安装）
    if platform.system() == "Windows":
        soffice_candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif platform.system() == "Darwin":
        soffice_candidates = ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    else:
        soffice_candidates = ["soffice", "/usr/bin/soffice"]

    # 导出参数：嵌入字体、无损/高质量图像，减少版式错乱
    pdf_export_opts = {
        "EmbedStandardFonts": {"type": "boolean", "value": "true"},
        "UseLosslessCompression": {"type": "boolean", "value": "true"},
        "Quality": {"type": "long", "value": "100"},
        "ReduceImageResolution": {"type": "boolean", "value": "false"},
    }
    convert_to_spec = "pdf:writer_pdf_Export:" + json.dumps(pdf_export_opts, separators=(",", ":"))

    profile_dir = tempfile.mkdtemp(prefix="lo_pdf_")
    try:
        profile_uri = Path(profile_dir).as_uri()
        for exe in soffice_candidates:
            p = Path(exe)
            if p.is_absolute() and not p.exists():
                continue
            try:
                subprocess.run(
                    [
                        exe,
                        "--headless",
                        "--invisible",
                        "--nologo",
                        "--nofirststartwizard",
                        f"-env:UserInstallation={profile_uri}",
                        "--convert-to",
                        convert_to_spec,
                        "--outdir",
                        str(out_pdf_path.parent),
                        str(in_docx_path),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=90,
                    cwd=str(in_docx_path.parent),
                )
                generated = out_pdf_path.parent / (in_docx_path.stem + ".pdf")
                if generated.exists():
                    if generated != out_pdf_path:
                        generated.rename(out_pdf_path)
                    return
            except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
                continue
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)

    raise RuntimeError(
        "PDF 转换失败：未安装 docx2pdf（依赖本机 Word）或 LibreOffice。"
        "请安装: pip install docx2pdf，或安装 LibreOffice 并加入 PATH。"
    )
