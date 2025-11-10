"""ASEAN cosmetics regulation scraper"""

from typing import Dict, Any
from .base_scraper import BaseScraper
from ..utils import parse_date


class ASEANScraper(BaseScraper):
    """Scraper for ASEAN cosmetics regulations"""

    def __init__(self):
        super().__init__("ASEAN")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch ASEAN cosmetics regulation data

        Data from ASEAN Cosmetic Directive (ACD)
        Harmonized regulations across ASEAN member states

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching ASEAN cosmetics regulation data")

        data = {
            "source": "ASEAN Cosmetic Directive",
            "regulation": "ASEAN Cosmetic Directive (ACD)",
            "url": "https://asean.org/",
            "last_update": "2023-12-15",
            "member_states": [
                "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
                "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"
            ],
            "annexes": self._fetch_annexes(),
        }

        return data

    def _fetch_annexes(self) -> Dict[str, Any]:
        """
        Fetch ASEAN Cosmetic Directive annexes

        Similar structure to EU but with ASEAN-specific adaptations
        """
        return {
            "annex_ii": {
                "name": "Prohibited Substances",
                "description": "List of substances which cosmetic products must not contain",
                "entries": self._fetch_prohibited(),
            },
            "annex_iii": {
                "name": "Restricted Substances",
                "description": "List of substances subject to restrictions",
                "entries": self._fetch_restricted(),
            },
            "annex_iv": {
                "name": "Permitted Colorants",
                "description": "List of colorants allowed for use in cosmetic products",
                "entries": self._fetch_colorants(),
            },
            "annex_v": {
                "name": "Permitted Preservatives",
                "description": "List of preservatives allowed for use in cosmetic products",
                "entries": self._fetch_preservatives(),
            },
            "annex_vi": {
                "name": "Permitted UV Filters",
                "description": "List of UV filters allowed for use in cosmetic products",
                "entries": self._fetch_uv_filters(),
            },
        }

    def _fetch_prohibited(self) -> list:
        """Fetch prohibited substances (Annex II)"""
        return [
            {
                "entry_number": "1",
                "substance_name": "Formaldehyde",
                "cas": "50-00-0",
                "inci": "Formaldehyde",
                "notes": "Except as preservative within the limits specified in Annex V"
            },
            {
                "entry_number": "15",
                "substance_name": "Hydroquinone",
                "cas": "123-31-9",
                "inci": "Hydroquinone",
                "notes": "Except as oxidizing agent for hair colouring at ≤0.3%"
            },
            {
                "entry_number": "89",
                "substance_name": "Mercury and its compounds",
                "cas": "7439-97-6",
                "inci": "Mercury",
                "notes": "Except trace amounts from unavoidable contamination (≤1ppm)"
            },
        ]

    def _fetch_restricted(self) -> list:
        """Fetch restricted substances (Annex III)"""
        return [
            {
                "entry_number": "5",
                "substance_name": "Hydrogen peroxide",
                "cas": "7722-84-1",
                "inci": "Hydrogen Peroxide",
                "conditions_of_use": {
                    "hair_products": "≤12% (40 volumes)",
                    "skin_products": "≤4%",
                    "nail_hardening": "≤2%",
                    "tooth_whitening": "≤0.1%"
                },
                "warnings": "Contains hydrogen peroxide. Avoid contact with eyes.",
                "restrictions": "Not to be used on eyebrows or eyelashes"
            },
            {
                "entry_number": "6",
                "substance_name": "Salicylic acid and its salts",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "conditions_of_use": {
                    "rinse_off": "≤3%",
                    "leave_on": "≤2%",
                    "other_hair_care": "≤3%"
                },
                "warnings": "Contains salicylic acid. Not to be used for children under 3 years except in shampoos",
                "restrictions": "Not in oral products"
            },
            {
                "entry_number": "9",
                "substance_name": "Thioglycolic acid and its salts",
                "cas": "68-11-1",
                "inci": "Thioglycolic Acid",
                "conditions_of_use": {
                    "general_use": "≤8% (as TG)",
                    "professional_use": "≤11% (as TG)",
                    "pH_general": "≥7.0",
                    "pH_professional": "≥9.0"
                },
                "warnings": "Contains thioglycolic acid. Follow instructions. Keep out of reach of children.",
                "restrictions": "For professional use only when concentration >8%"
            },
        ]

    def _fetch_colorants(self) -> list:
        """Fetch permitted colorants (Annex IV)"""
        return [
            {
                "entry_number": "1",
                "colour_index": "CI 10006",
                "substance_name": "Naphthol Yellow S",
                "inci": "CI 10006",
                "restrictions": "Not for use in products applied near the eyes"
            },
            {
                "entry_number": "25",
                "colour_index": "CI 77491",
                "substance_name": "Iron Oxides",
                "inci": "CI 77491",
                "restrictions": "None"
            },
            {
                "entry_number": "30",
                "colour_index": "CI 77891",
                "substance_name": "Titanium Dioxide",
                "inci": "CI 77891",
                "restrictions": "None"
            },
        ]

    def _fetch_preservatives(self) -> list:
        """Fetch permitted preservatives (Annex V)"""
        return [
            {
                "entry_number": "3",
                "substance_name": "Benzoic acid, its salts and esters",
                "inci": "Benzoic Acid",
                "cas": "65-85-0",
                "maximum_concentration": "0.5%",
                "other_limitations": "As acid",
                "warnings": None
            },
            {
                "entry_number": "4",
                "substance_name": "Salicylic acid and its salts",
                "inci": "Salicylic Acid",
                "cas": "69-72-7",
                "maximum_concentration": "0.5%",
                "other_limitations": "As acid. Not in preparations for children under 3 years except in shampoos",
                "warnings": "Contains salicylic acid"
            },
        ]

    def _fetch_uv_filters(self) -> list:
        """Fetch permitted UV filters (Annex VI)"""
        return [
            {
                "entry_number": "2",
                "substance_name": "Homosalate",
                "inci": "Homosalate",
                "cas": "118-56-9",
                "maximum_concentration": "10%",
                "other_limitations": None
            },
            {
                "entry_number": "5",
                "substance_name": "Ethylhexyl Methoxycinnamate",
                "inci": "Ethylhexyl Methoxycinnamate",
                "cas": "5466-77-3",
                "maximum_concentration": "10%",
                "other_limitations": None
            },
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw ASEAN data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": last_update.isoformat() if last_update else None,
            "effective_date": last_update.isoformat() if last_update else None,
            "version": last_update_str.replace("-", "") if last_update_str else None,
            "member_states": raw_data.get("member_states"),
        }
