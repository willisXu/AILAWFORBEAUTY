"""ASEAN regulation parser"""

from typing import Dict, Any, List
from parsers.base_parser import BaseParser
from utils import extract_percentage


class ASEANParser(BaseParser):
    """Parser for ASEAN cosmetics regulations"""

    def __init__(self):
        super().__init__("ASEAN")

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ASEAN regulation data"""
        self.logger.info("Parsing ASEAN regulation data")

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
                "id": f"ASEAN-AII-{entry.get('entry_number')}",
                "jurisdiction": "ASEAN",
                "annex": "II",
                "category": "banned",
                "ingredient_ref": entry.get("inci", entry.get("substance_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "substance_name": entry.get("substance_name"),
                "conditions": {},
                "notes": entry.get("notes", ""),
                "source_ref": f"ASEAN CD Annex II, Entry {entry.get('entry_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iii(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex III (Restricted substances)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            conditions_data = entry.get("conditions_of_use", {})

            # Extract max concentration from conditions
            max_pct = None
            for key, value in conditions_data.items():
                if isinstance(value, str):
                    extracted = extract_percentage(value)
                    if extracted and (max_pct is None or extracted > max_pct):
                        max_pct = extracted

            clause = {
                "id": f"ASEAN-AIII-{entry.get('entry_number')}",
                "jurisdiction": "ASEAN",
                "annex": "III",
                "category": "restricted",
                "ingredient_ref": entry.get("inci", entry.get("substance_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "substance_name": entry.get("substance_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "specific_conditions": conditions_data,
                    "restrictions": entry.get("restrictions"),
                },
                "warnings": entry.get("warnings"),
                "notes": "",
                "source_ref": f"ASEAN CD Annex III, Entry {entry.get('entry_number')}",
            }
            clauses.append(clause)

        return clauses

    def _parse_annex_iv(self, annex: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Annex IV (Colorants)"""
        clauses = []
        entries = annex.get("entries", [])

        for entry in entries:
            clause = {
                "id": f"ASEAN-AIV-{entry.get('entry_number')}",
                "jurisdiction": "ASEAN",
                "annex": "IV",
                "category": "colorant",
                "ingredient_ref": entry.get("inci", entry.get("colour_index")),
                "inci": entry.get("inci"),
                "colour_index": entry.get("colour_index"),
                "substance_name": entry.get("substance_name"),
                "conditions": {
                    "restrictions": entry.get("restrictions"),
                },
                "notes": "",
                "source_ref": f"ASEAN CD Annex IV, Entry {entry.get('entry_number')}",
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
                "id": f"ASEAN-AV-{entry.get('entry_number')}",
                "jurisdiction": "ASEAN",
                "annex": "V",
                "category": "preservative",
                "ingredient_ref": entry.get("inci", entry.get("substance_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "substance_name": entry.get("substance_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "other_limitations": entry.get("other_limitations"),
                },
                "warnings": entry.get("warnings"),
                "notes": "",
                "source_ref": f"ASEAN CD Annex V, Entry {entry.get('entry_number')}",
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
                "id": f"ASEAN-AVI-{entry.get('entry_number')}",
                "jurisdiction": "ASEAN",
                "annex": "VI",
                "category": "uv_filter",
                "ingredient_ref": entry.get("inci", entry.get("substance_name")),
                "inci": entry.get("inci"),
                "cas": entry.get("cas"),
                "substance_name": entry.get("substance_name"),
                "conditions": {
                    "max_pct": max_pct,
                    "other_limitations": entry.get("other_limitations"),
                },
                "notes": "",
                "source_ref": f"ASEAN CD Annex VI, Entry {entry.get('entry_number')}",
            }
            clauses.append(clause)

        return clauses
