"""
Japan Parser V2 - 支持多表架构

解析 MHLW Notification No.331 的各个附录：
- Appendix 1: 禁用物质（Prohibited）
- Appendix 2: 限用物质（Restricted）- 三层限用结构
- Appendix 3: 防腐剂（Preservatives）- 三栏矩阵式
- Appendix 4: UV 过滤剂（UV Filters）- 三栏矩阵式

特殊处理：
- 浓度单位：g/100g → %（数值相同）
- 特殊符号：○ = 无上限，空白 = 禁止，- = 不适用
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.base_parser_v2 import BaseParserV2
from schema.database_schema import (
    BaseRegulationRecord,
    ProductType,
    Status,
)
from utils import setup_logger
from utils.unit_converter import parse_japanese_concentration

logger = setup_logger(__name__)


class JPParserV2(BaseParserV2):
    """日本法规解析器 V2"""

    def __init__(self):
        super().__init__("JP")

        # Appendix 映射到表类型
        self.appendix_to_table = {
            "1": "prohibited",
            "2": "restricted",
            "3": "preservatives",
            "4": "uv_filters",
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
        # 获取对应的 Appendix
        appendix = None
        for app_num, ttype in self.appendix_to_table.items():
            if ttype == table_type:
                appendix = app_num
                break

        if not appendix:
            # 日本没有色料和白名单，返回空列表
            return []

        # 从原始数据中获取对应 Appendix 的数据
        # 实际数据结构：
        # {
        #   "raw_data": {
        #     "categories": {
        #       "prohibited": [...],
        #       "preservative": [...],
        #       ...
        #     }
        #   }
        # }
        # 支持两种结构
        if 'raw_data' in raw_data:
            categories = raw_data.get('raw_data', {}).get('categories', {})
            # 直接使用table_type从categories获取数据
            appendix_data = categories.get(table_type, [])
        else:
            appendices = raw_data.get('appendices', {})
            appendix_data = appendices.get(appendix, [])

        # 解析每个条目
        records = []

        # 防腐剂和 UV 过滤剂使用特殊的三栏矩阵格式
        if table_type in ['preservatives', 'uv_filters']:
            records = self._parse_three_column_matrix(table_type, appendix_data)
        else:
            # 禁用和限用物质使用标准格式
            for item in appendix_data:
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

    def _parse_three_column_matrix(
        self,
        table_type: str,
        data: List[Dict[str, Any]]
    ) -> List[BaseRegulationRecord]:
        """
        解析日本特殊的三栏矩阵格式

        三栏表示：
        - Column 1: 非粘膜·冲洗类（Non-Mucosa Rinse-Off）
        - Column 2: 非粘膜·驻留类（Non-Mucosa Leave-On）
        - Column 3: 可用于粘膜（Mucosa）

        每个栏位的值：
        - 数值：最大允用浓度（g/100g）
        - ○：无上限
        - 空白：禁止
        - -：不适用

        对于每个成分，会生成 1-3 条记录，每条对应一个产品类型。

        Args:
            table_type: 表类型
            data: 原始数据

        Returns:
            记录列表
        """
        records = []

        # 字段映射（从配置获取）
        table_config = self.field_mappings.get(table_type, {})
        field_mapping = table_config.get('field_mapping', {})

        # 获取三栏字段名
        rinse_field = field_mapping.get('Max_Conc_Percent_Rinse', [''])[0]
        leave_field = field_mapping.get('Max_Conc_Percent_Leave', [''])[0]
        mucosa_field = field_mapping.get('Max_Conc_Percent_Mucosa', [''])[0]

        for item in data:
            if not isinstance(item, dict):
                continue

            # 获取成分基本信息
            inci_name = self.map_field_value(table_type, 'INCI_Name', item)
            cas_no = self.map_field_value(table_type, 'CAS_No', item)
            conditions = self.map_field_value(table_type, 'Conditions', item)

            if not inci_name:
                continue

            # 解析三栏数据
            columns = [
                {
                    'field': rinse_field,
                    'product_type': ProductType.RINSE_OFF,
                    'value': item.get(rinse_field),
                },
                {
                    'field': leave_field,
                    'product_type': ProductType.LEAVE_ON,
                    'value': item.get(leave_field),
                },
                {
                    'field': mucosa_field,
                    'product_type': ProductType.MUCOSA,
                    'value': item.get(mucosa_field),
                },
            ]

            # 为每一栏创建记录
            for col in columns:
                value = col['value']

                if value is None or str(value).strip() == '':
                    # 空白表示禁止，跳过（不创建记录）
                    continue

                # 解析浓度值
                concentration, special_note = parse_japanese_concentration(
                    str(value),
                    source_unit='g/100g'
                )

                # 创建记录参数
                record_data = {
                    'INCI_Name': inci_name,
                    'CAS_No': cas_no,
                    'Product_Type': col['product_type'],
                    'Max_Conc_Percent': concentration,
                    'Conditions': conditions,
                }

                # 添加特殊标记到 Notes
                if special_note:
                    record_data['Notes'] = special_note

                # 创建记录
                record = self.create_record(
                    table_type=table_type,
                    source_data=record_data,
                    update_date=None
                )

                if record:
                    records.append(record)

        return records

    def parse_appendix_1_prohibited(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Appendix 1（禁用物质）

        Args:
            data: Appendix 1 原始数据

        Returns:
            禁用物质记录列表
        """
        return self.parse_table("prohibited", {"appendices": {"1": data}})

    def parse_appendix_2_restricted(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Appendix 2（限用物质）

        三层限用结构：
        1. 全类别限用
        2. 依用途限用
        3. 依产品型态限用

        Args:
            data: Appendix 2 原始数据

        Returns:
            限用物质记录列表
        """
        return self.parse_table("restricted", {"appendices": {"2": data}})

    def parse_appendix_3_preservatives(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Appendix 3（防腐剂）- 三栏矩阵

        Args:
            data: Appendix 3 原始数据

        Returns:
            防腐剂记录列表
        """
        return self.parse_table("preservatives", {"appendices": {"3": data}})

    def parse_appendix_4_uv_filters(self, data: List[Dict]) -> List[BaseRegulationRecord]:
        """
        解析 Appendix 4（UV 过滤剂）- 三栏矩阵

        Args:
            data: Appendix 4 原始数据

        Returns:
            UV 过滤剂记录列表
        """
        return self.parse_table("uv_filters", {"appendices": {"4": data}})


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
            "source": "MHLW Notification No.331",
        },
        "appendices": {
            "1": [
                {
                    "成分名称": "ホルムアルデヒド",
                    "CAS番号": "50-00-0",
                    "備考": "全面禁用"
                }
            ],
            "2": [
                {
                    "成分名称": "トリクロサン",
                    "CAS番号": "3380-34-5",
                    "配合限度": "0.3",
                    "適用範囲": "全类别",
                }
            ],
            "3": [
                {
                    "成分名称": "安息香酸",
                    "CAS番号": "65-85-0",
                    "粘膜に使用されることがない化粧品のうち洗い流すもの": "1.0",
                    "粘膜に使用されることがない化粧品のうち洗い流さないもの": "0.5",
                    "粘膜に使用されることがある化粧品": "",  # 空白 = 禁止
                }
            ],
            "4": [
                {
                    "成分名称": "オキシベンゾン",
                    "CAS番号": "131-57-7",
                    "粘膜に使用されることがない化粧品のうち洗い流すもの": "○",  # 无上限
                    "粘膜に使用されることがない化粧品のうち洗い流さないもの": "6.0",
                    "粘膜に使用されることがある化粧品": "0.5",
                }
            ],
        }
    }

    # 保存测试数据
    test_file = Path("/tmp/jp_test_data.json")
    save_json(test_data, test_file)

    # 解析测试数据
    parser = JPParserV2()
    result = parser.run(test_file)

    print("\n=== Test Parsing Results ===")
    print(f"Statistics: {result['statistics']}")
    print(f"\nDetailed table statistics:")
    for table_type, stats in result['statistics']['tables'].items():
        print(f"  {table_type}: {stats['actual']} actual records (total: {stats['total']})")
