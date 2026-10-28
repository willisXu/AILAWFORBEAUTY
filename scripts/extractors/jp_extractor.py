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
            texts = self.extract_text_pypdf2(pdf_path, start_page=0, end_page=100)

            # 查找各類表格
            print("\n掃描PDF內容...")

            # 查找Appendix 1（禁用清單）
            prohibited_page = None
            for i, text in enumerate(texts):
                if "Appendix 1" in text or ("ネガティブリスト" in text or "配合してはならない" in text):
                    prohibited_page = i
                    print(f"   ✓ 找到禁用清單（Appendix 1）於第 {i + 1} 頁")
                    break

            # 查找Appendix 2（限用清單）
            restricted_page = None
            for i, text in enumerate(texts):
                if "Appendix 2" in text:
                    restricted_page = i
                    print(f"   ✓ 找到限用清單（Appendix 2）於第 {i + 1} 頁")
                    break

            # 查找Appendix 3（防腐劑、著色劑）或Appendix 4（UV過濾劑）
            positive_page = None
            for i, text in enumerate(texts):
                if "Appendix 3" in text or "Appendix 4" in text or ("ポジティブリスト" in text or "配合できる" in text):
                    if positive_page is None:  # 只記錄第一個
                        positive_page = i
                        print(f"   ✓ 找到準用清單（Appendix 3/4）於第 {i + 1} 頁")
                        break

            # 提取實際表格數據
            all_data = {}

            # 提取禁用清單
            if prohibited_page is not None:
                all_data["prohibited"] = self.extract_negative_list(pdf_path, prohibited_page)
            else:
                all_data["prohibited"] = {
                    "name": "Appendix 1 - Negative List",
                    "description": "Prohibited ingredients",
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "not_found"
                }

            # 提取限用成分
            if restricted_page is not None:
                all_data["restricted"] = self.extract_restricted_list(pdf_path, restricted_page)
            else:
                all_data["restricted"] = {
                    "name": "Appendix 2 - Restricted Ingredients",
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "not_found"
                }

            # 提取準用清單
            if positive_page is not None:
                all_data["positive_list"] = self.extract_positive_list(pdf_path, positive_page)
            else:
                all_data["positive_list"] = {
                    "name": "Appendix 3/4 - Positive List",
                    "description": "Allowed ingredients (preservatives, UV filters, colorants)",
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

    def extract_negative_list(self, pdf_path: Path, start_page: int) -> Dict[str, Any]:
        """提取禁用清單 (Negative List)"""
        print("\n提取ネガティブリスト...")

        try:
            import pdfplumber

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 從找到的起始頁開始掃描（通常禁用清單不會太長）
                for page_num in range(start_page, min(start_page + 30, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        for row in table:
                            if len(row) < 2:
                                continue

                            # 跳過表頭
                            first_col = str(row[0] or "").strip()
                            if any(keyword in first_col for keyword in ["番号", "成分", "物質", "No"]):
                                continue

                            # 提取數據
                            ref_number = self.clean_text(str(row[0])) if row[0] else ""
                            ingredient_name = self.clean_text(str(row[1])) if len(row) > 1 and row[1] else ""

                            # 跳過空行
                            if not ingredient_name or not ref_number:
                                continue

                            # 提取CAS號
                            cas_no = None
                            if len(row) > 2 and row[2]:
                                cas_text = self.clean_text(str(row[2]))
                                cas_no = self.extract_cas_number(cas_text)

                            ingredient = {
                                "reference_number": ref_number,
                                "ingredient_name": ingredient_name,
                                "cas_no": cas_no,
                                "list_type": "negative"
                            }

                            ingredients.append(ingredient)

                    # 進度顯示
                    if (page_num - start_page) % 5 == 0:
                        print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "name": "ネガティブリスト (Negative List)",
                "description": "配合してはならない成分",
                "start_page": start_page + 1,
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝")
            return {
                "name": "ネガティブリスト (Negative List)",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending",
                "note": "需要安裝pdfplumber"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "name": "ネガティブリスト (Negative List)",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }

    def extract_restricted_list(self, pdf_path: Path, start_page: int) -> Dict[str, Any]:
        """提取限用成分 (Appendix 2)"""
        print("\n提取Appendix 2: Restricted Ingredients...")

        try:
            import pdfplumber

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 掃描Appendix 2（通常包含兩個部分：全部化妝品的限用成分 + 按類型限用的成分）
                for page_num in range(start_page, min(start_page + 5, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        for row in table:
                            if len(row) < 2:
                                continue

                            # 跳過表頭
                            first_col = str(row[0] or "").strip()
                            if any(keyword in first_col.lower() for keyword in ["ingredient name", "maximum amount", "cosmetics"]):
                                continue

                            # 提取數據（第一列是成分名稱，第二列是最大量）
                            ingredient_name = self.clean_text(str(row[0])) if row[0] else ""
                            max_amount = self.clean_text(str(row[1])) if len(row) > 1 and row[1] else ""

                            # 跳過空行
                            if not ingredient_name or len(ingredient_name) < 3:
                                continue

                            # 提取CAS號
                            cas_no = self.extract_cas_number(ingredient_name)

                            ingredient = {
                                "ingredient_name": ingredient_name,
                                "max_amount": max_amount,
                                "cas_no": cas_no,
                                "list_type": "restricted"
                            }

                            ingredients.append(ingredient)

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "name": "Appendix 2 - Restricted Ingredients",
                "description": "Ingredients with usage restrictions",
                "start_page": start_page + 1,
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝")
            return {
                "name": "Appendix 2 - Restricted Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "name": "Appendix 2 - Restricted Ingredients",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }

    def extract_positive_list(self, pdf_path: Path, start_page: int) -> Dict[str, Any]:
        """提取準用清單 (Positive List)"""
        print("\n提取ポジティブリスト...")

        try:
            import pdfplumber

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 掃描準用清單（可能包含防腐劑、UV過濾劑、著色劑等）
                for page_num in range(start_page, min(start_page + 50, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        for row in table:
                            if len(row) < 2:
                                continue

                            # 跳過表頭
                            first_col = str(row[0] or "").strip()
                            if any(keyword in first_col for keyword in ["番号", "成分", "物質", "名称"]):
                                continue

                            # 提取數據
                            ingredient_name = self.clean_text(str(row[0])) if row[0] else ""
                            usage = self.clean_text(str(row[1])) if len(row) > 1 and row[1] else ""

                            # 跳過空行
                            if not ingredient_name:
                                continue

                            # 提取CAS號
                            cas_no = self.extract_cas_number(ingredient_name)
                            if not cas_no and len(row) > 2:
                                cas_no = self.extract_cas_number(str(row[2]))

                            ingredient = {
                                "ingredient_name": ingredient_name,
                                "usage": usage,
                                "cas_no": cas_no,
                                "list_type": "positive"
                            }

                            ingredients.append(ingredient)

                    # 進度顯示
                    if (page_num - start_page) % 10 == 0:
                        print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "name": "ポジティブリスト (Positive List)",
                "description": "配合できる成分",
                "start_page": start_page + 1,
                "includes": ["防腐劑", "UV過濾劑", "著色劑"],
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝")
            return {
                "name": "ポジティブリスト (Positive List)",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "name": "ポジティブリスト (Positive List)",
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }


if __name__ == "__main__":
    extractor = JPExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
