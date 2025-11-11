"""
Main Application
主程式 - 整合所有模組並執行完整流程
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.eu_parser import EUAnnexParser
from src.parsers.asean_parser import ASEANParser
from src.parsers.japan_parser import JapanParser
from src.parsers.canada_parser import CanadaParser
from src.parsers.china_parser import ChinaParser
from src.comparison_engine import ComparisonEngine
from src.reports.report_generator import ReportManager
from src.models.data_models import RegionEnum


class CosmeticComplianceSystem:
    """化妝品法規合規系統"""

    def __init__(self, data_dir: Path, output_dir: Path):
        """
        初始化系統

        Args:
            data_dir: 法規文件目錄
            output_dir: 輸出目錄
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.comparison_engine = ComparisonEngine(fuzzy_threshold=85, cas_priority=True)
        self.report_manager = ReportManager(output_dir)

    def run(self):
        """執行完整流程"""
        print("=" * 80)
        print("GLOBAL COSMETIC REGULATION COMPLIANCE SYSTEM")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        # 步驟 1: 解析 EU 法規
        print("Step 1/5: Parsing EU COSING Annexes...")
        eu_data = self._parse_eu()
        print(f"✓ EU: {len(eu_data)} ingredients parsed\n")

        # 步驟 2: 解析 ASEAN 法規
        print("Step 2/5: Parsing ASEAN Cosmetic Directive...")
        asean_data = self._parse_asean()
        print(f"✓ ASEAN: {len(asean_data)} ingredients parsed\n")

        # 步驟 3: 解析日本法規
        print("Step 3/5: Parsing Japan MHLW Standards...")
        japan_data = self._parse_japan()
        print(f"✓ Japan: {len(japan_data)} ingredients parsed\n")

        # 步驟 4: 解析加拿大法規
        print("Step 4/5: Parsing Canada Health Canada Regulations...")
        canada_data = self._parse_canada()
        print(f"✓ Canada: {len(canada_data)} ingredients parsed\n")

        # 步驟 5: 解析中國法規
        print("Step 5/5: Parsing China NMPA STSC/IECIC...")
        china_data = self._parse_china()
        print(f"✓ China: {len(china_data)} ingredients parsed\n")

        # 整合資料
        print("Integrating data from all regions...")
        self.comparison_engine.add_regional_data(RegionEnum.EU, eu_data)
        self.comparison_engine.add_regional_data(RegionEnum.ASEAN, asean_data)
        self.comparison_engine.add_regional_data(RegionEnum.JAPAN, japan_data)
        self.comparison_engine.add_regional_data(RegionEnum.CANADA, canada_data)
        self.comparison_engine.add_regional_data(RegionEnum.CHINA, china_data)
        print("✓ Data integration completed\n")

        # 分析與比對
        print("Analyzing cross-region compliance...")
        statistics = self.comparison_engine.get_statistics()
        conflicts = self.comparison_engine.export_conflicts_only()
        differences = self.comparison_engine.get_limit_differences()
        print(f"✓ Analysis completed")
        print(f"  - Total ingredients: {statistics['total_ingredients']}")
        print(f"  - Conflicts: {len(conflicts)}")
        print(f"  - Limit differences: {len(differences)}\n")

        # 生成報表
        print("Generating reports...")
        unified_data = self.comparison_engine.to_list()
        self.report_manager.generate_all_reports(
            data=unified_data,
            statistics=statistics,
            conflicts=conflicts,
            differences=differences
        )

        print("\n" + "=" * 80)
        print("PROCESS COMPLETED SUCCESSFULLY!")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def _parse_eu(self) -> list:
        """解析 EU 法規"""
        try:
            parser = EUAnnexParser(self.data_dir)
            all_annexes = parser.parse_all()

            # 合併所有 Annex 的資料
            eu_data = []
            for annex_type, ingredients in all_annexes.items():
                eu_data.extend(ingredients)

            return eu_data

        except Exception as e:
            print(f"Error parsing EU data: {e}")
            return []

    def _parse_asean(self) -> list:
        """解析 ASEAN 法規"""
        try:
            pdf_path = self.data_dir / "annexes-of-the-asean-cosmetic-directive-(updated-dec24).pdf"

            if not pdf_path.exists():
                print(f"Warning: ASEAN file not found: {pdf_path}")
                return []

            parser = ASEANParser(pdf_path)
            all_annexes = parser.parse_all_annexes()

            # 合併所有 Annex 的資料
            asean_data = []
            for annex_name, ingredients in all_annexes.items():
                asean_data.extend(ingredients)

            return asean_data

        except Exception as e:
            print(f"Error parsing ASEAN data: {e}")
            return []

    def _parse_japan(self) -> list:
        """解析日本法規"""
        try:
            pdf_path = self.data_dir / "001257665.pdf"

            if not pdf_path.exists():
                print(f"Warning: Japan file not found: {pdf_path}")
                return []

            parser = JapanParser(pdf_path)
            all_appendices = parser.parse_all_appendices()

            # 合併所有附錄的資料
            japan_data = []
            for appendix_name, ingredients in all_appendices.items():
                japan_data.extend(ingredients)

            return japan_data

        except Exception as e:
            print(f"Error parsing Japan data: {e}")
            return []

    def _parse_canada(self) -> list:
        """解析加拿大法規"""
        try:
            xlsx_path = self.data_dir / "加拿大法規.xlsx"

            if not xlsx_path.exists():
                print(f"Warning: Canada file not found: {xlsx_path}")
                return []

            parser = CanadaParser(xlsx_path)
            canada_data = parser.parse()

            return canada_data

        except Exception as e:
            print(f"Error parsing Canada data: {e}")
            return []

    def _parse_china(self) -> list:
        """解析中國法規"""
        try:
            stsc_path = self.data_dir / "1686130272110055533.xlsx"

            if not stsc_path.exists():
                print(f"Warning: China STSC file not found: {stsc_path}")
                return []

            parser = ChinaParser(stsc_path)
            china_data = parser.parse_stsc()

            return china_data

        except Exception as e:
            print(f"Error parsing China data: {e}")
            return []


def main():
    """主函數"""
    # 設定路徑
    current_dir = Path(__file__).parent.parent
    data_dir = current_dir
    output_dir = current_dir / "output"

    # 創建並執行系統
    system = CosmeticComplianceSystem(data_dir, output_dir)

    try:
        system.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
