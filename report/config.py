# report/config.py
"""配置：下拉选项、常量、路径"""

from pathlib import Path

# 机构名称（固定）
ORG_NAME: str = "临沂正直宠物医院"

# 机构编号前缀：LS + 诊疗机构名称首字母，正直宠物医院=ZZCW
ORG_ABBREV: str = "ZZCWYY"

# 报告序号存储文件（用于递增计数）
COUNTER_FILE: Path = Path(__file__).resolve().parent.parent / "report_counter.json"

# 样品名称下拉选项
SAMPLE_NAME_OPTIONS: list[str] = [
    "犬血清",
    "猫血清",
    "卷毛比熊犬血清",
    "金毛犬血清",
    "拉布拉多犬血清",
    "其他（手填）",
]


# 宠物性别
PET_GENDER_OPTIONS: list[str] = ["公", "母"]

# 检验结论：抗体保护水平（达到 / 未达到）
CONCLUSION_LEVEL_OPTIONS: list[str] = ["达到", "未达到"]

# 图片插入宽度（cm）
SAMPLING_PHOTO_WIDTH_CM: float = 12.0

# 项目根目录
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# 模板路径（使用 templatepet.docx 以保持格式排版）
TEMPLATE_PATH: Path = PROJECT_ROOT / "templates" / "templatepet.docx"

# 输出目录
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"

# 数据记录目录（按日期保存 CSV）
DATA_DIR: Path = PROJECT_ROOT / "data"
