#!/usr/bin/env python3
"""
Extract Regulations from PDFs

從各轄區的PDF法規文件中提取化妝品成分數據。

使用方法:
    # 提取所有轄區
    python scripts/extract_regulations_from_pdfs.py

    # 提取特定轄區
    python scripts/extract_regulations_from_pdfs.py --jurisdictions CN EU

    # 僅列出PDF文件
    python scripts/extract_regulations_from_pdfs.py --list-only

依賴:
    pip install pdfplumber PyPDF2

注意:
    - 在支持pdfplumber的環境中運行可獲得完整表格提取
    - 在受限環境中僅提取文本和結構信息
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extractors import (
    CNExtractor,
    EUExtractor,
    JPExtractor,
    CAExtractor,
)


EXTRACTORS = {
    "CN": CNExtractor,
    "EU": EUExtractor,
    "JP": JPExtractor,
    "CA": CAExtractor,
}


def list_pdf_files():
    """列出所有PDF文件"""
    print("\n" + "=" * 80)
    print("掃描PDF法規文件")
    print("=" * 80 + "\n")

    raw_data_dir = Path("data/raw")

    for jurisdiction in ["EU", "ASEAN", "JP", "CN", "CA"]:
        jur_dir = raw_data_dir / jurisdiction
        print(f"\n{jurisdiction}:")

        if not jur_dir.exists():
            print(f"  ⚠️  目錄不存在: {jur_dir}")
            continue

        # 查找PDF
        pdf_files = list(jur_dir.glob("*.pdf"))
        pdfs_subdir = jur_dir / "pdfs"
        if pdfs_subdir.exists():
            pdf_files.extend(pdfs_subdir.glob("*.pdf"))

        if not pdf_files:
            print(f"  ⚠️  未找到PDF文件")
        else:
            for pdf in sorted(pdf_files):
                size_mb = pdf.stat().st_size / (1024 * 1024)
                print(f"  📄 {pdf.name} ({size_mb:.1f} MB)")


def extract_jurisdiction(jurisdiction: str) -> dict:
    """
    提取單個轄區的數據

    Args:
        jurisdiction: 轄區代碼

    Returns:
        提取結果
    """
    if jurisdiction not in EXTRACTORS:
        print(f"❌ 不支持的轄區: {jurisdiction}")
        print(f"   支持的轄區: {', '.join(EXTRACTORS.keys())}")
        return {}

    extractor_class = EXTRACTORS[jurisdiction]
    extractor = extractor_class()

    try:
        result = extractor.run()
        return result
    except Exception as e:
        print(f"❌ {jurisdiction} 提取失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="從PDF法規文件中提取化妝品成分數據",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 提取所有轄區
  python scripts/extract_regulations_from_pdfs.py

  # 提取中國法規
  python scripts/extract_regulations_from_pdfs.py --jurisdictions CN

  # 提取多個轄區
  python scripts/extract_regulations_from_pdfs.py --jurisdictions CN EU JP

  # 僅列出PDF文件
  python scripts/extract_regulations_from_pdfs.py --list-only

環境要求:
  在本地環境或CI中運行以獲得完整功能:
  pip install pdfplumber PyPDF2
        """
    )

    parser.add_argument(
        "--jurisdictions",
        nargs="+",
        choices=list(EXTRACTORS.keys()),
        help="要提取的轄區（不指定則提取全部）"
    )

    parser.add_argument(
        "--list-only",
        action="store_true",
        help="僅列出PDF文件，不執行提取"
    )

    args = parser.parse_args()

    # 檢查依賴
    print("\n檢查依賴...")
    try:
        import PyPDF2
        print("✓ PyPDF2 已安裝")
    except ImportError:
        print("⚠️  PyPDF2 未安裝 (pip install PyPDF2)")

    try:
        import pdfplumber
        print("✓ pdfplumber 已安裝（可提取完整表格）")
    except ImportError:
        print("⚠️  pdfplumber 未安裝（僅能提取基本信息）")
        print("   建議安裝: pip install pdfplumber")

    # 僅列出文件
    if args.list_only:
        list_pdf_files()
        return

    # 確定要提取的轄區
    jurisdictions = args.jurisdictions if args.jurisdictions else list(EXTRACTORS.keys())

    print(f"\n{'='*80}")
    print(f"準備提取 {len(jurisdictions)} 個轄區: {', '.join(jurisdictions)}")
    print(f"{'='*80}\n")

    # 執行提取
    results = {}
    for jurisdiction in jurisdictions:
        result = extract_jurisdiction(jurisdiction)
        results[jurisdiction] = result

    # 生成摘要
    print(f"\n{'='*80}")
    print("提取摘要")
    print(f"{'='*80}\n")

    total_ingredients = 0
    for jurisdiction, result in results.items():
        if result and "metadata" in result:
            count = result["metadata"].get("total_ingredients", 0)
            total_ingredients += count
            status = "✓" if count > 0 else "⚠️"
            print(f"{status} {jurisdiction}: {count} 條記錄")
        else:
            print(f"❌ {jurisdiction}: 提取失敗")

    print(f"\n總計: {total_ingredients} 條記錄")
    print(f"\n{'='*80}")

    # 提示後續步驟
    if total_ingredients == 0:
        print("\n💡 提示:")
        print("   當前環境無法提取完整數據（需要pdfplumber支持）")
        print("   請在本地環境或GitHub Actions中執行:")
        print("   1. pip install pdfplumber")
        print("   2. python scripts/extract_regulations_from_pdfs.py")
        print("   3. 提取完成後將data/extracted/目錄推送到repository")


if __name__ == "__main__":
    main()
