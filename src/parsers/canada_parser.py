"""
Health Canada Cosmetics Parser
加拿大法規解析器 - 解析 Health Canada 化妝品資料表
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..models.data_models import StatusEnum
from ..utils.text_utils import clean_cas_number, normalize_ingredient_name


class CanadaParser:
    """加拿大 Health Canada 法規解析器"""

    def __init__(self, xlsx_path: Path):
        """
        初始化解析器

        Args:
            xlsx_path: Excel 文件路徑
        """
        self.xlsx_path = Path(xlsx_path)
        if not self.xlsx_path.exists():
            raise FileNotFoundError(f"File not found: {xlsx_path}")

    def parse(self) -> List[Dict]:
        """
        解析加拿大法規文件

        Returns:
            解析後的成分列表
        """
        ingredients = []

        try:
            # 載入 Excel 文件
            df = pd.read_excel(self.xlsx_path)

            # 提取更新日期 (通常在文件名或第一行)
            update_date = self._extract_update_date(df)

            # 識別欄位名稱 (可能是英文或法文)
            column_mapping = self._identify_columns(df)

            if not column_mapping:
                raise ValueError("Cannot identify required columns in the Excel file")

            # 遍歷每一行
            for idx, row in df.iterrows():
                ingredient = self._parse_row(row, column_mapping, update_date)
                if ingredient:
                    ingredients.append(ingredient)

            print(f"Parsed {len(ingredients)} ingredients from Canada regulations")

        except Exception as e:
            print(f"Error parsing Canada regulations: {e}")
            raise

        return ingredients

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        識別欄位名稱

        Args:
            df: DataFrame

        Returns:
            欄位映射字典
        """
        column_mapping = {}

        # 可能的欄位名稱
        name_columns = ['INCI', 'Ingredient Name', 'Chemical Name', 'Substance']
        cas_columns = ['CAS Number', 'CAS No', 'CAS', 'CAS Registry Number']
        category_columns = ['Category', 'Status', 'Classification']
        restriction_columns = ['Restriction', 'Limit', 'Conditions']

        for col in df.columns:
            col_str = str(col).strip()

            # 匹配成分名稱
            if any(name in col_str for name in name_columns):
                column_mapping['name'] = col_str

            # 匹配 CAS 號碼
            elif any(cas in col_str for cas in cas_columns):
                column_mapping['cas'] = col_str

            # 匹配分類
            elif any(cat in col_str for cat in category_columns):
                column_mapping['category'] = col_str

            # 匹配限制條件
            elif any(rest in col_str for rest in restriction_columns):
                column_mapping['restriction'] = col_str

        return column_mapping

    def _parse_row(self, row: pd.Series, column_mapping: Dict, update_date: Optional[datetime]) -> Optional[Dict]:
        """
        解析單一行

        Args:
            row: DataFrame 行
            column_mapping: 欄位映射
            update_date: 更新日期

        Returns:
            成分字典或 None
        """
        try:
            # 提取成分名稱
            name_col = column_mapping.get('name')
            if not name_col or pd.isna(row.get(name_col)):
                return None

            ingredient_name = str(row[name_col]).strip()

            if not ingredient_name or ingredient_name.lower() in ['nan', 'none', '']:
                return None

            # 提取 CAS 號碼
            cas_number = None
            cas_col = column_mapping.get('cas')
            if cas_col and not pd.isna(row.get(cas_col)):
                cas_number = clean_cas_number(str(row[cas_col]))

            # 提取分類
            category = None
            category_col = column_mapping.get('category')
            if category_col and not pd.isna(row.get(category_col)):
                category = str(row[category_col]).strip()

            # 判斷狀態
            status = self._determine_status(category)

            # 提取限制條件
            restriction = None
            restriction_col = column_mapping.get('restriction')
            if restriction_col and not pd.isna(row.get(restriction_col)):
                restriction = str(row[restriction_col]).strip()

            ingredient = {
                'ingredient_name': normalize_ingredient_name(ingredient_name),
                'cas_number': cas_number,
                'category': category,
                'status': status,
                'restriction': restriction,
                'update_date': update_date,
                'source_document': self.xlsx_path.name
            }

            return ingredient

        except Exception as e:
            print(f"Error parsing Canada row: {e}")
            return None

    def _determine_status(self, category: Optional[str]) -> StatusEnum:
        """
        根據分類判斷狀態

        Args:
            category: 分類字串

        Returns:
            狀態枚舉
        """
        if not category:
            return StatusEnum.NOT_LISTED

        category_lower = category.lower()

        if any(keyword in category_lower for keyword in ['prohibit', 'banned', 'forbidden']):
            return StatusEnum.PROHIBITED
        elif any(keyword in category_lower for keyword in ['restrict', 'limit', 'condition']):
            return StatusEnum.RESTRICTED
        elif any(keyword in category_lower for keyword in ['allow', 'permit']):
            return StatusEnum.ALLOWED
        else:
            return StatusEnum.NOT_LISTED

    def _extract_update_date(self, df: pd.DataFrame) -> Optional[datetime]:
        """
        提取更新日期

        Args:
            df: DataFrame

        Returns:
            更新日期或 None
        """
        # 嘗試從文件名提取
        import re
        filename = self.xlsx_path.stem

        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})(\d{2})(\d{2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    year, month, day = match.groups()
                    return datetime(int(year), int(month), int(day))
                except:
                    pass

        # 嘗試從第一行提取
        if len(df) > 0:
            first_row_str = ' '.join([str(val) for val in df.iloc[0].values])

            for pattern in date_patterns:
                match = re.search(pattern, first_row_str)
                if match:
                    try:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    except:
                        pass

        return None

    def to_dataframe(self, ingredients: List[Dict]) -> pd.DataFrame:
        """
        轉換為 DataFrame

        Args:
            ingredients: 解析後的成分列表

        Returns:
            DataFrame
        """
        return pd.DataFrame(ingredients)
