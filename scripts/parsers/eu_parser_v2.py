"""
EU Parser V2 - 支持多表架构

解析 EU Regulation (EC) No 1223/2009 的各个附录：
- Annex II: 禁用物质（Prohibited）
- Annex III: 限用物质（Restricted）
- Annex IV: 色料（Colorants）
- Annex V: 防腐剂（Preservatives）
- Annex VI: UV 过滤剂（UV Filters）
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.base_parser_v2 import BaseParserV2
from schema.database_schema import BaseRegulationRecord
from utils import setup_logger

logger = setup_logger(__name__)


class EUParserV2(BaseParserV2):
    """EU 法规解析器 V2"""

    def __init__(self):
        super().__init__("EU")

        # EU Annex 映射到表类型
        self.annex_to_table = {
            "II": "prohibited",
            "III": "restricted",
            "IV": "colorants",
            "V": "preservatives",
            "VI": "uv_filters",
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
            # EU 没有白名单，返回空列表
            return []

        # 从原始数据中获取对应 Annex 的数据
        # 实际数据结构：
        # {
        #   "raw_data": {
        #     "annexes": {
        #       "annex_ii": { "ingredients": [...] },
        #       ...
        #     }
        #   }
        # }
        # 支持两种结构：新的（raw_data包装）和旧的（直接annexes）
        if 'raw_data' in raw_data:
            annexes = raw_data.get('raw_data', {}).get('annexes', {})
        else:
            annexes = raw_data.get('annexes', {})

        # 转换Annex编号为键名：II -> annex_ii
        annex_key_map = {
            "II": "annex_ii",
            "III": "annex_iii",
            "IV": "annex_iv",
            "V": "annex_v",
            "VI": "annex_vi"
        }
        annex_key = annex_key_map.get(annex, annex)

        # 获取annex数据，可能是对象或数组
        annex_data = annexes.get(annex_key, annexes.get(annex, []))

        # 如果是对象且包含ingredients字段，提取ingredients数组
        if isinstance(annex_data, dict) and 'ingredients' in annex_data:
            annex_data = annex_data['ingredients']

        if isinstance(annex_data, dict):
            # 如果是字典，可能有多个子部分
            # 例如 Annex IV 可能分为不同的部分
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
                update_date=None  # 将从 metadata 中获取
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

    def parse_annex_v_preservatives(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex V（防腐剂）

        Args:
            data: Annex V 原始数据

        Returns:
            防腐剂记录列表
        """
        return self.parse_table("preservatives", {"annexes": {"V": data}})

    def parse_annex_vi_uv_filters(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Annex VI（UV 过滤剂）

        Args:
            data: Annex VI 原始数据

        Returns:
            UV 过滤剂记录列表
        """
        return self.parse_table("uv_filters", {"annexes": {"VI": data}})


if __name__ == "__main__":
    """测试代码"""
    import logging
    from utils import load_json

    logging.basicConfig(level=logging.INFO)

    # 测试解析
    parser = EUParserV2()

    # 假设原始数据文件存在
    raw_data_file = Path(__file__).parent.parent.parent / "data" / "raw" / "EU" / "latest.json"

    if raw_data_file.exists():
        result = parser.run(raw_data_file)
        print("\n=== Parsing Results ===")
        print(f"Statistics: {result['statistics']}")
        print(f"Output files: {result['output_paths']}")
    else:
        print(f"Raw data file not found: {raw_data_file}")

        # 创建测试数据
        test_data = {
            "metadata": {
                "version": "20240424",
                "published_at": "2024-04-04",
                "source": "European Commission - CosIng Database",
            },
            "annexes": {
                "II": [
                    {
                        "Reference number": "1",
                        "Chemical name": "Formaldehyde",
                        "CAS No": "50-00-0",
                        "Scope": "All cosmetic products"
                    }
                ],
                "III": [
                    {
                        "Ingredient Name": "Triclosan",
                        "CAS No": "3380-34-5",
                        "Maximum concentration in ready for use preparation": "0.3",
                        "Product type, Body parts": "All products",
                        "Other limitations and requirements": "pH 3-9"
                    }
                ],
                "V": [
                    {
                        "Ingredient Name": "Benzoic acid",
                        "CAS No": "65-85-0",
                        "Maximum concentration in ready for use preparation": "0.5",
                        "Wording of conditions of use and warnings": "Not for use in products for children under 3 years"
                    }
                ]
            }
        }

        # 保存测试数据
        test_file = Path("/tmp/eu_test_data.json")
        from utils import save_json
        save_json(test_data, test_file)

        # 解析测试数据
        result = parser.run(test_file)
        print("\n=== Test Parsing Results ===")
        print(f"Statistics: {result['statistics']}")
