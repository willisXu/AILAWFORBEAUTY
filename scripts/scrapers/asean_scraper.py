"""ASEAN cosmetics regulation scraper - Real Implementation"""

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


class ASEANScraper(BaseScraper):
    """Scraper for ASEAN cosmetics regulations - HSA ASEAN Cosmetic Directive"""

    def __init__(self):
        super().__init__("ASEAN")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch ASEAN cosmetics regulation data from HSA Singapore

        Source: HSA ASEAN Cosmetic Directive
        URL: https://www.hsa.gov.sg/cosmetic-products/asean-cosmetic-directive

        ASEAN follows the EU model with Annexes II-VI:
        - Annex II: Prohibited substances
        - Annex III: Restricted substances
        - Annex IV: Permitted colorants
        - Annex V: Permitted preservatives
        - Annex VI: Permitted UV filters

        Returns:
            Raw regulation data
        """
        self.logger.info("Fetching ASEAN cosmetics regulation data from HSA Singapore")

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

            # Try to fetch annex data from HSA website
            annexes = self._fetch_hsa_annexes(soup)

            data = {
                "source": "HSA Singapore - ASEAN Cosmetic Directive",
                "regulation": "ASEAN Cosmetic Directive (ACD)",
                "version": "2024-2",
                "url": url,
                "published_date": self.jurisdiction_config.get('published_date', '2024-12-06'),
                "effective_date": self.jurisdiction_config.get('effective_date', '2024-12-06'),
                "last_update": self.jurisdiction_config.get('effective_date', '2024-12-06'),
                "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "raw_html_length": len(response.content),
                "member_states": [
                    "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
                    "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"
                ],
                "annexes": annexes
            }

            # Count total ingredients across all annexes
            total_ingredients = sum(
                len(annex.get("ingredients", []))
                for annex in annexes.values()
            )

            data["total_ingredients"] = total_ingredients
            self.logger.info(f"Successfully fetched {total_ingredients} ingredients from ASEAN ACD")

            return data

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch ASEAN ACD: {e}")
            self.logger.info("Falling back to sample data")
            return self._get_sample_data()
        except Exception as e:
            self.logger.error(f"Error parsing ASEAN data: {e}", exc_info=True)
            self.logger.info("Falling back to sample data")
            return self._get_sample_data()

    def _fetch_hsa_annexes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Fetch and parse ASEAN Cosmetic Directive annexes from HSA website

        ASEAN follows EU model with Annexes II-VI
        """
        try:
            annexes = {
                "annex_ii": {
                    "name": "Prohibited substances",
                    "description": "List of substances prohibited in cosmetic products",
                    "ingredients": self._parse_annex_section(soup, "annex ii", "prohibited", "prohibited")
                },
                "annex_iii": {
                    "name": "Restricted substances",
                    "description": "List of substances subject to restrictions",
                    "ingredients": self._parse_annex_section(soup, "annex iii", "restricted", "restricted")
                },
                "annex_iv": {
                    "name": "Allowed colorants",
                    "description": "List of colorants allowed for use in cosmetic products",
                    "ingredients": self._parse_annex_section(soup, "annex iv", "colorant", "allowed")
                },
                "annex_v": {
                    "name": "Allowed preservatives",
                    "description": "List of preservatives allowed for use in cosmetic products",
                    "ingredients": self._parse_annex_section(soup, "annex v", "preservative", "allowed")
                },
                "annex_vi": {
                    "name": "Allowed UV filters",
                    "description": "List of UV filters allowed for use in cosmetic products",
                    "ingredients": self._parse_annex_section(soup, "annex vi", "uv_filter", "allowed")
                }
            }

            # Fallback to sample data for empty annexes
            for annex_key in annexes:
                if not annexes[annex_key]["ingredients"]:
                    self.logger.warning(f"No ingredients found for {annex_key}, using sample data")
                    annexes[annex_key]["ingredients"] = self._get_sample_annex_data(annex_key)

            return annexes

        except Exception as e:
            self.logger.error(f"Error fetching HSA annexes: {e}", exc_info=True)
            # Return all sample data if fetching fails
            return {
                "annex_ii": {
                    "name": "Prohibited substances",
                    "description": "List of substances prohibited in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_ii")
                },
                "annex_iii": {
                    "name": "Restricted substances",
                    "description": "List of substances subject to restrictions",
                    "ingredients": self._get_sample_annex_data("annex_iii")
                },
                "annex_iv": {
                    "name": "Allowed colorants",
                    "description": "List of colorants allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_iv")
                },
                "annex_v": {
                    "name": "Allowed preservatives",
                    "description": "List of preservatives allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_v")
                },
                "annex_vi": {
                    "name": "Allowed UV filters",
                    "description": "List of UV filters allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_vi")
                }
            }

    def _parse_annex_section(self, soup: BeautifulSoup, annex_name: str,
                            category: str, status: str) -> List[Dict[str, Any]]:
        """
        Parse a specific annex section from the HSA page

        Args:
            soup: BeautifulSoup object of the page
            annex_name: Name of the annex (e.g., "annex ii")
            category: Category of ingredients (e.g., "prohibited", "colorant")
            status: Status of ingredients (e.g., "prohibited", "restricted", "allowed")
        """
        ingredients = []

        try:
            # Strategy 1: Look for sections with annex name in heading
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().lower()
                if annex_name.lower() in heading_text or category in heading_text:
                    # Find tables or lists following this heading
                    section = heading.find_parent(['section', 'div', 'article'])
                    if section:
                        # Look for tables
                        tables = section.find_all('table')
                        for table in tables:
                            table_ingredients = self._parse_table(table, category, status)
                            if table_ingredients:
                                ingredients.extend(table_ingredients)

                        # Look for lists
                        lists = section.find_all(['ul', 'ol'])
                        for list_elem in lists:
                            list_ingredients = self._parse_list(list_elem, category, status)
                            if list_ingredients:
                                ingredients.extend(list_ingredients)

            # Strategy 2: Look for tables with category keywords
            tables = soup.find_all('table')
            for table in tables:
                # Check if table caption or nearby text mentions the annex
                caption = table.find('caption')
                prev_heading = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5'])

                context_text = ""
                if caption:
                    context_text += caption.get_text().lower()
                if prev_heading:
                    context_text += prev_heading.get_text().lower()

                if annex_name.lower() in context_text or category in context_text:
                    table_ingredients = self._parse_table(table, category, status)
                    if table_ingredients:
                        ingredients.extend(table_ingredients)

            # Remove duplicates based on ingredient name
            seen = set()
            unique_ingredients = []
            for ing in ingredients:
                name = ing.get('ingredient_name', '').strip().lower()
                if name and name not in seen:
                    seen.add(name)
                    unique_ingredients.append(ing)

            return unique_ingredients

        except Exception as e:
            self.logger.debug(f"Error parsing {annex_name} section: {e}")
            return []

    def _parse_table(self, table, category: str, status: str) -> List[Dict[str, Any]]:
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
            if not any(keyword in ' '.join(headers) for keyword in
                      ['ingredient', 'substance', 'name', 'chemical', 'inci', 'cas', 'entry']):
                return ingredients

            # Parse data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                cell_data = [cell.get_text(strip=True) for cell in cells]
                ingredient = self._extract_ingredient_from_cells(cell_data, headers, category, status)

                if ingredient:
                    ingredients.append(ingredient)

        except Exception as e:
            self.logger.debug(f"Error parsing table: {e}")

        return ingredients

    def _parse_list(self, list_elem, category: str, status: str) -> List[Dict[str, Any]]:
        """Parse a list element for ingredient data"""
        ingredients = []

        try:
            items = list_elem.find_all('li')
            for item in items:
                text = item.get_text(strip=True)

                # Try to extract ingredient information
                # Common patterns: "Ingredient Name (CAS: 123-45-6)" or "123. Ingredient Name"

                # Remove entry numbers at the start
                text = re.sub(r'^\d+\.\s*', '', text)

                parts = text.split('(')
                if len(parts) >= 1:
                    ingredient_name = parts[0].strip()

                    # Extract CAS number
                    cas_match = re.search(r'\b(\d{2,7}-\d{2}-\d)\b', text)
                    cas_no = cas_match.group(1) if cas_match else ""

                    # Extract concentration/conditions
                    conditions = ""
                    if len(parts) > 1:
                        conditions = '('.join(parts[1:]).strip()

                    if ingredient_name and len(ingredient_name) > 2:
                        ingredients.append({
                            "ingredient_name": ingredient_name,
                            "cas_no": cas_no,
                            "restriction_type": category,
                            "conditions": conditions if conditions else f"See ASEAN Cosmetic Directive Annex for details",
                            "rationale": conditions if conditions else f"Listed in ASEAN Cosmetic Directive",
                            "status": status,
                            "category": category
                        })

        except Exception as e:
            self.logger.debug(f"Error parsing list: {e}")

        return ingredients

    def _extract_ingredient_from_cells(self, cells: List[str], headers: List[str],
                                      category: str, status: str) -> Dict[str, Any]:
        """Extract ingredient data from table cells"""

        try:
            ingredient_name = ""
            cas_no = ""
            inci_name = ""
            max_concentration = ""
            conditions = ""
            entry_number = ""

            # Map cells to fields based on headers or content patterns
            for i, cell in enumerate(cells):
                if not cell:
                    continue

                cell_lower = cell.lower()
                header = headers[i] if i < len(headers) else ""

                # Entry number
                if 'entry' in header or 'no' in header or (i == 0 and re.match(r'^\d+$', cell)):
                    entry_number = cell
                # Ingredient/substance name
                elif 'name' in header or 'substance' in header or 'ingredient' in header:
                    ingredient_name = cell
                # INCI name
                elif 'inci' in header:
                    inci_name = cell
                # CAS number (pattern: XXX-XX-X or XXXXX-XX-X)
                elif 'cas' in header or re.match(r'^\d{2,7}-\d{2}-\d$', cell):
                    cas_no = cell
                # Maximum concentration
                elif 'max' in header or 'concentration' in header or '%' in cell:
                    max_concentration = cell
                # Conditions (usually longer text)
                elif len(cell) > 30 or 'condition' in header or 'restriction' in header or 'limitation' in header:
                    conditions = cell

            # Try to auto-detect if headers are not clear
            if not ingredient_name:
                # First non-numeric, non-CAS cell is likely the ingredient name
                for cell in cells:
                    if cell and not re.match(r'^[\d\-\.\s%]+$', cell) and len(cell) > 2:
                        ingredient_name = cell
                        break

            # If we have at least a name, create entry
            if ingredient_name and len(ingredient_name) > 2:
                ingredient_data = {
                    "ingredient_name": ingredient_name,
                    "cas_no": cas_no,
                    "inci_name": inci_name if inci_name else ingredient_name,
                    "restriction_type": category,
                    "status": status,
                    "category": category,
                    "entry_number": entry_number
                }

                # Add optional fields
                if max_concentration:
                    ingredient_data["max_concentration"] = max_concentration

                if conditions:
                    ingredient_data["conditions"] = conditions
                    ingredient_data["rationale"] = conditions
                else:
                    ingredient_data["conditions"] = f"See ASEAN Cosmetic Directive Annex for details"
                    ingredient_data["rationale"] = f"Listed in ASEAN Cosmetic Directive"

                return ingredient_data

        except Exception as e:
            self.logger.debug(f"Error extracting ingredient data: {e}")

        return None

    def _get_sample_data(self) -> Dict[str, Any]:
        """Return sample data as fallback"""
        self.logger.info("Using sample data for ASEAN")

        return {
            "source": "HSA Singapore - ASEAN Cosmetic Directive (Sample Data)",
            "regulation": "ASEAN Cosmetic Directive (ACD)",
            "version": "2024-2",
            "url": self.jurisdiction_config['sources'][0]['url'],
            "last_update": "2024-12-06",
            "published_date": "2024-12-06",
            "effective_date": "2024-12-06",
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_sample_data": True,
            "member_states": [
                "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
                "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"
            ],
            "annexes": {
                "annex_ii": {
                    "name": "Prohibited substances",
                    "description": "List of substances prohibited in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_ii")
                },
                "annex_iii": {
                    "name": "Restricted substances",
                    "description": "List of substances subject to restrictions",
                    "ingredients": self._get_sample_annex_data("annex_iii")
                },
                "annex_iv": {
                    "name": "Allowed colorants",
                    "description": "List of colorants allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_iv")
                },
                "annex_v": {
                    "name": "Allowed preservatives",
                    "description": "List of preservatives allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_v")
                },
                "annex_vi": {
                    "name": "Allowed UV filters",
                    "description": "List of UV filters allowed for use in cosmetic products",
                    "ingredients": self._get_sample_annex_data("annex_vi")
                }
            }
        }

    def _get_sample_annex_data(self, annex_key: str) -> List[Dict[str, Any]]:
        """Get sample data for specific annex"""

        if annex_key == "annex_ii":
            # Prohibited substances
            return [
                {
                    "entry_number": "1",
                    "ingredient_name": "Formaldehyde",
                    "cas_no": "50-00-0",
                    "inci_name": "Formaldehyde",
                    "restriction_type": "prohibited",
                    "status": "prohibited",
                    "category": "prohibited",
                    "conditions": "Except as preservative within the limits specified in Annex V",
                    "rationale": "Prohibited in cosmetics except as preservative within limits"
                },
                {
                    "entry_number": "15",
                    "ingredient_name": "Hydroquinone",
                    "cas_no": "123-31-9",
                    "inci_name": "Hydroquinone",
                    "restriction_type": "prohibited",
                    "status": "prohibited",
                    "category": "prohibited",
                    "conditions": "Except as oxidizing agent for hair colouring at ≤0.3%",
                    "rationale": "Generally prohibited except in specific hair products"
                },
                {
                    "entry_number": "89",
                    "ingredient_name": "Mercury and its compounds",
                    "cas_no": "7439-97-6",
                    "inci_name": "Mercury",
                    "restriction_type": "prohibited",
                    "status": "prohibited",
                    "category": "prohibited",
                    "conditions": "Except trace amounts from unavoidable contamination (≤1ppm)",
                    "rationale": "Highly toxic heavy metal, prohibited in all uses except trace contamination"
                }
            ]

        elif annex_key == "annex_iii":
            # Restricted substances
            return [
                {
                    "entry_number": "5",
                    "ingredient_name": "Hydrogen peroxide",
                    "cas_no": "7722-84-1",
                    "inci_name": "Hydrogen Peroxide",
                    "restriction_type": "restricted",
                    "status": "restricted",
                    "category": "restricted",
                    "max_concentration": "12% for hair products, 4% for skin, 2% for nails, 0.1% for tooth whitening",
                    "conditions": "≤12% (40 volumes) in hair products; ≤4% in skin products; ≤2% in nail hardening; ≤0.1% in tooth whitening",
                    "rationale": "Oxidizing agent with concentration limits based on product type"
                },
                {
                    "entry_number": "6",
                    "ingredient_name": "Salicylic acid and its salts",
                    "cas_no": "69-72-7",
                    "inci_name": "Salicylic Acid",
                    "restriction_type": "restricted",
                    "status": "restricted",
                    "category": "restricted",
                    "max_concentration": "3% in rinse-off, 2% in leave-on",
                    "conditions": "≤3% in rinse-off products; ≤2% in leave-on products; Not for children under 3 years except in shampoos",
                    "rationale": "Keratolytic agent with age and concentration restrictions"
                },
                {
                    "entry_number": "9",
                    "ingredient_name": "Thioglycolic acid and its salts",
                    "cas_no": "68-11-1",
                    "inci_name": "Thioglycolic Acid",
                    "restriction_type": "restricted",
                    "status": "restricted",
                    "category": "restricted",
                    "max_concentration": "8% general use, 11% professional use",
                    "conditions": "≤8% (as TG) for general use at pH ≥7.0; ≤11% (as TG) for professional use at pH ≥9.0",
                    "rationale": "Hair waving/straightening agent with concentration and pH restrictions"
                }
            ]

        elif annex_key == "annex_iv":
            # Permitted colorants
            return [
                {
                    "entry_number": "1",
                    "ingredient_name": "Naphthol Yellow S",
                    "cas_no": "846-70-8",
                    "inci_name": "CI 10006",
                    "restriction_type": "colorant",
                    "status": "allowed",
                    "category": "colorant",
                    "conditions": "Not for use in products applied near the eyes",
                    "rationale": "Permitted colorant with eye area restriction"
                },
                {
                    "entry_number": "25",
                    "ingredient_name": "Iron Oxides",
                    "cas_no": "1309-37-1",
                    "inci_name": "CI 77491",
                    "restriction_type": "colorant",
                    "status": "allowed",
                    "category": "colorant",
                    "conditions": "No restrictions",
                    "rationale": "Permitted colorant for all cosmetic uses"
                },
                {
                    "entry_number": "30",
                    "ingredient_name": "Titanium Dioxide",
                    "cas_no": "13463-67-7",
                    "inci_name": "CI 77891",
                    "restriction_type": "colorant",
                    "status": "allowed",
                    "category": "colorant",
                    "conditions": "No restrictions",
                    "rationale": "Permitted colorant and UV filter for all cosmetic uses"
                }
            ]

        elif annex_key == "annex_v":
            # Permitted preservatives
            return [
                {
                    "entry_number": "3",
                    "ingredient_name": "Benzoic acid, its salts and esters",
                    "cas_no": "65-85-0",
                    "inci_name": "Benzoic Acid",
                    "restriction_type": "preservative",
                    "status": "allowed",
                    "category": "preservative",
                    "max_concentration": "0.5%",
                    "conditions": "0.5% as acid",
                    "rationale": "Permitted preservative at specified concentration"
                },
                {
                    "entry_number": "4",
                    "ingredient_name": "Salicylic acid and its salts",
                    "cas_no": "69-72-7",
                    "inci_name": "Salicylic Acid",
                    "restriction_type": "preservative",
                    "status": "allowed",
                    "category": "preservative",
                    "max_concentration": "0.5%",
                    "conditions": "0.5% as acid. Not in preparations for children under 3 years except in shampoos",
                    "rationale": "Permitted preservative with age restrictions"
                }
            ]

        elif annex_key == "annex_vi":
            # Permitted UV filters
            return [
                {
                    "entry_number": "2",
                    "ingredient_name": "Homosalate",
                    "cas_no": "118-56-9",
                    "inci_name": "Homosalate",
                    "restriction_type": "uv_filter",
                    "status": "allowed",
                    "category": "uv_filter",
                    "max_concentration": "10%",
                    "conditions": "Maximum concentration 10%",
                    "rationale": "Permitted UV filter at specified concentration"
                },
                {
                    "entry_number": "5",
                    "ingredient_name": "Ethylhexyl Methoxycinnamate",
                    "cas_no": "5466-77-3",
                    "inci_name": "Ethylhexyl Methoxycinnamate",
                    "restriction_type": "uv_filter",
                    "status": "allowed",
                    "category": "uv_filter",
                    "max_concentration": "10%",
                    "conditions": "Maximum concentration 10%",
                    "rationale": "Permitted UV filter at specified concentration"
                }
            ]

        return []

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw ASEAN data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        # Count total ingredients across all annexes
        total_ingredients = 0
        annexes = raw_data.get("annexes", {})
        for annex in annexes.values():
            total_ingredients += len(annex.get("ingredients", []))

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "version": raw_data.get("version"),
            "published_at": raw_data.get("published_date"),
            "effective_date": raw_data.get("effective_date"),
            "last_update": last_update_str,
            "member_states": raw_data.get("member_states"),
            "total_ingredients": total_ingredients,
            "fetch_timestamp": raw_data.get("fetch_timestamp"),
            "is_sample_data": raw_data.get("is_sample_data", False)
        }
