"""Canada regulation parser"""

from typing import Dict, Any, List
from parsers.base_parser import BaseParser
from utils import extract_percentage


class CAParser(BaseParser):
    """Parser for Canada cosmetics regulations"""

    def __init__(self):
        super().__init__("CA")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Canada regulation data"""
        self.logger.info("Parsing Canada regulation data")

        raw_data_content = raw_data.get("raw_data", {})
        hotlist = raw_data_content.get("hotlist", {})

        clauses = []

        # Parse prohibited
        clauses.extend(self._parse_prohibited(hotlist.get("prohibited", [])))

        # Parse restricted
        clauses.extend(self._parse_restricted(hotlist.get("restricted", [])))

        return {"clauses": clauses}

    def _parse_prohibited(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse prohibited substances from Hotlist"""
        clauses = []

        for entry in entries:
            clause = {
                "id": f"CA-{entry.get('hotlist_entry')}",
                "jurisdiction": "CA",
                "category": "banned",
                "ingredient_ref": entry.get("inci", entry.get("ingredient_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "ingredient_name": entry.get("ingredient_name"),
                "conditions": {},
                "notes": entry.get("restrictions", ""),
                "source_ref": f"Health Canada Hotlist - {entry.get('hotlist_entry')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_restricted(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse restricted substances from Hotlist"""
        clauses = []

        for entry in entries:
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            conditions_data = entry.get("conditions", {})

            clause = {
                "id": f"CA-{entry.get('hotlist_entry')}",
                "jurisdiction": "CA",
                "category": "restricted",
                "ingredient_ref": entry.get("inci", entry.get("ingredient_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "ingredient_name": entry.get("ingredient_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": conditions_data,
                },
                "warnings": conditions_data.get("warnings"),
                "notes": "",
                "source_ref": f"Health Canada Hotlist - {entry.get('hotlist_entry')}",
            }
            clauses.append(clause)

        return clauses
