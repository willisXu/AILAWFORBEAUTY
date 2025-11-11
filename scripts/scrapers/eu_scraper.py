"""EU cosmetics regulation scraper - PDF Implementation"""

from typing import Dict, Any, List
import requests
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base_scraper import BaseScraper
from config import SCRAPING_CONFIG, RAW_DATA_DIR

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class EUScraper(BaseScraper):
    """Scraper for EU cosmetics regulations using official PDF files"""

    def __init__(self):
        super().__init__("EU")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch EU cosmetics regulation data from official PDF files

        Downloads Annexes II-VI PDFs from European Commission CosIng database

        Returns:
            Raw regulation data with PDF paths
        """
        self.logger.info("Fetching EU cosmetics regulation data from official PDFs")

        try:
            pdf_dir = RAW_DATA_DIR / self.jurisdiction_code / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)

            annexes = {}

            # Download each Annex PDF
            for source in self.jurisdiction_config['sources']:
                if source['type'] != 'pdf':
                    continue

                annex_num = source['annex']
                annex_name = f"annex_{annex_num.lower()}"

                self.logger.info(f"Downloading Annex {annex_num}...")
                pdf_path = self._download_pdf(source['url'], pdf_dir, f"Annex_{annex_num}.pdf")

                if pdf_path:
                    # Parse PDF to extract table data
                    ingredients = self._parse_pdf(pdf_path, annex_num)

                    annexes[annex_name] = {
                        "name": source['name'],
                        "description": source['description'],
                        "pdf_path": str(pdf_path),
                        "ingredients": ingredients
                    }

                    self.logger.info(f"Annex {annex_num}: Extracted {len(ingredients)} ingredients")
                else:
                    self.logger.warning(f"Failed to download Annex {annex_num}")

            data = {
                "source": "European Commission - CosIng Database (PDF)",
                "regulation": "Regulation (EC) No 1223/2009",
                "published_date": self.jurisdiction_config.get('published_date', '2024-04-04'),
                "effective_date": self.jurisdiction_config.get('effective_date', '2024-04-24'),
                "last_update": self.jurisdiction_config.get('effective_date', '2024-04-24'),
                "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "annexes": annexes
            }

            total_ingredients = sum(len(annex.get('ingredients', [])) for annex in annexes.values())
            self.logger.info(f"Successfully fetched {total_ingredients} ingredients from {len(annexes)} EU Annexes")

            return data

        except Exception as e:
            self.logger.error(f"Failed to fetch EU data: {e}", exc_info=True)
            raise Exception(f"EU PDF scraper failed: {e}") from e

    def _download_pdf(self, url: str, pdf_dir: Path, filename: str) -> Path:
        """Download PDF file"""
        try:
            time.sleep(1)  # Be respectful

            headers = {
                'User-Agent': SCRAPING_CONFIG['user_agent'],
                'Accept': 'application/pdf,*/*',
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=120,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()

            pdf_path = pdf_dir / filename

            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = pdf_path.stat().st_size / 1024 / 1024
            self.logger.info(f"Downloaded {filename} ({size_mb:.2f} MB)")

            return pdf_path

        except Exception as e:
            self.logger.error(f"Error downloading PDF from {url}: {e}")
            return None

    def _parse_pdf(self, pdf_path: Path, annex_num: str) -> List[Dict[str, Any]]:
        """Parse PDF to extract ingredient tables"""

        if not pdfplumber:
            self.logger.warning(f"pdfplumber not available, cannot parse {pdf_path}")
            return []

        ingredients = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.logger.info(f"Parsing {len(pdf.pages)} pages from {pdf_path.name}...")

                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables from page
                    tables = page.extract_tables()

                    if not tables:
                        continue

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # Try to parse table
                        parsed_ingredients = self._parse_table(table, annex_num)
                        ingredients.extend(parsed_ingredients)

                self.logger.info(f"Extracted {len(ingredients)} ingredients from {pdf_path.name}")

        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_path}: {e}", exc_info=True)

        return ingredients

    def _parse_table(self, table: List[List[str]], annex_num: str) -> List[Dict[str, Any]]:
        """Parse a table to extract ingredient information"""

        if not table or len(table) < 2:
            return []

        ingredients = []
        headers = table[0] if table else []

        # Identify column indices
        ref_col = cas_col = name_col = cond_col = -1

        for i, header in enumerate(headers):
            if not header:
                continue
            header_lower = header.lower()

            if 'reference' in header_lower or 'ref' in header_lower or 'entry' in header_lower:
                ref_col = i
            elif 'cas' in header_lower:
                cas_col = i
            elif 'chemical name' in header_lower or 'substance' in header_lower or 'ingredient' in header_lower:
                name_col = i
            elif 'condition' in header_lower or 'restriction' in header_lower or 'maximum' in header_lower:
                cond_col = i

        # Parse data rows
        for row in table[1:]:
            if not row or len(row) < 2:
                continue

            # Skip empty rows or header repetitions
            if not any(cell for cell in row if cell and cell.strip()):
                continue

            # Extract ingredient data
            ingredient = {
                "ingredient_name": "",
                "cas_no": "",
                "ec_no": "",
                "entry_number": "",
                "conditions": "",
                "category": self._get_category_for_annex(annex_num),
                "restriction_type": self._get_category_for_annex(annex_num),
                "status": self._get_status_for_annex(annex_num)
            }

            # Extract values
            if name_col >= 0 and name_col < len(row):
                ingredient["ingredient_name"] = (row[name_col] or "").strip()

            if cas_col >= 0 and cas_col < len(row):
                ingredient["cas_no"] = (row[cas_col] or "").strip()

            if ref_col >= 0 and ref_col < len(row):
                ingredient["entry_number"] = (row[ref_col] or "").strip()

            if cond_col >= 0 and cond_col < len(row):
                ingredient["conditions"] = (row[cond_col] or "").strip()

            # If no specific columns found, use positions
            if not ingredient["ingredient_name"] and len(row) > 1:
                ingredient["ingredient_name"] = (row[1] or "").strip()

            if not ingredient["cas_no"] and len(row) > 2:
                cas_candidate = (row[2] or "").strip()
                # Check if it looks like a CAS number
                if cas_candidate and '-' in cas_candidate:
                    ingredient["cas_no"] = cas_candidate

            # Only add if we have a name
            if ingredient["ingredient_name"] and len(ingredient["ingredient_name"]) > 2:
                ingredients.append(ingredient)

        return ingredients

    def _get_category_for_annex(self, annex_num: str) -> str:
        """Get category based on annex number"""
        categories = {
            "II": "prohibited",
            "III": "restricted",
            "IV": "colorant",
            "V": "preservative",
            "VI": "uv_filter"
        }
        return categories.get(annex_num, "unknown")

    def _get_status_for_annex(self, annex_num: str) -> str:
        """Get status based on annex number"""
        if annex_num == "II":
            return "prohibited"
        elif annex_num == "III":
            return "restricted"
        else:
            return "allowed"

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
            "is_sample_data": False
        }
