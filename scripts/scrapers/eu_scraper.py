"""EU cosmetics regulation scraper"""

from typing import Dict, Any
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..utils import fetch_url, parse_date


class EUScraper(BaseScraper):
    """Scraper for EU cosmetics regulations"""

    def __init__(self):
        super().__init__("EU")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch EU cosmetics regulation data

        The EU regulation data comes from:
        - CosIng database (https://ec.europa.eu/growth/tools-databases/cosing/)
        - Annexes to Regulation (EC) No 1223/2009

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching EU cosmetics regulation data")

        # Note: In a real implementation, this would scrape the actual CosIng database
        # For this demo, we'll create a structure that represents the data

        data = {
            "source": "European Commission - CosIng Database",
            "regulation": "Regulation (EC) No 1223/2009",
            "url": "https://ec.europa.eu/growth/tools-databases/cosing/",
            "last_update": "2024-02-14",
            "annexes": self._fetch_annexes(),
        }

        return data

    def _fetch_annexes(self) -> Dict[str, Any]:
        """
        Fetch annex data

        EU Regulation has several annexes:
        - Annex II: Substances prohibited in cosmetic products
        - Annex III: Substances restricted in cosmetic products
        - Annex IV: Colorants allowed in cosmetic products
        - Annex V: Preservatives allowed in cosmetic products
        - Annex VI: UV filters allowed in cosmetic products

        Returns:
            Dictionary of annex data
        """
        annexes = {
            "annex_ii": {
                "name": "Prohibited substances",
                "description": "List of substances prohibited in cosmetic products",
                "entries": self._fetch_annex_ii(),
            },
            "annex_iii": {
                "name": "Restricted substances",
                "description": "List of substances subject to restrictions",
                "entries": self._fetch_annex_iii(),
            },
            "annex_iv": {
                "name": "Allowed colorants",
                "description": "List of colorants allowed in cosmetic products",
                "entries": self._fetch_annex_iv(),
            },
            "annex_v": {
                "name": "Allowed preservatives",
                "description": "List of preservatives allowed in cosmetic products",
                "entries": self._fetch_annex_v(),
            },
            "annex_vi": {
                "name": "Allowed UV filters",
                "description": "List of UV filters allowed in cosmetic products",
                "entries": self._fetch_annex_vi(),
            },
        }

        return annexes

    def _fetch_annex_ii(self) -> list:
        """Fetch Annex II (Prohibited substances)"""
        # Sample data - in real implementation, scrape from CosIng
        return [
            {
                "reference_number": "1",
                "chemical_name": "Formaldehyde",
                "cas": "50-00-0",
                "inci": "Formaldehyde",
                "restrictions": "Prohibited in all cosmetic products",
                "notes": "Except as preservative under specific conditions in Annex V"
            },
            {
                "reference_number": "98",
                "chemical_name": "Hydroquinone",
                "cas": "123-31-9",
                "inci": "Hydroquinone",
                "restrictions": "Prohibited",
                "notes": "Except as oxidizing agent in hair dye preparations (≤0.3%)"
            },
            {
                "reference_number": "254",
                "chemical_name": "Methyl alcohol",
                "cas": "67-56-1",
                "inci": "Methanol",
                "restrictions": "Prohibited",
                "notes": "Except when denatured"
            },
        ]

    def _fetch_annex_iii(self) -> list:
        """Fetch Annex III (Restricted substances)"""
        return [
            {
                "reference_number": "12",
                "chemical_name": "Hydrogen peroxide",
                "cas": "7722-84-1",
                "inci": "Hydrogen Peroxide",
                "maximum_concentration": "12%",
                "product_type": ["hair products", "nail hardening products", "tooth whitening products"],
                "conditions": {
                    "hair_products": "≤12% as released (40 volumes)",
                    "nail_products": "≤2%",
                    "tooth_whitening": "≤6%"
                },
                "warnings": "Contains hydrogen peroxide. Avoid contact with eyes."
            },
            {
                "reference_number": "13",
                "chemical_name": "Salicylic acid and its salts",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "maximum_concentration": "3%",
                "product_type": ["rinse-off products", "leave-on products"],
                "conditions": {
                    "rinse_off": "≤3%",
                    "leave_on": "≤2%",
                    "exceptions": "Not to be used in preparations for children under 3 years"
                },
                "warnings": "Contains salicylic acid. Not to be used for children under 3 years."
            },
            {
                "reference_number": "15",
                "chemical_name": "Benzoic acid, its salts and esters",
                "cas": "65-85-0",
                "inci": "Benzoic Acid",
                "maximum_concentration": "2.5%",
                "product_type": ["all"],
                "conditions": {
                    "as_preservative": "See Annex V",
                    "as_uv_filter": "See Annex VI"
                }
            },
        ]

    def _fetch_annex_iv(self) -> list:
        """Fetch Annex IV (Allowed colorants)"""
        return [
            {
                "reference_number": "1",
                "colour_index": "CI 10006",
                "chemical_name": "Naphthol Yellow S",
                "inci": "CI 10006",
                "restrictions": "Not for use in products applied near the eyes",
                "purity_criteria": "E102"
            },
            {
                "reference_number": "15",
                "colour_index": "CI 77491",
                "chemical_name": "Iron Oxides",
                "inci": "CI 77491",
                "restrictions": "None",
                "purity_criteria": "E172"
            },
        ]

    def _fetch_annex_v(self) -> list:
        """Fetch Annex V (Allowed preservatives)"""
        return [
            {
                "reference_number": "3",
                "chemical_name": "Benzoic acid, its salts and esters",
                "inci": "Benzoic Acid",
                "cas": "65-85-0",
                "maximum_concentration": "0.5%",
                "product_type": ["all"],
                "conditions": "As acid",
                "warnings": None
            },
            {
                "reference_number": "5",
                "chemical_name": "Salicylic acid and its salts",
                "inci": "Salicylic Acid",
                "cas": "69-72-7",
                "maximum_concentration": "0.5%",
                "product_type": ["all"],
                "conditions": "As acid. Not to be used in preparations for children under 3 years except in shampoos",
                "warnings": "Contains salicylic acid"
            },
        ]

    def _fetch_annex_vi(self) -> list:
        """Fetch Annex VI (Allowed UV filters)"""
        return [
            {
                "reference_number": "2",
                "chemical_name": "Homosalate",
                "inci": "Homosalate",
                "cas": "118-56-9",
                "maximum_concentration": "10%",
                "product_type": ["all"],
                "conditions": None,
                "warnings": None
            },
            {
                "reference_number": "5",
                "chemical_name": "Octyl methoxycinnamate / Ethylhexyl methoxycinnamate",
                "inci": "Ethylhexyl Methoxycinnamate",
                "cas": "5466-77-3",
                "maximum_concentration": "10%",
                "product_type": ["all"],
                "conditions": None,
                "warnings": None
            },
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw EU data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": last_update.isoformat() if last_update else None,
            "effective_date": last_update.isoformat() if last_update else None,
            "version": last_update_str.replace("-", "") if last_update_str else None,
        }
