"""
EU COSING Annex Parser
歐盟法規解析器 - 解析 COSING Annex II, III, IV, VI
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..models.data_models import (
    IngredientBase, EUStatus, StatusEnum, RegionEnum
)
from ..utils.text_utils import clean_cas_number, normalize_ingredient_name


class EUAnnexParser:
    """EU COSING Annex 解析器"""

    def __init__(self, base_path: Path):
        """
        初始化解析器

        Args:
            base_path: 法規文件所在目錄
        """
        self.base_path = Path(base_path)
        self.annexes = {
            'II': None,   # Prohibited
            'III': None,  # Restricted
            'IV': None,   # Colorants
            'VI': None    # UV filters
        }

    def parse_annex_ii(self, file_path: Path) -> List[Dict]:
        """
        解析 Annex II - 禁用物質清單

        Args:
            file_path: Annex II 文件路徑

        Returns:
            解析後的成分列表
        """
        ingredients = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取更新日期
        update_date_match = re.search(r'Last update:\s*(\d{2}/\d{2}/\d{4})', content)
        update_date = None
        if update_date_match:
            update_date = datetime.strptime(update_date_match.group(1), '%d/%m/%Y')

        # 分行處理
        lines = content.split('\n')

        # 找到標題行
        header_index = -1
        for i, line in enumerate(lines):
            if 'Reference Number' in line and 'Chemical name' in line:
                header_index = i
                break

        if header_index == -1:
            raise ValueError("Cannot find header in Annex II file")

        # 從標題行後開始解析
        for line in lines[header_index + 1:]:
            if not line.strip():
                continue

            # 使用逗號分隔,但要處理引號內的逗號
            parts = self._split_csv_line(line)

            if len(parts) < 4:
                continue

            try:
                ref_number = parts[0].strip()
                chemical_name = parts[1].strip().strip('"')
                cas_number = parts[2].strip().strip('"')
                ec_number = parts[3].strip().strip('"')

                # 提取 CMR 資訊
                cmr_info = None
                if len(parts) > 9:
                    cmr_info = parts[9].strip().strip('"')

                # 提取更新日期
                item_update_date = None
                if len(parts) > 10:
                    date_str = parts[10].strip().strip('"')
                    if date_str:
                        try:
                            item_update_date = datetime.strptime(date_str, '%d/%m/%Y')
                        except:
                            pass

                # 清理 CAS 號碼
                cas_clean = clean_cas_number(cas_number)

                if chemical_name:
                    ingredient = {
                        'reference_number': ref_number,
                        'chemical_name': normalize_ingredient_name(chemical_name),
                        'cas_number': cas_clean,
                        'ec_number': ec_number if ec_number != '-' else None,
                        'annex_type': 'II',
                        'status': StatusEnum.PROHIBITED,
                        'cmr_category': cmr_info,
                        'update_date': item_update_date or update_date,
                        'source_document': file_path.name
                    }
                    ingredients.append(ingredient)

            except Exception as e:
                # 記錄錯誤但繼續處理
                print(f"Error parsing line in Annex II: {e}")
                continue

        return ingredients

    def parse_annex_iii(self, file_path: Path) -> List[Dict]:
        """
        解析 Annex III - 限用物質清單

        Args:
            file_path: Annex III 文件路徑

        Returns:
            解析後的成分列表
        """
        ingredients = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取更新日期
        update_date_match = re.search(r'Last update:\s*(\d{2}/\d{2}/\d{4})', content)
        update_date = None
        if update_date_match:
            update_date = datetime.strptime(update_date_match.group(1), '%d/%m/%Y')

        lines = content.split('\n')

        # 找到標題行
        header_index = -1
        for i, line in enumerate(lines):
            if 'Reference Number' in line and 'Chemical name' in line:
                header_index = i
                break

        if header_index == -1:
            raise ValueError("Cannot find header in Annex III file")

        # 解析數據行
        for line in lines[header_index + 1:]:
            if not line.strip():
                continue

            parts = self._split_csv_line(line)

            if len(parts) < 4:
                continue

            try:
                ref_number = parts[0].strip()
                chemical_name = parts[1].strip().strip('"')
                cas_number = parts[2].strip().strip('"')
                ec_number = parts[3].strip().strip('"')

                # Annex III 特有欄位
                restriction = None
                conditions = None
                max_concentration = None
                product_type = None

                if len(parts) > 5:
                    restriction = parts[5].strip().strip('"')

                if len(parts) > 6:
                    conditions = parts[6].strip().strip('"')

                # 提取最大濃度
                if restriction:
                    conc_match = re.search(r'(\d+(?:\.\d+)?)\s*%', restriction)
                    if conc_match:
                        max_concentration = conc_match.group(0)

                # 提取產品類型
                if conditions:
                    if 'rinse-off' in conditions.lower():
                        product_type = 'rinse-off'
                    elif 'leave-on' in conditions.lower():
                        product_type = 'leave-on'

                cas_clean = clean_cas_number(cas_number)

                if chemical_name:
                    ingredient = {
                        'reference_number': ref_number,
                        'chemical_name': normalize_ingredient_name(chemical_name),
                        'cas_number': cas_clean,
                        'ec_number': ec_number if ec_number != '-' else None,
                        'annex_type': 'III',
                        'status': StatusEnum.RESTRICTED,
                        'limit': max_concentration,
                        'conditions': conditions,
                        'product_type': product_type,
                        'update_date': update_date,
                        'source_document': file_path.name
                    }
                    ingredients.append(ingredient)

            except Exception as e:
                print(f"Error parsing line in Annex III: {e}")
                continue

        return ingredients

    def parse_annex_iv(self, file_path: Path) -> List[Dict]:
        """
        解析 Annex IV - 著色劑清單

        Args:
            file_path: Annex IV 文件路徑

        Returns:
            解析後的成分列表
        """
        ingredients = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        update_date_match = re.search(r'Last update:\s*(\d{2}/\d{2}/\d{4})', content)
        update_date = None
        if update_date_match:
            update_date = datetime.strptime(update_date_match.group(1), '%d/%m/%Y')

        lines = content.split('\n')

        header_index = -1
        for i, line in enumerate(lines):
            if 'Colour Index' in line or 'Chemical name' in line:
                header_index = i
                break

        if header_index == -1:
            raise ValueError("Cannot find header in Annex IV file")

        for line in lines[header_index + 1:]:
            if not line.strip():
                continue

            parts = self._split_csv_line(line)

            if len(parts) < 3:
                continue

            try:
                colour_index = parts[0].strip().strip('"')
                chemical_name = parts[1].strip().strip('"')
                cas_number = parts[2].strip().strip('"')

                # 提取使用範圍
                conditions = None
                if len(parts) > 3:
                    conditions = parts[3].strip().strip('"')

                cas_clean = clean_cas_number(cas_number)

                if chemical_name:
                    ingredient = {
                        'colour_index': colour_index,
                        'chemical_name': normalize_ingredient_name(chemical_name),
                        'cas_number': cas_clean,
                        'annex_type': 'IV',
                        'status': StatusEnum.ALLOWED,
                        'product_type': 'colorant',
                        'conditions': conditions,
                        'update_date': update_date,
                        'source_document': file_path.name
                    }
                    ingredients.append(ingredient)

            except Exception as e:
                print(f"Error parsing line in Annex IV: {e}")
                continue

        return ingredients

    def parse_annex_vi(self, file_path: Path) -> List[Dict]:
        """
        解析 Annex VI - UV 濾劑清單

        Args:
            file_path: Annex VI 文件路徑

        Returns:
            解析後的成分列表
        """
        ingredients = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        update_date_match = re.search(r'Last update:\s*(\d{2}/\d{2}/\d{4})', content)
        update_date = None
        if update_date_match:
            update_date = datetime.strptime(update_date_match.group(1), '%d/%m/%Y')

        lines = content.split('\n')

        header_index = -1
        for i, line in enumerate(lines):
            if 'Chemical name' in line or 'Reference' in line:
                header_index = i
                break

        if header_index == -1:
            raise ValueError("Cannot find header in Annex VI file")

        for line in lines[header_index + 1:]:
            if not line.strip():
                continue

            parts = self._split_csv_line(line)

            if len(parts) < 3:
                continue

            try:
                ref_number = parts[0].strip()
                chemical_name = parts[1].strip().strip('"')
                cas_number = parts[2].strip().strip('"')

                # UV 濾劑的最大濃度
                max_concentration = None
                conditions = None

                if len(parts) > 4:
                    max_concentration = parts[4].strip().strip('"')

                if len(parts) > 5:
                    conditions = parts[5].strip().strip('"')

                cas_clean = clean_cas_number(cas_number)

                if chemical_name:
                    ingredient = {
                        'reference_number': ref_number,
                        'chemical_name': normalize_ingredient_name(chemical_name),
                        'cas_number': cas_clean,
                        'annex_type': 'VI',
                        'status': StatusEnum.ALLOWED,
                        'product_type': 'uv_filter',
                        'limit': max_concentration,
                        'conditions': conditions,
                        'update_date': update_date,
                        'source_document': file_path.name
                    }
                    ingredients.append(ingredient)

            except Exception as e:
                print(f"Error parsing line in Annex VI: {e}")
                continue

        return ingredients

    def parse_all(self) -> Dict[str, List[Dict]]:
        """
        解析所有 Annex 文件

        Returns:
            按 Annex 類型分組的成分字典
        """
        results = {}

        # Annex II
        annex_ii_path = self.base_path / "COSING_Annex_II_v2.txt"
        if annex_ii_path.exists():
            results['II'] = self.parse_annex_ii(annex_ii_path)
            print(f"Parsed {len(results['II'])} ingredients from Annex II")

        # Annex III
        annex_iii_path = self.base_path / "COSING_Annex_III_v2.txt"
        if annex_iii_path.exists():
            results['III'] = self.parse_annex_iii(annex_iii_path)
            print(f"Parsed {len(results['III'])} ingredients from Annex III")

        # Annex IV
        annex_iv_path = self.base_path / "COSING_Annex_IV_v2.txt"
        if annex_iv_path.exists():
            results['IV'] = self.parse_annex_iv(annex_iv_path)
            print(f"Parsed {len(results['IV'])} ingredients from Annex IV")

        # Annex VI
        annex_vi_path = self.base_path / "COSING_Annex_VI_v2.txt"
        if annex_vi_path.exists():
            results['VI'] = self.parse_annex_vi(annex_vi_path)
            print(f"Parsed {len(results['VI'])} ingredients from Annex VI")

        return results

    def _split_csv_line(self, line: str) -> List[str]:
        """
        分割 CSV 行,處理引號內的逗號

        Args:
            line: CSV 行

        Returns:
            分割後的欄位列表
        """
        parts = []
        current = []
        in_quotes = False

        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def to_dataframe(self, annex_data: List[Dict]) -> pd.DataFrame:
        """
        轉換為 DataFrame

        Args:
            annex_data: 解析後的成分列表

        Returns:
            DataFrame
        """
        return pd.DataFrame(annex_data)
