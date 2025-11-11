"""
File Loading Utilities
文件載入工具
"""

import os
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Union, List, Dict, Optional
from .text_utils import detect_encoding


class FileLoader:
    """文件載入器基類"""

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def load(self):
        """載入文件 - 需要在子類實作"""
        raise NotImplementedError


class TextFileLoader(FileLoader):
    """文字文件載入器"""

    def load(self, encoding: Optional[str] = None) -> str:
        """
        載入文字文件

        Args:
            encoding: 編碼格式,如未指定則自動檢測

        Returns:
            文件內容字串
        """
        if encoding is None:
            encoding = detect_encoding(str(self.file_path))

        try:
            with open(self.file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # 嘗試其他常見編碼
            for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(self.file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue

            raise ValueError(f"Unable to decode file: {self.file_path}")


class ExcelFileLoader(FileLoader):
    """Excel 文件載入器"""

    def load(self, sheet_name: Union[str, int, None] = 0) -> pd.DataFrame:
        """
        載入 Excel 文件

        Args:
            sheet_name: 工作表名稱或索引

        Returns:
            DataFrame
        """
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            return df
        except Exception as e:
            raise ValueError(f"Error loading Excel file {self.file_path}: {str(e)}")

    def load_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        載入所有工作表

        Returns:
            字典,鍵為工作表名稱,值為 DataFrame
        """
        try:
            all_sheets = pd.read_excel(self.file_path, sheet_name=None)
            return all_sheets
        except Exception as e:
            raise ValueError(f"Error loading Excel file {self.file_path}: {str(e)}")

    def get_sheet_names(self) -> List[str]:
        """
        取得所有工作表名稱

        Returns:
            工作表名稱列表
        """
        import openpyxl
        wb = openpyxl.load_workbook(self.file_path, read_only=True)
        return wb.sheetnames


class CSVFileLoader(FileLoader):
    """CSV 文件載入器"""

    def load(self, encoding: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        載入 CSV 文件

        Args:
            encoding: 編碼格式
            **kwargs: pandas read_csv 的其他參數

        Returns:
            DataFrame
        """
        if encoding is None:
            encoding = detect_encoding(str(self.file_path))

        try:
            df = pd.read_csv(self.file_path, encoding=encoding, **kwargs)
            return df
        except Exception as e:
            raise ValueError(f"Error loading CSV file {self.file_path}: {str(e)}")


class PDFFileLoader(FileLoader):
    """PDF 文件載入器"""

    def load_text(self) -> str:
        """
        使用 PyMuPDF 載入 PDF 文字內容

        Returns:
            文字內容
        """
        try:
            doc = fitz.open(self.file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise ValueError(f"Error loading PDF file {self.file_path}: {str(e)}")

    def load_tables(self) -> List[pd.DataFrame]:
        """
        使用 pdfplumber 載入 PDF 表格

        Returns:
            DataFrame 列表
        """
        try:
            tables = []
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            # 轉換為 DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append(df)
            return tables
        except Exception as e:
            raise ValueError(f"Error extracting tables from PDF {self.file_path}: {str(e)}")

    def load_tables_advanced(self) -> List[Dict]:
        """
        進階 PDF 表格提取,包含頁碼資訊

        Returns:
            包含表格和元數據的字典列表
        """
        try:
            results = []
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables, 1):
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            results.append({
                                'page': page_num,
                                'table_number': table_num,
                                'dataframe': df,
                                'raw_data': table
                            })
            return results
        except Exception as e:
            raise ValueError(f"Error extracting tables from PDF {self.file_path}: {str(e)}")


def load_file(file_path: Union[str, Path], **kwargs):
    """
    根據文件類型自動載入

    Args:
        file_path: 文件路徑
        **kwargs: 額外參數

    Returns:
        載入的內容
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in ['.txt', '.text']:
        loader = TextFileLoader(file_path)
        return loader.load()

    elif suffix in ['.xlsx', '.xls']:
        loader = ExcelFileLoader(file_path)
        return loader.load(**kwargs)

    elif suffix == '.csv':
        loader = CSVFileLoader(file_path)
        return loader.load(**kwargs)

    elif suffix == '.pdf':
        loader = PDFFileLoader(file_path)
        # 預設嘗試提取表格,如果沒有表格則返回文字
        tables = loader.load_tables()
        if tables:
            return tables
        else:
            return loader.load_text()

    else:
        raise ValueError(f"Unsupported file type: {suffix}")
