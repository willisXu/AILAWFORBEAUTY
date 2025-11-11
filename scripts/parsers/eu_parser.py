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
        entries = annex.get("entries", [])

        for entry in entries:
            clause = {
                "id": f"EU-AII-{entry.get('reference_number')}",
                "jurisdiction": "EU",
                "annex": "II",
                "category": "banned",
                "ingredient_ref": entry.get("inci", entry.get("chemical_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "chemical_name": entry.get("chemical_name"),
                "conditions": {},
                "notes": entry.get("notes", ""),
                "source_ref": f"Annex II, Entry {entry.get('reference_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iii(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex III (Restricted substances)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            product_types = entry.get("product_type", [])
            conditions_data = entry.get("conditions", {})

            clause = {
                "id": f"EU-AIII-{entry.get('reference_number')}",
                "jurisdiction": "EU",
                "annex": "III",
                "category": "restricted",
                "ingredient_ref": entry.get("inci", entry.get("chemical_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "chemical_name": entry.get("chemical_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "product_type": product_types,
                    "specific_conditions": conditions_data,
                },
                "warnings": entry.get("warnings"),
                "notes": entry.get("notes", ""),
                "source_ref": f"Annex III, Entry {entry.get('reference_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iv(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex IV (Colorants)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            clause = {
                "id": f"EU-AIV-{entry.get('reference_number')}",
                "jurisdiction": "EU",
                "annex": "IV",
                "category": "colorant",
                "ingredient_ref": entry.get("inci", entry.get("colour_index")),
                "inci": entry.get("inci"),
                "colour_index": entry.get("colour_index"),
                "chemical_name": entry.get("chemical_name"),
                "conditions": {
                    "restrictions": entry.get("restrictions"),
                    "purity_criteria": entry.get("purity_criteria"),
                },
                "notes": entry.get("notes", ""),
                "source_ref": f"Annex IV, Entry {entry.get('reference_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_v(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex V (Preservatives)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"EU-AV-{entry.get('reference_number')}",
                "jurisdiction": "EU",
                "annex": "V",
                "category": "preservative",
                "ingredient_ref": entry.get("inci", entry.get("chemical_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "chemical_name": entry.get("chemical_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions"),
                },
                "warnings": entry.get("warnings"),
                "notes": entry.get("notes", ""),
                "source_ref": f"Annex V, Entry {entry.get('reference_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_vi(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex VI (UV Filters)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            max_pct = None
            max_pct_str = entry.get("maximum_concentration", "")
            if max_pct_str:
                max_pct = extract_percentage(max_pct_str)

            clause = {
                "id": f"EU-AVI-{entry.get('reference_number')}",
                "jurisdiction": "EU",
                "annex": "VI",
                "category": "uv_filter",
                "ingredient_ref": entry.get("inci", entry.get("chemical_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "chemical_name": entry.get("chemical_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": entry.get("conditions"),
                },
                "warnings": entry.get("warnings"),
                "notes": entry.get("notes", ""),
                "source_ref": f"Annex VI, Entry {entry.get('reference_number')}",
            }
            clauses.append(clause)

        return clauses
