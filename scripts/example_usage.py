"""
示例：如何使用优化后的法规解析系统

展示完整的工作流程：
1. 解析各国法规数据
2. 整合数据
3. 验证数据
4. 查询数据
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.eu_parser_v2 import EUParserV2
from parsers.jp_parser_v2 import JPParserV2
from integration.data_integrator import DataIntegrator
from validation.data_validator import DataValidator
from utils import setup_logger, save_json

logger = setup_logger(__name__)


def example_1_parse_regulations():
    """示例 1: 解析法规数据"""
    print("\n" + "=" * 80)
    print("示例 1: 解析法规数据")
    print("=" * 80)

    # 创建测试数据
    eu_test_data = {
        "metadata": {
            "version": "20240424",
            "published_at": "2024-04-04",
            "source": "European Commission - CosIng Database",
        },
        "annexes": {
            "II": [
                {
                    "Chemical name": "Formaldehyde",
                    "CAS No": "50-00-0",
                    "Scope": "All cosmetic products"
                },
                {
                    "Chemical name": "Lead and its compounds",
                    "CAS No": "7439-92-1",
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
                    "Wording of conditions of use and warnings": "Not for children under 3"
                }
            ]
        }
    }

    # 保存测试数据
    test_file = Path("/tmp/eu_test_regulations.json")
    save_json(eu_test_data, test_file)

    # 解析 EU 数据
    print("\n解析 EU 法规数据...")
    eu_parser = EUParserV2()
    eu_result = eu_parser.run(test_file)

    print(f"\n解析结果:")
    print(f"  总记录数: {eu_result['statistics']['total_records']}")
    for table_type, stats in eu_result['statistics']['tables'].items():
        print(f"  {table_type}: {stats['actual']} 条有效记录")

    return eu_parser


def example_2_integrate_data(parsers):
    """示例 2: 整合多国数据"""
    print("\n" + "=" * 80)
    print("示例 2: 整合多国数据")
    print("=" * 80)

    # 创建整合器
    integrator = DataIntegrator(output_dir=Path("/tmp/integrated"))

    # 从解析器中提取数据并添加到整合器
    for parser in parsers:
        for table_type, records in parser.tables.items():
            if records:
                integrator.add_records(table_type, records)
                print(f"添加 {len(records)} 条 {table_type} 记录（来自 {parser.jurisdiction_code}）")

    # 执行整合
    print("\n执行数据整合...")
    integrator.integrate()

    # 显示统计信息
    stats = integrator.get_statistics()
    print(f"\n整合后统计:")
    print(f"  总成分数: {stats['total_ingredients']}")
    print(f"  总记录数: {stats['total_records']}")

    return integrator


def example_3_validate_data(integrator):
    """示例 3: 验证数据"""
    print("\n" + "=" * 80)
    print("示例 3: 验证数据")
    print("=" * 80)

    # 创建验证器
    validator = DataValidator()

    # 验证每个表
    for table_type, records in integrator.tables.items():
        if not records:
            continue

        print(f"\n验证 {table_type} 表...")
        stats = validator.validate_table(table_type, records)

        print(f"  总记录: {stats['total_records']}")
        print(f"  有效记录: {stats['valid_records']}")
        print(f"  无效记录: {stats['invalid_records']}")
        print(f"  错误: {stats['errors']}")
        print(f"  警告: {stats['warnings']}")

    # 打印详细报告
    validator.print_report()


def example_4_query_data():
    """示例 4: 查询数据（模拟 API）"""
    print("\n" + "=" * 80)
    print("示例 4: 查询数据")
    print("=" * 80)

    # 加载 MasterView
    master_view_file = Path("/tmp/integrated/master_view.json")

    if not master_view_file.exists():
        print("MasterView 文件不存在，请先运行示例 2")
        return

    with open(master_view_file, 'r', encoding='utf-8') as f:
        master_view = json.load(f)

    # 查询单个成分
    print("\n查询: Triclosan")
    for ingredient in master_view['data']:
        if ingredient['INCI_Name'].lower() == 'triclosan':
            print(f"\nINCI Name: {ingredient['INCI_Name']}")
            print(f"CAS No: {ingredient['CAS_No']}")
            print(f"\n各国法规状态:")

            for jurisdiction, regulation in ingredient['Regulations'].items():
                status = regulation.get('Status', '未规定')
                max_conc = regulation.get('Max_Conc_Percent')

                print(f"  {jurisdiction}: {status}", end='')
                if max_conc:
                    print(f" (最大浓度: {max_conc}%)", end='')
                print()

            break

    # 多国比对
    print("\n" + "-" * 80)
    print("多国比对: Benzoic acid")

    for ingredient in master_view['data']:
        if 'benzoic' in ingredient['INCI_Name'].lower():
            print(f"\nINCI Name: {ingredient['INCI_Name']}")

            print("\n比对结果:")
            print(f"{'法规属地':<10} {'状态':<15} {'最大浓度':<15} {'使用条件'}")
            print("-" * 80)

            for jurisdiction in ['EU', 'ASEAN', 'JP', 'CA', 'CN']:
                regulation = ingredient['Regulations'].get(jurisdiction, {})
                status = regulation.get('Status', '未规定')
                max_conc = regulation.get('Max_Conc_Percent', '-')
                conditions = regulation.get('Conditions', '-')

                if max_conc != '-':
                    max_conc = f"{max_conc}%"

                # 截断长字符串
                if conditions and len(conditions) > 30:
                    conditions = conditions[:27] + '...'

                print(f"{jurisdiction:<10} {status:<15} {str(max_conc):<15} {conditions}")

            break


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("法规解析系统优化 - 使用示例")
    print("=" * 80)

    try:
        # 示例 1: 解析法规数据
        eu_parser = example_1_parse_regulations()

        # 示例 2: 整合多国数据
        integrator = example_2_integrate_data([eu_parser])

        # 示例 3: 验证数据
        example_3_validate_data(integrator)

        # 示例 4: 查询数据
        example_4_query_data()

        print("\n" + "=" * 80)
        print("所有示例执行完成!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"示例执行失败: {e}", exc_info=True)
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
