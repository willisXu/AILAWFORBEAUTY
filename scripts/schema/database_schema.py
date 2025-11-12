"""
数据库 Schema 定义
根据多表架构（Multi-Table Model）管理法规资料

六张主表：
1. Prohibited_Table - 禁用物质清单
2. Restricted_Table - 限用物质清单
3. Allowed_Preservatives - 防腐剂允用表
4. Allowed_UV_Filters - 紫外线吸收剂允用表
5. Allowed_Colorants - 色料允用表
6. General_Whitelist - 一般白名单（原料名录）
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import date


class Jurisdiction(str, Enum):
    """法规属地"""
    EU = "EU"
    ASEAN = "ASEAN"
    JP = "JP"
    CA = "CA"
    CN = "CN"


class Status(str, Enum):
    """状态分类"""
    PROHIBITED = "Prohibited"           # 禁用
    RESTRICTED = "Restricted"           # 限用
    ALLOWED = "Allowed"                 # 允用
    LISTED = "Listed"                   # 已列入（白名单）
    NOT_LISTED = "Not_Listed"           # 未列入（白名单）
    NOT_SPECIFIED = "未规定"             # 未规定


class ProductType(str, Enum):
    """适用产品类别"""
    HAIR = "Hair"
    SKIN = "Skin"
    EYE = "Eye"
    LIP = "Lip"
    NAIL = "Nail"
    ORAL = "Oral"
    MUCOSA = "Mucosa"                   # 粘膜
    NON_MUCOSA = "Non_Mucosa"           # 非粘膜
    RINSE_OFF = "Rinse_Off"             # 冲洗类
    LEAVE_ON = "Leave_On"               # 驻留类
    OTHER = "Other"
    NOT_SPECIFIED = "未规定"


@dataclass
class BaseRegulationRecord:
    """所有表的基础字段（通用字段）"""

    # 必填字段
    INCI_Name: str                      # 成分国际命名（含同义名对照）
    Jurisdiction: Jurisdiction          # 法规属地
    Status: Status                      # 状态分类

    # 可选字段
    CAS_No: Optional[str] = None        # 化学登录号（可为 NULL）
    Product_Type: Optional[ProductType] = ProductType.NOT_SPECIFIED  # 适用产品类别
    Max_Conc_Percent: Optional[float] = None  # 最大允用浓度（%）
    Conditions: Optional[str] = None    # 使用条件（pH、部位、标示语等）
    Legal_Basis: Optional[str] = None   # 法规依据（附录/附件）
    Update_Date: Optional[date] = None  # 官方版本日期
    Notes: Optional[str] = None         # 备注或例外条件

    # 内部字段
    Synonyms: List[str] = field(default_factory=list)  # 同义名列表

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 转换枚举为字符串
        if isinstance(result['Jurisdiction'], Enum):
            result['Jurisdiction'] = result['Jurisdiction'].value
        if isinstance(result['Status'], Enum):
            result['Status'] = result['Status'].value
        if result['Product_Type'] and isinstance(result['Product_Type'], Enum):
            result['Product_Type'] = result['Product_Type'].value
        # 转换日期为字符串
        if result['Update_Date']:
            result['Update_Date'] = result['Update_Date'].isoformat()
        return result


@dataclass
class ProhibitedRecord(BaseRegulationRecord):
    """禁用物质记录

    对应法规来源：
    - EU Annex II
    - ASEAN Annex II
    - Japan Appendix 1
    - China STSC Annex 2
    - Canada Hotlist (Prohibited)
    """

    def __post_init__(self):
        # 禁用物质的状态必须是 Prohibited
        self.Status = Status.PROHIBITED


@dataclass
class RestrictedRecord(BaseRegulationRecord):
    """限用物质记录

    对应法规来源：
    - EU Annex III
    - ASEAN Annex III
    - Japan Appendix 2
    - China STSC Annex 3
    - Canada Hotlist (Restricted)
    """

    def __post_init__(self):
        # 限用物质的状态必须是 Restricted
        self.Status = Status.RESTRICTED


@dataclass
class AllowedPreservativeRecord(BaseRegulationRecord):
    """防腐剂允用记录

    对应法规来源：
    - EU Annex V
    - ASEAN Annex VI
    - Japan Appendix 3
    - China STSC Annex 4
    """

    Label_Warnings: Optional[str] = None  # 特殊标示语要求

    def __post_init__(self):
        # 防腐剂的状态必须是 Allowed
        self.Status = Status.ALLOWED


@dataclass
class AllowedUVFilterRecord(BaseRegulationRecord):
    """紫外线吸收剂允用记录

    对应法规来源：
    - EU Annex VI
    - ASEAN Annex VII
    - Japan Appendix 4
    - China STSC Annex 5
    """

    Label_Warnings: Optional[str] = None  # 特殊标示语要求

    def __post_init__(self):
        # UV过滤剂的状态必须是 Allowed
        self.Status = Status.ALLOWED


@dataclass
class AllowedColorantRecord(BaseRegulationRecord):
    """色料允用记录

    对应法规来源：
    - EU Annex IV
    - ASEAN Annex IV
    - China STSC Annex 6
    """

    Colour_Index: Optional[str] = None  # CI 编号
    Body_Area: Optional[str] = None     # 可用部位（如：face, eye, lip, hair等）

    def __post_init__(self):
        # 色料的状态必须是 Allowed
        self.Status = Status.ALLOWED


@dataclass
class GeneralWhitelistRecord(BaseRegulationRecord):
    """一般白名单（原料名录）记录

    对应法规来源：
    - China IECIC（已使用化妆品原料目录）
    - ASEAN 通用名录（如有）
    """

    List_Name: Optional[str] = None     # 白名单来源名称（如：IECIC 2021）
    IECIC_Status: Optional[str] = None  # IECIC 特定状态（如：已使用、新原料等）

    def __post_init__(self):
        # 白名单的状态可以是 Listed 或 Not_Listed
        if self.Status not in [Status.LISTED, Status.NOT_LISTED, Status.NOT_SPECIFIED]:
            self.Status = Status.LISTED


# 表类型映射
TABLE_TYPES = {
    "prohibited": ProhibitedRecord,
    "restricted": RestrictedRecord,
    "preservatives": AllowedPreservativeRecord,
    "uv_filters": AllowedUVFilterRecord,
    "colorants": AllowedColorantRecord,
    "whitelist": GeneralWhitelistRecord,
}


# 法规来源映射
REGULATION_SOURCE_MAPPING = {
    Jurisdiction.EU: {
        "prohibited": "Annex II",
        "restricted": "Annex III",
        "colorants": "Annex IV",
        "preservatives": "Annex V",
        "uv_filters": "Annex VI",
        "whitelist": None,  # EU 未提供白名单
    },
    Jurisdiction.ASEAN: {
        "prohibited": "Annex II",
        "restricted": "Annex III",
        "colorants": "Annex IV",
        "preservatives": "Annex VI",
        "uv_filters": "Annex VII",
        "whitelist": None,  # ASEAN 无官方白名单
    },
    Jurisdiction.JP: {
        "prohibited": "Appendix 1",
        "restricted": "Appendix 2",
        "preservatives": "Appendix 3",
        "uv_filters": "Appendix 4",
        "colorants": None,  # Japan 未列色料清单
        "whitelist": None,  # Japan 未列白名单
    },
    Jurisdiction.CA: {
        "prohibited": "Hotlist - Prohibited",
        "restricted": "Hotlist - Restricted",
        "preservatives": None,
        "uv_filters": None,
        "colorants": None,
        "whitelist": None,
    },
    Jurisdiction.CN: {
        "prohibited": "STSC Annex 2",
        "restricted": "STSC Annex 3",
        "preservatives": "STSC Annex 4",
        "uv_filters": "STSC Annex 5",
        "colorants": "STSC Annex 6",
        "whitelist": "IECIC 2021",
    },
}


def get_legal_basis(jurisdiction: Jurisdiction, table_type: str) -> Optional[str]:
    """获取法规依据"""
    return REGULATION_SOURCE_MAPPING.get(jurisdiction, {}).get(table_type)


def create_not_specified_record(
    inci_name: str,
    cas_no: Optional[str],
    jurisdiction: Jurisdiction,
    table_type: str
) -> BaseRegulationRecord:
    """创建"未规定"状态的记录

    当某个地区/表格未含对应项目时，系统自动创建此记录
    """
    RecordClass = TABLE_TYPES.get(table_type, BaseRegulationRecord)

    return RecordClass(
        INCI_Name=inci_name,
        CAS_No=cas_no,
        Jurisdiction=jurisdiction,
        Status=Status.NOT_SPECIFIED,
        Product_Type=ProductType.NOT_SPECIFIED,
        Max_Conc_Percent=None,
        Conditions=None,
        Legal_Basis=None,
        Update_Date=None,
        Notes="该地区未规定此成分",
    )
