"""
Base PDF Extractor

PDF表格提取器基類，提供通用的PDF解析功能。
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class BasePDFExtractor(ABC):
    """PDF提取器基類"""

    def __init__(self, jurisdiction: str):
        """
        初始化提取器

        Args:
            jurisdiction: 轄區代碼 (EU, ASEAN, JP, CN, CA)
        """
        self.jurisdiction = jurisdiction
        self.raw_data_dir = Path("data/raw") / jurisdiction
        self.output_dir = Path("data/extracted") / jurisdiction
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def find_pdf_files(self, pattern: str = "*.pdf") -> List[Path]:
        """
        查找PDF文件

        Args:
            pattern: 文件名模式

        Returns:
            PDF文件路徑列表
        """
        pdf_files = []

        # 在主目錄查找
        pdf_files.extend(self.raw_data_dir.glob(pattern))

        # 在pdfs子目錄查找
        pdfs_dir = self.raw_data_dir / "pdfs"
        if pdfs_dir.exists():
            pdf_files.extend(pdfs_dir.glob(pattern))

        return sorted(pdf_files)

    def extract_text_pypdf2(self, pdf_path: Path, start_page: int = 0,
                           end_page: Optional[int] = None) -> List[str]:
        """
        使用PyPDF2提取文本

        Args:
            pdf_path: PDF文件路徑
            start_page: 起始頁碼（0-based）
            end_page: 結束頁碼（不含），None表示到最後

        Returns:
            每頁的文本列表
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        if end_page is None:
            end_page = total_pages
        else:
            end_page = min(end_page, total_pages)

        texts = []
        for i in range(start_page, end_page):
            page = reader.pages[i]
            text = page.extract_text()
            texts.append(text)

        return texts

    def extract_tables_pdfplumber(self, pdf_path: Path, start_page: int = 0,
                                  end_page: Optional[int] = None) -> List[List[List[str]]]:
        """
        使用pdfplumber提取表格

        Args:
            pdf_path: PDF文件路徑
            start_page: 起始頁碼（0-based）
            end_page: 結束頁碼（不含），None表示到最後

        Returns:
            每頁的表格列表（每個表格是二維字符串列表）
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")

        all_tables = []

        with pdfplumber.open(str(pdf_path)) as pdf:
            total_pages = len(pdf.pages)

            if end_page is None:
                end_page = total_pages
            else:
                end_page = min(end_page, total_pages)

            for i in range(start_page, end_page):
                page = pdf.pages[i]
                tables = page.extract_tables()
                all_tables.append(tables if tables else [])

        return all_tables

    def find_table_start(self, texts: List[str], keywords: List[str]) -> Optional[int]:
        """
        查找表格開始頁碼

        Args:
            texts: 頁面文本列表
            keywords: 關鍵詞列表（任一匹配即可）

        Returns:
            頁碼（0-based），找不到返回None
        """
        for i, text in enumerate(texts):
            if any(keyword in text for keyword in keywords):
                return i
        return None

    def clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理後的文本
        """
        if not text:
            return ""

        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def extract_cas_number(self, text: str) -> Optional[str]:
        """
        從文本中提取CAS號

        Args:
            text: 文本

        Returns:
            CAS號，找不到返回None
        """
        if not text:
            return None

        # CAS號格式: XXXXXX-XX-X 或 XXXXX-XX-X 或 XXXX-XX-X
        pattern = r'\b\d{2,7}-\d{2}-\d\b'
        match = re.search(pattern, text)

        return match.group(0) if match else None

    def save_json(self, data: Dict[str, Any], filename: str):
        """
        保存JSON文件

        Args:
            data: 數據字典
            filename: 文件名
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存: {output_path}")

    def create_metadata(self, total_ingredients: int, **kwargs) -> Dict[str, Any]:
        """
        創建元數據

        Args:
            total_ingredients: 成分總數
            **kwargs: 其他元數據字段

        Returns:
            元數據字典
        """
        metadata = {
            "jurisdiction": self.jurisdiction,
            "extracted_at": datetime.utcnow().isoformat() + "Z",
            "total_ingredients": total_ingredients,
            "extractor": "pdf_table_extractor",
            "extractor_version": "1.0.0",
        }

        metadata.update(kwargs)
        return metadata

    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """
        提取數據（子類必須實現）

        Returns:
            提取的數據字典
        """
        pass

    def run(self) -> Dict[str, Any]:
        """
        運行提取器

        Returns:
            提取結果
        """
        print(f"\n{'='*80}")
        print(f"開始提取 {self.jurisdiction} 法規PDF數據")
        print(f"{'='*80}\n")

        result = self.extract()

        print(f"\n{'='*80}")
        print(f"{self.jurisdiction} 數據提取完成")
        print(f"{'='*80}\n")

        return result
