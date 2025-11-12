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

        # Check if data is in new format (ingredients list)
        ingredients = raw_data_content.get("ingredients", [])
        if ingredients:
            # New format from scraper
            prohibited = [ing for ing in ingredients if ing.get("restriction_type") == "prohibited" or ing.get("status") == "prohibited"]
            restricted = [ing for ing in ingredients if ing.get("restriction_type") == "restricted" or ing.get("status") == "restricted"]
        else:
            # Old format (fallback)
            hotlist = raw_data_content.get("hotlist", {})
            prohibited = hotlist.get("prohibited", [])
            restricted = hotlist.get("restricted", [])

        clauses = []

        # Parse prohibited
        clauses.extend(self._parse_prohibited(prohibited))

        # Parse restricted
        clauses.extend(self._parse_restricted(restricted))

        return {"clauses": clauses}

    def _parse_prohibited(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse prohibited substances from Hotlist"""
        clauses = []

        for idx, entry in enumerate(entries, 1):
            clause = {
                "id": f"CA-PROHIBITED-{idx}",
                "jurisdiction": "CA",
                "category": "banned",
                "ingredient_ref": entry.get("inci") or entry.get("ingredient_name"),
                "inci": entry.get("inci") or entry.get("ingredient_name"),
                "cas": entry.get("cas") or entry.get("cas_no"),
                "ingredient_name": entry.get("ingredient_name"),
                "conditions": {},
                "notes": entry.get("restrictions") or entry.get("conditions", ""),
                "source_ref": f"Health Canada Hotlist - Prohibited",
            }
            clauses.append(clause)

        return clauses

    def _parse_restricted(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse restricted substances from Hotlist"""
        clauses = []

        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            # Handle both old and new format conditions
            conditions_text = entry.get("conditions")
            if isinstance(conditions_text, dict):
                conditions_data = conditions_text
            else:
                conditions_data = {"description": conditions_text} if conditions_text else {}

            clause = {
                "id": f"CA-RESTRICTED-{idx}",
                "jurisdiction": "CA",
                "category": "restricted",
                "ingredient_ref": entry.get("inci") or entry.get("ingredient_name"),
                "inci": entry.get("inci") or entry.get("ingredient_name"),
                "cas": entry.get("cas") or entry.get("cas_no"),
                "ingredient_name": entry.get("ingredient_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": conditions_data,
                },
                "warnings": entry.get("warnings") or conditions_data.get("warnings"),
                "notes": entry.get("rationale", ""),
                "source_ref": f"Health Canada Hotlist - Restricted",
            }
            clauses.append(clause)

        return clauses
