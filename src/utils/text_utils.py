"""
Text Processing Utilities
文字處理工具函數
"""

import re
import chardet
from typing import Optional, List, Tuple
from fuzzywuzzy import fuzz


def detect_encoding(file_path: str) -> str:
    """
    自動檢測文件編碼

    Args:
        file_path: 文件路徑

    Returns:
        編碼名稱
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def clean_cas_number(cas: str) -> Optional[str]:
    """
    清理並標準化 CAS 號碼

    Args:
        cas: 原始 CAS 號碼

    Returns:
        標準化的 CAS 號碼 或 None
    """
    if not cas or cas.strip() == '':
        return None

    # 移除空格和特殊字符
    cas = str(cas).strip().upper()

    # CAS 號碼格式: XXXXX-XX-X
    pattern = r'^\d{2,7}-\d{2}-\d$'

    # 提取數字和連字符
    cas_clean = re.sub(r'[^\d-]', '', cas)

    if re.match(pattern, cas_clean):
        return cas_clean

    # 嘗試修復格式
    digits = re.findall(r'\d+', cas)
    if len(digits) >= 3:
        return f"{digits[0]}-{digits[1]}-{digits[2]}"

    return None


def normalize_ingredient_name(name: str) -> str:
    """
    標準化成分名稱

    Args:
        name: 原始成分名稱

    Returns:
        標準化名稱
    """
    if not name:
        return ""

    # 轉換為小寫並移除多餘空格
    name = ' '.join(name.strip().split())

    # 移除特殊符號但保留連字符和括號
    name = re.sub(r'[^\w\s\-(),/]', '', name)

    return name


def fuzzy_match_names(name1: str, name2: str, threshold: int = 85) -> Tuple[bool, int]:
    """
    模糊匹配兩個成分名稱

    Args:
        name1: 第一個名稱
        name2: 第二個名稱
        threshold: 相似度閾值 (0-100)

    Returns:
        (是否匹配, 相似度分數)
    """
    if not name1 or not name2:
        return False, 0

    # 標準化名稱
    name1_norm = normalize_ingredient_name(name1).lower()
    name2_norm = normalize_ingredient_name(name2).lower()

    # 完全匹配
    if name1_norm == name2_norm:
        return True, 100

    # 使用 token_sort_ratio 進行模糊匹配
    score = fuzz.token_sort_ratio(name1_norm, name2_norm)

    return score >= threshold, score


def extract_concentration(text: str) -> Optional[str]:
    """
    從文字中提取濃度資訊

    Args:
        text: 包含濃度的文字

    Returns:
        提取的濃度字串
    """
    if not text:
        return None

    # 匹配各種濃度格式
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%',  # 10%, 0.5%
        r'(\d+(?:\.\d+)?)\s*ppm',  # 10ppm
        r'max\.?\s*(\d+(?:\.\d+)?)\s*%',  # max 10%
        r'≤\s*(\d+(?:\.\d+)?)\s*%',  # ≤10%
        r'<=\s*(\d+(?:\.\d+)?)\s*%',  # <=10%
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def extract_cas_from_text(text: str) -> List[str]:
    """
    從文字中提取所有 CAS 號碼

    Args:
        text: 輸入文字

    Returns:
        CAS 號碼列表
    """
    pattern = r'\b\d{2,7}-\d{2}-\d\b'
    matches = re.findall(pattern, text)
    return [clean_cas_number(cas) for cas in matches if clean_cas_number(cas)]


def is_chinese(text: str) -> bool:
    """
    判斷文字是否包含中文

    Args:
        text: 輸入文字

    Returns:
        是否包含中文
    """
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def split_multilingual_text(text: str) -> dict:
    """
    分離多語言文字

    Args:
        text: 包含多語言的文字

    Returns:
        {'chinese': str, 'english': str}
    """
    if not text:
        return {'chinese': '', 'english': ''}

    chinese_pattern = r'[\u4e00-\u9fff]+'
    chinese_parts = re.findall(chinese_pattern, text)

    english_text = re.sub(chinese_pattern, '', text).strip()
    chinese_text = ''.join(chinese_parts).strip()

    return {
        'chinese': chinese_text,
        'english': english_text
    }


def parse_ph_range(text: str) -> Optional[Tuple[float, float]]:
    """
    解析 pH 值範圍

    Args:
        text: 包含 pH 資訊的文字

    Returns:
        (最小值, 最大值) 或 None
    """
    if not text:
        return None

    # 匹配 pH 範圍格式: pH 3-10, pH 3.0-10.0
    pattern = r'pH\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return (float(match.group(1)), float(match.group(2)))

    # 匹配單一 pH 值: pH > 3, pH < 10
    pattern_single = r'pH\s*([><]=?)\s*(\d+(?:\.\d+)?)'
    match = re.search(pattern_single, text, re.IGNORECASE)

    if match:
        operator = match.group(1)
        value = float(match.group(2))

        if '>' in operator:
            return (value, 14.0)
        else:
            return (0.0, value)

    return None


def clean_whitespace(text: str) -> str:
    """
    清理多餘空白字符

    Args:
        text: 輸入文字

    Returns:
        清理後的文字
    """
    if not text:
        return ""

    # 替換多個空格為單一空格
    text = re.sub(r'\s+', ' ', text)

    # 移除行首行尾空格
    text = text.strip()

    return text


def extract_product_types(text: str) -> List[str]:
    """
    提取產品類型

    Args:
        text: 包含產品類型的文字

    Returns:
        產品類型列表
    """
    if not text:
        return []

    # 常見產品類型關鍵字
    product_keywords = [
        'rinse-off', 'leave-on', 'shampoo', 'conditioner',
        'soap', 'cream', 'lotion', 'gel', 'serum',
        'lipstick', 'nail', 'hair dye', 'colorant',
        'oxidative', 'non-oxidative', 'oral', 'eye area'
    ]

    text_lower = text.lower()
    found_types = []

    for keyword in product_keywords:
        if keyword in text_lower:
            found_types.append(keyword)

    return found_types
