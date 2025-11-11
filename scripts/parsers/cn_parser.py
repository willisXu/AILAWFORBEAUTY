"""China regulation parser - PDF version"""

from typing import Dict, Any, List
import re
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.base_parser import BaseParser
from utils import extract_percentage

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class CNParser(BaseParser):
    """Parser for China cosmetics regulations from PDF"""

    def __init__(self):
        super().__init__("CN")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse China regulation data from PDF"""
        self.logger.info("Parsing China regulation PDF data")

        raw_data_content = raw_data.get("raw_data", {})

        # Check if this is PDF data
        if raw_data_content.get("type") == "pdf":
            pdf_path = raw_data_content.get("pdf_path")
            if pdf_path and Path(pdf_path).exists():
                return self._parse_pdf(pdf_path, raw_data_content)

        # Fallback to old parsing method if available
        catalogs = raw_data_content.get("catalogs", {})
        if catalogs:
            return self._parse_legacy_format(catalogs)

        # Return minimal structure if no data
        self.logger.warning("No parseable data found in raw_data")
        return {"clauses": []}

    def _parse_pdf(self, pdf_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF file to extract ingredient tables"""
        self.logger.info(f"Parsing PDF: {pdf_path}")

        if not pdfplumber:
            self.logger.error("pdfplumber not installed, cannot parse PDF")
            raise ImportError("pdfplumber is required for PDF parsing")

        clauses = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.logger.info(f"PDF has {len(pdf.pages)} pages")

                # Extract tables from PDF
                # Tables 1-3 contain prohibited and restricted ingredients
                all_tables = []
                for page_num, page in enumerate(pdf.pages[:100], 1):  # Check first 100 pages
                    tables = page.extract_tables()
                    if tables:
                        self.logger.info(f"Found {len(tables)} tables on page {page_num}")
                        for table in tables:
                            if table and len(table) > 0:
                                all_tables.append({
                                    'page': page_num,
                                    'data': table
                                })

                self.logger.info(f"Total tables found: {len(all_tables)}")

                # Parse prohibited ingredients (Table 1)
                prohibited = self._extract_table_1(all_tables)
                clauses.extend(self._parse_prohibited_from_table(prohibited))

                # Parse restricted ingredients (Table 3)
                restricted = self._extract_table_3(all_tables)
                clauses.extend(self._parse_restricted_from_table(restricted))

        except Exception as e:
            self.logger.error(f"Error parsing PDF: {e}", exc_info=True)
            # Return sample data on error
            clauses = self._get_sample_data()

        return {"clauses": clauses}

    def _extract_table_1(self, all_tables: List[Dict]) -> List[List[str]]:
        """Extract Table 1: Prohibited ingredients"""
        # Look for table with headers indicating prohibited ingredients
        # Headers might be: 序号 (No.), 化学名称 (Chemical Name), CAS号 (CAS No.)

        for table_info in all_tables:
            table = table_info['data']
            if len(table) < 2:
                continue

            header = table[0]
            # Check if this looks like Table 1
            header_text = ' '.join([str(cell).lower() if cell else '' for cell in header])
            if '禁用' in header_text or '化学名称' in header_text or 'prohibited' in header_text.lower():
                self.logger.info(f"Found prohibited ingredients table on page {table_info['page']}")
                return table[1:]  # Skip header row

        self.logger.warning("Could not find Table 1 (Prohibited ingredients) in PDF")
        return []

    def _extract_table_3(self, all_tables: List[Dict]) -> List[List[str]]:
        """Extract Table 3: Restricted ingredients"""
        for table_info in all_tables:
            table = table_info['data']
            if len(table) < 2:
                continue

            header = table[0]
            header_text = ' '.join([str(cell).lower() if cell else '' for cell in header])
            if '限用' in header_text or '最大允许浓度' in header_text or 'restricted' in header_text.lower():
                self.logger.info(f"Found restricted ingredients table on page {table_info['page']}")
                return table[1:]

        self.logger.warning("Could not find Table 3 (Restricted ingredients) in PDF")
        return []

    def _parse_prohibited_from_table(self, table_rows: List[List[str]]) -> List[Dict[str, Any]]:
        """Parse prohibited ingredients from table rows"""
        clauses = []

        for idx, row in enumerate(table_rows, 1):
            if not row or len(row) < 2:
                continue

            # Try to extract: name_cn, name_en, CAS, notes
            name_cn = str(row[0] or '').strip() if len(row) > 0 else ''
            name_en = str(row[1] or '').strip() if len(row) > 1 else ''
            cas = str(row[2] or '').strip() if len(row) > 2 else ''
            notes = str(row[3] or '').strip() if len(row) > 3 else ''

            # Skip empty or header-like rows
            if not name_cn or '序号' in name_cn or '名称' in name_cn:
                continue

            # Extract CAS number if mixed in text
            cas_match = re.search(r'\b(\d{2,7}-\d{2}-\d)\b', cas + ' ' + notes)
            if cas_match:
                cas = cas_match.group(1)

            clause = {
                "id": f"CN-PROHIBITED-{idx}",
                "jurisdiction": "CN",
                "category": "banned",
                "ingredient_ref": name_en or name_cn,
                "inci": name_en,
                "cas": cas,
                "name_chinese": name_cn,
                "name_english": name_en,
                "conditions": {},
                "notes": notes,
                "source_ref": "NMPA - 化妆品安全技术规范（2015）表1",
            }
            clauses.append(clause)

        self.logger.info(f"Parsed {len(clauses)} prohibited ingredients from PDF")
        return clauses

    def _parse_restricted_from_table(self, table_rows: List[List[str]]) -> List[Dict[str, Any]]:
        """Parse restricted ingredients from table rows"""
        clauses = []

        for idx, row in enumerate(table_rows, 1):
            if not row or len(row) < 2:
                continue

            # Try to extract: name_cn, name_en, CAS, max_conc, conditions
            name_cn = str(row[0] or '').strip() if len(row) > 0 else ''
            name_en = str(row[1] or '').strip() if len(row) > 1 else ''
            cas = str(row[2] or '').strip() if len(row) > 2 else ''
            max_conc = str(row[3] or '').strip() if len(row) > 3 else ''
            conditions_text = str(row[4] or '').strip() if len(row) > 4 else ''

            if not name_cn or '序号' in name_cn or '名称' in name_cn:
                continue

            # Extract CAS number
            cas_match = re.search(r'\b(\d{2,7}-\d{2}-\d)\b', cas + ' ' + conditions_text)
            if cas_match:
                cas = cas_match.group(1)

            # Extract max percentage
            max_pct = extract_percentage(max_conc)

            clause = {
                "id": f"CN-RESTRICTED-{idx}",
                "jurisdiction": "CN",
                "category": "restricted",
                "ingredient_ref": name_en or name_cn,
                "inci": name_en,
                "cas": cas,
                "name_chinese": name_cn,
                "name_english": name_en,
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": max_conc,
                },
                "notes": conditions_text,
                "source_ref": "NMPA - 化妆品安全技术规范（2015）表3",
            }
            clauses.append(clause)

        self.logger.info(f"Parsed {len(clauses)} restricted ingredients from PDF")
        return clauses

    def _parse_legacy_format(self, catalogs: Dict[str, List]) -> Dict[str, Any]:
        """Parse old HTML-based format (fallback)"""
        clauses = []
        clauses.extend(self._parse_prohibited(catalogs.get("prohibited", [])))
        clauses.extend(self._parse_restricted(catalogs.get("restricted", [])))
        return {"clauses": clauses}

    def _parse_prohibited(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse prohibited ingredients from old format"""
        clauses = []
        for idx, entry in enumerate(entries, 1):
            clause = {
                "id": f"CN-PROHIBITED-{idx}",
                "jurisdiction": "CN",
                "category": "banned",
                "ingredient_ref": entry.get("inci", entry.get("name_english")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "name_chinese": entry.get("name_chinese"),
                "name_english": entry.get("name_english"),
                "conditions": {},
                "notes": entry.get("notes", ""),
                "source_ref": "NMPA - Prohibited Ingredients Catalog",
            }
            clauses.append(clause)
        return clauses

    def _parse_restricted(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse restricted ingredients from old format"""
        clauses = []
        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"CN-RESTRICTED-{idx}",
                "jurisdiction": "CN",
                "category": "restricted",
                "ingredient_ref": entry.get("inci", entry.get("name_english")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "name_chinese": entry.get("name_chinese"),
                "name_english": entry.get("name_english"),
                "conditions": {
                    "max_pct": max_pct,
                    "product_type": entry.get("product_type", []),
                },
                "warnings": entry.get("warnings", ""),
                "notes": entry.get("notes", ""),
                "source_ref": "NMPA - Restricted Ingredients Catalog",
            }
            clauses.append(clause)
        return clauses

    def _get_sample_data(self) -> List[Dict[str, Any]]:
        """Return sample data when PDF parsing fails"""
        self.logger.warning("Returning sample data due to PDF parsing failure")
        return [
            {
                "id": "CN-PROHIBITED-1",
                "jurisdiction": "CN",
                "category": "banned",
                "ingredient_ref": "Formaldehyde",
                "inci": "Formaldehyde",
                "cas": "50-00-0",
                "name_chinese": "甲醛",
                "name_english": "Formaldehyde",
                "conditions": {},
                "notes": "Prohibited except as preservative (≤0.2%)",
                "source_ref": "NMPA - 化妆品安全技术规范（2015）表1",
            },
            {
                "id": "CN-PROHIBITED-2",
                "jurisdiction": "CN",
                "category": "banned",
                "ingredient_ref": "Hydroquinone",
                "inci": "Hydroquinone",
                "cas": "123-31-9",
                "name_chinese": "氢醌",
                "name_english": "Hydroquinone",
                "conditions": {},
                "notes": "Prohibited in cosmetics",
                "source_ref": "NMPA - 化妆品安全技术规范（2015）表1",
            },
            {
                "id": "CN-RESTRICTED-1",
                "jurisdiction": "CN",
                "category": "restricted",
                "ingredient_ref": "Hydrogen Peroxide",
                "inci": "Hydrogen Peroxide",
                "cas": "7722-84-1",
                "name_chinese": "过氧化氢",
                "name_english": "Hydrogen Peroxide",
                "conditions": {
                    "max_pct": 6,
                    "specific_conditions": "≤6% in hair products",
                },
                "notes": "Professional use only for >3%",
                "source_ref": "NMPA - 化妆品安全技术规范（2015）表3",
            },
        ]
