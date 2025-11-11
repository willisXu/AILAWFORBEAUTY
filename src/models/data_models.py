"""
Data Models for Global Cosmetic Regulation Compliance System
統一資料模型定義
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class RegionEnum(str, Enum):
    """地區枚舉"""
    EU = "EU"
    ASEAN = "ASEAN"
    JAPAN = "Japan"
    CANADA = "Canada"
    CHINA = "China"


class StatusEnum(str, Enum):
    """成分狀態枚舉"""
    PROHIBITED = "Prohibited"      # 禁止
    RESTRICTED = "Restricted"      # 限用
    ALLOWED = "Allowed"           # 允用
    NOT_LISTED = "Not_Listed"     # 未列入


@dataclass
class IngredientBase:
    """成分基本資訊"""
    inci_name: str
    cas_no: Optional[str] = None
    chinese_name: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)

    def __post_init__(self):
        # 清理 CAS 號碼格式
        if self.cas_no:
            self.cas_no = self.cas_no.strip().upper()


@dataclass
class RegionalStatus:
    """地區法規狀態"""
    region: RegionEnum
    status: StatusEnum
    limit: Optional[str] = None
    product_type: Optional[str] = None
    conditions: Optional[str] = None
    annex_reference: Optional[str] = None
    update_date: Optional[datetime] = None
    source_document: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class EUStatus(RegionalStatus):
    """歐盟法規狀態"""
    annex_type: Optional[str] = None  # II, III, IV, VI
    ec_number: Optional[str] = None

    def __post_init__(self):
        self.region = RegionEnum.EU


@dataclass
class ASEANStatus(RegionalStatus):
    """東協法規狀態"""
    annex_type: Optional[str] = None
    restriction_text: Optional[str] = None

    def __post_init__(self):
        self.region = RegionEnum.ASEAN


@dataclass
class JapanStatus(RegionalStatus):
    """日本法規狀態"""
    appendix_type: Optional[str] = None  # Appendix I, II, etc.
    notification_number: Optional[str] = None

    def __post_init__(self):
        self.region = RegionEnum.JAPAN


@dataclass
class CanadaStatus(RegionalStatus):
    """加拿大法規狀態"""
    category: Optional[str] = None
    hotlist_category: Optional[str] = None

    def __post_init__(self):
        self.region = RegionEnum.CANADA


@dataclass
class ChinaStatus(RegionalStatus):
    """中國法規狀態"""
    stsc_category: Optional[str] = None  # STSC 附錄類別
    iecic_listed: bool = False  # 是否在 IECIC 名錄中
    concentration_limit: Optional[str] = None
    scope_of_application: Optional[str] = None  # 使用範圍
    labeling_requirement: Optional[str] = None  # 標示要求
    ph_requirement: Optional[str] = None
    announcement_number: Optional[str] = None  # 公告號

    def __post_init__(self):
        self.region = RegionEnum.CHINA


@dataclass
class UnifiedIngredient:
    """統一成分資料模型 - 整合所有地區資訊"""
    base_info: IngredientBase
    regional_status: Dict[RegionEnum, RegionalStatus] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    data_quality_score: float = 1.0  # 資料品質評分

    def add_regional_status(self, status: RegionalStatus):
        """添加地區狀態"""
        self.regional_status[status.region] = status

    def get_status(self, region: RegionEnum) -> Optional[RegionalStatus]:
        """取得特定地區狀態"""
        return self.regional_status.get(region)

    def detect_conflicts(self) -> List[str]:
        """檢測跨國衝突"""
        conflicts = []
        statuses = list(self.regional_status.values())

        for i, status1 in enumerate(statuses):
            for status2 in statuses[i+1:]:
                if status1.status == StatusEnum.PROHIBITED and \
                   status2.status == StatusEnum.ALLOWED:
                    conflicts.append(
                        f"Conflict: {status1.region.value} prohibits but "
                        f"{status2.region.value} allows"
                    )
                elif status1.status == StatusEnum.ALLOWED and \
                     status2.status == StatusEnum.PROHIBITED:
                    conflicts.append(
                        f"Conflict: {status1.region.value} allows but "
                        f"{status2.region.value} prohibits"
                    )

        self.conflicts = conflicts
        return conflicts

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'INCI_Name': self.base_info.inci_name,
            'CAS_No': self.base_info.cas_no,
            'Chinese_Name': self.base_info.chinese_name,
            'EU_Status': self.regional_status.get(RegionEnum.EU).status.value
                        if RegionEnum.EU in self.regional_status else 'Not_Listed',
            'EU_Limit': self.regional_status.get(RegionEnum.EU).limit
                       if RegionEnum.EU in self.regional_status else None,
            'ASEAN_Status': self.regional_status.get(RegionEnum.ASEAN).status.value
                           if RegionEnum.ASEAN in self.regional_status else 'Not_Listed',
            'Japan_Status': self.regional_status.get(RegionEnum.JAPAN).status.value
                           if RegionEnum.JAPAN in self.regional_status else 'Not_Listed',
            'Canada_Status': self.regional_status.get(RegionEnum.CANADA).status.value
                            if RegionEnum.CANADA in self.regional_status else 'Not_Listed',
            'China_Status': self.regional_status.get(RegionEnum.CHINA).status.value
                           if RegionEnum.CHINA in self.regional_status else 'Not_Listed',
            'China_IECIC': self.regional_status.get(RegionEnum.CHINA).iecic_listed
                          if RegionEnum.CHINA in self.regional_status else False,
            'Conflicts': '; '.join(self.conflicts),
            'Last_Updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        }


@dataclass
class ComparisonReport:
    """比對報告"""
    total_ingredients: int
    by_region: Dict[RegionEnum, Dict[str, int]]
    conflicts: List[Dict]
    differences: List[Dict]
    generation_time: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
