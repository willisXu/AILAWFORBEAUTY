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

        # 由於環境限制，返回佔位符
        return {
            "table_name": config["name"],
            "table_number": config["table_number"],
            "expected_count": config["expected_count"],
            "ingredients_count": 0,
            "ingredients": [],
            "extraction_status": "pending",
            "note": "需要在本地環境或CI中使用pdfplumber提取完整表格數據"
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
