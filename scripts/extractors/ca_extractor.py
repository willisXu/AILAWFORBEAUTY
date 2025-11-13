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

            # 提取實際表格數據
            all_data = {}

            # 提取禁用成分
            if prohibited_page is not None:
                all_data["prohibited"] = self.extract_prohibited(pdf_path, prohibited_page)
            else:
                all_data["prohibited"] = {
                    "name": "Prohibited Ingredients",
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "not_found"
                }

            # 提取限用成分
            if restricted_page is not None:
                all_data["restricted"] = self.extract_restricted(pdf_path, restricted_page)
            else:
                all_data["restricted"] = {
                    "name": "Restricted Ingredients",
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "not_found"
                }

            # 計算總數
            total_count = sum(
                data.get("ingredients_count", 0)
                for data in all_data.values()
                if isinstance(data, dict)
            )

        except Exception as e:
            print(f"❌ 提取失敗: {str(e)}")
            import traceback
            traceback.print_exc()
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

    def extract_prohibited(self, pdf_path: Path, start_page: int) -> Dict[str, Any]:
        """提取禁用成分"""
        print("\n提取Prohibited Ingredients...")

        try:
            import pdfplumber

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 掃描所有頁面（CA Hotlist可能很長）
                for page_num in range(start_page, len(pdf.pages)):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    # 如果沒有表格，檢查是否到了Restricted部分
                    page_text = page.extract_text()
                    if page_text and "Restricted" in page_text and page_num > start_page + 5:
                        break

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        for row in table:
                            if len(row) < 2:
                                continue

                            # 跳過表頭
                            first_col = str(row[0] or "").strip().lower()
                            if any(keyword in first_col for keyword in ["ingredient name", "cas", "nom de", "prohibited"]):
                                continue

                            # 提取數據（CA表格通常有：Ingredient Name, CAS Number, Restriction）
                            ingredient_name = self.clean_text(str(row[0])) if row[0] else ""
                            cas_no = self.clean_text(str(row[1])) if len(row) > 1 and row[1] else ""

                            # 跳過空行
                            if not ingredient_name or len(ingredient_name) < 3:
                                continue

                            # 清理CAS號
                            if not self.extract_cas_number(cas_no):
                                # 嘗試從成分名稱提取CAS號
                                extracted_cas = self.extract_cas_number(ingredient_name)
                                if extracted_cas:
                                    cas_no = extracted_cas
                                else:
                                    cas_no = cas_no  # 保留原始值

                            # 提取限制信息（如果有第三列）
                            restriction = ""
                            if len(row) > 2 and row[2]:
                                restriction = self.clean_text(str(row[2]))

                            ingredient = {
                                "ingredient_name": ingredient_name,
                                "cas_no": cas_no,
                                "restriction": restriction,
                                "status": "prohibited"
                            }

                            ingredients.append(ingredient)

                    # 進度顯示
                    if (page_num - start_page) % 20 == 0:
                        print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "name": "Prohibited Ingredients",
                "start_page": start_page + 1,
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝")
            return {
                "name": "Prohibited Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "name": "Prohibited Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }

    def extract_restricted(self, pdf_path: Path, start_page: int) -> Dict[str, Any]:
        """提取限用成分"""
        print("\n提取Restricted Ingredients...")

        try:
            import pdfplumber

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 從Restricted部分開始掃描到文件結束
                for page_num in range(start_page, len(pdf.pages)):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        for row in table:
                            if len(row) < 3:
                                continue

                            # 跳過表頭
                            first_col = str(row[0] or "").strip().lower()
                            if any(keyword in first_col for keyword in ["ingredient name", "cas", "nom de", "restricted"]):
                                continue

                            # 提取數據（CA Restricted表格：Ingredient Name, CAS, Restriction）
                            ingredient_name = self.clean_text(str(row[0])) if row[0] else ""
                            cas_no = self.clean_text(str(row[1])) if len(row) > 1 and row[1] else ""
                            restriction = self.clean_text(str(row[2])) if len(row) > 2 and row[2] else ""

                            # 跳過空行
                            if not ingredient_name or len(ingredient_name) < 3:
                                continue

                            # 清理CAS號
                            if not self.extract_cas_number(cas_no):
                                extracted_cas = self.extract_cas_number(ingredient_name)
                                if extracted_cas:
                                    cas_no = extracted_cas

                            ingredient = {
                                "ingredient_name": ingredient_name,
                                "cas_no": cas_no,
                                "restriction": restriction,
                                "status": "restricted"
                            }

                            ingredients.append(ingredient)

                    # 進度顯示
                    if (page_num - start_page) % 20 == 0:
                        print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "name": "Restricted Ingredients",
                "start_page": start_page + 1,
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝")
            return {
                "name": "Restricted Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "name": "Restricted Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }


if __name__ == "__main__":
    extractor = CAExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
