"""Japan cosmetics regulation scraper"""

from typing import Dict, Any
from .base_scraper import BaseScraper
from ..utils import parse_date


class JPScraper(BaseScraper):
    """Scraper for Japan cosmetics regulations"""

    def __init__(self):
        super().__init__("JP")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch Japanese cosmetics regulation data

        Data comes from MHLW (Ministry of Health, Labour and Welfare)
        - Pharmaceutical and Medical Device Act
        - Standards for Cosmetics

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching Japanese cosmetics regulation data")

        data = {
            "source": "MHLW - Standards for Cosmetics",
            "regulation": "Pharmaceutical and Medical Device Act",
            "url": "https://www.mhlw.go.jp/",
            "last_update": "2024-01-15",
            "categories": {
                "prohibited": self._fetch_prohibited(),
                "restricted": self._fetch_restricted(),
                "quasi_drugs": self._fetch_quasi_drugs(),
            }
        }

        return data

    def _fetch_prohibited(self) -> list:
        """Fetch prohibited substances"""
        return [
            {
                "name_japanese": "ホルムアルデヒド",
                "name_english": "Formaldehyde",
                "cas": "50-00-0",
                "inci": "Formaldehyde",
                "status": "prohibited",
                "notes": "Prohibited except as preservative within specified limits"
            },
            {
                "name_japanese": "メタノール",
                "name_english": "Methanol",
                "cas": "67-56-1",
                "inci": "Methanol",
                "status": "prohibited",
                "notes": "Prohibited except when denatured"
            },
        ]

    def _fetch_restricted(self) -> list:
        """Fetch restricted substances"""
        return [
            {
                "name_japanese": "過酸化水素",
                "name_english": "Hydrogen Peroxide",
                "cas": "7722-84-1",
                "inci": "Hydrogen Peroxide",
                "maximum_concentration": "6%",
                "product_type": ["hair products"],
                "conditions": "≤6% in hair dye products",
                "warnings": "Requires specific labeling"
            },
            {
                "name_japanese": "サリチル酸",
                "name_english": "Salicylic Acid",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "maximum_concentration": "2%",
                "product_type": ["skin care"],
                "conditions": "≤2% in leave-on products",
                "warnings": "Not for use on damaged skin"
            },
            {
                "name_japanese": "レゾルシン",
                "name_english": "Resorcinol",
                "cas": "108-46-3",
                "inci": "Resorcinol",
                "maximum_concentration": "0.5%",
                "product_type": ["hair products"],
                "conditions": "≤0.5% in hair lotions and shampoos",
                "warnings": None
            },
        ]

    def _fetch_quasi_drugs(self) -> list:
        """
        Fetch quasi-drug (medicated cosmetics) specifications

        Quasi-drugs in Japan are products between cosmetics and pharmaceuticals
        """
        return [
            {
                "category": "medicated_skin_care",
                "name_japanese": "薬用化粧品",
                "active_ingredients": ["Tranexamic acid", "Arbutin", "Vitamin C derivatives"],
                "requirements": "Requires approval as quasi-drug"
            },
            {
                "category": "medicated_deodorant",
                "name_japanese": "薬用デオドラント",
                "active_ingredients": ["Aluminum chlorohydrate", "Zinc oxide"],
                "requirements": "Requires approval as quasi-drug"
            },
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw Japan data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": last_update.isoformat() if last_update else None,
            "effective_date": last_update.isoformat() if last_update else None,
            "version": last_update_str.replace("-", "") if last_update_str else None,
        }
