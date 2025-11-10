"""China regulation parser"""

from typing import Dict, Any, List
from .base_parser import BaseParser
from ..utils import extract_percentage


class CNParser(BaseParser):
    """Parser for China cosmetics regulations"""

    def __init__(self):
        super().__init__("CN")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse China regulation data"""
        self.logger.info("Parsing China regulation data")

        raw_data_content = raw_data.get("raw_data", {})
        catalogs = raw_data_content.get("catalogs", {})

        clauses = []

        # Parse prohibited
        clauses.extend(self._parse_prohibited(catalogs.get("prohibited", [])))

        # Parse restricted
        clauses.extend(self._parse_restricted(catalogs.get("restricted", [])))

        # Parse preservatives
        clauses.extend(self._parse_preservatives(catalogs.get("preservatives", [])))

        # Parse colorants
        clauses.extend(self._parse_colorants(catalogs.get("colorants", [])))

        return {"clauses": clauses}

    def _parse_prohibited(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse prohibited ingredients"""
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
        """Parse restricted ingredients"""
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
                    "specific_conditions": entry.get("conditions"),
                },
                "warnings": entry.get("warnings"),
                "notes": entry.get("notes", ""),
                "source_ref": "NMPA - Restricted Ingredients Catalog",
            }
            clauses.append(clause)

        return clauses

    def _parse_preservatives(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse permitted preservatives"""
        clauses = []

        for entry in entries:
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"CN-PRESERVATIVE-{entry.get('serial_number')}",
                "jurisdiction": "CN",
                "category": "preservative",
                "ingredient_ref": entry.get("inci", entry.get("name_english")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "name_chinese": entry.get("name_chinese"),
                "name_english": entry.get("name_english"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions"),
                },
                "notes": entry.get("notes", ""),
                "source_ref": f"NMPA - Permitted Preservatives, Serial {entry.get('serial_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_colorants(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse permitted colorants"""
        clauses = []

        for entry in entries:
            clause = {
                "id": f"CN-COLORANT-{entry.get('serial_number')}",
                "jurisdiction": "CN",
                "category": "colorant",
                "ingredient_ref": entry.get("inci", entry.get("ci_number")),
                "inci": entry.get("inci"),
                "ci_number": entry.get("ci_number"),
                "name_chinese": entry.get("name_chinese"),
                "name_english": entry.get("name_english"),
                "conditions": {
                    "restrictions": entry.get("restrictions"),
                },
                "notes": entry.get("notes", ""),
                "source_ref": f"NMPA - Permitted Colorants, Serial {entry.get('serial_number')}",
            }
            clauses.append(clause)

        return clauses
