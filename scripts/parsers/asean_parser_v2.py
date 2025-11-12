"""
ASEAN Parser V2 - 支持多表架构

解析 ASEAN Cosmetic Directive 的各个附录：
- Annex II: 禁用物质（Prohibited）
- Annex III: 限用物质（Restricted）
- Annex IV: 色料（Colorants）
- Annex VI: 防腐剂（Preservatives）
- Annex VII: UV 过滤剂（UV Filters）

ASEAN 与 EU 结构相似，但有细微差异。
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


class ASEANParserV2(BaseParserV2):
    """ASEAN 法规解析器 V2"""

    def __init__(self):
        super().__init__("ASEAN")

        # ASEAN Annex 映射到表类型
        self.annex_to_table = {
            "II": "prohibited",
            "III": "restricted",
            "IV": "colorants",
            "VI": "preservatives",   # 注意：ASEAN 是 Annex VI（不是 V）
            "VII": "uv_filters",     # ASEAN 是 Annex VII（不是 VI）
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
        # 获取对应的 Annex
        annex = None
        for annex_num, ttype in self.annex_to_table.items():
            if ttype == table_type:
                annex = annex_num
                break

        if not annex:
            # ASEAN 没有白名单，返回空列表
            return []

        # 从原始数据中获取对应 Annex 的数据
        annexes = raw_data.get('annexes', {})
        annex_data = annexes.get(annex, [])

        if isinstance(annex_data, dict):
            # 如果是字典，可能有多个子部分
            items = []
            for key, value in annex_data.items():
                if isinstance(value, list):
                    items.extend(value)
                else:
                    items.append(value)
            annex_data = items

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

    def parse_annex_ii_prohibited(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex II（禁用物质）

        Args:
            data: Annex II 原始数据

        Returns:
            禁用物质记录列表
        """
        return self.parse_table("prohibited", {"annexes": {"II": data}})

    def parse_annex_iii_restricted(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex III（限用物质）

        Args:
            data: Annex III 原始数据

        Returns:
            限用物质记录列表
        """
        return self.parse_table("restricted", {"annexes": {"III": data}})

    def parse_annex_iv_colorants(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex IV（色料）

        Args:
            data: Annex IV 原始数据

        Returns:
            色料记录列表
        """
        return self.parse_table("colorants", {"annexes": {"IV": data}})

    def parse_annex_vi_preservatives(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex VI（防腐剂）

        Args:
            data: Annex VI 原始数据

        Returns:
            防腐剂记录列表
        """
        return self.parse_table("preservatives", {"annexes": {"VI": data}})

    def parse_annex_vii_uv_filters(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex VII（UV 过滤剂）

        Args:
            data: Annex VII 原始数据

        Returns:
            UV 过滤剂记录列表
        """
        return self.parse_table("uv_filters", {"annexes": {"VII": data}})


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
            "source": "ASEAN Cosmetic Directive",
        },
        "annexes": {
            "II": [
                {
                    "Ingredient name": "Formaldehyde",
                    "CAS No": "50-00-0",
                    "Scope": "All products"
                }
            ],
            "III": [
                {
                    "Ingredient name": "Triclosan",
                    "CAS No": "3380-34-5",
                    "Maximum concentration": "0.3",
                    "Product type, Body parts": "All products"
                }
            ],
            "VI": [
                {
                    "Ingredient name": "Benzoic acid",
                    "CAS No": "65-85-0",
                    "Maximum concentration": "0.5"
                }
            ],
            "VII": [
                {
                    "Ingredient name": "Benzophenone-3",
                    "CAS No": "131-57-7",
                    "Maximum concentration": "6.0"
                }
            ]
        }
    }

    # 保存测试数据
    test_file = Path("/tmp/asean_test_data.json")
    save_json(test_data, test_file)

    # 解析测试数据
    parser = ASEANParserV2()
    result = parser.run(test_file)

    print("\n=== Test Parsing Results ===")
    print(f"Statistics: {result['statistics']}")
    print(f"\nDetailed table statistics:")
    for table_type, stats in result['statistics']['tables'].items():
        print(f"  {table_type}: {stats['actual']} actual records")
