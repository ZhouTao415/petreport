# app.py
"""Streamlit 入口：表单填写、生成报告、下载"""

import base64
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from report.config import (
    CONCLUSION_LEVEL_OPTIONS,
    ORG_ABBREV,
    ORG_NAME,
    OUTPUT_DIR,
    PET_GENDER_OPTIONS,
    SAMPLE_NAME_OPTIONS,
    TEMPLATE_PATH,
)
from report.data_logger import save_submission_to_csv
from report.generator import (
    build_conclusion_text,
    build_test_result_text,
    convert_to_pdf,
    format_issue_date_cn,
    make_report_no,
    render_docx,
)


def _safe_report_no() -> str:
    """获取报告编号，失败时返回当日占位编号，避免云端刷新后因写文件失败导致页面空白。"""
    try:
        return make_report_no()
    except Exception:
        return f"LS{ORG_ABBREV}{date.today().strftime('%Y%m%d')}-W-01"


st.set_page_config(page_title="狂犬病毒抗体检测报告", layout="wide")

st.title("狂犬病毒抗体检测报告生成")
st.caption("填写表单，上传采样照片，生成 Word 报告并导出 PDF")


def _ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)


# ----- 表单分组 -----
with st.form("report_form", clear_on_submit=False):
    # 1. 基本信息
    st.subheader("基本信息")
    col1, col2 = st.columns(2)
    with col1:
        report_no = st.text_input("报告编号（自动生成）", value=_safe_report_no(), disabled=True)
        client_name = st.text_input("客户姓名 *", placeholder="请输入客户姓名", max_chars=50)
        client_address = st.text_input("客户地址", placeholder="请输入地址", max_chars=200)
    with col2:
        recv_date = st.date_input("收样日期", value=date.today(), format="YYYY-MM-DD")
        issue_date_cn = format_issue_date_cn(date.today())
        st.text_input("签发日期（自动）", value=issue_date_cn, disabled=True)

    # 2. 宠物信息
    st.subheader("宠物信息")
    col1, col2 = st.columns(2)
    with col1:
        sample_name_choice = st.selectbox(
            "样品名称 *",
            options=SAMPLE_NAME_OPTIONS,
            index=0,
            help="可下拉选择，或选“其他（手填）”后自行输入",
        )
        other_sample_name = st.text_input(
            "自定义样品名称（选“其他”时填写）",
            placeholder="选“其他（手填）”时在此输入，如：田园犬血清",
            max_chars=50,
            label_visibility="visible",
        )
        sample_name = (other_sample_name or "").strip() or sample_name_choice
    with col2:
        pet_gender = st.selectbox("宠物性别", options=PET_GENDER_OPTIONS, index=0)
        pet_age = st.text_input("宠物年龄", placeholder="如：2岁", max_chars=20)

    # 3. 检验信息
    st.subheader("检验信息")
    col1, col2 = st.columns(2)
    with col1:
        sender_name = st.text_input(
            "送样者",
            placeholder="请输入送样者姓名",
            max_chars=30,
            help="即送样者姓名/宠物主人姓名",
        )
    with col2:
        antibody_value_raw = st.text_input(
            "抗体滴度 (IU/ml) *",
            placeholder="如：0 或 1.2",
            help="输入数值，程序将生成完整检验结果文本",
        )
        conclusion_level = st.selectbox(
            "抗体保护水平",
            options=CONCLUSION_LEVEL_OPTIONS,
            index=1,
            help="达到：抗体达标；未达到：抗体未达标",
        )

    # 4. 照片与备注
    st.subheader("照片与备注")
    st.caption("可将照片直接拖拽到此区域，或点击选择文件（支持 jpg、png）")
    sampling_photo = st.file_uploader(
        "拖拽或点击上传采样照片",
        type=["jpg", "jpeg", "png"],
        help="从微信、文件夹等按住照片拖入上方虚线框即可",
        label_visibility="collapsed",
    )
    sampling_note = st.text_area("采样备注", placeholder="可留空", max_chars=500, height=80)

    # 生成报告按钮：放在最下方居中
    _, btn_col, _ = st.columns([1.5, 1, 1])
    with btn_col:
        submitted = st.form_submit_button("生成报告")


if submitted:
    _ensure_dirs()

    if not TEMPLATE_PATH.exists():
        st.error(f"模板文件不存在，请将 templatepet.docx 放入 {TEMPLATE_PATH.parent} 目录")
        st.stop()

    if not client_name or not client_name.strip():
        st.warning("请填写客户姓名")
        st.stop()

    # 解析抗体数值
    try:
        antibody_value = float(antibody_value_raw.strip()) if antibody_value_raw and antibody_value_raw.strip() else 0.0
    except ValueError:
        st.warning("抗体滴度请输入有效数字")
        st.stop()

    if sample_name_choice == "其他（手填）" and not (other_sample_name and str(other_sample_name).strip()):
        st.warning('选择"其他（手填）"时请填写样品名称')
        st.stop()

    report_no_final = make_report_no()

    # 适配 templatepet.docx 占位符
    recv_str = recv_date.strftime("%Y-%m-%d")
    data_dict = {
        "org_name": ORG_NAME,
        "report_no": report_no_final,
        "sample_name": sample_name,
        "client_name": client_name.strip(),
        "client_address": (client_address or "").strip(),
        "pet_gender": pet_gender,
        "pet_age": (pet_age or "").strip(),
        "sender_name": (sender_name or "").strip(),
        "recv_date": recv_str,
        "antibody_value": antibody_value,
        "test_result_text": build_test_result_text(antibody_value),
        "test_date": recv_str,
        "conclusion_text": build_conclusion_text(sample_name, conclusion_level),
        "issue_date_cn": format_issue_date_cn(recv_date),
        "sampling_note": (sampling_note or "").strip(),
    }

    out_docx = OUTPUT_DIR / f"{report_no_final}.docx"
    out_pdf = OUTPUT_DIR / f"{report_no_final}.pdf"

    photo_path: Path | None = None
    if sampling_photo is not None:
        suffix = Path(sampling_photo.name).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(sampling_photo.getvalue())
            photo_path = Path(tmp.name)

    try:
        render_docx(data_dict, TEMPLATE_PATH, out_docx, photo_path)
        convert_to_pdf(out_docx, out_pdf)

        photo_bytes: bytes | None = None
        photo_ext: str = ".jpg"
        if sampling_photo is not None:
            photo_bytes = sampling_photo.getvalue()
            ext = Path(sampling_photo.name).suffix
            photo_ext = ext if ext else ".jpg"
        save_submission_to_csv(
            report_no=report_no_final,
            recv_date=recv_str,
            client_name=client_name.strip(),
            client_address=(client_address or "").strip(),
            sample_name=sample_name,
            pet_gender=pet_gender,
            pet_age=(pet_age or "").strip(),
            antibody_value=antibody_value,
            sampling_note=(sampling_note or "").strip(),
            photo_bytes=photo_bytes,
            photo_extension=photo_ext,
        )

        st.success("报告生成成功！")
        st.info(f"输出路径：\n- {out_docx}\n- {out_pdf}")

        col1, col2, col3 = st.columns(3)
        with col1:
            with open(out_docx, "rb") as f:
                st.download_button(
                    "下载 DOCX",
                    data=f.read(),
                    file_name=out_docx.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        with col2:
            with open(out_pdf, "rb") as f:
                st.download_button(
                    "下载 PDF",
                    data=f.read(),
                    file_name=out_pdf.name,
                    mime="application/pdf",
                )
        with col3:
            with open(out_pdf, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<a href="data:application/pdf;base64,{pdf_b64}" target="_blank" '
                'style="display:inline-block;padding:0.5rem 1.5rem;background:#262730;color:white;text-decoration:none;'
                'border-radius:0.5rem;font-size:0.9rem;">打印</a>',
                unsafe_allow_html=True,
            )
            st.caption("新窗口打开后按 Ctrl+P 打印")
    except FileNotFoundError as e:
        st.error(str(e))
    except RuntimeError as e:
        st.error(f"转换失败：{e}")
    finally:
        if photo_path is not None and photo_path.exists() and str(photo_path).startswith(tempfile.gettempdir()):
            photo_path.unlink(missing_ok=True)
