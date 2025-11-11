"""
Cross-Country Comparison Engine
跨國比對引擎 - 整合多國法規並進行比對分析
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from .models.data_models import (
    UnifiedIngredient, IngredientBase, RegionalStatus,
    EUStatus, ASEANStatus, JapanStatus, CanadaStatus, ChinaStatus,
    StatusEnum, RegionEnum, ComparisonReport
)
from .utils.text_utils import fuzzy_match_names, clean_cas_number


class ComparisonEngine:
    """跨國法規比對引擎"""

    def __init__(self, fuzzy_threshold: int = 85, cas_priority: bool = True):
        """
        初始化比對引擎

        Args:
            fuzzy_threshold: 模糊匹配閾值 (0-100)
            cas_priority: CAS 號碼是否優先匹配
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.cas_priority = cas_priority
        self.unified_ingredients: Dict[str, UnifiedIngredient] = {}
        self.cas_index: Dict[str, str] = {}  # CAS -> ingredient key
        self.name_index: Dict[str, str] = {}  # normalized name -> ingredient key

    def add_regional_data(self, region: RegionEnum, ingredients: List[Dict]):
        """
        添加某地區的法規資料

        Args:
            region: 地區枚舉
            ingredients: 該地區的成分列表
        """
        for ingredient_data in ingredients:
            self._integrate_ingredient(region, ingredient_data)

    def _integrate_ingredient(self, region: RegionEnum, data: Dict):
        """
        整合單一成分到統一資料庫

        Args:
            region: 地區
            data: 成分資料
        """
        # 提取基本資訊
        inci_name = data.get('inci_name') or data.get('ingredient_name') or \
                   data.get('chemical_name') or data.get('substance_name')

        if not inci_name:
            return

        cas_number = data.get('cas_number')

        # 嘗試找到匹配的現有成分
        existing_key = self._find_matching_ingredient(inci_name, cas_number)

        if existing_key:
            # 更新現有成分
            ingredient = self.unified_ingredients[existing_key]
        else:
            # 創建新成分
            ingredient = UnifiedIngredient(
                base_info=IngredientBase(
                    inci_name=inci_name,
                    cas_no=cas_number,
                    chinese_name=data.get('chinese_name')
                )
            )
            # 生成唯一鍵
            key = self._generate_key(inci_name, cas_number)
            self.unified_ingredients[key] = ingredient

            # 更新索引
            if cas_number:
                self.cas_index[cas_number] = key
            self.name_index[inci_name.lower()] = key

        # 添加地區狀態
        regional_status = self._create_regional_status(region, data)
        ingredient.add_regional_status(regional_status)

    def _find_matching_ingredient(self, inci_name: str, cas_number: Optional[str]) -> Optional[str]:
        """
        尋找匹配的現有成分

        Args:
            inci_name: INCI 名稱
            cas_number: CAS 號碼

        Returns:
            匹配成分的鍵,如果沒找到則返回 None
        """
        # 優先使用 CAS 號碼匹配
        if self.cas_priority and cas_number and cas_number in self.cas_index:
            return self.cas_index[cas_number]

        # 使用名稱精確匹配
        name_key = inci_name.lower()
        if name_key in self.name_index:
            return self.name_index[name_key]

        # 模糊匹配
        for existing_name, key in self.name_index.items():
            is_match, score = fuzzy_match_names(inci_name, existing_name, self.fuzzy_threshold)
            if is_match:
                return key

        return None

    def _generate_key(self, inci_name: str, cas_number: Optional[str]) -> str:
        """
        生成成分唯一鍵

        Args:
            inci_name: INCI 名稱
            cas_number: CAS 號碼

        Returns:
            唯一鍵
        """
        if cas_number:
            return f"{cas_number}_{inci_name.lower()}"
        else:
            return f"no_cas_{inci_name.lower()}"

    def _create_regional_status(self, region: RegionEnum, data: Dict) -> RegionalStatus:
        """
        創建地區狀態物件

        Args:
            region: 地區
            data: 原始資料

        Returns:
            RegionalStatus 物件
        """
        # 基本參數
        status = data.get('status', StatusEnum.NOT_LISTED)
        if isinstance(status, str):
            status = StatusEnum(status)

        base_params = {
            'region': region,
            'status': status,
            'limit': data.get('limit'),
            'product_type': data.get('product_type'),
            'conditions': data.get('conditions'),
            'source_document': data.get('source_document')
        }

        # 根據地區創建對應的狀態物件
        if region == RegionEnum.EU:
            return EUStatus(
                **base_params,
                annex_type=data.get('annex_type'),
                ec_number=data.get('ec_number')
            )

        elif region == RegionEnum.ASEAN:
            return ASEANStatus(
                **base_params,
                annex_type=data.get('annex_type'),
                restriction_text=data.get('restriction')
            )

        elif region == RegionEnum.JAPAN:
            return JapanStatus(
                **base_params,
                appendix_type=data.get('appendix_type'),
                notification_number=data.get('notification_number')
            )

        elif region == RegionEnum.CANADA:
            return CanadaStatus(
                **base_params,
                category=data.get('category'),
                hotlist_category=data.get('hotlist_category')
            )

        elif region == RegionEnum.CHINA:
            return ChinaStatus(
                **base_params,
                stsc_category=data.get('stsc_category'),
                iecic_listed=data.get('iecic_listed', False),
                concentration_limit=data.get('limit'),
                scope_of_application=data.get('scope_of_application'),
                labeling_requirement=data.get('labeling_requirement'),
                announcement_number=data.get('announcement_number')
            )

        else:
            return RegionalStatus(**base_params)

    def detect_all_conflicts(self) -> List[UnifiedIngredient]:
        """
        檢測所有成分的跨國衝突

        Returns:
            有衝突的成分列表
        """
        conflicted = []

        for ingredient in self.unified_ingredients.values():
            conflicts = ingredient.detect_conflicts()
            if conflicts:
                conflicted.append(ingredient)

        return conflicted

    def get_status_matrix(self) -> Dict:
        """
        生成狀態矩陣

        Returns:
            包含各地區狀態統計的字典
        """
        matrix = {
            region: {
                'Prohibited': 0,
                'Restricted': 0,
                'Allowed': 0,
                'Not_Listed': 0
            }
            for region in RegionEnum
        }

        for ingredient in self.unified_ingredients.values():
            for region, status_obj in ingredient.regional_status.items():
                status_str = status_obj.status.value
                matrix[region][status_str] += 1

        return matrix

    def get_limit_differences(self) -> List[Dict]:
        """
        分析各地限量差異

        Returns:
            限量差異列表
        """
        differences = []

        for key, ingredient in self.unified_ingredients.items():
            limits = {}

            for region, status_obj in ingredient.regional_status.items():
                if status_obj.limit:
                    limits[region.value] = status_obj.limit

            if len(limits) > 1:
                # 有多個地區設定了不同的限量
                differences.append({
                    'ingredient': ingredient.base_info.inci_name,
                    'cas_number': ingredient.base_info.cas_no,
                    'limits': limits
                })

        return differences

    def generate_report(self) -> ComparisonReport:
        """
        生成比對報告

        Returns:
            ComparisonReport 物件
        """
        total = len(self.unified_ingredients)
        matrix = self.get_status_matrix()
        conflicts = self.detect_all_conflicts()
        differences = self.get_limit_differences()

        # 轉換為簡化格式
        conflict_list = [
            {
                'ingredient': ing.base_info.inci_name,
                'cas_number': ing.base_info.cas_no,
                'conflicts': ing.conflicts
            }
            for ing in conflicts
        ]

        report = ComparisonReport(
            total_ingredients=total,
            by_region=matrix,
            conflicts=conflict_list,
            differences=differences
        )

        return report

    def get_ingredient_by_name(self, name: str) -> Optional[UnifiedIngredient]:
        """
        根據名稱查詢成分

        Args:
            name: 成分名稱

        Returns:
            UnifiedIngredient 或 None
        """
        key = self.name_index.get(name.lower())
        if key:
            return self.unified_ingredients[key]

        # 嘗試模糊匹配
        for existing_name, key in self.name_index.items():
            is_match, _ = fuzzy_match_names(name, existing_name, self.fuzzy_threshold)
            if is_match:
                return self.unified_ingredients[key]

        return None

    def get_ingredient_by_cas(self, cas: str) -> Optional[UnifiedIngredient]:
        """
        根據 CAS 號碼查詢成分

        Args:
            cas: CAS 號碼

        Returns:
            UnifiedIngredient 或 None
        """
        cas_clean = clean_cas_number(cas)
        if not cas_clean:
            return None

        key = self.cas_index.get(cas_clean)
        if key:
            return self.unified_ingredients[key]

        return None

    def to_list(self) -> List[Dict]:
        """
        轉換為字典列表

        Returns:
            成分字典列表
        """
        return [ing.to_dict() for ing in self.unified_ingredients.values()]

    def export_conflicts_only(self) -> List[Dict]:
        """
        僅匯出有衝突的成分

        Returns:
            衝突成分字典列表
        """
        conflicted = self.detect_all_conflicts()
        return [ing.to_dict() for ing in conflicted]

    def get_statistics(self) -> Dict:
        """
        取得統計資訊

        Returns:
            統計資訊字典
        """
        stats = {
            'total_ingredients': len(self.unified_ingredients),
            'with_cas': sum(1 for ing in self.unified_ingredients.values()
                          if ing.base_info.cas_no),
            'conflicts': len(self.detect_all_conflicts()),
            'limit_differences': len(self.get_limit_differences()),
            'by_region': {}
        }

        # 各地區統計
        for region in RegionEnum:
            count = sum(1 for ing in self.unified_ingredients.values()
                       if region in ing.regional_status)
            stats['by_region'][region.value] = count

        return stats
