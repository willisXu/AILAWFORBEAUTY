"""
单元测试：数据 Schema

测试数据模型的创建、验证和转换功能。
"""

import unittest
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema.database_schema import (
    Jurisdiction,
    Status,
    ProductType,
    ProhibitedRecord,
    RestrictedRecord,
    AllowedPreservativeRecord,
    AllowedUVFilterRecord,
    AllowedColorantRecord,
    GeneralWhitelistRecord,
    get_legal_basis,
    create_not_specified_record,
)


class TestJurisdiction(unittest.TestCase):
    """测试法规属地枚举"""

    def test_jurisdiction_values(self):
        """测试法规属地值"""
        self.assertEqual(Jurisdiction.EU.value, 'EU')
        self.assertEqual(Jurisdiction.ASEAN.value, 'ASEAN')
        self.assertEqual(Jurisdiction.JP.value, 'JP')
        self.assertEqual(Jurisdiction.CA.value, 'CA')
        self.assertEqual(Jurisdiction.CN.value, 'CN')

    def test_jurisdiction_count(self):
        """测试法规属地数量"""
        self.assertEqual(len(Jurisdiction), 5)


class TestStatus(unittest.TestCase):
    """测试状态枚举"""

    def test_status_values(self):
        """测试状态值"""
        self.assertEqual(Status.PROHIBITED.value, 'Prohibited')
        self.assertEqual(Status.RESTRICTED.value, 'Restricted')
        self.assertEqual(Status.ALLOWED.value, 'Allowed')
        self.assertEqual(Status.LISTED.value, 'Listed')
        self.assertEqual(Status.NOT_LISTED.value, 'Not_Listed')
        self.assertEqual(Status.NOT_SPECIFIED.value, '未规定')


class TestProductType(unittest.TestCase):
    """测试产品类型枚举"""

    def test_product_type_values(self):
        """测试产品类型值"""
        self.assertEqual(ProductType.HAIR.value, 'Hair')
        self.assertEqual(ProductType.RINSE_OFF.value, 'Rinse_Off')
        self.assertEqual(ProductType.LEAVE_ON.value, 'Leave_On')
        self.assertEqual(ProductType.MUCOSA.value, 'Mucosa')


class TestProhibitedRecord(unittest.TestCase):
    """测试禁用物质记录"""

    def test_create_prohibited_record(self):
        """测试创建禁用记录"""
        record = ProhibitedRecord(
            INCI_Name='Formaldehyde',
            CAS_No='50-00-0',
            Jurisdiction=Jurisdiction.EU,
        )

        self.assertEqual(record.INCI_Name, 'Formaldehyde')
        self.assertEqual(record.CAS_No, '50-00-0')
        self.assertEqual(record.Jurisdiction, Jurisdiction.EU)
        self.assertEqual(record.Status, Status.PROHIBITED)

    def test_prohibited_record_to_dict(self):
        """测试禁用记录转字典"""
        record = ProhibitedRecord(
            INCI_Name='Lead',
            CAS_No='7439-92-1',
            Jurisdiction=Jurisdiction.CN,
            Notes='Heavy metal'
        )

        data = record.to_dict()

        self.assertIsInstance(data, dict)
        self.assertEqual(data['INCI_Name'], 'Lead')
        self.assertEqual(data['Jurisdiction'], 'CN')
        self.assertEqual(data['Status'], 'Prohibited')


class TestRestrictedRecord(unittest.TestCase):
    """测试限用物质记录"""

    def test_create_restricted_record(self):
        """测试创建限用记录"""
        record = RestrictedRecord(
            INCI_Name='Triclosan',
            CAS_No='3380-34-5',
            Jurisdiction=Jurisdiction.EU,
            Max_Conc_Percent=0.3,
            Conditions='pH 3-9'
        )

        self.assertEqual(record.INCI_Name, 'Triclosan')
        self.assertEqual(record.Status, Status.RESTRICTED)
        self.assertEqual(record.Max_Conc_Percent, 0.3)
        self.assertEqual(record.Conditions, 'pH 3-9')


class TestAllowedRecords(unittest.TestCase):
    """测试允用记录（防腐剂、UV、色料）"""

    def test_create_preservative_record(self):
        """测试创建防腐剂记录"""
        record = AllowedPreservativeRecord(
            INCI_Name='Benzoic acid',
            CAS_No='65-85-0',
            Jurisdiction=Jurisdiction.EU,
            Max_Conc_Percent=0.5,
            Label_Warnings='Not for children under 3'
        )

        self.assertEqual(record.Status, Status.ALLOWED)
        self.assertEqual(record.Max_Conc_Percent, 0.5)
        self.assertEqual(record.Label_Warnings, 'Not for children under 3')

    def test_create_uv_filter_record(self):
        """测试创建 UV 过滤剂记录"""
        record = AllowedUVFilterRecord(
            INCI_Name='Benzophenone-3',
            CAS_No='131-57-7',
            Jurisdiction=Jurisdiction.JP,
            Max_Conc_Percent=6.0
        )

        self.assertEqual(record.Status, Status.ALLOWED)
        self.assertEqual(record.Max_Conc_Percent, 6.0)

    def test_create_colorant_record(self):
        """测试创建色料记录"""
        record = AllowedColorantRecord(
            INCI_Name='Titanium Dioxide',
            CAS_No='13463-67-7',
            Jurisdiction=Jurisdiction.CN,
            Colour_Index='CI 77891',
            Body_Area='Face, Body'
        )

        self.assertEqual(record.Status, Status.ALLOWED)
        self.assertEqual(record.Colour_Index, 'CI 77891')
        self.assertEqual(record.Body_Area, 'Face, Body')


class TestWhitelistRecord(unittest.TestCase):
    """测试白名单记录"""

    def test_create_whitelist_record(self):
        """测试创建白名单记录"""
        record = GeneralWhitelistRecord(
            INCI_Name='Water',
            CAS_No='7732-18-5',
            Jurisdiction=Jurisdiction.CN,
            List_Name='IECIC 2021',
            IECIC_Status='已使用'
        )

        self.assertEqual(record.Status, Status.LISTED)
        self.assertEqual(record.List_Name, 'IECIC 2021')
        self.assertEqual(record.IECIC_Status, '已使用')


class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""

    def test_get_legal_basis(self):
        """测试获取法规依据"""
        # EU
        self.assertEqual(get_legal_basis(Jurisdiction.EU, 'prohibited'), 'Annex II')
        self.assertEqual(get_legal_basis(Jurisdiction.EU, 'restricted'), 'Annex III')
        self.assertEqual(get_legal_basis(Jurisdiction.EU, 'preservatives'), 'Annex V')

        # JP
        self.assertEqual(get_legal_basis(Jurisdiction.JP, 'prohibited'), 'Appendix 1')
        self.assertEqual(get_legal_basis(Jurisdiction.JP, 'preservatives'), 'Appendix 3')

        # CN
        self.assertEqual(get_legal_basis(Jurisdiction.CN, 'prohibited'), 'STSC Annex 2')
        self.assertEqual(get_legal_basis(Jurisdiction.CN, 'whitelist'), 'IECIC 2021')

        # 不存在的表
        self.assertIsNone(get_legal_basis(Jurisdiction.EU, 'whitelist'))

    def test_create_not_specified_record(self):
        """测试创建"未规定"记录"""
        record = create_not_specified_record(
            inci_name='Test Ingredient',
            cas_no='12345-67-8',
            jurisdiction=Jurisdiction.CA,
            table_type='preservatives'
        )

        self.assertEqual(record.INCI_Name, 'Test Ingredient')
        self.assertEqual(record.CAS_No, '12345-67-8')
        self.assertEqual(record.Jurisdiction, Jurisdiction.CA)
        self.assertEqual(record.Status, Status.NOT_SPECIFIED)
        self.assertIn('未规定', record.Notes)


class TestRecordValidation(unittest.TestCase):
    """测试记录验证"""

    def test_required_fields(self):
        """测试必填字段"""
        # 正常创建
        record = ProhibitedRecord(
            INCI_Name='Test',
            Jurisdiction=Jurisdiction.EU
        )
        self.assertIsNotNone(record)

        # CAS_No 可以为 None
        self.assertIsNone(record.CAS_No)

    def test_optional_fields_defaults(self):
        """测试可选字段默认值"""
        record = RestrictedRecord(
            INCI_Name='Test',
            Jurisdiction=Jurisdiction.EU
        )

        self.assertIsNone(record.Max_Conc_Percent)
        self.assertIsNone(record.Conditions)
        self.assertIsNone(record.Notes)
        self.assertEqual(record.Product_Type, ProductType.NOT_SPECIFIED)


if __name__ == '__main__':
    unittest.main(verbosity=2)
