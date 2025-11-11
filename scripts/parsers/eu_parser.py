"""EU regulation parser"""

from typing import Dict, Any, List
from parsers.base_parser import BaseParser
from utils import extract_percentage, clean_ingredient_name


class EUParser(BaseParser):
    """Parser for EU cosmetics regulations"""

    def __init__(self):
        super().__init__("EU")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse EU regulation data"""
        self.logger.info("Parsing EU regulation data")

        raw_data_content = raw_data.get("raw_data", {})
        annexes = raw_data_content.get("annexes", {})

        clauses = []

        # Parse Annex II (Prohibited)
        clauses.extend(self._parse_annex_ii(annexes.get("annex_ii", {})))

        # Parse Annex III (Restricted)
        clauses.extend(self._parse_annex_iii(annexes.get("annex_iii", {})))

        # Parse Annex IV (Colorants)
        clauses.extend(self._parse_annex_iv(annexes.get("annex_iv", {})))

        # Parse Annex V (Preservatives)
        clauses.extend(self._parse_annex_v(annexes.get("annex_v", {})))

        # Parse Annex VI (UV Filters)
        clauses.extend(self._parse_annex_vi(annexes.get("annex_vi", {})))

        return {"clauses": clauses}

    def _parse_annex_ii(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex II (Prohibited substances)"""
        clauses = []
        entries = annex.get("ingredients", [])

        for idx, entry in enumerate(entries, 1):
            clause = {
                "id": f"EU-AII-{idx}",
                "jurisdiction": "EU",
                "annex": "II",
                "category": "banned",
                "ingredient_ref": entry.get("ingredient_name") or entry.get("inci_name"),
                "inci": entry.get("inci_name"),
                "cas": entry.get("cas_no") or entry.get("cas"),
                "chemical_name": entry.get("ingredient_name"),
                "conditions": entry.get("conditions", ""),
                "notes": entry.get("rationale", ""),
                "source_ref": f"Annex II",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iii(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex III (Restricted substances)"""
        clauses = []
        entries = annex.get("ingredients", [])

        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"EU-AIII-{idx}",
                "jurisdiction": "EU",
                "annex": "III",
                "category": "restricted",
                "ingredient_ref": entry.get("ingredient_name") or entry.get("inci_name"),
                "inci": entry.get("inci_name"),
                "cas": entry.get("cas_no") or entry.get("cas"),
                "chemical_name": entry.get("ingredient_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions", ""),
                },
                "notes": entry.get("rationale", ""),
                "source_ref": f"Annex III",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iv(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex IV (Colorants)"""
        clauses = []
        entries = annex.get("ingredients", [])

        for idx, entry in enumerate(entries, 1):
            clause = {
                "id": f"EU-AIV-{idx}",
                "jurisdiction": "EU",
                "annex": "IV",
                "category": "colorant",
                "ingredient_ref": entry.get("ingredient_name") or entry.get("inci_name"),
                "inci": entry.get("inci_name"),
                "cas": entry.get("cas_no") or entry.get("cas"),
                "colour_index": entry.get("colour_index"),
                "chemical_name": entry.get("ingredient_name"),
                "conditions": entry.get("conditions", ""),
                "notes": entry.get("rationale", ""),
                "source_ref": f"Annex IV",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_v(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex V (Preservatives)"""
        clauses = []
        entries = annex.get("ingredients", [])

        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"EU-AV-{idx}",
                "jurisdiction": "EU",
                "annex": "V",
                "category": "preservative",
                "ingredient_ref": entry.get("ingredient_name") or entry.get("inci_name"),
                "inci": entry.get("inci_name"),
                "cas": entry.get("cas_no") or entry.get("cas"),
                "chemical_name": entry.get("ingredient_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions", ""),
                },
                "notes": entry.get("rationale", ""),
                "source_ref": f"Annex V",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_vi(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex VI (UV Filters)"""
        clauses = []
        entries = annex.get("ingredients", [])

        for idx, entry in enumerate(entries, 1):
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"EU-AVI-{idx}",
                "jurisdiction": "EU",
                "annex": "VI",
                "category": "uv_filter",
                "ingredient_ref": entry.get("ingredient_name") or entry.get("inci_name"),
                "inci": entry.get("inci_name"),
                "cas": entry.get("cas_no") or entry.get("cas"),
                "chemical_name": entry.get("ingredient_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions", ""),
                },
                "notes": entry.get("rationale", ""),
                "source_ref": f"Annex VI",
            }
            clauses.append(clause)

        return clauses
