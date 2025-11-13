"""
将extracted PDF数据转换成parsed格式

这个脚本将data/extracted/目录下的PDF提取数据转换成
data/parsed/目录下的parsed格式，以便前端API可以使用。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def convert_jurisdiction(jurisdiction: str, extracted_file: Path) -> Dict[str, int]:
    """
    转换单个管辖区的数据

    Args:
        jurisdiction: 管辖区代码
        extracted_file: extracted数据文件路径

    Returns:
        转换统计信息
    """
    print(f"\n{'='*80}")
    print(f"转换 {jurisdiction} 数据")
    print(f"{'='*80}")

    # 加载extracted数据
    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)

    # 输出目录
    parsed_dir = Path(f"data/parsed/{jurisdiction}/v2")
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # 表类型映射
    table_mapping = {
        # EU
        "Annex II - Prohibited Substances": "prohibited",
        "Annex III - Restricted Substances": "restricted",
        "Annex IV - Colorants": "colorants",
        "Annex V - Preservatives": "preservatives",
        "Annex VI - UV Filters": "uv_filters",
        # JP
        "ネガティブリスト (Negative List)": "prohibited",
        "Appendix 1 - Negative List": "prohibited",
        "Appendix 2 - Restricted Ingredients": "restricted",
        "ポジティブリスト (Positive List)": "preservatives",  # 包含多种
        # CA
        "Prohibited Ingredients": "prohibited",
        "Restricted Ingredients": "restricted",
        # CN
        "prohibited": "prohibited",
        "restricted": "restricted",
        "preservatives": "preservatives",
        "uv_filters": "uv_filters",
        "colorants": "colorants",
    }

    stats = {}
    generated_at = datetime.utcnow().isoformat() + 'Z'
    version = datetime.now().strftime("%Y%m%d")

    # 处理每个表
    if 'tables' in extracted_data:
        # CN格式
        for table_name, table_data in extracted_data['tables'].items():
            if not isinstance(table_data, dict):
                continue

            ingredients = table_data.get('ingredients', [])
            if not ingredients:
                continue

            table_type = table_mapping.get(table_name, table_name)

            # 转换成parsed格式
            parsed_data = {
                "jurisdiction": jurisdiction,
                "table_type": table_type,
                "version": version,
                "generated_at": generated_at,
                "total_records": len(ingredients),
                "records": ingredients
            }

            # 保存
            output_file = parsed_dir / f"{table_type}_latest.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)

            stats[table_type] = len(ingredients)
            print(f"✓ {table_type}: {len(ingredients)} 条记录 -> {output_file}")

    elif 'categories' in extracted_data or 'annexes' in extracted_data:
        # EU/JP/CA格式
        data_source = extracted_data.get('categories') or extracted_data.get('annexes', {})
        for cat_name, cat_data in data_source.items():
            if not isinstance(cat_data, dict):
                continue

            ingredients = cat_data.get('ingredients', [])
            if not ingredients:
                continue

            # 查找表类型映射
            table_name = cat_data.get('name', cat_name)
            table_type = table_mapping.get(table_name, cat_name)

            # JP的positive_list可能包含多种类型，暂时归类为preservatives
            if cat_name == 'positive_list':
                # 可以根据usage字段进一步分类，但暂时统一归类
                table_type = 'preservatives'

            # 转换成parsed格式
            parsed_data = {
                "jurisdiction": jurisdiction,
                "table_type": table_type,
                "version": version,
                "generated_at": generated_at,
                "total_records": len(ingredients),
                "records": ingredients
            }

            # 保存
            output_file = parsed_dir / f"{table_type}_latest.json"

            # 如果文件已存在，合并数据（例如JP的positive_list包含多种）
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_records = existing_data.get('records', [])
                    parsed_data['records'] = existing_records + ingredients
                    parsed_data['total_records'] = len(parsed_data['records'])

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)

            current_count = stats.get(table_type, 0)
            stats[table_type] = current_count + len(ingredients)
            print(f"✓ {cat_name} -> {table_type}: {len(ingredients)} 条记录 -> {output_file}")

    return stats


def main():
    """主函数"""
    print("="*80)
    print("PDF Extracted数据 -> Parsed数据转换工具")
    print("="*80)

    jurisdictions = ['CN', 'EU', 'JP', 'CA']
    total_stats = {}

    for jurisdiction in jurisdictions:
        extracted_file = Path(f"data/extracted/{jurisdiction}/extracted_latest.json")

        if not extracted_file.exists():
            print(f"\n⚠️  {jurisdiction}: 未找到extracted数据文件")
            continue

        try:
            stats = convert_jurisdiction(jurisdiction, extracted_file)
            total_stats[jurisdiction] = stats
        except Exception as e:
            print(f"\n❌ {jurisdiction}: 转换失败 - {e}")
            import traceback
            traceback.print_exc()

    # 打印总结
    print("\n" + "="*80)
    print("转换总结")
    print("="*80)

    grand_total = 0
    for jurisdiction, stats in total_stats.items():
        j_total = sum(stats.values())
        grand_total += j_total
        print(f"\n{jurisdiction}: {j_total} 条记录")
        for table_type, count in stats.items():
            print(f"  - {table_type}: {count} 条")

    print(f"\n总计: {grand_total} 条记录")
    print("="*80)


if __name__ == "__main__":
    main()
