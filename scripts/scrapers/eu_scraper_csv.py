"""EU cosmetics regulation scraper - CSV/API Implementation"""

from typing import Dict, Any, List
import requests
from pathlib import Path
import sys
import time
import csv
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base_scraper import BaseScraper
from config import SCRAPING_CONFIG, RAW_DATA_DIR


class EUScraperCSV(BaseScraper):
    """Scraper for EU cosmetics regulations using OpenDataSoft API and CSV data"""

    def __init__(self):
        super().__init__("EU")

        # OpenDataSoft API endpoints for EU CosIng data
        self.api_base = "https://public.opendatasoft.com/api/records/1.0/search/"
        self.dataset_id = "cosmetic-ingredient-database-ingredients-and-fragrance-inventory"

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch EU cosmetics regulation data from OpenDataSoft API

        Downloads CosIng ingredient data via OpenDataSoft public API

        Returns:
            Raw regulation data with all ingredients
        """
        self.logger.info("Fetching EU cosmetics regulation data from OpenDataSoft API")

        try:
            csv_dir = RAW_DATA_DIR / self.jurisdiction_code / "csv"
            csv_dir.mkdir(parents=True, exist_ok=True)

            # Download all CosIng ingredients
            all_ingredients = self._fetch_all_ingredients()

            self.logger.info(f"Downloaded {len(all_ingredients)} total ingredients from CosIng")

            # Group ingredients by Annex
            annexes = self._group_by_annex(all_ingredients)

            data = {
                "source": "European Commission - CosIng Database (OpenDataSoft API)",
                "regulation": "Regulation (EC) No 1223/2009",
                "published_date": self.jurisdiction_config.get('published_date', '2024-04-04'),
                "effective_date": self.jurisdiction_config.get('effective_date', '2024-04-24'),
                "last_update": self.jurisdiction_config.get('effective_date', '2024-04-24'),
                "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "annexes": annexes,
                "api_source": "OpenDataSoft"
            }

            total_ingredients = sum(len(annex.get('ingredients', [])) for annex in annexes.values())
            self.logger.info(f"Successfully fetched {total_ingredients} ingredients across {len(annexes)} EU Annexes")

            return data

        except Exception as e:
            self.logger.error(f"Failed to fetch EU data: {e}", exc_info=True)
            raise Exception(f"EU CSV scraper failed: {e}") from e

    def _fetch_all_ingredients(self) -> List[Dict[str, Any]]:
        """Fetch all ingredients from OpenDataSoft API with pagination"""

        all_records = []
        rows_per_page = 1000
        start = 0

        while True:
            try:
                time.sleep(0.5)  # Be respectful to API

                params = {
                    "dataset": self.dataset_id,
                    "rows": rows_per_page,
                    "start": start,
                    "format": "json"
                }

                headers = {
                    'User-Agent': SCRAPING_CONFIG['user_agent']
                }

                response = requests.get(
                    self.api_base,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                records = data.get('records', [])

                if not records:
                    break

                all_records.extend(records)
                self.logger.info(f"Fetched {len(all_records)} ingredients so far...")

                # Check if we've reached the end
                if len(records) < rows_per_page:
                    break

                start += rows_per_page

            except Exception as e:
                self.logger.error(f"Error fetching page at start={start}: {e}")
                break

        return all_records

    def _group_by_annex(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group ingredients by their Annex"""

        annexes = {
            "annex_ii": {
                "name": "Prohibited substances",
                "description": "List of substances prohibited in cosmetic products",
                "ingredients": []
            },
            "annex_iii": {
                "name": "Restricted substances",
                "description": "List of substances subject to restrictions",
                "ingredients": []
            },
            "annex_iv": {
                "name": "Allowed colorants",
                "description": "List of colorants allowed for use in cosmetic products",
                "ingredients": []
            },
            "annex_v": {
                "name": "Allowed preservatives",
                "description": "List of preservatives allowed for use in cosmetic products",
                "ingredients": []
            },
            "annex_vi": {
                "name": "Allowed UV filters",
                "description": "List of UV filters allowed for use in cosmetic products",
                "ingredients": []
            }
        }

        for record in ingredients:
            fields = record.get('fields', {})

            # Determine which annex this ingredient belongs to
            # Based on the CosIng data structure
            annex_info = fields.get('annex', '')
            inci_name = fields.get('inci_name', '')
            chem_name = fields.get('chem_iupac_name', '')
            cas_no = fields.get('cas', '')
            ec_no = fields.get('ec', '')

            # Create ingredient entry
            ingredient = {
                "ingredient_name": inci_name or chem_name,
                "inci_name": inci_name,
                "cas_no": cas_no,
                "ec_no": ec_no,
                "chemical_name": chem_name,
                "function": fields.get('functions', ''),
                "restrictions": fields.get('restrictions', ''),
                "conditions": fields.get('conditions', ''),
                "annex_info": annex_info
            }

            # Determine category based on annex information
            if annex_info:
                annex_lower = annex_info.lower()

                if 'ii' in annex_lower or 'prohibited' in annex_lower:
                    ingredient['category'] = 'prohibited'
                    ingredient['restriction_type'] = 'prohibited'
                    ingredient['status'] = 'prohibited'
                    annexes['annex_ii']['ingredients'].append(ingredient)

                elif 'iii' in annex_lower or 'restricted' in annex_lower:
                    ingredient['category'] = 'restricted'
                    ingredient['restriction_type'] = 'restricted'
                    ingredient['status'] = 'restricted'
                    annexes['annex_iii']['ingredients'].append(ingredient)

                elif 'iv' in annex_lower or 'colorant' in annex_lower or 'colour' in annex_lower:
                    ingredient['category'] = 'colorant'
                    ingredient['restriction_type'] = 'colorant'
                    ingredient['status'] = 'allowed'
                    annexes['annex_iv']['ingredients'].append(ingredient)

                elif 'v' in annex_lower or 'preservative' in annex_lower:
                    ingredient['category'] = 'preservative'
                    ingredient['restriction_type'] = 'preservative'
                    ingredient['status'] = 'allowed'
                    annexes['annex_v']['ingredients'].append(ingredient)

                elif 'vi' in annex_lower or 'uv' in annex_lower or 'filter' in annex_lower:
                    ingredient['category'] = 'uv_filter'
                    ingredient['restriction_type'] = 'uv_filter'
                    ingredient['status'] = 'allowed'
                    annexes['annex_vi']['ingredients'].append(ingredient)

        return annexes

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw EU data"""

        # Count total ingredients across all annexes
        total_ingredients = 0
        if "annexes" in raw_data:
            for annex_data in raw_data["annexes"].values():
                total_ingredients += len(annex_data.get("ingredients", []))

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": raw_data.get("published_date"),
            "effective_date": raw_data.get("effective_date"),
            "version": raw_data.get("effective_date", "").replace("-", "") if raw_data.get("effective_date") else None,
            "total_ingredients": total_ingredients,
            "fetch_timestamp": raw_data.get("fetch_timestamp"),
            "is_sample_data": False,
            "api_source": raw_data.get("api_source")
        }
