"""
Japan MHLW Standards Parser
日本法規解析器 - 解析日本厚生勞動省化妝品標準
"""

import re
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..models.data_models import StatusEnum
from ..utils.text_utils import clean_cas_number, normalize_ingredient_name, extract_concentration


class JapanParser:
    """日本 MHLW 法規解析器"""

    def __init__(self, pdf_path: Path):
        """
        初始化解析器

        Args:
            pdf_path: 日本法規 PDF 文件路徑
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")

    def extract_metadata(self) -> Dict:
        """
        提取文件元數據

        Returns:
            元數據字典
        """
        metadata = {
            'notification_number': None,
            'issue_date': None,
            'title': None
        }

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # 提取前幾頁的文字
                first_page_text = pdf.pages[0].extract_text()

                # 提取通知號碼
                # 日本厚生勞動省通知格式: 薬生発0000第0号
                notification_pattern = r'[薬藥]生発?\d{4}第\d+号'
                notification_match = re.search(notification_pattern, first_page_text)
                if notification_match:
                    metadata['notification_number'] = notification_match.group(0)

                # 提取日期 (日文格式)
                date_patterns = [
                    r'令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日',  # 令和年
                    r'平成\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日',  # 平成年
                ]

                for pattern in date_patterns:
                    date_match = re.search(pattern, first_page_text)
                    if date_match:
                        metadata['issue_date'] = date_match.group(0)
                        break

        except Exception as e:
            print(f"Error extracting Japan metadata: {e}")

        return metadata

    def parse_appendix(self, appendix_name: str) -> List[Dict]:
        """
        解析特定附錄 (Appendix)

        Args:
            appendix_name: 附錄名稱 (如 "Appendix I")

        Returns:
            解析後的成分列表
        """
        ingredients = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # 找到附錄所在頁碼
                start_page = None
                end_page = None

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue

                    # 尋找附錄標題
                    if re.search(f'{appendix_name}', text, re.IGNORECASE):
                        if start_page is None:
                            start_page = i

                    # 如果找到下一個附錄,結束當前範圍
                    if start_page is not None and i > start_page:
                        if re.search(r'Appendix\s+[IVX]+', text, re.IGNORECASE):
                            end_page = i
                            break

                if start_page is None:
                    print(f"Cannot find {appendix_name} in the PDF")
                    return ingredients

                if end_page is None:
                    end_page = len(pdf.pages)

                # 提取相關頁面的表格
                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]

                    # 提取表格
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        # 解析表格
                        ingredients.extend(self._parse_japan_table(table, appendix_name))

        except Exception as e:
            print(f"Error parsing Japan {appendix_name}: {e}")

        return ingredients

    def _parse_japan_table(self, table: List[List], appendix_name: str) -> List[Dict]:
        """
        解析日本法規表格

        Args:
            table: 表格數據
            appendix_name: 附錄名稱

        Returns:
            成分列表
        """
        ingredients = []

        if not table or len(table) < 2:
            return ingredients

        # 找到標題行
        header_row = 0
        headers = table[header_row]

        # 識別欄位
        name_idx = None
        cas_idx = None
        limit_idx = None

        for i, header in enumerate(headers):
            if not header:
                continue

            header_str = str(header).lower()

            if any(keyword in header_str for keyword in ['ingredient', 'name', '成分', '名称']):
                name_idx = i
            elif 'cas' in header_str:
                cas_idx = i
            elif any(keyword in header_str for keyword in ['limit', 'amount', '量', '濃度']):
                limit_idx = i

        # 解析數據行
        for row in table[header_row + 1:]:
            if not row or len(row) < 2:
                continue

            try:
                ingredient_name = None
                cas_number = None
                limit = None

                if name_idx is not None and name_idx < len(row):
                    ingredient_name = str(row[name_idx]).strip()

                if cas_idx is not None and cas_idx < len(row):
                    cas_number = str(row[cas_idx]).strip()

                if limit_idx is not None and limit_idx < len(row):
                    limit = str(row[limit_idx]).strip()

                if not ingredient_name or ingredient_name in ['None', '', 'nan']:
                    continue

                # 清理 CAS 號碼
                cas_clean = clean_cas_number(cas_number) if cas_number else None

                # 判斷狀態
                status = self._determine_japan_status(appendix_name)

                # 提取限量
                concentration = extract_concentration(limit) if limit else None

                ingredient = {
                    'ingredient_name': normalize_ingredient_name(ingredient_name),
                    'cas_number': cas_clean,
                    'appendix_type': appendix_name,
                    'status': status,
                    'limit': concentration,
                    'conditions': limit,
                    'source_document': self.pdf_path.name
                }

                ingredients.append(ingredient)

            except Exception as e:
                print(f"Error parsing Japan table row: {e}")
                continue

        return ingredients

    def _determine_japan_status(self, appendix_name: str) -> StatusEnum:
        """
        根據附錄類型判斷狀態

        Args:
            appendix_name: 附錄名稱

        Returns:
            狀態枚舉
        """
        appendix_lower = appendix_name.lower()

        # Appendix I: 禁用成分
        if 'i' in appendix_lower and 'ii' not in appendix_lower:
            return StatusEnum.PROHIBITED
        # Appendix II, III: 限用成分
        elif any(x in appendix_lower for x in ['ii', 'iii']):
            return StatusEnum.RESTRICTED
        else:
            return StatusEnum.NOT_LISTED

    def parse_all_appendices(self) -> Dict[str, List[Dict]]:
        """
        解析所有附錄

        Returns:
            按附錄分組的成分字典
        """
        results = {}

        # 日本法規常見的附錄
        appendices = [
            'Appendix I',    # 禁用成分
            'Appendix II',   # 限用成分
            'Appendix III',  # 限用成分
        ]

        for appendix in appendices:
            ingredients = self.parse_appendix(appendix)
            if ingredients:
                results[appendix] = ingredients
                print(f"Parsed {len(ingredients)} ingredients from Japan {appendix}")

        return results

    def to_dataframe(self, ingredients: List[Dict]) -> pd.DataFrame:
        """
        轉換為 DataFrame

        Args:
            ingredients: 解析後的成分列表

        Returns:
            DataFrame
        """
        return pd.DataFrame(ingredients)
