#!/usr/bin/env python3
"""
Parse All V2 - 统一解析脚本

一次性解析所有法规属地的数据，并执行数据整合。

使用方法：
    python parse_all_v2.py
    python parse_all_v2.py --jurisdictions EU JP CN
    python parse_all_v2.py --integrate --validate
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.eu_parser_v2 import EUParserV2
from parsers.asean_parser_v2 import ASEANParserV2
from parsers.jp_parser_v2 import JPParserV2
from parsers.cn_parser_v2 import CNParserV2
from parsers.ca_parser_v2 import CAParserV2
from integration.data_integrator import DataIntegrator
from validation.data_validator import DataValidator
from config import RAW_DATA_DIR
from utils import setup_logger, save_json

logger = setup_logger(__name__)


# 解析器映射
PARSERS = {
    'EU': EUParserV2,
    'ASEAN': ASEANParserV2,
    'JP': JPParserV2,
    'CN': CNParserV2,
    'CA': CAParserV2,
}


def parse_jurisdiction(
    jurisdiction: str,
    raw_data_file: Path = None
) -> Dict:
    """
    解析单个法规属地

    Args:
        jurisdiction: 法规属地代码
        raw_data_file: 原始数据文件路径（可选）

    Returns:
        解析结果字典
    """
    logger.info(f"\n{'=' * 80}")
    logger.info(f"解析 {jurisdiction} 法规数据")
    logger.info(f"{'=' * 80}")

    # 获取解析器类
    ParserClass = PARSERS.get(jurisdiction)
    if not ParserClass:
        logger.error(f"不支持的法规属地: {jurisdiction}")
        return None

    # 创建解析器
    parser = ParserClass()

    # 确定原始数据文件
    if raw_data_file is None:
        raw_data_file = RAW_DATA_DIR / jurisdiction / "latest.json"

    if not raw_data_file.exists():
        logger.warning(f"原始数据文件不存在: {raw_data_file}")
        logger.warning(f"跳过 {jurisdiction}")
        return None

    try:
        # 执行解析
        result = parser.run(raw_data_file)

        logger.info(f"\n{jurisdiction} 解析完成:")
        logger.info(f"  总记录数: {result['statistics']['total_records']}")

        for table_type, stats in result['statistics']['tables'].items():
            if stats['actual'] > 0:
                logger.info(f"  {table_type}: {stats['actual']} 条有效记录")

        return {
            'jurisdiction': jurisdiction,
            'parser': parser,
            'result': result,
            'success': True
        }

    except Exception as e:
        logger.error(f"解析 {jurisdiction} 失败: {e}", exc_info=True)
        return {
            'jurisdiction': jurisdiction,
            'error': str(e),
            'success': False
        }


def integrate_data(parse_results: List[Dict], output_dir: Path) -> Dict:
    """
    整合所有法规属地的数据

    Args:
        parse_results: 解析结果列表
        output_dir: 输出目录

    Returns:
        整合结果字典
    """
    logger.info(f"\n{'=' * 80}")
    logger.info("开始数据整合")
    logger.info(f"{'=' * 80}")

    # 创建整合器
    integrator = DataIntegrator(output_dir=output_dir)

    # 添加所有解析后的数据
    for parse_result in parse_results:
        if not parse_result.get('success'):
            continue

        jurisdiction = parse_result['jurisdiction']
        parser = parse_result['parser']

        logger.info(f"\n添加 {jurisdiction} 数据到整合器...")

        for table_type, records in parser.tables.items():
            if records:
                integrator.add_records(table_type, records)
                logger.info(f"  {table_type}: {len(records)} 条记录")

    # 执行整合
    try:
        integrator.integrate()

        # 获取统计信息
        stats = integrator.get_statistics()

        logger.info(f"\n整合完成:")
        logger.info(f"  总成分数: {stats['total_ingredients']}")
        logger.info(f"  总记录数: {stats['total_records']}")

        for table_type, table_stats in stats['tables'].items():
            logger.info(f"  {table_type}: {table_stats['total']} 条记录")

        return {
            'success': True,
            'statistics': stats,
            'output_dir': str(output_dir)
        }

    except Exception as e:
        logger.error(f"数据整合失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def validate_data(parse_results: List[Dict]) -> Dict:
    """
    验证所有解析的数据

    Args:
        parse_results: 解析结果列表

    Returns:
        验证结果字典
    """
    logger.info(f"\n{'=' * 80}")
    logger.info("开始数据验证")
    logger.info(f"{'=' * 80}")

    # 创建验证器
    validator = DataValidator()

    validation_stats = {}

    # 验证每个法规属地的数据
    for parse_result in parse_results:
        if not parse_result.get('success'):
            continue

        jurisdiction = parse_result['jurisdiction']
        parser = parse_result['parser']

        logger.info(f"\n验证 {jurisdiction} 数据...")

        jurisdiction_stats = {}

        for table_type, records in parser.tables.items():
            if not records:
                continue

            stats = validator.validate_table(table_type, records)
            jurisdiction_stats[table_type] = stats

            logger.info(f"  {table_type}:")
            logger.info(f"    有效: {stats['valid_records']}/{stats['total_records']}")
            logger.info(f"    错误: {stats['errors']}")
            logger.info(f"    警告: {stats['warnings']}")

        validation_stats[jurisdiction] = jurisdiction_stats

    # 打印详细报告
    validator.print_report()

    return {
        'statistics': validation_stats,
        'report': validator.get_report()
    }


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='解析所有法规属地的数据（V2 版本）'
    )
    parser.add_argument(
        '--jurisdictions',
        nargs='+',
        choices=['EU', 'ASEAN', 'JP', 'CN', 'CA'],
        default=['EU', 'ASEAN', 'JP', 'CN', 'CA'],
        help='要解析的法规属地（默认全部）'
    )
    parser.add_argument(
        '--integrate',
        action='store_true',
        help='执行数据整合'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='执行数据验证'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/integrated'),
        help='整合数据输出目录'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 80)
    logger.info("法规解析系统 V2 - 批量解析")
    logger.info("=" * 80)
    logger.info(f"解析法规属地: {', '.join(args.jurisdictions)}")
    logger.info(f"数据整合: {'是' if args.integrate else '否'}")
    logger.info(f"数据验证: {'是' if args.validate else '否'}")

    start_time = datetime.now()

    # 1. 解析所有法规属地
    parse_results = []

    for jurisdiction in args.jurisdictions:
        result = parse_jurisdiction(jurisdiction)
        if result:
            parse_results.append(result)

    # 统计成功和失败
    success_count = sum(1 for r in parse_results if r.get('success'))
    failed_count = len(parse_results) - success_count

    logger.info(f"\n{'=' * 80}")
    logger.info(f"解析完成: {success_count} 成功, {failed_count} 失败")
    logger.info(f"{'=' * 80}")

    # 2. 数据整合（可选）
    if args.integrate and parse_results:
        integrate_result = integrate_data(parse_results, args.output_dir)

        if integrate_result.get('success'):
            logger.info("\n数据整合成功!")
        else:
            logger.error(f"\n数据整合失败: {integrate_result.get('error')}")

    # 3. 数据验证（可选）
    if args.validate and parse_results:
        validate_result = validate_data(parse_results)

        # 保存验证报告
        report_file = args.output_dir / 'validation_report.json'
        args.output_dir.mkdir(parents=True, exist_ok=True)
        save_json(validate_result['report'], report_file)
        logger.info(f"\n验证报告已保存到: {report_file}")

    # 计算总耗时
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"\n{'=' * 80}")
    logger.info(f"全部任务完成! 总耗时: {duration:.2f} 秒")
    logger.info(f"{'=' * 80}")


if __name__ == "__main__":
    main()
