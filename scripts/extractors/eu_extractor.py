"""
EU (European Union) PDF Extractor

從歐盟化妝品法規PDF中提取數據。

數據來源：
- Regulation (EC) No 1223/2009
- 5個Annex PDF文件：
  * 附件1-1: LIST OF SUBSTANCES PROHIBITED (Annex II)
  * 附件1-2: LIST OF SUBSTANCES RESTRICTED (Annex III)
  * 附件1-3: LIST OF COLORANTS ALLOWED (Annex IV)
  * 附件1-4: LIST OF PRESERVATIVES ALLOWED (Annex V)
  * 附件1-5: LIST OF UV FILTERS ALLOWED (Annex VI)
"""

from pathlib import Path
from typing import Dict, List, Any
from .base_extractor import BasePDFExtractor


class EUExtractor(BasePDFExtractor):
    """歐盟法規PDF提取器"""

    def __init__(self):
        super().__init__("EU")

        # PDF文件映射
        self.pdf_mappings = {
            "prohibited": {
                "name": "Annex II - Prohibited Substances",
                "filename_pattern": "*附件1-1*PROHIBITED*.pdf",
                "keywords": ["Annex II", "PROHIBITED", "Reference number"],
            },
            "restricted": {
                "name": "Annex III - Restricted Substances",
                "filename_pattern": "*附件1-2*.pdf",
                "keywords": ["Annex III", "RESTRICTED", "Reference number"],
            },
            "colorants": {
                "name": "Annex IV - Colorants",
                "filename_pattern": "*附件1-3*COLORANTS*.pdf",
                "keywords": ["Annex IV", "COLORANTS", "Colour Index"],
            },
            "preservatives": {
                "name": "Annex V - Preservatives",
                "filename_pattern": "*附件1-4*PRESERVATIVES*.pdf",
                "keywords": ["Annex V", "PRESERVATIVES", "Reference number"],
            },
            "uv_filters": {
                "name": "Annex VI - UV Filters",
                "filename_pattern": "*附件1-5*UV*.pdf",
                "keywords": ["Annex VI", "UV", "Reference number"],
            }
        }

    def extract(self) -> Dict[str, Any]:
        """
        提取EU法規數據

        Returns:
            提取的數據字典
        """
        print(f"📁 掃描PDF文件...")

        all_data = {}
        total_count = 0

        for table_type, config in self.pdf_mappings.items():
            print(f"\n處理 {config['name']}...")

            # 查找對應的PDF
            pdf_files = list(self.raw_data_dir.glob(config["filename_pattern"]))

            if not pdf_files:
                print(f"   ⚠️  未找到文件: {config['filename_pattern']}")
                all_data[table_type] = {
                    "name": config["name"],
                    "status": "file_not_found",
                    "ingredients_count": 0,
                    "ingredients": []
                }
                continue

            pdf_path = pdf_files[0]
            print(f"   📄 {pdf_path.name}")

            # 提取表格數據
            data = self.extract_annex_table(pdf_path, config)
            all_data[table_type] = data
            total_count += data.get("ingredients_count", 0)

        # 生成輸出
        output = {
            "jurisdiction": "EU",
            "source": "European Commission - CosIng Database",
            "source_url": "https://ec.europa.eu/growth/tools-databases/cosing/",
            "regulation": "Regulation (EC) No 1223/2009",
            "metadata": self.create_metadata(
                total_ingredients=total_count,
                source="European Commission - CosIng Database",
                regulation="Regulation (EC) No 1223/2009",
                published_at="2024-04-04",
                effective_date="2024-04-24"
            ),
            "annexes": all_data
        }

        # 保存結果
        self.save_json(output, "extracted_latest.json")

        return output

    def extract_annex_table(self, pdf_path: Path, config: Dict) -> Dict[str, Any]:
        """
        提取單個Annex表格

        Args:
            pdf_path: PDF文件路徑
            config: 表格配置

        Returns:
            提取的數據
        """
        try:
            # 使用PyPDF2提取文本
            texts = self.extract_text_pypdf2(pdf_path)

            # 查找表格開始
            start_page = self.find_table_start(texts, config["keywords"])

            if start_page is None:
                print(f"   ⚠️  未找到表格開始標記")
                return {
                    "name": config["name"],
                    "pdf_file": pdf_path.name,
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
                }

            print(f"   ✓ 表格開始於第 {start_page + 1} 頁")

            # 使用pdfplumber提取表格數據
            try:
                import pdfplumber

                ingredients = []

                with pdfplumber.open(str(pdf_path)) as pdf:
                    # 從找到的起始頁開始掃描
                    for page_num in range(start_page, len(pdf.pages)):
                        page = pdf.pages[page_num]
                        tables = page.extract_tables()

                        for table in tables:
                            if not table or len(table) < 2:
                                continue

                            # EU表格通常有5列：Reference Number, Chemical name/INN, CAS Number, 等
                            for row in table:
                                if len(row) < 3:
                                    continue

                                # 跳過表頭行
                                first_col = str(row[0] or "").strip().lower()
                                if any(keyword in first_col for keyword in ["reference", "number", "substance"]):
                                    continue

                                # 提取數據
                                ref_number = self.clean_text(str(row[0])) if row[0] else ""

                                # 第二列通常是化學名稱或INN名稱
                                chemical_name = self.clean_text(str(row[1])) if row[1] else ""

                                # 第三列通常是CAS號或其他識別信息
                                cas_text = self.clean_text(str(row[2])) if len(row) > 2 and row[2] else ""

                                # 跳過空行
                                if not chemical_name or not ref_number:
                                    continue

                                # 提取CAS號
                                cas_no = self.extract_cas_number(cas_text)
                                if not cas_no and chemical_name:
                                    # 嘗試從化學名稱中提取CAS號
                                    cas_no = self.extract_cas_number(chemical_name)

                                # 提取其他限制信息（第4、5列）
                                restrictions = ""
                                conditions = ""
                                if len(row) > 3 and row[3]:
                                    restrictions = self.clean_text(str(row[3]))
                                if len(row) > 4 and row[4]:
                                    conditions = self.clean_text(str(row[4]))

                                ingredient = {
                                    "reference_number": ref_number,
                                    "chemical_name": chemical_name,
                                    "cas_no": cas_no,
                                    "restrictions": restrictions,
                                    "conditions": conditions,
                                    "annex": config["name"]
                                }

                                ingredients.append(ingredient)

                        # 進度顯示
                        if (page_num - start_page) % 10 == 0:
                            print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

                print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

                return {
                    "name": config["name"],
                    "pdf_file": pdf_path.name,
                    "pdf_path": str(pdf_path),
                    "table_start_page": start_page + 1,
                    "ingredients_count": len(ingredients),
                    "ingredients": ingredients,
                    "extraction_status": "completed"
                }

            except ImportError:
                print("   ⚠️  pdfplumber未安裝，僅返回結構信息")
                return {
                    "name": config["name"],
                    "pdf_file": pdf_path.name,
                    "pdf_path": str(pdf_path),
                    "table_start_page": start_page + 1,
                    "ingredients_count": 0,
                    "ingredients": [],
                    "extraction_status": "pending",
                    "note": "需要安裝pdfplumber: pip install pdfplumber"
                }

        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "name": config["name"],
                "pdf_file": pdf_path.name,
                "error": str(e),
                "ingredients_count": 0,
                "ingredients": []
            }


if __name__ == "__main__":
    extractor = EUExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
