"""
数据验证模块

提供法规数据的验证功能：
1. Schema 验证（字段类型、必填字段）
2. 数据完整性验证（CAS 号格式、浓度范围）
3. 逻辑一致性验证（状态与表类型匹配）
4. 跨表关联验证（成分在多表中的一致性）
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

from scripts.schema.database_schema import (
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
)

logger = logging.getLogger(__name__)


class ValidationError:
    """验证错误"""

    def __init__(
        self,
        severity: str,  # 'error', 'warning', 'info'
        code: str,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[Dict] = None
    ):
        self.severity = severity
        self.code = code
        self.message = message
        self.field = field
        self.value = value
        self.context = context or {}

    def to_dict(self) -> Dict:
        return {
            'severity': self.severity,
            'code': self.code,
            'message': self.message,
            'field': self.field,
            'value': self.value,
            'context': self.context,
        }

    def __str__(self):
        return f"[{self.severity.upper()}] {self.code}: {self.message}"


class DataValidator:
    """数据验证器"""

    # CAS 号码格式正则
    CAS_PATTERN = re.compile(r'^\d{1,7}-\d{2}-\d$')

    # 浓度范围（%）
    CONCENTRATION_MIN = 0.0
    CONCENTRATION_MAX = 100.0

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []

    def reset(self):
        """重置验证结果"""
        self.errors = []
        self.warnings = []
        self.info = []

    def add_error(self, code: str, message: str, **kwargs):
        """添加错误"""
        error = ValidationError('error', code, message, **kwargs)
        self.errors.append(error)
        logger.error(str(error))

    def add_warning(self, code: str, message: str, **kwargs):
        """添加警告"""
        warning = ValidationError('warning', code, message, **kwargs)
        self.warnings.append(warning)
        logger.warning(str(warning))

    def add_info(self, code: str, message: str, **kwargs):
        """添加信息"""
        info = ValidationError('info', code, message, **kwargs)
        self.info.append(info)
        logger.info(str(info))

    def validate_record(
        self,
        record: BaseRegulationRecord,
        table_type: str
    ) -> bool:
        """
        验证单条记录

        Args:
            record: 记录对象
            table_type: 表类型

        Returns:
            是否通过验证（无错误）
        """
        initial_error_count = len(self.errors)

        # 1. 必填字段验证
        self._validate_required_fields(record)

        # 2. 字段格式验证
        self._validate_field_formats(record)

        # 3. 数据范围验证
        self._validate_data_ranges(record)

        # 4. 逻辑一致性验证
        self._validate_logic_consistency(record, table_type)

        # 返回是否通过（无新增错误）
        return len(self.errors) == initial_error_count

    def _validate_required_fields(self, record: BaseRegulationRecord):
        """验证必填字段"""
        # INCI_Name 必填
        if not record.INCI_Name or not record.INCI_Name.strip():
            self.add_error(
                'REQUIRED_FIELD_MISSING',
                'INCI_Name is required',
                field='INCI_Name',
                context={'record': str(record)}
            )

        # Jurisdiction 必填
        if not record.Jurisdiction:
            self.add_error(
                'REQUIRED_FIELD_MISSING',
                'Jurisdiction is required',
                field='Jurisdiction',
                context={'record': str(record)}
            )

        # Status 必填
        if not record.Status:
            self.add_error(
                'REQUIRED_FIELD_MISSING',
                'Status is required',
                field='Status',
                context={'record': str(record)}
            )

        # CAS_No 虽然不是严格必填，但如果缺失应给予警告
        if not record.CAS_No:
            self.add_warning(
                'CAS_MISSING',
                f'CAS number is missing for {record.INCI_Name}',
                field='CAS_No',
                context={'INCI_Name': record.INCI_Name}
            )

    def _validate_field_formats(self, record: BaseRegulationRecord):
        """验证字段格式"""
        # CAS 号码格式
        if record.CAS_No:
            if not self.CAS_PATTERN.match(record.CAS_No):
                self.add_error(
                    'INVALID_CAS_FORMAT',
                    f'Invalid CAS number format: {record.CAS_No}',
                    field='CAS_No',
                    value=record.CAS_No,
                    context={'expected_format': 'XXXXXXX-XX-X'}
                )

        # Update_Date 格式
        if record.Update_Date:
            if not isinstance(record.Update_Date, date):
                self.add_error(
                    'INVALID_DATE_FORMAT',
                    f'Update_Date must be a date object, got {type(record.Update_Date)}',
                    field='Update_Date',
                    value=record.Update_Date
                )

    def _validate_data_ranges(self, record: BaseRegulationRecord):
        """验证数据范围"""
        # 浓度范围
        if record.Max_Conc_Percent is not None:
            if not isinstance(record.Max_Conc_Percent, (int, float)):
                self.add_error(
                    'INVALID_CONCENTRATION_TYPE',
                    f'Max_Conc_Percent must be a number, got {type(record.Max_Conc_Percent)}',
                    field='Max_Conc_Percent',
                    value=record.Max_Conc_Percent
                )
            elif record.Max_Conc_Percent < self.CONCENTRATION_MIN:
                self.add_error(
                    'CONCENTRATION_OUT_OF_RANGE',
                    f'Concentration cannot be negative: {record.Max_Conc_Percent}%',
                    field='Max_Conc_Percent',
                    value=record.Max_Conc_Percent
                )
            elif record.Max_Conc_Percent > self.CONCENTRATION_MAX:
                self.add_error(
                    'CONCENTRATION_OUT_OF_RANGE',
                    f'Concentration cannot exceed 100%: {record.Max_Conc_Percent}%',
                    field='Max_Conc_Percent',
                    value=record.Max_Conc_Percent
                )

    def _validate_logic_consistency(
        self,
        record: BaseRegulationRecord,
        table_type: str
    ):
        """验证逻辑一致性"""
        # 状态与表类型的一致性
        expected_status = {
            'prohibited': Status.PROHIBITED,
            'restricted': Status.RESTRICTED,
            'preservatives': Status.ALLOWED,
            'uv_filters': Status.ALLOWED,
            'colorants': Status.ALLOWED,
            'whitelist': [Status.LISTED, Status.NOT_LISTED],
        }

        expected = expected_status.get(table_type)

        if expected:
            if isinstance(expected, list):
                if record.Status not in expected and record.Status != Status.NOT_SPECIFIED:
                    self.add_warning(
                        'STATUS_TABLE_MISMATCH',
                        f'Status {record.Status.value} may not be appropriate for {table_type} table',
                        field='Status',
                        value=record.Status.value,
                        context={'table_type': table_type, 'expected': [s.value for s in expected]}
                    )
            else:
                if record.Status != expected and record.Status != Status.NOT_SPECIFIED:
                    self.add_warning(
                        'STATUS_TABLE_MISMATCH',
                        f'Status {record.Status.value} does not match table type {table_type}',
                        field='Status',
                        value=record.Status.value,
                        context={'table_type': table_type, 'expected': expected.value}
                    )

        # 禁用物质不应有最大浓度
        if isinstance(record, ProhibitedRecord):
            if record.Max_Conc_Percent is not None:
                self.add_warning(
                    'PROHIBITED_WITH_CONCENTRATION',
                    f'Prohibited ingredient should not have Max_Conc_Percent: {record.INCI_Name}',
                    field='Max_Conc_Percent',
                    value=record.Max_Conc_Percent
                )

        # 限用物质应该有最大浓度或使用条件
        if isinstance(record, RestrictedRecord):
            if record.Max_Conc_Percent is None and not record.Conditions:
                self.add_warning(
                    'RESTRICTED_WITHOUT_LIMITS',
                    f'Restricted ingredient should have Max_Conc_Percent or Conditions: {record.INCI_Name}',
                    field='Max_Conc_Percent',
                    context={'INCI_Name': record.INCI_Name}
                )

    def validate_table(
        self,
        table_type: str,
        records: List[BaseRegulationRecord]
    ) -> Dict[str, Any]:
        """
        验证整个表

        Args:
            table_type: 表类型
            records: 记录列表

        Returns:
            验证结果统计
        """
        self.reset()

        valid_count = 0
        invalid_count = 0

        for i, record in enumerate(records):
            if self.validate_record(record, table_type):
                valid_count += 1
            else:
                invalid_count += 1

        return {
            'table_type': table_type,
            'total_records': len(records),
            'valid_records': valid_count,
            'invalid_records': invalid_count,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'info': len(self.info),
        }

    def get_report(self) -> Dict[str, Any]:
        """
        获取验证报告

        Returns:
            验证报告字典
        """
        return {
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'total_info': len(self.info),
            },
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'info': [i.to_dict() for i in self.info],
        }

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        print(f"\nSummary:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Info: {len(self.info)}")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:10]:  # 只显示前 10 个
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:10]:
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    """测试代码"""
    import logging
    from datetime import date

    logging.basicConfig(level=logging.INFO)

    # 创建测试记录
    validator = DataValidator()

    # 测试有效记录
    valid_record = ProhibitedRecord(
        INCI_Name="Formaldehyde",
        CAS_No="50-00-0",
        Jurisdiction=Jurisdiction.EU,
        Update_Date=date.today(),
    )

    # 测试无效记录
    invalid_record = RestrictedRecord(
        INCI_Name="",  # 缺失 INCI_Name
        CAS_No="invalid-cas",  # 无效 CAS 格式
        Jurisdiction=Jurisdiction.EU,
        Max_Conc_Percent=150.0,  # 超出范围
    )

    print("Testing valid record:")
    result = validator.validate_record(valid_record, 'prohibited')
    print(f"Valid: {result}")

    print("\nTesting invalid record:")
    result = validator.validate_record(invalid_record, 'restricted')
    print(f"Valid: {result}")

    validator.print_report()
