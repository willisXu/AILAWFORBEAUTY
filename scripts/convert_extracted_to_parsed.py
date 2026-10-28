"""
将extracted PDF数据转换成parsed格式（前端兼容版本）

这个脚本将data/extracted/目录下的PDF提取数据转换成
data/parsed/目录下的前端兼容格式。

前端期望的字段格式：
- INCI_Name: 成分的国际通用名（必须）
- CAS_No: CAS编号
- CN_Name: 中文名
- Status: 状态（PROHIBITED/RESTRICTED/ALLOWED/LISTED）（必须）
- Table_Type: 表格类型
- Max_Conc_Percent: 最大浓度百分比（可选）
- Product_Type: 产品类型（可选）
- Conditions: 条件/限制（可选）

用法（在仓库根目录执行）：
    python scripts/convert_extracted_to_parsed.py [--jurisdictions CN EU] [--sync]

--sync 会把 data/parsed/<J>/v2/*_latest.json 复制到前端读取的位置：
    data/parsed/<J>/*_latest.json 与 app/public/data/parsed/<J>/*_latest.json
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent))

from extractors.cn_extractor import split_merged_tables

ALL_JURISDICTIONS = ['CN', 'EU', 'JP', 'CA']

STATUS_MAPPING = {
    'prohibited': 'PROHIBITED',
    'restricted': 'RESTRICTED',
    'preservatives': 'ALLOWED',
    'uv_filters': 'ALLOWED',
    'colorants': 'ALLOWED',
    'whitelist': 'LISTED',
}

# 表类型映射
TABLE_MAPPING = {
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
    # 准用染发剂只允许在染发产品中限量使用，归入限用表
    "hair_dyes": "restricted",
}


def map_to_frontend_format(ingredient: Dict[str, Any], table_type: str, jurisdiction: str) -> Dict[str, Any]:
    """
    将extracted数据格式映射到前端期望的格式

    Args:
        ingredient: 原始成分数据
        table_type: 表格类型 (prohibited, restricted, etc.)
        jurisdiction: 管辖区代码

    Returns:
        前端兼容格式的记录
    """
    # 提取INCI名称（英文名称）
    inci_name = (
        ingredient.get('ingredient_name_en') or  # CN格式
        ingredient.get('chemical_name') or  # EU格式
        ingredient.get('ingredient_name') or  # JP/CA格式
        ingredient.get('INCI_Name') or
        ''
    )

    # 提取CAS号
    cas_no = ingredient.get('cas_no') or ingredient.get('CAS_No') or ingredient.get('CAS_NO') or ''

    # 提取中文名称
    cn_name = (
        ingredient.get('ingredient_name_cn') or  # CN格式
        ingredient.get('CN_Name') or
        ''
    )

    # 提取限制条件/最大浓度
    restrictions = ingredient.get('restrictions') or ingredient.get('restriction') or ''
    max_amount = ingredient.get('max_amount') or ingredient.get('Max_Conc_Percent') or ''
    conditions = ingredient.get('conditions') or ingredient.get('Conditions') or restrictions or ''

    # 尝试提取浓度百分比
    max_conc_percent = None
    if max_amount:
        # 尝试从字符串中提取数字（例如 "0.5 g" -> 0.5）
        match = re.search(r'([\d.]+)', str(max_amount))
        if match:
            try:
                max_conc_percent = float(match.group(1))
            except ValueError:
                pass

    # 构建前端兼容格式
    mapped_record = {
        'INCI_Name': inci_name,
        'CAS_No': cas_no,
        'CN_Name': cn_name,
        'Status': STATUS_MAPPING.get(table_type, 'NOT_SPECIFIED'),
        'Table_Type': table_type,
    }

    # 添加可选字段
    if max_conc_percent is not None:
        mapped_record['Max_Conc_Percent'] = max_conc_percent

    if conditions:
        mapped_record['Conditions'] = conditions

    if ingredient.get('source_table'):
        mapped_record['Legal_Basis'] = ingredient['source_table']

    # 添加原始数据作为参考（调试用）
    mapped_record['_original'] = {
        'reference_number': ingredient.get('reference_number') or ingredient.get('serial_number'),
        'jurisdiction': jurisdiction
    }

    return mapped_record


def write_table(parsed_dir: Path, jurisdiction: str, table_type: str, records: List[Dict[str, Any]],
                version: str, generated_at: str) -> Path:
    parsed_data = {
        "jurisdiction": jurisdiction,
        "table_type": table_type,
        "version": version,
        "generated_at": generated_at,
        "total_records": len(records),
        "records": records
    }
    output_file = parsed_dir / f"{table_type}_latest.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    return output_file


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

    generated_at = datetime.now(timezone.utc).isoformat()
    version = datetime.now().strftime("%Y%m%d")

    # 每种表类型可能来自多个来源表（例如 CN 的限用组分 + 准用染发剂），先汇总再写出
    records_by_type: Dict[str, List[Dict[str, Any]]] = {}

    if 'tables' in extracted_data:
        # CN格式
        tables = extracted_data['tables']
        if jurisdiction == 'CN':
            # 旧的提取结果可能把所有表都放在 prohibited 里
            tables = split_merged_tables(tables)

        for table_name, table_data in tables.items():
            if not isinstance(table_data, dict):
                continue

            ingredients = table_data.get('ingredients', [])
            if not ingredients:
                continue

            table_type = TABLE_MAPPING.get(table_name, table_name)
            mapped = [map_to_frontend_format(ing, table_type, jurisdiction) for ing in ingredients]
            records_by_type.setdefault(table_type, []).extend(mapped)
            print(f"  {table_name} -> {table_type}: {len(mapped)} 条记录")

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
            table_type = TABLE_MAPPING.get(table_name, cat_name)

            # JP的positive_list可能包含多种类型，暂时归类为preservatives
            if cat_name == 'positive_list':
                table_type = 'preservatives'

            mapped = [map_to_frontend_format(ing, table_type, jurisdiction) for ing in ingredients]
            records_by_type.setdefault(table_type, []).extend(mapped)
            print(f"  {cat_name} -> {table_type}: {len(mapped)} 条记录")

    stats = {}
    for table_type, records in records_by_type.items():
        output_file = write_table(parsed_dir, jurisdiction, table_type, records, version, generated_at)
        stats[table_type] = len(records)
        print(f"✓ {table_type}: {len(records)} 条记录 -> {output_file}")

    return stats


def sync_frontend_copies(jurisdiction: str) -> None:
    """把 v2 的 *_latest.json 复制到前端读取的两个位置"""
    source_dir = Path(f"data/parsed/{jurisdiction}/v2")
    for target_dir in (Path(f"data/parsed/{jurisdiction}"), Path(f"app/public/data/parsed/{jurisdiction}")):
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.glob("*_latest.json")):
            shutil.copyfile(source, target_dir / source.name)
            print(f"  同步 {source} -> {target_dir / source.name}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PDF Extracted数据 -> Parsed数据转换工具")
    parser.add_argument('--jurisdictions', nargs='+', choices=ALL_JURISDICTIONS, default=ALL_JURISDICTIONS,
                        help='要转换的管辖区（默认全部）')
    parser.add_argument('--sync', action='store_true',
                        help='同步 v2 结果到 data/parsed/<J>/ 与 app/public/data/parsed/<J>/')
    args = parser.parse_args()

    print("="*80)
    print("PDF Extracted数据 -> Parsed数据转换工具")
    print("="*80)

    total_stats = {}

    for jurisdiction in args.jurisdictions:
        extracted_file = Path(f"data/extracted/{jurisdiction}/extracted_latest.json")

        if not extracted_file.exists():
            print(f"\n⚠️  {jurisdiction}: 未找到extracted数据文件")
            continue

        try:
            stats = convert_jurisdiction(jurisdiction, extracted_file)
            total_stats[jurisdiction] = stats
            if args.sync:
                sync_frontend_copies(jurisdiction)
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
