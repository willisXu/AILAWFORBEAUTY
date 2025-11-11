"""
Multi-Format Report Generator
多格式報表生成器 - 支援 CSV, JSON, PDF
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class CSVReporter:
    """CSV 報表生成器"""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, data: List[Dict]):
        """
        生成 CSV 報表

        Args:
            data: 資料列表
        """
        df = pd.DataFrame(data)
        df.to_csv(self.output_path, index=False, encoding='utf-8-sig')
        print(f"CSV report generated: {self.output_path}")


class JSONReporter:
    """JSON 報表生成器"""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, data: List[Dict], pretty: bool = True):
        """
        生成 JSON 報表

        Args:
            data: 資料列表
            pretty: 是否美化格式
        """
        with open(self.output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)

        print(f"JSON report generated: {self.output_path}")

    def generate_structured(self, data: Dict):
        """
        生成結構化 JSON (包含元數據)

        Args:
            data: 包含元數據的字典
        """
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'total_records': len(data.get('ingredients', []))
            },
            'data': data
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Structured JSON report generated: {self.output_path}")


class PDFReporter:
    """PDF 報表生成器 (摘要報告)"""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_summary(self, statistics: Dict, conflicts: List[Dict],
                        differences: List[Dict]):
        """
        生成 PDF 摘要報告

        Args:
            statistics: 統計資訊
            conflicts: 衝突列表
            differences: 差異列表

        Note: 此為簡化版本,實際實作可使用 reportlab 或 fpdf
        """
        # 由於 PDF 生成需要額外的庫,這裡先創建文字版摘要
        # 實際應用中可以使用 reportlab 或 matplotlib 生成圖表

        summary_text = self._create_text_summary(statistics, conflicts, differences)

        # 暫時輸出為文字檔 (可擴展為 PDF)
        text_output = self.output_path.with_suffix('.txt')
        with open(text_output, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        print(f"Summary report generated: {text_output}")
        print("Note: For PDF generation, please install reportlab or fpdf library")

    def _create_text_summary(self, statistics: Dict, conflicts: List[Dict],
                            differences: List[Dict]) -> str:
        """
        創建文字摘要

        Args:
            statistics: 統計資訊
            conflicts: 衝突列表
            differences: 差異列表

        Returns:
            摘要文字
        """
        lines = []
        lines.append("=" * 80)
        lines.append("GLOBAL COSMETIC REGULATION COMPLIANCE REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 總體統計
        lines.append("OVERALL STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Total Ingredients: {statistics.get('total_ingredients', 0)}")
        lines.append(f"With CAS Number: {statistics.get('with_cas', 0)}")
        lines.append(f"Conflicts Detected: {statistics.get('conflicts', 0)}")
        lines.append(f"Limit Differences: {statistics.get('limit_differences', 0)}")
        lines.append("")

        # 各地區統計
        lines.append("BY REGION")
        lines.append("-" * 80)
        by_region = statistics.get('by_region', {})
        for region, count in by_region.items():
            lines.append(f"{region:15} : {count:5} ingredients")
        lines.append("")

        # 衝突摘要
        if conflicts:
            lines.append("CONFLICTS SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Total conflicts: {len(conflicts)}")
            lines.append("")
            lines.append("Top 10 conflicts:")
            for i, conflict in enumerate(conflicts[:10], 1):
                ingredient = conflict.get('ingredient', 'Unknown')
                cas = conflict.get('cas_number', 'N/A')
                conflict_desc = conflict.get('conflicts', [])
                lines.append(f"{i}. {ingredient} (CAS: {cas})")
                for desc in conflict_desc[:2]:  # 只顯示前兩個衝突
                    lines.append(f"   - {desc}")
            lines.append("")

        # 限量差異
        if differences:
            lines.append("LIMIT DIFFERENCES SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Total ingredients with different limits: {len(differences)}")
            lines.append("")
            lines.append("Top 10 examples:")
            for i, diff in enumerate(differences[:10], 1):
                ingredient = diff.get('ingredient', 'Unknown')
                limits = diff.get('limits', {})
                lines.append(f"{i}. {ingredient}")
                for region, limit in limits.items():
                    lines.append(f"   {region:10} : {limit}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)


class ReportManager:
    """報表管理器 - 統一管理所有格式的報表生成"""

    def __init__(self, output_dir: Path):
        """
        初始化報表管理器

        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self, data: List[Dict], statistics: Dict,
                           conflicts: List[Dict], differences: List[Dict]):
        """
        生成所有格式的報表

        Args:
            data: 統一成分資料
            statistics: 統計資訊
            conflicts: 衝突列表
            differences: 差異列表
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Excel 報表
        from .excel_reporter import ExcelReporter
        excel_path = self.output_dir / 'excel' / f'compliance_report_{timestamp}.xlsx'
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        excel_reporter = ExcelReporter(excel_path)
        excel_reporter.generate_compliance_report(data, statistics, conflicts, differences)

        # CSV 報表
        csv_path = self.output_dir / 'csv' / f'compliance_data_{timestamp}.csv'
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_reporter = CSVReporter(csv_path)
        csv_reporter.generate(data)

        # JSON 報表
        json_path = self.output_dir / 'json' / f'compliance_data_{timestamp}.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_reporter = JSONReporter(json_path)

        structured_data = {
            'ingredients': data,
            'statistics': statistics,
            'conflicts': conflicts,
            'differences': differences
        }
        json_reporter.generate_structured(structured_data)

        # PDF 摘要
        pdf_path = self.output_dir / 'pdf' / f'compliance_summary_{timestamp}.pdf'
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_reporter = PDFReporter(pdf_path)
        pdf_reporter.generate_summary(statistics, conflicts, differences)

        print("\n" + "=" * 80)
        print("All reports generated successfully!")
        print("=" * 80)
        print(f"Excel: {excel_path}")
        print(f"CSV:   {csv_path}")
        print(f"JSON:  {json_path}")
        print(f"PDF:   {pdf_path.with_suffix('.txt')}")
        print("=" * 80)
