"""
ASEAN Cosmetic Directive Parser
東協法規解析器 - 解析 ASEAN Cosmetic Directive PDF
"""

import re
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..models.data_models import StatusEnum
from ..utils.text_utils import clean_cas_number, normalize_ingredient_name, extract_concentration


class ASEANParser:
    """ASEAN 法規解析器"""

    def __init__(self, pdf_path: Path):
        """
        初始化解析器

        Args:
            pdf_path: ASEAN PDF 文件路徑
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")

    def extract_version_info(self) -> Dict:
        """
        提取版本資訊

        Returns:
            版本資訊字典
        """
        version_info = {
            'version': None,
            'update_date': None
        }

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # 通常版本資訊在第一頁
                first_page_text = pdf.pages[0].extract_text()

                # 提取版本號 (如 2024-2)
                version_match = re.search(r'(?:Version|Ver\.?)\s*:?\s*(\d{4}-\d+)',
                                         first_page_text, re.IGNORECASE)
                if version_match:
                    version_info['version'] = version_match.group(1)

                # 提取更新日期
                date_patterns = [
                    r'(?:Updated?|Revision)\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})',
                    r'(?:Updated?|Revision)\s*:?\s*(\d{4}-\d{2}-\d{2})',
                    r'(?:December|Dec)\s+(\d{4})'
                ]

                for pattern in date_patterns:
                    date_match = re.search(pattern, first_page_text, re.IGNORECASE)
                    if date_match:
                        version_info['update_date'] = date_match.group(1)
                        break

        except Exception as e:
            print(f"Error extracting version info: {e}")

        return version_info

    def parse_annex(self, annex_name: str, start_page: int = None, end_page: int = None) -> List[Dict]:
        """
        解析特定 Annex

        Args:
            annex_name: Annex 名稱 (如 "Annex II", "Annex III")
            start_page: 起始頁碼
            end_page: 結束頁碼

        Returns:
            解析後的成分列表
        """
        ingredients = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # 如果沒有指定頁碼,嘗試自動找到
                if start_page is None:
                    start_page, end_page = self._find_annex_pages(pdf, annex_name)

                if start_page is None:
                    print(f"Cannot find {annex_name} in the PDF")
                    return ingredients

                # 遍歷相關頁面
                for page_num in range(start_page - 1, end_page if end_page else len(pdf.pages)):
                    page = pdf.pages[page_num]

                    # 提取表格
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        # 找到標題行
                        header_row = None
                        for i, row in enumerate(table):
                            if any('Substance' in str(cell) or 'CAS' in str(cell)
                                  for cell in row if cell):
                                header_row = i
                                break

                        if header_row is None:
                            continue

                        # 解析數據行
                        headers = table[header_row]
                        for row in table[header_row + 1:]:
                            if not row or len(row) < 2:
                                continue

                            ingredient = self._parse_asean_row(row, headers, annex_name)
                            if ingredient:
                                ingredients.append(ingredient)

        except Exception as e:
            print(f"Error parsing ASEAN {annex_name}: {e}")

        return ingredients

    def _parse_asean_row(self, row: List, headers: List, annex_name: str) -> Optional[Dict]:
        """
        解析單一表格行

        Args:
            row: 表格行數據
            headers: 標題行
            annex_name: Annex 名稱

        Returns:
            成分字典或 None
        """
        try:
            # 找到關鍵欄位的索引
            substance_idx = None
            cas_idx = None
            restriction_idx = None

            for i, header in enumerate(headers):
                if header:
                    header_lower = str(header).lower()
                    if 'substance' in header_lower or 'name' in header_lower:
                        substance_idx = i
                    elif 'cas' in header_lower:
                        cas_idx = i
                    elif 'restriction' in header_lower or 'condition' in header_lower:
                        restriction_idx = i

            if substance_idx is None:
                return None

            substance_name = str(row[substance_idx]).strip() if substance_idx < len(row) else None
            cas_number = str(row[cas_idx]).strip() if cas_idx is not None and cas_idx < len(row) else None
            restriction = str(row[restriction_idx]).strip() if restriction_idx is not None and restriction_idx < len(row) else None

            if not substance_name or substance_name in ['None', '', 'nan']:
                return None

            # 清理 CAS 號碼
            cas_clean = clean_cas_number(cas_number) if cas_number else None

            # 判斷狀態
            status = self._determine_asean_status(annex_name)

            # 提取限量
            limit = extract_concentration(restriction) if restriction else None

            ingredient = {
                'substance_name': normalize_ingredient_name(substance_name),
                'cas_number': cas_clean,
                'annex_type': annex_name,
                'status': status,
                'restriction': restriction,
                'limit': limit,
                'source_document': self.pdf_path.name
            }

            return ingredient

        except Exception as e:
            print(f"Error parsing ASEAN row: {e}")
            return None

    def _determine_asean_status(self, annex_name: str) -> StatusEnum:
        """
        根據 Annex 類型判斷狀態

        Args:
            annex_name: Annex 名稱

        Returns:
            狀態枚舉
        """
        annex_lower = annex_name.lower()

        if 'ii' in annex_lower or 'prohibited' in annex_lower:
            return StatusEnum.PROHIBITED
        elif 'iii' in annex_lower or 'restricted' in annex_lower:
            return StatusEnum.RESTRICTED
        elif 'iv' in annex_lower or 'colorant' in annex_lower:
            return StatusEnum.ALLOWED
        else:
            return StatusEnum.NOT_LISTED

    def _find_annex_pages(self, pdf, annex_name: str) -> tuple:
        """
        自動找到 Annex 的頁碼範圍

        Args:
            pdf: PDF 物件
            annex_name: Annex 名稱

        Returns:
            (起始頁, 結束頁)
        """
        start_page = None
        end_page = None

        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            if annex_name.lower() in text.lower():
                if start_page is None:
                    start_page = i + 1

            # 如果找到下一個 Annex,結束當前範圍
            if start_page is not None:
                next_annex_pattern = r'Annex\s+[IVX]+'
                matches = re.finditer(next_annex_pattern, text, re.IGNORECASE)
                for match in matches:
                    match_text = match.group(0)
                    if match_text.lower() != annex_name.lower():
                        end_page = i
                        break

            if end_page:
                break

        return start_page, end_page

    def parse_all_annexes(self) -> Dict[str, List[Dict]]:
        """
        解析所有 Annex

        Returns:
            按 Annex 分組的成分字典
        """
        results = {}

        # 常見的 Annex 清單
        annexes = [
            'Annex II',   # Prohibited
            'Annex III',  # Restricted
            'Annex IV',   # Colorants
            'Annex V',    # Preservatives
            'Annex VI'    # UV filters
        ]

        for annex in annexes:
            ingredients = self.parse_annex(annex)
            if ingredients:
                results[annex] = ingredients
                print(f"Parsed {len(ingredients)} ingredients from {annex}")

        return results

    def to_dataframe(self, annex_data: List[Dict]) -> pd.DataFrame:
        """
        轉換為 DataFrame

        Args:
            annex_data: 解析後的成分列表

        Returns:
            DataFrame
        """
        return pd.DataFrame(annex_data)
