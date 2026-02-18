# report/data_logger.py
"""将每次填写的数据追加保存到按日期命名的 CSV 文件，照片保存到 data/{日期}/photos/"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from report.config import DATA_DIR


def save_submission_to_csv(
    *,
    report_no: str,
    recv_date: str,
    client_name: str,
    client_address: str,
    sample_name: str,
    pet_gender: str,
    pet_age: str,
    antibody_value: float | int,
    sampling_note: str,
    photo_bytes: bytes | None = None,
    photo_extension: str = ".jpg",
) -> Path:
    """
    将本次提交数据追加到 data/{日期}.csv。
    若有照片，保存到 data/{日期}/photos/{report_no}.jpg，CSV 中存相对路径。

    Returns:
        写入的 CSV 文件路径
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"{recv_date}.csv"

    photo_rel_path: str = ""
    if photo_bytes:
        photos_dir = DATA_DIR / recv_date / "photos"
        photos_dir.mkdir(parents=True, exist_ok=True)
        suffix = photo_extension if photo_extension.startswith(".") else f".{photo_extension}"
        photo_file = photos_dir / f"{report_no}{suffix}"
        photo_file.write_bytes(photo_bytes)
        photo_rel_path = f"{recv_date}/photos/{photo_file.name}"

    fieldnames = [
        "客户编号",
        "日期",
        "客户姓名",
        "客户地址",
        "样品名称",
        "宠物性别",
        "宠物年龄",
        "抗体滴度(IU/ml)",
        "照片与备注",
        "照片",
    ]
    row: dict[str, Any] = {
        "客户编号": report_no,
        "日期": recv_date,
        "客户姓名": client_name,
        "客户地址": client_address,
        "样品名称": sample_name,
        "宠物性别": pet_gender,
        "宠物年龄": pet_age,
        "抗体滴度(IU/ml)": antibody_value,
        "照片与备注": sampling_note,
        "照片": photo_rel_path,
    }

    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return csv_path
