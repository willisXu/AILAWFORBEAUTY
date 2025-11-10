"""Japan regulation parser"""

from typing import Dict, Any, List
from .base_parser import BaseParser
from ..utils import extract_percentage


class JPParser(BaseParser):
    """Parser for Japan cosmetics regulations"""

    def __init__(self):
        super().__init__("JP")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Japan regulation data"""
        self.logger.info("Parsing Japan regulation data")

        raw_data_content = raw_data.get("raw_data", {})
        categories = raw_data_content.get("categories", {})

        clauses = []

        # Parse prohibited
        clauses.extend(self._parse_prohibited(categories.get("prohibited", [])))

        # Parse restricted
        clauses.extend(self._parse_restricted(categories.get("restricted", [])))

        return {"clauses": clauses}

    def _parse_prohibited(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse prohibited substances"""
        clauses = []

        for idx, entry in enumerate(entries, 1):
            clause = {
                "id": f"JP-PROHIBITED-{idx}",
                "jurisdiction": "JP",
                "category": "banned",
                "ingredient_ref": entry.get("inci", entry.get("name_english")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "name_japanese": entry.get("name_japanese"),
                "name_english": entry.get("name_english"),
                "conditions": {},
                "notes": entry.get("notes", ""),
                "source_ref": "MHLW Standards for Cosmetics - Prohibited List",
            }
            clauses.append(clause)

        return clauses

    def _parse_restricted(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse restricted substances"""
        clauses = []

        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"JP-RESTRICTED-{idx}",
                "jurisdiction": "JP",
                "category": "restricted",
                "ingredient_ref": entry.get("inci", entry.get("name_english")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "name_japanese": entry.get("name_japanese"),
                "name_english": entry.get("name_english"),
                "conditions": {
                    "max_pct": max_pct,
                    "product_type": entry.get("product_type", []),
                    "specific_conditions": entry.get("conditions"),
                },
                "warnings": entry.get("warnings"),
                "notes": entry.get("notes", ""),
                "source_ref": "MHLW Standards for Cosmetics - Restricted List",
            }
            clauses.append(clause)

        return clauses
