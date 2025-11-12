"""
China Parser V2 - 支持多表架构

解析 NMPA（国家药品监督管理局）法规：
- STSC Annex 2: 禁用物质（Prohibited）
- STSC Annex 3: 限用物质（Restricted）
- STSC Annex 4: 防腐剂（Preservatives）
- STSC Annex 5: UV 过滤剂（UV Filters）
- STSC Annex 6: 色料（Colorants）
- IECIC 2021: 已使用化妆品原料目录（Whitelist）

特点：
- 支持中文字段名
- IECIC 白名单特殊处理（未列入标记为 Not_Listed）
"""

from pathlib import Path
from typing import Dict, Any, List
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.base_parser_v2 import BaseParserV2
from schema.database_schema import (
    BaseRegulationRecord,
    Status,
    GeneralWhitelistRecord,
)
from utils import setup_logger

logger = setup_logger(__name__)


class CNParserV2(BaseParserV2):
    """中国法规解析器 V2"""

    def __init__(self):
        super().__init__("CN")

        # STSC Annex 映射到表类型
        self.annex_to_table = {
            "2": "prohibited",      # STSC 附录 2
            "3": "restricted",      # STSC 附录 3
            "4": "preservatives",   # STSC 附录 4
            "5": "uv_filters",      # STSC 附录 5
            "6": "colorants",       # STSC 附录 6
        }

    def parse_table(
        self,
        table_type: str,
        raw_data: Dict[str, Any]
    ) -> List[BaseRegulationRecord]:
        """
        解析特定表的数据

        Args:
            table_type: 表类型
            raw_data: 原始数据

        Returns:
            解析后的记录列表
        """
        # 白名单特殊处理
        if table_type == "whitelist":
            return self._parse_iecic_whitelist(raw_data)

        # 获取对应的 STSC Annex
        annex = None
        for annex_num, ttype in self.annex_to_table.items():
            if ttype == table_type:
                annex = annex_num
                break

        if not annex:
            return []

        # 从原始数据中获取对应 Annex 的数据
        # 假设数据结构为：
        # {
        #   "metadata": {...},
        #   "stsc": {
        #     "annex_2": [...],
        #     "annex_3": [...],
        #     ...
        #   }
        # }
        stsc_data = raw_data.get('stsc', {})
        annex_key = f"annex_{annex}"
        annex_data = stsc_data.get(annex_key, [])

        # 解析每个条目
        records = []
        for item in annex_data:
            if not isinstance(item, dict):
                continue

            record = self.create_record(
                table_type=table_type,
                source_data=item,
                update_date=None
            )

            if record:
                records.append(record)

        return records

    def _parse_iecic_whitelist(self, raw_data: Dict[str, Any]) -> List[BaseRegulationRecord]:
        """
        解析 IECIC 白名单（已使用化妆品原料目录）

        IECIC（Inventory of Existing Cosmetic Ingredients in China）

        Args:
            raw_data: 原始数据

        Returns:
            白名单记录列表
        """
        records = []

        # 获取 IECIC 数据
        iecic_data = raw_data.get('iecic', [])

        for item in iecic_data:
            if not isinstance(item, dict):
                continue

            # 获取基本信息
            inci_name = self.map_field_value('whitelist', 'INCI_Name', item)
            cas_no = self.map_field_value('whitelist', 'CAS_No', item)

            if not inci_name:
                continue

            # 创建白名单记录
            record_data = {
                'INCI_Name': inci_name,
                'CAS_No': cas_no,
                'List_Name': 'IECIC 2021',
                'IECIC_Status': item.get('使用状态') or item.get('备注'),
                'Conditions': self.map_field_value('whitelist', 'Conditions', item),
                'Notes': self.map_field_value('whitelist', 'Notes', item),
            }

            # 设置状态为 Listed
            # 注意：在 create_record 中会自动设置
            record = self.create_record(
                table_type='whitelist',
                source_data=record_data,
                update_date=None
            )

            if record:
                # 确保状态是 Listed
                record.Status = Status.LISTED
                records.append(record)

        return records

    def parse_stsc_annex_2_prohibited(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 STSC 附录 2（禁用物质）

        Args:
            data: STSC Annex 2 原始数据

        Returns:
            禁用物质记录列表
        """
        return self.parse_table("prohibited", {"stsc": {"annex_2": data}})

    def parse_stsc_annex_3_restricted(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 STSC 附录 3（限用物质）

        Args:
            data: STSC Annex 3 原始数据

        Returns:
            限用物质记录列表
        """
        return self.parse_table("restricted", {"stsc": {"annex_3": data}})

    def parse_stsc_annex_4_preservatives(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 STSC 附录 4（防腐剂）

        Args:
            data: STSC Annex 4 原始数据

        Returns:
            防腐剂记录列表
        """
        return self.parse_table("preservatives", {"stsc": {"annex_4": data}})

    def parse_stsc_annex_5_uv_filters(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 STSC 附录 5（UV 过滤剂）

        Args:
            data: STSC Annex 5 原始数据

        Returns:
            UV 过滤剂记录列表
        """
        return self.parse_table("uv_filters", {"stsc": {"annex_5": data}})

    def parse_stsc_annex_6_colorants(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 STSC 附录 6（色料）

        Args:
            data: STSC Annex 6 原始数据

        Returns:
            色料记录列表
        """
        return self.parse_table("colorants", {"stsc": {"annex_6": data}})

    def parse_iecic_whitelist(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 IECIC 白名单

        Args:
            data: IECIC 原始数据

        Returns:
            白名单记录列表
        """
        return self.parse_table("whitelist", {"iecic": data})


if __name__ == "__main__":
    """测试代码"""
    import logging
    from utils import save_json

    logging.basicConfig(level=logging.INFO)

    # 创建测试数据
    test_data = {
        "metadata": {
            "version": "20240101",
            "published_at": "2024-01-01",
            "source": "NMPA STSC + IECIC 2021",
        },
        "stsc": {
            "annex_2": [
                {
                    "化妆品原料名称": "甲醛",
                    "中文名称": "甲醛",
                    "CAS号": "50-00-0",
                    "使用范围": "禁止"
                }
            ],
            "annex_3": [
                {
                    "化妆品原料名称": "三氯生",
                    "中文名称": "三氯生",
                    "CAS号": "3380-34-5",
                    "最大允许使用浓度": "0.3",
                    "使用范围": "全部产品"
                }
            ],
            "annex_4": [
                {
                    "化妆品原料名称": "苯甲酸",
                    "中文名称": "苯甲酸",
                    "CAS号": "65-85-0",
                    "最大允许使用浓度": "0.5"
                }
            ],
            "annex_5": [
                {
                    "化妆品原料名称": "二苯酮-3",
                    "中文名称": "二苯酮-3",
                    "CAS号": "131-57-7",
                    "最大允许使用浓度": "6.0"
                }
            ],
            "annex_6": [
                {
                    "化妆品原料名称": "CI 77891",
                    "中文名称": "钛白粉",
                    "CAS号": "13463-67-7",
                    "色素索引号": "CI 77891",
                    "使用范围": "全部产品"
                }
            ]
        },
        "iecic": [
            {
                "INCI名称": "Water",
                "化妆品原料名称": "水",
                "中文名称": "水",
                "CAS号": "7732-18-5",
                "使用状态": "已使用",
                "目录名称": "IECIC 2021"
            },
            {
                "INCI名称": "Glycerin",
                "化妆品原料名称": "甘油",
                "中文名称": "甘油",
                "CAS号": "56-81-5",
                "使用状态": "已使用",
                "目录名称": "IECIC 2021"
            }
        ]
    }

    # 保存测试数据
    test_file = Path("/tmp/cn_test_data.json")
    save_json(test_data, test_file)

    # 解析测试数据
    parser = CNParserV2()
    result = parser.run(test_file)

    print("\n=== Test Parsing Results ===")
    print(f"Statistics: {result['statistics']}")
    print(f"\nDetailed table statistics:")
    for table_type, stats in result['statistics']['tables'].items():
        if stats['actual'] > 0:
            print(f"  {table_type}: {stats['actual']} actual records")

    # 显示白名单示例
    if parser.tables['whitelist']:
        print(f"\nWhitelist sample (first 2):")
        for record in parser.tables['whitelist'][:2]:
            print(f"  - {record.INCI_Name} ({record.CAS_No}): {record.Status.value}")
