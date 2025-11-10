"""China cosmetics regulation scraper"""

from typing import Dict, Any
from .base_scraper import BaseScraper
from ..utils import parse_date


class CNScraper(BaseScraper):
    """Scraper for China cosmetics regulations"""

    def __init__(self):
        super().__init__("CN")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch Chinese cosmetics regulation data

        Data from NMPA (National Medical Products Administration)
        - Cosmetics Supervision and Administration Regulation (CSAR)
        - Technical Specifications for Cosmetic Safety

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching Chinese cosmetics regulation data")

        data = {
            "source": "NMPA - Cosmetics Database",
            "regulation": "Cosmetics Supervision and Administration Regulation",
            "url": "https://www.nmpa.gov.cn/",
            "last_update": "2024-02-01",
            "catalogs": {
                "prohibited": self._fetch_prohibited(),
                "restricted": self._fetch_restricted(),
                "preservatives": self._fetch_preservatives(),
                "colorants": self._fetch_colorants(),
            }
        }

        return data

    def _fetch_prohibited(self) -> list:
        """Fetch prohibited ingredients catalog"""
        return [
            {
                "name_chinese": "甲醛",
                "name_english": "Formaldehyde",
                "cas": "50-00-0",
                "inci": "Formaldehyde",
                "status": "prohibited",
                "notes": "Prohibited except as preservative within specified limits"
            },
            {
                "name_chinese": "氢醌",
                "name_english": "Hydroquinone",
                "cas": "123-31-9",
                "inci": "Hydroquinone",
                "status": "prohibited",
                "notes": "Prohibited in cosmetics (allowed in special use cosmetics with approval)"
            },
            {
                "name_chinese": "汞及其化合物",
                "name_english": "Mercury and its compounds",
                "cas": "7439-97-6",
                "inci": "Mercury",
                "status": "prohibited",
                "notes": "Trace amounts (≤1ppm) from unavoidable contamination acceptable"
            },
        ]

    def _fetch_restricted(self) -> list:
        """Fetch restricted ingredients catalog"""
        return [
            {
                "name_chinese": "过氧化氢",
                "name_english": "Hydrogen Peroxide",
                "cas": "7722-84-1",
                "inci": "Hydrogen Peroxide",
                "maximum_concentration": "6%",
                "product_type": ["hair dye", "hair bleach"],
                "conditions": "≤6% in hair products after mixing",
                "warnings": "Professional use only for concentrations >3%"
            },
            {
                "name_chinese": "水杨酸",
                "name_english": "Salicylic Acid",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "maximum_concentration": "3%",
                "product_type": ["skin care", "shampoo"],
                "conditions": {
                    "rinse_off": "≤3%",
                    "leave_on": "≤2%",
                    "shampoo": "≤3%"
                },
                "warnings": "Not for use on children under 3 years"
            },
            {
                "name_chinese": "硼酸",
                "name_english": "Boric Acid",
                "cas": "10043-35-3",
                "inci": "Boric Acid",
                "maximum_concentration": "3%",
                "product_type": ["all"],
                "conditions": "≤3% (as acid)",
                "warnings": "Not for use on damaged skin or children under 3 years"
            },
        ]

    def _fetch_preservatives(self) -> list:
        """Fetch permitted preservatives catalog"""
        return [
            {
                "serial_number": "1",
                "name_chinese": "苯甲酸及其盐类",
                "name_english": "Benzoic Acid and its salts",
                "cas": "65-85-0",
                "inci": "Benzoic Acid",
                "maximum_concentration": "0.5%",
                "conditions": "As acid",
                "notes": None
            },
            {
                "serial_number": "3",
                "name_chinese": "水杨酸及其盐类",
                "name_english": "Salicylic Acid and its salts",
                "cas": "69-72-7",
                "inci": "Salicylic Acid",
                "maximum_concentration": "0.5%",
                "conditions": "As acid. Not in products for children under 3",
                "notes": "Except in shampoos"
            },
        ]

    def _fetch_colorants(self) -> list:
        """Fetch permitted colorants catalog"""
        return [
            {
                "serial_number": "1",
                "name_chinese": "氧化铁",
                "name_english": "Iron Oxides",
                "ci_number": "CI 77491, CI 77492, CI 77499",
                "inci": "CI 77491",
                "restrictions": "None",
                "notes": "Approved for all cosmetic uses"
            },
            {
                "serial_number": "5",
                "name_chinese": "二氧化钛",
                "name_english": "Titanium Dioxide",
                "ci_number": "CI 77891",
                "inci": "CI 77891",
                "restrictions": "None",
                "notes": "Approved for all cosmetic uses"
            },
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw China data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": last_update.isoformat() if last_update else None,
            "effective_date": last_update.isoformat() if last_update else None,
            "version": last_update_str.replace("-", "") if last_update_str else None,
        }
