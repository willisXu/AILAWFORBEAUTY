"""
JP (Japan) PDF Extractor

從日本化妝品標準PDF中提取數據。

數據來源：
- 化粧品基準 / Standards for Cosmetics
- MHLW (Ministry of Health, Labour and Welfare)
- 附件2-1: Standards for Cosmetic Products

包含：
- Negative List (禁用物質)
- Positive List (準用物質)
- 使用基準 (使用標準)
"""

from pathlib import Path
from typing import Dict, List, Any
from .base_extractor import BasePDFExtractor


class JPExtractor(BasePDFExtractor):
    """日本法規PDF提取器"""

    def __init__(self):
        super().__init__("JP")

    def extract(self) -> Dict[str, Any]:
        """
        提取JP法規數據

        Returns:
            提取的數據字典
        """
        # 查找PDF文件
        pdf_files = self.find_pdf_files("*附件2-1*Standards*.pdf")

        if not pdf_files:
            pdf_files = self.find_pdf_files()

        if not pdf_files:
            print(f"❌ 未找到PDF文件: {self.raw_data_dir}")
            return {}

        pdf_path = pdf_files[0]
        print(f"📄 處理文件: {pdf_path.name}")

        try:
            # 使用PyPDF2提取文本
            texts = self.extract_text_pypdf2(pdf_path, start_page=0, end_page=50)

            # 查找各類表格
            print("\n掃描PDF內容...")

            # 查找ネガティブリスト（禁用清單）
            prohibited_page = None
            for i, text in enumerate(texts):
                if "ネガティブリスト" in text or "配合してはならない" in text:
                    prohibited_page = i
                    print(f"   ✓ 找到禁用清單於第 {i + 1} 頁")
                    break

            # 查找ポジティブリスト（準用清單）
            positive_page = None
            for i, text in enumerate(texts):
                if "ポジティブリスト" in text or "配合できる" in text:
                    positive_page = i
                    print(f"   ✓ 找到準用清單於第 {i + 1} 頁")
                    break

            all_data = {
                "prohibited": {
                    "name": "ネガティブリスト (Negative List)",
                    "description": "配合してはならない成分",
                    "start_page": prohibited_page + 1 if prohibited_page else None,
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
                },
                "restricted": {
                    "name": "配合制限のある成分 (Restricted Ingredients)",
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
                },
                "positive_list": {
                    "name": "ポジティブリスト (Positive List)",
                    "description": "配合できる成分",
                    "start_page": positive_page + 1 if positive_page else None,
                    "includes": ["防腐劑", "UV過濾劑", "著色劑"],
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
                }
            }

            total_count = 0

        except Exception as e:
            print(f"❌ 提取失敗: {str(e)}")
            all_data = {}
            total_count = 0

        # 生成輸出
        output = {
            "jurisdiction": "JP",
            "source": "MHLW - Ministry of Health, Labour and Welfare",
            "source_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/",
            "regulation": "化粧品基準 / Standards for Cosmetics",
            "pdf_path": str(pdf_path),
            "metadata": self.create_metadata(
                total_ingredients=total_count,
                source="MHLW - Ministry of Health, Labour and Welfare",
                regulation="化粧品基準 / Standards for Cosmetics",
                published_at="2000-09-29",
                effective_date="2001-04-01"
            ),
            "categories": all_data
        }

        # 保存結果
        self.save_json(output, "extracted_latest.json")

        return output


if __name__ == "__main__":
    extractor = JPExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
