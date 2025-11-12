"""
Canada Parser V2 - 支持多表架构

解析 Health Canada Cosmetic Ingredient Hotlist：
- Prohibited: 禁用物质
- Restricted: 限用物质

注意：
- 加拿大只有禁用和限用两类，没有防腐剂、UV、色料的专门清单
- 其他表格（preservatives, uv_filters, colorants, whitelist）标记为"未规定"
"""

from pathlib import Path
from typing import Dict, Any, List
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.base_parser_v2 import BaseParserV2
from schema.database_schema import BaseRegulationRecord
from utils import setup_logger

logger = setup_logger(__name__)


class CAParserV2(BaseParserV2):
    """加拿大法规解析器 V2"""

    def __init__(self):
        super().__init__("CA")

        # Hotlist 分类映射到表类型
        self.category_to_table = {
            "prohibited": "prohibited",
            "restricted": "restricted",
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
        # 加拿大只有禁用和限用
        if table_type not in ["prohibited", "restricted"]:
            return []

        # 从原始数据中获取对应的 Hotlist 数据
        # 假设数据结构为：
        # {
        #   "metadata": {...},
        #   "hotlist": {
        #     "prohibited": [...],
        #     "restricted": [...]
        #   }
        # }
        hotlist_data = raw_data.get('hotlist', {})
        category_data = hotlist_data.get(table_type, [])

        # 解析每个条目
        records = []
        for item in category_data:
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

    def parse_hotlist_prohibited(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Hotlist 禁用物质

        Args:
            data: Hotlist Prohibited 原始数据

        Returns:
            禁用物质记录列表
        """
        return self.parse_table("prohibited", {"hotlist": {"prohibited": data}})

    def parse_hotlist_restricted(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Hotlist 限用物质

        Args:
            data: Hotlist Restricted 原始数据

        Returns:
            限用物质记录列表
        """
        return self.parse_table("restricted", {"hotlist": {"restricted": data}})


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
            "source": "Health Canada Cosmetic Ingredient Hotlist",
        },
        "hotlist": {
            "prohibited": [
                {
                    "Ingredient Name": "Formaldehyde",
                    "Chemical Name": "Formaldehyde",
                    "CAS Registry Number": "50-00-0",
                    "Restrictions": "Prohibited in all cosmetics",
                    "Comments": "Strong allergen and carcinogen"
                },
                {
                    "Ingredient Name": "Lead and its compounds",
                    "Chemical Name": "Lead",
                    "CAS Registry Number": "7439-92-1",
                    "Restrictions": "Prohibited",
                    "Comments": "Heavy metal toxicity"
                }
            ],
            "restricted": [
                {
                    "Ingredient Name": "Triclosan",
                    "Chemical Name": "Triclosan",
                    "CAS Registry Number": "3380-34-5",
                    "Maximum Concentration": "0.3",
                    "Restrictions": "Must not be used in products for children under 3",
                    "Conditions": "pH 3-9",
                    "Comments": "Antimicrobial agent"
                },
                {
                    "Ingredient Name": "Benzoic acid",
                    "Chemical Name": "Benzoic acid",
                    "CAS Registry Number": "65-85-0",
                    "Maximum Concentration": "0.5",
                    "Restrictions": "Not for use in products applied to mucous membranes",
                    "Comments": "Preservative"
                }
            ]
        }
    }

    # 保存测试数据
    test_file = Path("/tmp/ca_test_data.json")
    save_json(test_data, test_file)

    # 解析测试数据
    parser = CAParserV2()
    result = parser.run(test_file)

    print("\n=== Test Parsing Results ===")
    print(f"Statistics: {result['statistics']}")
    print(f"\nDetailed table statistics:")
    for table_type, stats in result['statistics']['tables'].items():
        if stats['actual'] > 0:
            print(f"  {table_type}: {stats['actual']} actual records")
        elif stats['total'] == 0:
            print(f"  {table_type}: 0 records (not covered by CA regulations)")
