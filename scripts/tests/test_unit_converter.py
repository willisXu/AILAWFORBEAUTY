"""
单元测试：单位转换工具

测试单位转换、日本特殊符号处理、产品类型标准化等功能。
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.unit_converter import (
    convert_concentration_to_percent,
    parse_japanese_concentration,
    normalize_product_type,
    parse_cas_number,
    validate_concentration,
    extract_ph_range,
    format_concentration_display,
)


class TestUnitConverter(unittest.TestCase):
    """测试单位转换功能"""

    def test_convert_concentration_basic(self):
        """测试基本单位转换"""
        # % → %
        self.assertEqual(convert_concentration_to_percent(5, '%'), 5.0)
        self.assertEqual(convert_concentration_to_percent('5%'), 5.0)

        # g/100g → %
        self.assertEqual(convert_concentration_to_percent(10, 'g/100g'), 10.0)

        # ppm → %
        self.assertEqual(convert_concentration_to_percent(1000, 'ppm'), 0.1)
        self.assertEqual(convert_concentration_to_percent(10000, 'ppm'), 1.0)

    def test_convert_concentration_edge_cases(self):
        """测试边界情况"""
        # 空值
        self.assertIsNone(convert_concentration_to_percent(''))
        self.assertIsNone(convert_concentration_to_percent(None))
        self.assertIsNone(convert_concentration_to_percent('N/A'))

        # 零值
        self.assertEqual(convert_concentration_to_percent(0, '%'), 0.0)

    def test_parse_japanese_concentration_symbols(self):
        """测试日本特殊符号"""
        # ○ = 无上限
        conc, note = parse_japanese_concentration('○')
        self.assertIsNone(conc)
        self.assertEqual(note, 'No Limit')

        # 空白 = 禁止
        conc, note = parse_japanese_concentration('')
        self.assertIsNone(conc)
        self.assertEqual(note, 'Prohibited')

        # - = 不适用
        conc, note = parse_japanese_concentration('-')
        self.assertIsNone(conc)
        self.assertEqual(note, 'Not Applicable')

    def test_parse_japanese_concentration_numbers(self):
        """测试日本数值转换"""
        # 数值（g/100g → %）
        conc, note = parse_japanese_concentration('0.5')
        self.assertEqual(conc, 0.5)
        self.assertIsNone(note)

        conc, note = parse_japanese_concentration('10')
        self.assertEqual(conc, 10.0)
        self.assertIsNone(note)

    def test_normalize_product_type_english(self):
        """测试产品类型标准化 - 英文"""
        self.assertEqual(normalize_product_type('hair'), 'Hair')
        self.assertEqual(normalize_product_type('rinse-off'), 'Rinse_Off')
        self.assertEqual(normalize_product_type('leave on'), 'Leave_On')
        self.assertEqual(normalize_product_type('mucous membrane'), 'Mucosa')

    def test_normalize_product_type_japanese(self):
        """测试产品类型标准化 - 日文"""
        self.assertEqual(normalize_product_type('洗い流す'), 'Rinse_Off')
        self.assertEqual(normalize_product_type('洗い流さない'), 'Leave_On')
        self.assertEqual(normalize_product_type('粘膜'), 'Mucosa')

    def test_normalize_product_type_chinese(self):
        """测试产品类型标准化 - 中文"""
        self.assertEqual(normalize_product_type('冲洗类'), 'Rinse_Off')
        self.assertEqual(normalize_product_type('驻留类'), 'Leave_On')
        self.assertEqual(normalize_product_type('头发'), 'Hair')

    def test_parse_cas_number_valid(self):
        """测试 CAS 号码解析 - 有效格式"""
        # 标准格式
        self.assertEqual(parse_cas_number('50-00-0'), '50-00-0')
        self.assertEqual(parse_cas_number('7732-18-5'), '7732-18-5')

        # 无连字符（尝试格式化）
        self.assertEqual(parse_cas_number('50000'), '50-00-0')

    def test_parse_cas_number_invalid(self):
        """测试 CAS 号码解析 - 无效格式"""
        self.assertIsNone(parse_cas_number('invalid'))
        self.assertIsNone(parse_cas_number('123'))
        self.assertIsNone(parse_cas_number(''))

    def test_validate_concentration_valid(self):
        """测试浓度验证 - 有效范围"""
        self.assertTrue(validate_concentration(0.0))
        self.assertTrue(validate_concentration(50.0))
        self.assertTrue(validate_concentration(100.0))
        self.assertTrue(validate_concentration(None))  # None 是有效的

    def test_validate_concentration_invalid(self):
        """测试浓度验证 - 无效范围"""
        self.assertFalse(validate_concentration(-1.0))
        self.assertFalse(validate_concentration(101.0))
        self.assertFalse(validate_concentration(1000.0))

    def test_extract_ph_range(self):
        """测试 pH 范围提取"""
        # 标准格式
        self.assertEqual(extract_ph_range('pH 3-9'), (3.0, 9.0))
        self.assertEqual(extract_ph_range('pH: 5.5 to 7.5'), (5.5, 7.5))

        # 无 pH 范围
        self.assertIsNone(extract_ph_range('No pH requirement'))
        self.assertIsNone(extract_ph_range(''))

    def test_format_concentration_display(self):
        """测试浓度显示格式化"""
        # 普通数值
        self.assertEqual(format_concentration_display(0.5), '0.5%')
        self.assertEqual(format_concentration_display(10.0), '10%')

        # 特殊标记
        self.assertEqual(format_concentration_display(None, 'No Limit'), '无上限')
        self.assertEqual(format_concentration_display(None, 'Prohibited'), '禁止')

        # None
        self.assertEqual(format_concentration_display(None), '未规定')


class TestUnitConverterIntegration(unittest.TestCase):
    """集成测试"""

    def test_eu_concentration_flow(self):
        """测试 EU 浓度转换流程"""
        # EU 使用 % 直接
        value = '0.3%'
        result = convert_concentration_to_percent(value)
        self.assertEqual(result, 0.3)
        self.assertTrue(validate_concentration(result))

    def test_jp_concentration_flow(self):
        """测试日本浓度转换流程"""
        # 日本使用 g/100g
        value = '0.5'
        conc, note = parse_japanese_concentration(value, 'g/100g')
        self.assertEqual(conc, 0.5)
        self.assertIsNone(note)
        self.assertTrue(validate_concentration(conc))

        # 日本特殊符号
        conc, note = parse_japanese_concentration('○')
        self.assertIsNone(conc)
        self.assertEqual(note, 'No Limit')

    def test_cn_concentration_flow(self):
        """测试中国浓度转换流程"""
        # 中国使用 %
        value = '0.5'
        result = convert_concentration_to_percent(value, '%')
        self.assertEqual(result, 0.5)
        self.assertTrue(validate_concentration(result))


if __name__ == '__main__':
    unittest.main(verbosity=2)
