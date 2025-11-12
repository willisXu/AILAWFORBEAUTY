"""
单位转换工具模块

提供法规数据中各种单位的转换功能：
- 浓度单位转换（g/100g, ppm, % 等）
- 日本特殊符号处理（○ = 无上限，空白 = 禁止）
- 产品类型标准化
"""

import re
from typing import Optional, Union, Tuple
import logging

logger = logging.getLogger(__name__)


# 单位转换系数（转换为 %）
UNIT_CONVERSION_FACTORS = {
    "g/100g": 1.0,          # g/100g 等于 %（数值相同）
    "%": 1.0,               # % 保持不变
    "w/w%": 1.0,            # w/w% = %
    "ppm": 0.0001,          # ppm → % = 值 × 0.0001
    "ppb": 0.0000001,       # ppb → % = 值 × 0.0000001
    "mg/kg": 0.0001,        # mg/kg = ppm
    "g/kg": 0.1,            # g/kg → %
}


def convert_concentration_to_percent(
    value: Union[str, float, int],
    source_unit: str = "%"
) -> Optional[float]:
    """
    将浓度值转换为百分比（%）

    Args:
        value: 原始浓度值（可能包含单位）
        source_unit: 源单位（如果 value 是数字）

    Returns:
        转换后的百分比值，失败返回 None

    Examples:
        >>> convert_concentration_to_percent("10 g/100g", "g/100g")
        10.0
        >>> convert_concentration_to_percent(1000, "ppm")
        0.1
        >>> convert_concentration_to_percent("5%")
        5.0
    """
    try:
        # 如果是字符串，先尝试提取数值和单位
        if isinstance(value, str):
            # 去除空格
            value = value.strip()

            # 处理空字符串
            if not value or value in ["", "-", "N/A", "n/a", "未规定"]:
                return None

            # 尝试从字符串中提取数值和单位
            match = re.match(
                r'^([0-9.,]+)\s*([a-zA-Z/%]+)?$',
                value.replace(',', '')
            )

            if match:
                number_str = match.group(1)
                unit_str = match.group(2) if match.group(2) else source_unit

                # 转换数值
                number = float(number_str)

                # 获取转换系数
                factor = UNIT_CONVERSION_FACTORS.get(unit_str.lower(), 1.0)

                return round(number * factor, 6)  # 保留6位小数

        # 如果是数字，直接转换
        elif isinstance(value, (int, float)):
            factor = UNIT_CONVERSION_FACTORS.get(source_unit.lower(), 1.0)
            return round(float(value) * factor, 6)

        return None

    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to convert concentration '{value}' with unit '{source_unit}': {e}")
        return None


def parse_japanese_concentration(
    value: str,
    source_unit: str = "g/100g"
) -> Tuple[Optional[float], Optional[str]]:
    """
    解析日本法规中的浓度值（包含特殊符号）

    日本特殊符号：
    - ○ : 无上限（No Limit）
    - 空白/"" : 禁止（Prohibited）
    - - : 不适用（Not Applicable）
    - 数值 : 实际浓度限制

    Args:
        value: 原始值
        source_unit: 源单位（默认为 g/100g）

    Returns:
        (浓度值, 特殊标记)
        - 如果是数值: (浓度值, None)
        - 如果是 ○: (None, "No Limit")
        - 如果是空白: (None, "Prohibited")
        - 如果是 -: (None, "Not Applicable")

    Examples:
        >>> parse_japanese_concentration("○")
        (None, "No Limit")
        >>> parse_japanese_concentration("0.5")
        (0.5, None)
        >>> parse_japanese_concentration("")
        (None, "Prohibited")
    """
    if not value or value.strip() == "":
        return (None, "Prohibited")

    value = value.strip()

    # 处理特殊符号
    if value == "○" or value.lower() in ["○", "o", "unlimited", "no limit"]:
        return (None, "No Limit")

    if value == "-" or value.lower() in ["-", "n/a", "not applicable"]:
        return (None, "Not Applicable")

    # 尝试转换为数值
    concentration = convert_concentration_to_percent(value, source_unit)

    if concentration is not None:
        return (concentration, None)
    else:
        return (None, "Prohibited")


def normalize_product_type(product_type_str: str) -> str:
    """
    标准化产品类型字符串

    Args:
        product_type_str: 原始产品类型字符串

    Returns:
        标准化后的产品类型（对应 ProductType 枚举）

    Examples:
        >>> normalize_product_type("hair products")
        "Hair"
        >>> normalize_product_type("洗い流す")
        "Rinse_Off"
        >>> normalize_product_type("冲洗类")
        "Rinse_Off"
    """
    if not product_type_str:
        return "未规定"

    product_type_str = product_type_str.strip().lower()

    # 产品类型映射表（从配置文件中提取）
    PRODUCT_TYPE_MAP = {
        # 英文
        "hair": "Hair",
        "skin": "Skin",
        "eye": "Eye",
        "lip": "Lip",
        "nail": "Nail",
        "oral": "Oral",
        "mucous membrane": "Mucosa",
        "mucosa": "Mucosa",
        "non-mucosa": "Non_Mucosa",
        "rinse-off": "Rinse_Off",
        "rinse off": "Rinse_Off",
        "leave-on": "Leave_On",
        "leave on": "Leave_On",
        "wash-off": "Rinse_Off",
        "wash off": "Rinse_Off",

        # 日文
        "洗い流す": "Rinse_Off",
        "洗い流さない": "Leave_On",
        "粘膜": "Mucosa",
        "粘膜に使用されることがない": "Non_Mucosa",
        "粘膜に使用されることがない化粧品": "Non_Mucosa",
        "粘膜に使用されることがある": "Mucosa",
        "粘膜に使用されることがある化粧品": "Mucosa",

        # 中文
        "冲洗类": "Rinse_Off",
        "驻留类": "Leave_On",
        "头发": "Hair",
        "皮肤": "Skin",
        "眼部": "Eye",
        "唇部": "Lip",
        "指甲": "Nail",
        "口腔": "Oral",
        "粘膜": "Mucosa",
        "非粘膜": "Non_Mucosa",
    }

    # 直接查找映射
    if product_type_str in PRODUCT_TYPE_MAP:
        return PRODUCT_TYPE_MAP[product_type_str]

    # 模糊匹配
    for key, value in PRODUCT_TYPE_MAP.items():
        if key in product_type_str or product_type_str in key:
            return value

    # 未找到匹配
    logger.debug(f"Unknown product type: {product_type_str}")
    return "未规定"


def validate_concentration(concentration: Optional[float]) -> bool:
    """
    验证浓度值是否在有效范围内（0-100%）

    Args:
        concentration: 浓度值

    Returns:
        是否有效
    """
    if concentration is None:
        return True  # None 是有效的（表示无限制或未规定）

    return 0.0 <= concentration <= 100.0


def format_concentration_display(
    concentration: Optional[float],
    special_note: Optional[str] = None
) -> str:
    """
    格式化浓度值用于显示

    Args:
        concentration: 浓度值
        special_note: 特殊标记（如 "No Limit"）

    Returns:
        格式化后的字符串

    Examples:
        >>> format_concentration_display(0.5)
        "0.5%"
        >>> format_concentration_display(None, "No Limit")
        "无上限"
        >>> format_concentration_display(None, "Prohibited")
        "禁止"
    """
    if special_note:
        note_map = {
            "No Limit": "无上限",
            "Prohibited": "禁止",
            "Not Applicable": "不适用",
        }
        return note_map.get(special_note, special_note)

    if concentration is None:
        return "未规定"

    # 格式化数值（去除不必要的小数位）
    if concentration == int(concentration):
        return f"{int(concentration)}%"
    else:
        return f"{concentration:.3g}%"


def parse_cas_number(cas_str: str) -> Optional[str]:
    """
    解析和验证 CAS 号码

    Args:
        cas_str: CAS 号码字符串

    Returns:
        标准格式的 CAS 号码，无效返回 None

    Examples:
        >>> parse_cas_number("50-00-0")
        "50-00-0"
        >>> parse_cas_number("50000")
        "50-00-0"
        >>> parse_cas_number("invalid")
        None
    """
    if not cas_str:
        return None

    cas_str = cas_str.strip()

    # CAS 号码格式: XXXXXXX-XX-X
    cas_pattern = re.compile(r'^\d{1,7}-\d{2}-\d$')

    # 如果已经是标准格式
    if cas_pattern.match(cas_str):
        return cas_str

    # 尝试从字符串中提取数字并格式化
    digits = re.sub(r'\D', '', cas_str)

    if len(digits) >= 5:
        # 最后一位是校验位
        check_digit = digits[-1]
        # 倒数第2-3位
        middle = digits[-3:-1]
        # 前面的位
        prefix = digits[:-3]

        formatted = f"{prefix}-{middle}-{check_digit}"

        # 验证格式
        if cas_pattern.match(formatted):
            return formatted

    return None


def extract_ph_range(condition_str: str) -> Optional[Tuple[float, float]]:
    """
    从条件字符串中提取 pH 范围

    Args:
        condition_str: 条件描述字符串

    Returns:
        (min_ph, max_ph) 或 None

    Examples:
        >>> extract_ph_range("pH 3-9")
        (3.0, 9.0)
        >>> extract_ph_range("pH range: 5.5 to 7.5")
        (5.5, 7.5)
    """
    if not condition_str:
        return None

    # 匹配 pH 范围的各种格式
    patterns = [
        r'pH\s*[:：]?\s*(\d+\.?\d*)\s*[-–~至to]\s*(\d+\.?\d*)',
        r'pH\s*(\d+\.?\d*)\s*[-–~至to]\s*(\d+\.?\d*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, condition_str, re.IGNORECASE)
        if match:
            try:
                min_ph = float(match.group(1))
                max_ph = float(match.group(2))

                # pH 范围应该在 0-14 之间
                if 0 <= min_ph <= 14 and 0 <= max_ph <= 14 and min_ph <= max_ph:
                    return (min_ph, max_ph)
            except ValueError:
                continue

    return None


if __name__ == "__main__":
    # 测试代码
    print("=== 单位转换测试 ===")
    print(f"10 g/100g = {convert_concentration_to_percent(10, 'g/100g')}%")
    print(f"1000 ppm = {convert_concentration_to_percent(1000, 'ppm')}%")
    print(f"5% = {convert_concentration_to_percent('5%')}%")

    print("\n=== 日本浓度解析测试 ===")
    print(f"○ = {parse_japanese_concentration('○')}")
    print(f"0.5 = {parse_japanese_concentration('0.5')}")
    print(f"'' = {parse_japanese_concentration('')}")

    print("\n=== 产品类型标准化测试 ===")
    print(f"hair = {normalize_product_type('hair')}")
    print(f"洗い流す = {normalize_product_type('洗い流す')}")
    print(f"冲洗类 = {normalize_product_type('冲洗类')}")

    print("\n=== CAS 号码解析测试 ===")
    print(f"50-00-0 = {parse_cas_number('50-00-0')}")
    print(f"50000 = {parse_cas_number('50000')}")

    print("\n=== pH 范围提取测试 ===")
    print(f"pH 3-9 = {extract_ph_range('pH 3-9')}")
    print(f"pH range: 5.5 to 7.5 = {extract_ph_range('pH range: 5.5 to 7.5')}")
