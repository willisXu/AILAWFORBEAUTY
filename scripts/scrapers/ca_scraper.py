"""Canada cosmetics regulation scraper - Real Implementation"""

from typing import Dict, Any, List
import requests
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base_scraper import BaseScraper
from utils import parse_date
from config import SCRAPING_CONFIG


class CAScraper(BaseScraper):
    """Scraper for Canada cosmetics regulations - Health Canada Hotlist"""

    def __init__(self):
        super().__init__("CA")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch Canadian cosmetics regulation data from Health Canada Hotlist

        Source: Health Canada Cosmetic Ingredient Hotlist
        URL: https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics/cosmetic-ingredient-hotlist-prohibited-restricted-ingredients.html

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching Canadian cosmetics regulation data from Health Canada")

        try:
            url = self.jurisdiction_config['sources'][0]['url']

            # Add delay to be respectful to the server
            time.sleep(1)

            # Fetch the webpage
            headers = {
                'User-Agent': SCRAPING_CONFIG['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=SCRAPING_CONFIG['timeout'],
                allow_redirects=True
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract ingredients
            ingredients = self._parse_hotlist_page(soup)

            data = {
                "source": "Health Canada - Cosmetic Ingredient Hotlist",
                "regulation": "Cosmetic Ingredient Hotlist",
                "url": url,
                "published_date": self.jurisdiction_config.get('published_date', '2025-02'),
                "effective_date": self.jurisdiction_config.get('effective_date', '2025-02-28'),
                "last_update": self.jurisdiction_config.get('effective_date', '2025-02-28'),
                "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "raw_html_length": len(response.content),
                "ingredients_count": len(ingredients),
                "ingredients": ingredients
            }

            self.logger.info(f"Successfully fetched {len(ingredients)} ingredients from Health Canada Hotlist")

            return data

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch Health Canada Hotlist: {e}")
            raise Exception(f"Canada scraper failed: Unable to fetch data from Health Canada website") from e
        except Exception as e:
            self.logger.error(f"Error parsing Health Canada data: {e}", exc_info=True)
            raise Exception(f"Canada scraper failed: Error parsing data from Health Canada Hotlist") from e

    def _get_sample_ingredients(self) -> List[Dict[str, Any]]:
        """Sample ingredients for testing/fallback"""
        return [
            {
                "ingredient_name": "Formaldehyde",
                "cas_no": "50-00-0",
                "restriction_type": "prohibited",
                "conditions": "Prohibited except as a preservative at concentrations ≤0.2%",
                "rationale": "Prohibited in cosmetics except as preservative within limits",
                "status": "prohibited"
            },
            {
                "ingredient_name": "Mercury and its compounds",
                "cas_no": "7439-97-6",
                "restriction_type": "prohibited",
                "conditions": "Prohibited in all cosmetic products",
                "rationale": "Highly toxic heavy metal, prohibited in all uses",
                "status": "prohibited"
            },
            {
                "ingredient_name": "Lead and its compounds",
                "cas_no": "7439-92-1",
                "restriction_type": "prohibited",
                "conditions": "Prohibited as ingredients; trace amounts from impurities acceptable",
                "rationale": "Toxic heavy metal, prohibited as ingredient",
                "status": "prohibited"
            },
            {
                "ingredient_name": "Hydroquinone",
                "cas_no": "123-31-9",
                "restriction_type": "restricted",
                "conditions": "Restricted to ≤2% in hair dyes, nail products",
                "rationale": "Allowed only in specific products with concentration limits",
                "status": "restricted"
            },
            {
                "ingredient_name": "Triclosan",
                "cas_no": "3380-34-5",
                "restriction_type": "restricted",
                "conditions": "Restricted to ≤0.3% in mouthwash, toothpaste, deodorant",
                "rationale": "Antimicrobial agent with usage restrictions",
                "status": "restricted"
            },
            {
                "ingredient_name": "Hydrogen Peroxide",
                "cas_no": "7722-84-1",
                "restriction_type": "restricted",
                "conditions": "Maximum 12% in hair products, 3% in tooth whitening, 2% in nail products",
                "rationale": "Oxidizing agent with concentration limits",
                "status": "restricted"
            },
            {
                "ingredient_name": "Salicylic Acid",
                "cas_no": "69-72-7",
                "restriction_type": "restricted",
                "conditions": "Maximum 2% in leave-on products, 3% in rinse-off products. Not for children under 3 years",
                "rationale": "Keratolytic agent with age and concentration restrictions",
                "status": "restricted"
            }
        ]

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw Canada data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": raw_data.get("published_date"),
            "effective_date": raw_data.get("effective_date"),
            "version": last_update_str.replace("-", "") if last_update_str else None,
            "total_ingredients": len(raw_data.get("ingredients", [])),
            "fetch_timestamp": raw_data.get("fetch_timestamp"),
            "is_sample_data": raw_data.get("is_sample_data", False)
        }
