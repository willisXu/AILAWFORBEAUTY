"""
China NMPA Parser
中國法規解析器 - 解析 NMPA STSC 和 IECIC
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

from ..models.data_models import StatusEnum
from ..utils.text_utils import (
    clean_cas_number, normalize_ingredient_name,
    extract_concentration, is_chinese, split_multilingual_text
)


class ChinaParser:
    """中國 NMPA 法規解析器"""

    def __init__(self, stsc_path: Path, iecic_path: Optional[Path] = None):
        """
        初始化解析器

        Args:
            stsc_path: STSC (已使用化妝品原料目錄) Excel 路徑
            iecic_path: IECIC (國際化妝品原料名稱目錄) 路徑 (可選)
        """
        self.stsc_path = Path(stsc_path)
        if not self.stsc_path.exists():
            raise FileNotFoundError(f"STSC file not found: {stsc_path}")

        self.iecic_path = Path(iecic_path) if iecic_path else None
        self.iecic_ingredients: Set[str] = set()

        # 如果提供了 IECIC,載入它
        if self.iecic_path and self.iecic_path.exists():
            self._load_iecic()

    def _load_iecic(self):
        """載入 IECIC 名錄"""
        try:
            df = pd.read_excel(self.iecic_path)

            # 找到 INCI 名稱欄位
            inci_col = None
            for col in df.columns:
                if 'INCI' in str(col).upper() or '名称' in str(col):
                    inci_col = col
                    break

            if inci_col:
                self.iecic_ingredients = set(
                    df[inci_col].dropna().astype(str).apply(normalize_ingredient_name)
                )
                print(f"Loaded {len(self.iecic_ingredients)} ingredients from IECIC")

        except Exception as e:
            print(f"Error loading IECIC: {e}")

    def parse_stsc(self) -> List[Dict]:
        """
        解析 STSC (已使用化妝品原料目錄)

        Returns:
            解析後的成分列表
        """
        ingredients = []

        try:
            # 嘗試讀取所有工作表
            excel_file = pd.ExcelFile(self.stsc_path)
            print(f"Found sheets: {excel_file.sheet_names}")

            # 遍歷所有工作表
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.stsc_path, sheet_name=sheet_name)

                # 識別欄位
                column_mapping = self._identify_stsc_columns(df)

                if not column_mapping:
                    print(f"Cannot identify columns in sheet: {sheet_name}")
                    continue

                print(f"Processing sheet: {sheet_name}")

                # 判斷附錄類型 (根據工作表名稱或內容)
                appendix_type = self._determine_appendix_type(sheet_name)

                # 遍歷每一行
                for idx, row in df.iterrows():
                    ingredient = self._parse_stsc_row(row, column_mapping, appendix_type, sheet_name)
                    if ingredient:
                        ingredients.append(ingredient)

            print(f"Parsed {len(ingredients)} ingredients from China STSC")

        except Exception as e:
            print(f"Error parsing China STSC: {e}")
            raise

        return ingredients

    def _identify_stsc_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        識別 STSC 欄位名稱

        Args:
            df: DataFrame

        Returns:
            欄位映射字典
        """
        column_mapping = {}

        for col in df.columns:
            col_str = str(col).strip()

            # INCI 名稱
            if 'INCI' in col_str.upper():
                column_mapping['inci'] = col_str

            # 中文名稱
            elif '中文名' in col_str or '名称' in col_str:
                if 'INCI' not in col_str:
                    column_mapping['chinese_name'] = col_str

            # CAS 號
            elif 'CAS' in col_str.upper() or 'CAS号' in col_str:
                column_mapping['cas'] = col_str

            # 限量條件
            elif '限量' in col_str or '最大' in col_str:
                column_mapping['limit'] = col_str

            # 使用範圍
            elif '使用範圍' in col_str or '適用' in col_str or '用途' in col_str:
                column_mapping['scope'] = col_str

            # 其他限制條件
            elif '限制' in col_str or '條件' in col_str or '要求' in col_str:
                column_mapping['conditions'] = col_str

            # 標示要求
            elif '標示' in col_str or '標簽' in col_str or '標籤' in col_str:
                column_mapping['labeling'] = col_str

        return column_mapping

    def _parse_stsc_row(self, row: pd.Series, column_mapping: Dict,
                       appendix_type: str, sheet_name: str) -> Optional[Dict]:
        """
        解析 STSC 單一行

        Args:
            row: DataFrame 行
            column_mapping: 欄位映射
            appendix_type: 附錄類型
            sheet_name: 工作表名稱

        Returns:
            成分字典或 None
        """
        try:
            # 提取 INCI 名稱
            inci_name = None
            inci_col = column_mapping.get('inci')
            if inci_col and not pd.isna(row.get(inci_col)):
                inci_name = str(row[inci_col]).strip()

            # 提取中文名稱
            chinese_name = None
            chinese_col = column_mapping.get('chinese_name')
            if chinese_col and not pd.isna(row.get(chinese_col)):
                chinese_name = str(row[chinese_col]).strip()

            # 至少需要一個名稱
            if not inci_name and not chinese_name:
                return None

            # 如果只有中文名,嘗試分離
            if not inci_name and chinese_name:
                multilingual = split_multilingual_text(chinese_name)
                if multilingual['english']:
                    inci_name = multilingual['english']
                    chinese_name = multilingual['chinese']

            # 提取 CAS 號碼
            cas_number = None
            cas_col = column_mapping.get('cas')
            if cas_col and not pd.isna(row.get(cas_col)):
                cas_number = clean_cas_number(str(row[cas_col]))

            # 提取限量
            limit = None
            limit_col = column_mapping.get('limit')
            if limit_col and not pd.isna(row.get(limit_col)):
                limit = str(row[limit_col]).strip()

            # 提取使用範圍
            scope = None
            scope_col = column_mapping.get('scope')
            if scope_col and not pd.isna(row.get(scope_col)):
                scope = str(row[scope_col]).strip()

            # 提取其他條件
            conditions = None
            conditions_col = column_mapping.get('conditions')
            if conditions_col and not pd.isna(row.get(conditions_col)):
                conditions = str(row[conditions_col]).strip()

            # 提取標示要求
            labeling = None
            labeling_col = column_mapping.get('labeling')
            if labeling_col and not pd.isna(row.get(labeling_col)):
                labeling = str(row[labeling_col]).strip()

            # 判斷狀態
            status = self._determine_china_status(appendix_type, limit, conditions)

            # 檢查是否在 IECIC 中
            iecic_listed = False
            if inci_name:
                iecic_listed = normalize_ingredient_name(inci_name) in self.iecic_ingredients

            ingredient = {
                'inci_name': normalize_ingredient_name(inci_name) if inci_name else None,
                'chinese_name': chinese_name,
                'cas_number': cas_number,
                'stsc_category': appendix_type,
                'status': status,
                'limit': limit,
                'scope_of_application': scope,
                'conditions': conditions,
                'labeling_requirement': labeling,
                'iecic_listed': iecic_listed,
                'source_document': f"{self.stsc_path.name} - {sheet_name}"
            }

            return ingredient

        except Exception as e:
            print(f"Error parsing China STSC row: {e}")
            return None

    def _determine_appendix_type(self, sheet_name: str) -> str:
        """
        根據工作表名稱判斷附錄類型

        Args:
            sheet_name: 工作表名稱

        Returns:
            附錄類型
        """
        sheet_lower = sheet_name.lower()

        # 常見的工作表名稱模式
        if '禁用' in sheet_name or 'prohibit' in sheet_lower:
            return '禁用組分'
        elif '限用' in sheet_name or 'restrict' in sheet_lower:
            return '限用組分'
        elif '准用' in sheet_name or '允許' in sheet_name or 'allow' in sheet_lower:
            return '准用組分'
        elif '防腐' in sheet_name or 'preserv' in sheet_lower:
            return '准用防腐劑'
        elif '防曬' in sheet_name or '紫外' in sheet_name or 'uv' in sheet_lower:
            return '准用防曬劑'
        elif '著色' in sheet_name or '染料' in sheet_name or 'color' in sheet_lower:
            return '准用著色劑'
        else:
            return sheet_name

    def _determine_china_status(self, appendix_type: str,
                               limit: Optional[str], conditions: Optional[str]) -> StatusEnum:
        """
        根據附錄類型和條件判斷狀態

        Args:
            appendix_type: 附錄類型
            limit: 限量
            conditions: 條件

        Returns:
            狀態枚舉
        """
        appendix_lower = appendix_type.lower()

        if '禁用' in appendix_type or 'prohibit' in appendix_lower:
            return StatusEnum.PROHIBITED
        elif '限用' in appendix_type or 'restrict' in appendix_lower:
            return StatusEnum.RESTRICTED
        elif '准用' in appendix_type or '允許' in appendix_type or 'allow' in appendix_lower:
            # 准用但有限制條件也算限用
            if limit or conditions:
                return StatusEnum.RESTRICTED
            return StatusEnum.ALLOWED
        else:
            return StatusEnum.NOT_LISTED

    def to_dataframe(self, ingredients: List[Dict]) -> pd.DataFrame:
        """
        轉換為 DataFrame

        Args:
            ingredients: 解析後的成分列表

        Returns:
            DataFrame
        """
        return pd.DataFrame(ingredients)

    def check_iecic_status(self, inci_name: str) -> bool:
        """
        檢查成分是否在 IECIC 中

        Args:
            inci_name: INCI 名稱

        Returns:
            是否在 IECIC 中
        """
        if not self.iecic_ingredients:
            return False

        normalized = normalize_ingredient_name(inci_name)
        return normalized in self.iecic_ingredients
