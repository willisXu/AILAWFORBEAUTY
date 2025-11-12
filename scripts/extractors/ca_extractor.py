"""
CA (Canada) PDF Extractor

從加拿大Cosmetic Ingredient Hotlist PDF中提取數據。

數據來源：
- Health Canada - Cosmetic Ingredient Hotlist
- 附件4: Cosmetic Ingredient Hotlist

包含：
- Prohibited Ingredients (禁用成分)
- Restricted Ingredients (限用成分)
"""

from pathlib import Path
from typing import Dict, List, Any
from .base_extractor import BasePDFExtractor


class CAExtractor(BasePDFExtractor):
    """加拿大法規PDF提取器"""

    def __init__(self):
        super().__init__("CA")

    def extract(self) -> Dict[str, Any]:
        """
        提取CA法規數據

        Returns:
            提取的數據字典
        """
        # 查找PDF文件
        pdf_files = self.find_pdf_files("*附件4*Hotlist*.pdf")

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

            # 查找表格
            print("\n掃描PDF內容...")

            # 查找Prohibited
            prohibited_page = None
            for i, text in enumerate(texts):
                if "Prohibited" in text and ("Ingredient" in text or "CAS" in text):
                    prohibited_page = i
                    print(f"   ✓ 找到Prohibited清單於第 {i + 1} 頁")
                    break

            # 查找Restricted
            restricted_page = None
            for i, text in enumerate(texts):
                if "Restricted" in text and ("Ingredient" in text or "CAS" in text):
                    restricted_page = i
                    print(f"   ✓ 找到Restricted清單於第 {i + 1} 頁")
                    break

            all_data = {
                "prohibited": {
                    "name": "Prohibited Ingredients",
                    "start_page": prohibited_page + 1 if prohibited_page else None,
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
                },
                "restricted": {
                    "name": "Restricted Ingredients",
                    "start_page": restricted_page + 1 if restricted_page else None,
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
            "jurisdiction": "CA",
            "source": "Health Canada - Cosmetic Ingredient Hotlist",
            "source_url": "https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics/cosmetic-ingredient-hotlist-prohibited-restricted-ingredients.html",
            "regulation": "Cosmetic Ingredient Hotlist",
            "pdf_path": str(pdf_path),
            "metadata": self.create_metadata(
                total_ingredients=total_count,
                source="Health Canada - Cosmetic Ingredient Hotlist",
                regulation="Cosmetic Ingredient Hotlist",
                published_at="2025-02",
                effective_date="2025-02-28"
            ),
            "categories": all_data
        }

        # 保存結果
        self.save_json(output, "extracted_latest.json")

        return output


if __name__ == "__main__":
    extractor = CAExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
