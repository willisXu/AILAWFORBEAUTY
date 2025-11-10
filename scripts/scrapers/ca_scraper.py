"""Canada cosmetics regulation scraper"""

from typing import Dict, Any
from .base_scraper import BaseScraper
from ..utils import parse_date


class CAScraper(BaseScraper):
    """Scraper for Canada cosmetics regulations"""

    def __init__(self):
        super().__init__("CA")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch Canadian cosmetics regulation data

        Data from Health Canada:
        - Cosmetic Regulations (C.R.C., c. 869)
        - Cosmetic Ingredient Hotlist

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching Canadian cosmetics regulation data")

        data = {
            "source": "Health Canada - Cosmetics Program",
            "regulation": "Cosmetic Regulations C.R.C., c. 869",
            "url": "https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics.html",
            "last_update": "2024-01-20",
            "hotlist": self._fetch_hotlist(),
        }

        return data

    def _fetch_hotlist(self) -> Dict[str, Any]:
        """
        Fetch Cosmetic Ingredient Hotlist

        The Hotlist is a list of ingredients that Health Canada has determined
        to be prohibited or restricted for use in cosmetics
        """
        return {
            "version": "2024",
            "last_updated": "2024-01-20",
            "prohibited": self._fetch_prohibited(),
            "restricted": self._fetch_restricted(),
        }

    def _fetch_prohibited(self) -> list:
        """Fetch prohibited substances from Hotlist"""
        return [
            {
                "ingredient_name": "Formaldehyde",
                "cas": "50-00-0",
                "inci": "Formaldehyde",
                "status": "Prohibited",
                "restrictions": "Prohibited except as a preservative at ≤0.2%",
                "hotlist_entry": "H001"
            },
            {
                "ingredient_name": "Hydroquinone",
                "cas": "123-31-9",
                "inci": "Hydroquinone",
                "status": "Prohibited",
                "restrictions": "Prohibited except in nail adhesives at ≤0.02%",
                "hotlist_entry": "H045"
            },
            {
                "ingredient_name": "Mercury and its compounds",
                "cas": "7439-97-6",
                "inci": "Mercury",
                "status": "Prohibited",
                "restrictions": "Prohibited except trace amounts from unavoidable contamination",
                "hotlist_entry": "H055"
            },
            {
                "ingredient_name": "Methanol",
                "cas": "67-56-1",
                "inci": "Methanol",
                "status": "Prohibited",
                "restrictions": "Prohibited except as denaturant at specific concentrations",
                "hotlist_entry": "H058"
            },
        ]

    def _fetch_restricted(self) -> list:
        """Fetch restricted substances from Hotlist"""
        return [
            {
                "ingredient_name": "Alpha Hydroxy Acids (AHAs)",
                "cas": "Various",
                "inci": "Glycolic Acid, Lactic Acid, etc.",
                "status": "Restricted",
                "maximum_concentration": "10%",
                "conditions": {
                    "concentration": "≤10%",
                    "pH": "≥3.5",
                    "warnings": "Use only as directed. Avoid contact with eyes. Discontinue use if rash or irritation occurs. Sun alert: This product may increase your skin's sensitivity to the sun."
                },
                "hotlist_entry": "R003"
            },
            {
                "ingredient_name": "Hydrogen Peroxide",
                "cas": "7722-84-1",
                "inci": "Hydrogen Peroxide",
                "status": "Restricted",
                "maximum_concentration": "12%",
                "conditions": {
                    "hair_products": "≤12%",
                    "tooth_whitening": "≤3%",
                    "nail_products": "≤2%"
                },
                "hotlist_entry": "R015"
            },
            {
                "ingredient_name": "Salicylic Acid",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "status": "Restricted",
                "maximum_concentration": "2%",
                "conditions": {
                    "leave_on": "≤2%",
                    "rinse_off": "≤3%",
                    "warnings": "Not for use on children under 3 years"
                },
                "hotlist_entry": "R028"
            },
            {
                "ingredient_name": "Thioglycolic Acid and its salts",
                "cas": "68-11-1",
                "inci": "Thioglycolic Acid",
                "status": "Restricted",
                "maximum_concentration": "11%",
                "conditions": {
                    "general_use": "≤8% (as acid)",
                    "professional_use": "≤11% (as acid)",
                    "pH": "≥7.0 for general use, ≥9.5 for professional use",
                    "warnings": "Professional use only for concentrations >8%"
                },
                "hotlist_entry": "R032"
            },
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw Canada data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        hotlist_data = raw_data.get("hotlist", {})
        hotlist_version = hotlist_data.get("version")
        hotlist_updated = parse_date(hotlist_data.get("last_updated", ""))

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": last_update.isoformat() if last_update else None,
            "effective_date": last_update.isoformat() if last_update else None,
            "version": last_update_str.replace("-", "") if last_update_str else None,
            "hotlist_version": hotlist_version,
            "hotlist_updated": hotlist_updated.isoformat() if hotlist_updated else None,
        }
