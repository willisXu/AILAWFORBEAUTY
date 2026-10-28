"""
CN (China) PDF Extractor

從中國《化妝品安全技術規範》(2015年版) PDF中提取法規數據。

數據來源：
- 化妝品安全技術規範（2015年版）
- 包含：1388項禁用組分、47項限用組分、310項準用組分

表格結構：
- 表2-1: 化妝品禁用組分 (1388項)
- 表2-2: 化妝品限用組分 (47項)
- 表3-1: 準用防腐劑 (51項)
- 表3-2: 準用防曬劑 (27項)
- 表3-3: 準用著色劑 (157項)
- 表3-4: 準用染髮劑 (75項)
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_extractor import BasePDFExtractor


# The STSC tables appear in the PDF in this order; each restarts its 序號 at 1.
# The prohibited-table sweep in extract_prohibited_table() captures all of them,
# so the merged list is split back apart at the serial-number resets.
MERGED_TABLE_ORDER = [
    ("prohibited", "表2-1 化妝品禁用組分", 1388),
    ("prohibited", "表2-2 化妝品禁用植（動）物組分", 98),
    ("restricted", "表3 化妝品限用組分", 47),
    ("preservatives", "表4 化妝品準用防腐劑", 51),
    ("uv_filters", "表5 化妝品準用防曬劑", 27),
    ("colorants", "表6 化妝品準用著色劑", 157),
    ("hair_dyes", "表7 化妝品準用染髮劑", 75),
]


def _serial_number(ingredient: Dict[str, Any]) -> Optional[int]:
    try:
        return int(str(ingredient.get("serial_number", "")).strip())
    except ValueError:
        return None


def split_merged_tables(tables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Split a merged CN "prohibited" ingredient list into the STSC tables.

    Only acts when the prohibited table is populated and every other table is
    empty. Returns the tables dict unchanged (with a status marker) if the
    serial-number resets do not line up with the seven expected tables.
    """
    prohibited = tables.get("prohibited") or {}
    ingredients = prohibited.get("ingredients") or []
    others_empty = all(
        not (tables.get(key) or {}).get("ingredients")
        for key, _, _ in MERGED_TABLE_ORDER if key != "prohibited"
    )
    if not ingredients or not others_empty:
        return tables

    segments: List[List[Dict[str, Any]]] = [[]]
    previous = None
    for ingredient in ingredients:
        number = _serial_number(ingredient)
        if number is not None and previous is not None and number < previous:
            segments.append([])
        segments[-1].append(ingredient)
        if number is not None:
            previous = number

    if len(segments) != len(MERGED_TABLE_ORDER):
        print(f"   ⚠️  序號重置 {len(segments)} 段，與預期的 {len(MERGED_TABLE_ORDER)} 張表不符，保持合併狀態")
        prohibited["extraction_status"] = "merged_tables_unsplit"
        return tables

    for segment, (_, label, expected) in zip(segments, MERGED_TABLE_ORDER):
        # Row loss during extraction is tolerated; gaining rows is not
        if not (0.8 * expected <= len(segment) <= expected + 5):
            print(f"   ⚠️  {label}: 找到 {len(segment)} 條，預期約 {expected} 條，保持合併狀態")
            prohibited["extraction_status"] = "merged_tables_unsplit"
            return tables

    split: Dict[str, List[Dict[str, Any]]] = {}
    for segment, (key, label, _) in zip(segments, MERGED_TABLE_ORDER):
        for ingredient in segment:
            ingredient["table"] = key
            ingredient["source_table"] = label
        split.setdefault(key, []).extend(segment)

    for key, _, _ in MERGED_TABLE_ORDER:
        table = dict(tables.get(key) or {})
        table.pop("note", None)
        table["ingredients"] = split.get(key, [])
        table["ingredients_count"] = len(table["ingredients"])
        table["extraction_status"] = "completed"
        tables[key] = table

    print("   ✓ 已依序號重置將合併表格拆分為 " + ", ".join(
        f"{key}={len(split.get(key, []))}" for key in dict.fromkeys(k for k, _, _ in MERGED_TABLE_ORDER)))
    return tables


class CNExtractor(BasePDFExtractor):
    """中國法規PDF提取器"""

    def __init__(self):
        super().__init__("CN")

        # 表格配置
        self.table_configs = {
            "prohibited": {
                "name": "化妝品禁用組分",
                "table_number": "表2-1",
                "expected_count": 1388,
                "keywords": ["化妆品禁用组分", "表2-1", "序号", "化妆品原料名称"],
                "columns": ["序號", "化妝品原料名稱", "使用目的/理由"]
            },
            "restricted": {
                "name": "化妝品限用組分",
                "table_number": "表2-2",
                "expected_count": 47,
                "keywords": ["化妆品限用组分", "表2-2"],
                "columns": ["序號", "化妝品原料名稱", "使用範圍/限用條件", "最大允許濃度"]
            },
            "preservatives": {
                "name": "準用防腐劑",
                "table_number": "表3-1",
                "expected_count": 51,
                "keywords": ["准用防腐剂", "表3-1"],
                "columns": ["序號", "防腐劑名稱", "最大允許濃度", "使用範圍/限用條件"]
            },
            "uv_filters": {
                "name": "準用防曬劑",
                "table_number": "表3-2",
                "expected_count": 27,
                "keywords": ["准用防晒剂", "表3-2"],
                "columns": ["序號", "防曬劑名稱", "最大允許濃度"]
            },
            "colorants": {
                "name": "準用著色劑",
                "table_number": "表3-3",
                "expected_count": 157,
                "keywords": ["准用着色剂", "表3-3"],
                "columns": ["序號", "著色劑名稱", "色素索引號", "使用範圍"]
            },
            "hair_dyes": {
                "name": "準用染髮劑",
                "table_number": "表3-4",
                "expected_count": 75,
                "keywords": ["准用染发剂", "表3-4"],
                "columns": ["序號", "染髮劑名稱", "最大允許濃度"]
            }
        }

    def extract(self) -> Dict[str, Any]:
        """
        提取CN法規數據

        Returns:
            提取的數據字典
        """
        # 查找PDF文件
        pdf_files = self.find_pdf_files()

        if not pdf_files:
            print(f"❌ 未找到PDF文件: {self.raw_data_dir}")
            return {}

        pdf_path = pdf_files[0]  # 使用第一個PDF
        print(f"📄 處理文件: {pdf_path.name}")

        # 提取所有表格數據
        all_data = {}

        try:
            # 使用PyPDF2提取文本（pdfplumber在環境中不可用）
            print("\n使用PyPDF2提取文本...")
            texts = self.extract_text_pypdf2(pdf_path, start_page=0, end_page=100)

            # 提取各表格
            all_data["prohibited"] = self.extract_prohibited_table(texts)
            all_data["restricted"] = self.extract_restricted_table(texts)
            all_data["preservatives"] = self.extract_preservatives_table(texts)
            all_data["uv_filters"] = self.extract_uv_filters_table(texts)
            all_data["colorants"] = self.extract_colorants_table(texts)
            all_data["hair_dyes"] = {
                "table_name": self.table_configs["hair_dyes"]["name"],
                "table_number": self.table_configs["hair_dyes"]["table_number"],
                "expected_count": self.table_configs["hair_dyes"]["expected_count"],
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending",
            }

            all_data = split_merged_tables(all_data)

            # 計算總數
            total_count = sum(
                data.get("ingredients_count", 0)
                for data in all_data.values()
                if isinstance(data, dict)
            )

            print(f"\n✓ 提取完成，共 {total_count} 條記錄")

        except Exception as e:
            print(f"❌ 提取失敗: {str(e)}")
            import traceback
            traceback.print_exc()

        # 生成輸出
        output = {
            "jurisdiction": "CN",
            "source": "化妝品安全技術規範（2015年版）",
            "source_url": "https://www.nmpa.gov.cn/directory/web/nmpa/images/MjAxNcTqtdoyNji6xbmruOa4vbz+LnBkZg==.pdf",
            "pdf_path": str(pdf_path),
            "metadata": self.create_metadata(
                total_ingredients=sum(
                    data.get("ingredients_count", 0)
                    for data in all_data.values()
                    if isinstance(data, dict)
                ),
                source="NMPA - 化妝品安全技術規範（2015年版）",
                regulation="Safety and Technical Standards for Cosmetics (2015 Edition)",
                published_at="2015-12-23",
                effective_date="2016-12-01"
            ),
            "tables": all_data
        }

        # 保存結果
        self.save_json(output, "extracted_latest.json")

        return output

    def extract_prohibited_table(self, texts: List[str]) -> Dict[str, Any]:
        """提取禁用組分表"""
        print("\n提取表2-1: 化妝品禁用組分...")

        config = self.table_configs["prohibited"]

        # 查找表格開始頁
        start_page = self.find_table_start(texts, config["keywords"])

        if start_page is None:
            print(f"⚠️  未找到 {config['name']} 表格")
            return {
                "table_name": config["name"],
                "table_number": config["table_number"],
                "ingredients_count": 0,
                "ingredients": [],
                "note": "PDF結構複雜，需要在支持pdfplumber的環境中提取"
            }

        print(f"   表格開始於第 {start_page + 1} 頁")

        # 使用pdfplumber提取表格
        try:
            import pdfplumber

            pdf_files = self.find_pdf_files()
            pdf_path = pdf_files[0]

            ingredients = []

            with pdfplumber.open(str(pdf_path)) as pdf:
                # 從第12頁開始到第250頁（估計表格範圍）
                for page_num in range(11, min(250, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # 檢查是否是目標表格（有序號、中文名稱、英文名稱列）
                        header = table[0]
                        if not (len(header) >= 3 and ('序号' in str(header[0]) or '序號' in str(header[0]))):
                            continue

                        # 提取數據行
                        for row in table[1:]:
                            if len(row) < 3:
                                continue

                            serial_number = self.clean_text(str(row[0])) if row[0] else ""
                            cn_name = self.clean_text(str(row[1])) if row[1] else ""
                            en_name = self.clean_text(str(row[2])) if row[2] else ""

                            # 跳過空行或表頭重複
                            if not cn_name or cn_name in ['中文名称', '中文名稱']:
                                continue

                            # 提取CAS號
                            cas_no = self.extract_cas_number(en_name)

                            ingredient = {
                                "serial_number": serial_number,
                                "ingredient_name_cn": cn_name,
                                "ingredient_name_en": en_name,
                                "cas_no": cas_no,
                                "table": "prohibited"
                            }

                            ingredients.append(ingredient)

                    # 進度顯示
                    if page_num % 20 == 0:
                        print(f"   已掃描到第 {page_num + 1} 頁，找到 {len(ingredients)} 條記錄...")

            print(f"   ✓ 提取完成：{len(ingredients)} 條記錄")

            return {
                "table_name": config["name"],
                "table_number": config["table_number"],
                "expected_count": config["expected_count"],
                "ingredients_count": len(ingredients),
                "ingredients": ingredients,
                "extraction_status": "completed"
            }

        except ImportError:
            print("   ⚠️  pdfplumber未安裝，僅返回結構信息")
            return {
                "table_name": config["name"],
                "table_number": config["table_number"],
                "expected_count": config["expected_count"],
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "pending",
                "note": "需要安裝pdfplumber: pip install pdfplumber"
            }
        except Exception as e:
            print(f"   ❌ 提取失敗: {str(e)}")
            return {
                "table_name": config["name"],
                "table_number": config["table_number"],
                "expected_count": config["expected_count"],
                "ingredients_count": 0,
                "ingredients": [],
                "extraction_status": "error",
                "error": str(e)
            }

    def extract_restricted_table(self, texts: List[str]) -> Dict[str, Any]:
        """提取限用組分表"""
        print("\n提取表2-2: 化妝品限用組分...")

        config = self.table_configs["restricted"]

        return {
            "table_name": config["name"],
            "table_number": config["table_number"],
            "expected_count": config["expected_count"],
            "ingredients_count": 0,
            "ingredients": [],
            "extraction_status": "pending",
            "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
        }

    def extract_preservatives_table(self, texts: List[str]) -> Dict[str, Any]:
        """提取準用防腐劑表"""
        print("\n提取表3-1: 準用防腐劑...")

        config = self.table_configs["preservatives"]

        return {
            "table_name": config["name"],
            "table_number": config["table_number"],
            "expected_count": config["expected_count"],
            "ingredients_count": 0,
            "ingredients": [],
            "extraction_status": "pending",
            "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
        }

    def extract_uv_filters_table(self, texts: List[str]) -> Dict[str, Any]:
        """提取準用防曬劑表"""
        print("\n提取表3-2: 準用防曬劑...")

        config = self.table_configs["uv_filters"]

        return {
            "table_name": config["name"],
            "table_number": config["table_number"],
            "expected_count": config["expected_count"],
            "ingredients_count": 0,
            "ingredients": [],
            "extraction_status": "pending",
            "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
        }

    def extract_colorants_table(self, texts: List[str]) -> Dict[str, Any]:
        """提取準用著色劑表"""
        print("\n提取表3-3: 準用著色劑...")

        config = self.table_configs["colorants"]

        return {
            "table_name": config["name"],
            "table_number": config["table_number"],
            "expected_count": config["expected_count"],
            "ingredients_count": 0,
            "ingredients": [],
            "extraction_status": "pending",
            "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
        }


if __name__ == "__main__":
    extractor = CNExtractor()
    result = extractor.run()
    print(f"\n提取結果摘要:")
    print(f"總記錄數: {result['metadata']['total_ingredients']}")
