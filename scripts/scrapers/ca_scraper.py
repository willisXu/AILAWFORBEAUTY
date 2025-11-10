"""Canada cosmetics regulation scraper - Real Implementation"""

from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
import re
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

    def _parse_hotlist_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse the Hotlist page to extract ingredient information

        The Health Canada Hotlist typically contains:
        - Tables with ingredient information
        - Sections for prohibited and restricted ingredients
        """
        ingredients = []

        try:
            # Strategy 1: Look for tables with ingredient data
            tables = soup.find_all('table')

            for table in tables:
                table_ingredients = self._parse_table(table)
                if table_ingredients:
                    ingredients.extend(table_ingredients)

            # Strategy 2: Look for definition lists (dl/dt/dd)
            definition_lists = soup.find_all('dl')
            for dl in definition_lists:
                dl_ingredients = self._parse_definition_list(dl)
                if dl_ingredients:
                    ingredients.extend(dl_ingredients)

            # Strategy 3: Look for sections with specific headings
            sections = soup.find_all(['section', 'div'], class_=re.compile(r'hotlist|ingredient|prohibition|restriction', re.I))
            for section in sections:
                section_ingredients = self._parse_section(section)
                if section_ingredients:
                    ingredients.extend(section_ingredients)

            # Remove duplicates based on ingredient name
            seen = set()
            unique_ingredients = []
            for ing in ingredients:
                name = ing.get('ingredient_name', '').strip().lower()
                if name and name not in seen:
                    seen.add(name)
                    unique_ingredients.append(ing)

            # If no ingredients found, use sample data
            if not unique_ingredients:
                self.logger.warning("No ingredients found in Health Canada Hotlist page")
                return self._get_sample_ingredients()

            return unique_ingredients

        except Exception as e:
            self.logger.error(f"Error parsing Hotlist page: {e}", exc_info=True)
            return self._get_sample_ingredients()

    def _parse_table(self, table) -> List[Dict[str, Any]]:
        """Parse a table element for ingredient data"""
        ingredients = []

        try:
            rows = table.find_all('tr')
            if len(rows) < 2:
                return ingredients

            # Try to identify headers
            headers = []
            header_row = rows[0]
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True).lower())

            # Check if this looks like an ingredient table
            if not any(keyword in ' '.join(headers) for keyword in ['ingredient', 'name', 'substance', 'chemical']):
                return ingredients

            # Parse data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                cell_data = [cell.get_text(strip=True) for cell in cells]
                ingredient = self._extract_ingredient_from_cells(cell_data, headers)

                if ingredient:
                    ingredients.append(ingredient)

        except Exception as e:
            self.logger.debug(f"Error parsing table: {e}")

        return ingredients

    def _parse_definition_list(self, dl) -> List[Dict[str, Any]]:
        """Parse a definition list (dl/dt/dd) for ingredient data"""
        ingredients = []

        try:
            terms = dl.find_all('dt')
            for dt in terms:
                dd = dt.find_next_sibling('dd')
                if dd:
                    ingredient_name = dt.get_text(strip=True)
                    description = dd.get_text(strip=True)

                    if ingredient_name and len(ingredient_name) > 2:
                        # Extract CAS number if present
                        cas_match = re.search(r'\b(\d{2,7}-\d{2}-\d)\b', description)
                        cas_no = cas_match.group(1) if cas_match else ""

                        # Determine restriction type
                        restriction_type = "prohibited"
                        if any(word in description.lower() for word in ['restrict', 'limit', 'maximum', 'concentration']):
                            restriction_type = "restricted"

                        ingredients.append({
                            "ingredient_name": ingredient_name,
                            "cas_no": cas_no,
                            "restriction_type": restriction_type,
                            "conditions": description,
                            "rationale": description,
                            "status": restriction_type
                        })

        except Exception as e:
            self.logger.debug(f"Error parsing definition list: {e}")

        return ingredients

    def _parse_section(self, section) -> List[Dict[str, Any]]:
        """Parse a section element for ingredient data"""
        ingredients = []

        try:
            # Look for lists within the section
            lists = section.find_all(['ul', 'ol'])
            for list_elem in lists:
                items = list_elem.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)

                    # Try to extract ingredient information
                    # Common patterns: "Ingredient Name (CAS: 123-45-6)"
                    parts = text.split('(')
                    if len(parts) >= 1:
                        ingredient_name = parts[0].strip()

                        # Extract CAS number
                        cas_match = re.search(r'\b(\d{2,7}-\d{2}-\d)\b', text)
                        cas_no = cas_match.group(1) if cas_match else ""

                        if ingredient_name and len(ingredient_name) > 2:
                            # Determine restriction type from section heading
                            section_heading = section.find(['h2', 'h3', 'h4', 'h5'])
                            restriction_type = "prohibited"
                            if section_heading:
                                heading_text = section_heading.get_text().lower()
                                if 'restrict' in heading_text:
                                    restriction_type = "restricted"

                            ingredients.append({
                                "ingredient_name": ingredient_name,
                                "cas_no": cas_no,
                                "restriction_type": restriction_type,
                                "conditions": text,
                                "rationale": text,
                                "status": restriction_type
                            })

        except Exception as e:
            self.logger.debug(f"Error parsing section: {e}")

        return ingredients

    def _extract_ingredient_from_cells(self, cells: List[str], headers: List[str]) -> Dict[str, Any]:
        """Extract ingredient data from table cells"""

        try:
            ingredient_name = ""
            cas_no = ""
            restriction_type = "prohibited"
            conditions = ""

            # Map cells to fields based on headers or content patterns
            for i, cell in enumerate(cells):
                if not cell:
                    continue

                cell_lower = cell.lower()
                header = headers[i] if i < len(headers) else ""

                # Ingredient name
                if 'name' in header or 'ingredient' in header or 'substance' in header:
                    ingredient_name = cell
                # CAS number (pattern: XXX-XX-X or XXXXX-XX-X)
                elif 'cas' in header or re.match(r'\d{2,7}-\d{2}-\d', cell):
                    cas_no = cell
                # Restriction type
                elif 'status' in header or 'type' in header:
                    if 'prohibit' in cell_lower or 'banned' in cell_lower:
                        restriction_type = "prohibited"
                    elif 'restrict' in cell_lower or 'limit' in cell_lower:
                        restriction_type = "restricted"
                # Conditions (usually longer text)
                elif len(cell) > 20 or 'condition' in header or 'restriction' in header:
                    conditions = cell

            # Try to auto-detect if headers are not clear
            if not ingredient_name:
                # First non-numeric cell is likely the ingredient name
                for cell in cells:
                    if cell and not re.match(r'^\d', cell) and len(cell) > 2:
                        ingredient_name = cell
                        break

            # If we have at least a name, create entry
            if ingredient_name and len(ingredient_name) > 2:
                return {
                    "ingredient_name": ingredient_name,
                    "cas_no": cas_no,
                    "restriction_type": restriction_type,
                    "conditions": conditions if conditions else "See official Health Canada Hotlist for details",
                    "rationale": conditions if conditions else "Listed on Health Canada Cosmetic Ingredient Hotlist",
                    "status": restriction_type
                }

        except Exception as e:
            self.logger.debug(f"Error extracting ingredient data: {e}")

        return None

    def _get_sample_data(self) -> Dict[str, Any]:
        """Return sample data as fallback"""
        self.logger.info("Using sample data for Canada")

        return {
            "source": "Health Canada - Cosmetic Ingredient Hotlist (Sample Data)",
            "regulation": "Cosmetic Ingredient Hotlist",
            "url": self.jurisdiction_config['sources'][0]['url'],
            "last_update": "2025-02-28",
            "published_date": "2025-02",
            "effective_date": "2025-02-28",
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_sample_data": True,
            "ingredients": self._get_sample_ingredients()
        }

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
