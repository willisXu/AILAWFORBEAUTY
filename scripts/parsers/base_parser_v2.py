"""
Base Parser V2 - 支持多表架构（Multi-Table Model）

重构版本，支持：
1. 六张主表的解析和输出
2. 基于 YAML 配置的字段映射
3. 单位转换和数据正规化
4. 与新的 Schema 定义集成
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import sys
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PARSED_DATA_DIR, RULES_DATA_DIR
from utils import setup_logger, save_json, load_json
from schema.database_schema import (
    Jurisdiction,
    Status,
    ProductType,
    BaseRegulationRecord,
    ProhibitedRecord,
    RestrictedRecord,
    AllowedPreservativeRecord,
    AllowedUVFilterRecord,
    AllowedColorantRecord,
    GeneralWhitelistRecord,
    TABLE_TYPES,
    get_legal_basis,
)
from utils.unit_converter import (
    convert_concentration_to_percent,
    parse_japanese_concentration,
    normalize_product_type,
    parse_cas_number,
    validate_concentration,
)

logger = setup_logger(__name__)


class BaseParserV2(ABC):
    """
    基础解析器 V2

    支持多表架构的解析器基类
    """

    def __init__(self, jurisdiction_code: str):
        """
        初始化解析器

        Args:
            jurisdiction_code: 法规属地代码（EU, JP, CN, CA, ASEAN）
        """
        self.jurisdiction_code = jurisdiction_code
        self.jurisdiction = Jurisdiction[jurisdiction_code]
        self.logger = setup_logger(f"{__name__}.{jurisdiction_code}")

        # 输出目录
        self.parsed_dir = PARSED_DATA_DIR / jurisdiction_code / "v2"
        self.rules_dir = RULES_DATA_DIR / jurisdiction_code / "v2"
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir.mkdir(parents=True, exist_ok=True)

        # 加载字段映射配置
        self.field_mappings = self._load_field_mappings()

        # 初始化六张表的数据
        self.tables: Dict[str, List[BaseRegulationRecord]] = {
            "prohibited": [],
            "restricted": [],
            "preservatives": [],
            "uv_filters": [],
            "colorants": [],
            "whitelist": [],
        }

    def _load_field_mappings(self) -> Dict[str, Any]:
        """
        加载字段映射配置（从 YAML 文件）

        Returns:
            字段映射配置字典
        """
        config_file = Path(__file__).parent.parent / "config" / "field_mappings.yaml"

        if not config_file.exists():
            self.logger.warning(f"Field mappings config not found: {config_file}")
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        jurisdiction_config = config.get(self.jurisdiction_code, {})
        jurisdiction_config['common'] = config.get('common', {})

        return jurisdiction_config

    @abstractmethod
    def parse_table(
        self,
        table_type: str,
        raw_data: Dict[str, Any]
    ) -> List[BaseRegulationRecord]:
        """
        解析特定表的数据

        Args:
            table_type: 表类型（prohibited, restricted, preservatives, uv_filters, colorants, whitelist）
            raw_data: 原始数据

        Returns:
            解析后的记录列表
        """
        pass

    def map_field_value(
        self,
        table_type: str,
        field_name: str,
        source_data: Dict[str, Any]
    ) -> Any:
        """
        根据配置映射字段值

        Args:
            table_type: 表类型
            field_name: 目标字段名
            source_data: 源数据

        Returns:
            映射后的字段值
        """
        table_config = self.field_mappings.get(table_type, {})
        field_mapping = table_config.get('field_mapping', {})

        # 获取该字段的可能源字段名列表
        source_field_names = field_mapping.get(field_name, [field_name])

        # 如果不是列表，转换为列表
        if not isinstance(source_field_names, list):
            source_field_names = [source_field_names]

        # 尝试从源数据中获取值
        for source_field in source_field_names:
            value = source_data.get(source_field)
            if value is not None:
                return value

        return None

    def normalize_concentration(
        self,
        value: Any,
        table_type: str
    ) -> Optional[float]:
        """
        正规化浓度值

        Args:
            value: 原始浓度值
            table_type: 表类型（用于确定单位）

        Returns:
            正规化后的浓度值（%）
        """
        if value is None:
            return None

        # 获取该表的浓度单位配置
        table_config = self.field_mappings.get(table_type, {})
        source_unit = table_config.get('concentration_unit', '%')

        # 转换为百分比
        concentration = convert_concentration_to_percent(value, source_unit)

        # 验证范围
        if concentration is not None and not validate_concentration(concentration):
            self.logger.warning(
                f"Invalid concentration value: {concentration}% (original: {value})"
            )
            return None

        return concentration

    def create_record(
        self,
        table_type: str,
        source_data: Dict[str, Any],
        update_date: Optional[date] = None
    ) -> Optional[BaseRegulationRecord]:
        """
        创建记录对象

        Args:
            table_type: 表类型
            source_data: 源数据
            update_date: 更新日期

        Returns:
            记录对象，失败返回 None
        """
        try:
            # 获取记录类
            RecordClass = TABLE_TYPES.get(table_type)
            if not RecordClass:
                raise ValueError(f"Invalid table type: {table_type}")

            # 映射通用字段
            inci_name = self.map_field_value(table_type, 'INCI_Name', source_data)
            cas_no = parse_cas_number(self.map_field_value(table_type, 'CAS_No', source_data))
            product_type_str = self.map_field_value(table_type, 'Product_Type', source_data)
            max_conc_raw = self.map_field_value(table_type, 'Max_Conc_Percent', source_data)
            conditions = self.map_field_value(table_type, 'Conditions', source_data)
            notes = self.map_field_value(table_type, 'Notes', source_data)

            # 必填字段验证
            if not inci_name:
                self.logger.warning(f"Missing INCI_Name in {table_type} record")
                return None

            # 正规化数据
            product_type = (
                ProductType[normalize_product_type(product_type_str)]
                if product_type_str
                else ProductType.NOT_SPECIFIED
            )
            max_conc = self.normalize_concentration(max_conc_raw, table_type)

            # 获取法规依据
            legal_basis = get_legal_basis(self.jurisdiction, table_type)

            # 创建基础参数
            base_params = {
                'INCI_Name': inci_name.strip(),
                'CAS_No': cas_no,
                'Jurisdiction': self.jurisdiction,
                'Product_Type': product_type,
                'Max_Conc_Percent': max_conc,
                'Conditions': conditions.strip() if conditions else None,
                'Legal_Basis': legal_basis,
                'Update_Date': update_date,
                'Notes': notes.strip() if notes else None,
            }

            # 表特殊字段
            if table_type in ['preservatives', 'uv_filters']:
                label_warnings = self.map_field_value(table_type, 'Label_Warnings', source_data)
                base_params['Label_Warnings'] = label_warnings.strip() if label_warnings else None

            elif table_type == 'colorants':
                colour_index = self.map_field_value(table_type, 'Colour_Index', source_data)
                body_area = self.map_field_value(table_type, 'Body_Area', source_data)
                base_params['Colour_Index'] = colour_index.strip() if colour_index else None
                base_params['Body_Area'] = body_area.strip() if body_area else None

            elif table_type == 'whitelist':
                list_name = self.map_field_value(table_type, 'List_Name', source_data)
                iecic_status = self.map_field_value(table_type, 'IECIC_Status', source_data)
                base_params['List_Name'] = list_name.strip() if list_name else None
                base_params['IECIC_Status'] = iecic_status.strip() if iecic_status else None

            # 创建记录
            record = RecordClass(**base_params)

            return record

        except Exception as e:
            self.logger.error(f"Failed to create record for {table_type}: {e}")
            self.logger.debug(f"Source data: {source_data}")
            return None

    def parse_all_tables(self, raw_data: Dict[str, Any]) -> None:
        """
        解析所有表

        Args:
            raw_data: 原始数据
        """
        # 获取更新日期
        metadata = raw_data.get('metadata', {})
        update_date_str = metadata.get('published_at') or metadata.get('effective_date')
        update_date = None

        if update_date_str:
            try:
                update_date = datetime.fromisoformat(update_date_str.replace('Z', '+00:00')).date()
            except:
                pass

        # 解析每个表
        for table_type in TABLE_TYPES.keys():
            self.logger.info(f"Parsing {table_type} table...")

            try:
                records = self.parse_table(table_type, raw_data)

                if records:
                    self.tables[table_type].extend(records)
                    self.logger.info(f"Parsed {len(records)} records for {table_type}")
                else:
                    self.logger.info(f"No records found for {table_type}")

            except Exception as e:
                self.logger.error(f"Failed to parse {table_type}: {e}", exc_info=True)

    def save_tables(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        保存所有表到文件

        Args:
            version: 版本标识符

        Returns:
            保存的文件路径字典
        """
        if version is None:
            version = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        output_paths = {}
        timestamp = datetime.now().isoformat()

        for table_type, records in self.tables.items():
            # 转换为字典列表
            data = {
                "jurisdiction": self.jurisdiction_code,
                "table_type": table_type,
                "version": version,
                "generated_at": timestamp,
                "total_records": len(records),
                "records": [r.to_dict() for r in records]
            }

            # 保存到版本文件
            version_file = self.parsed_dir / f"{table_type}_{version}.json"
            save_json(data, version_file)

            # 保存到 latest 文件
            latest_file = self.parsed_dir / f"{table_type}_latest.json"
            save_json(data, latest_file)

            output_paths[table_type] = version_file

            self.logger.info(f"Saved {len(records)} {table_type} records to {version_file}")

        return output_paths

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "jurisdiction": self.jurisdiction_code,
            "tables": {},
            "total_records": 0,
        }

        for table_type, records in self.tables.items():
            # 过滤掉"未规定"的记录
            actual_records = [
                r for r in records
                if r.Status != Status.NOT_SPECIFIED
            ]

            stats["tables"][table_type] = {
                "total": len(records),
                "actual": len(actual_records),
            }
            stats["total_records"] += len(actual_records)

        return stats

    def run(self, raw_data_path: Path) -> Dict[str, Any]:
        """
        运行完整的解析流程

        Args:
            raw_data_path: 原始数据文件路径

        Returns:
            解析结果统计
        """
        self.logger.info(f"Parsing {raw_data_path} with V2 parser...")

        # 加载原始数据
        raw_data = load_json(raw_data_path)

        # 解析所有表
        self.parse_all_tables(raw_data)

        # 保存表
        version = raw_data.get('metadata', {}).get('version')
        output_paths = self.save_tables(version)

        # 获取统计信息
        stats = self.get_statistics()

        self.logger.info(f"Parsing completed. Statistics: {stats}")

        return {
            "statistics": stats,
            "output_paths": {k: str(v) for k, v in output_paths.items()},
        }
