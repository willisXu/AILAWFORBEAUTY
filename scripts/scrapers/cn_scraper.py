"""China cosmetics regulation scraper - Real Implementation"""

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


class CNScraper(BaseScraper):
    """Scraper for China cosmetics regulations - NMPA Database"""

    def __init__(self):
        super().__init__("CN")

    def fetch(self) -> Dict[str, Any]:
        """
        Fetch Chinese cosmetics regulation data from NMPA PDF

        Source: NMPA (National Medical Products Administration)
        URL: https://www.nmpa.gov.cn/directory/web/nmpa/images/MjAxNcTqtdoyNji6xbmruOa4vbz+LnBkZg==.pdf

        Main regulation:
        - 化妆品安全技术规范（2015年版）
        - Safety and Technical Standards for Cosmetics (2015 Edition)

        Returns:
            Raw regulation data with PDF file path
        """
        self.logger.info("Fetching Chinese cosmetics regulation PDF from NMPA")

        try:
            pdf_url = self.jurisdiction_config['sources'][0]['url']

            # Add delay to be respectful to the server
            time.sleep(1)

            # Fetch the PDF
            headers = {
                'User-Agent': SCRAPING_CONFIG['user_agent'],
                'Accept': 'application/pdf,*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            }

            self.logger.info(f"Downloading PDF from: {pdf_url}")
            response = requests.get(
                pdf_url,
                headers=headers,
                timeout=120,  # Longer timeout for PDF download
                allow_redirects=True,
                stream=True
            )
            response.raise_for_status()

            # Save PDF to raw data directory
            from config import RAW_DATA_DIR
            pdf_dir = RAW_DATA_DIR / self.jurisdiction_code
            pdf_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = pdf_dir / "cosmetics_safety_technical_standards_2015.pdf"

            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            self.logger.info(f"Downloading {total_size / 1024 / 1024:.2f} MB...")

            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.logger.info(f"PDF saved to: {pdf_path}")

            data = {
                "source": "NMPA - 化妆品安全技术规范（2015年版）",
                "regulation": "Safety and Technical Standards for Cosmetics (2015 Edition)",
                "url": pdf_url,
                "published_date": self.jurisdiction_config.get('published_date', '2015-12-23'),
                "effective_date": self.jurisdiction_config.get('effective_date', '2016-12-01'),
                "last_update": self.jurisdiction_config.get('effective_date', '2016-12-01'),
                "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pdf_path": str(pdf_path),
                "pdf_size_mb": pdf_path.stat().st_size / 1024 / 1024,
                "type": "pdf",
                "tables": {
                    "table_1": "禁用原料目录 (Prohibited Ingredients)",
                    "table_2": "禁用植（动）物原料目录 (Prohibited Plant/Animal Ingredients)",
                    "table_3": "限用组分 (Restricted Ingredients)"
                }
            }

            self.logger.info(f"Successfully downloaded PDF ({data['pdf_size_mb']:.2f} MB)")

            return data

        except requests.RequestException as e:
            self.logger.error(f"Failed to download NMPA PDF: {e}")
            raise Exception(f"China scraper failed: Unable to download PDF from NMPA website") from e
        except Exception as e:
            self.logger.error(f"Error processing NMPA PDF: {e}", exc_info=True)
            raise Exception(f"China scraper failed: Error processing PDF from NMPA") from e

    def _get_sample_catalog_data(self, catalog_key: str) -> List[Dict[str, Any]]:
        """Get sample data for specific catalog"""

        if catalog_key == "prohibited":
            return [
                {
                    "serial_number": "1",
                    "name_chinese": "甲醛",
                    "name_english": "Formaldehyde",
                    "cas_no": "50-00-0",
                    "inci": "Formaldehyde",
                    "category": "prohibited",
                    "conditions": "禁止作为化妆品原料使用，防腐剂除外（需符合附录限量）/ Prohibited except as preservative within specified limits",
                    "rationale": "列于 NMPA 禁用组分目录 / Listed in NMPA Prohibited Ingredients Catalog"
                },
                {
                    "serial_number": "15",
                    "name_chinese": "氢醌",
                    "name_english": "Hydroquinone",
                    "cas_no": "123-31-9",
                    "inci": "Hydroquinone",
                    "category": "prohibited",
                    "conditions": "禁止在化妆品中使用（特殊用途化妆品经批准除外）/ Prohibited in cosmetics (allowed in special use cosmetics with approval)",
                    "rationale": "列于 NMPA 禁用组分目录 / Listed in NMPA Prohibited Ingredients Catalog"
                },
                {
                    "serial_number": "89",
                    "name_chinese": "汞及其化合物",
                    "name_english": "Mercury and its compounds",
                    "cas_no": "7439-97-6",
                    "inci": "Mercury",
                    "category": "prohibited",
                    "conditions": "禁止使用，痕量杂质（≤1ppm）除外 / Prohibited, trace amounts (≤1ppm) from unavoidable contamination acceptable",
                    "rationale": "重金属，剧毒 / Heavy metal, highly toxic"
                },
                {
                    "serial_number": "120",
                    "name_chinese": "铅及其化合物",
                    "name_english": "Lead and its compounds",
                    "cas_no": "7439-92-1",
                    "inci": "Lead",
                    "category": "prohibited",
                    "conditions": "禁止作为化妆品原料，痕量杂质可接受 / Prohibited as ingredient, trace amounts from impurities acceptable",
                    "rationale": "重金属，累积毒性 / Heavy metal, cumulative toxicity"
                }
            ]

        elif catalog_key == "restricted":
            return [
                {
                    "serial_number": "5",
                    "name_chinese": "过氧化氢",
                    "name_english": "Hydrogen Peroxide",
                    "cas_no": "7722-84-1",
                    "inci": "Hydrogen Peroxide",
                    "maximum_concentration": "6%",
                    "category": "restricted",
                    "conditions": "染发产品中最高浓度 6%（混合后）/ ≤6% in hair products after mixing",
                    "restrictions": "浓度 >3% 仅限专业使用 / Professional use only for concentrations >3%",
                    "rationale": "氧化剂，需限制浓度 / Oxidizing agent with concentration limits"
                },
                {
                    "serial_number": "6",
                    "name_chinese": "水杨酸",
                    "name_english": "Salicylic Acid",
                    "cas_no": "69-72-7",
                    "inci": "Salicylic Acid",
                    "maximum_concentration": "3%",
                    "category": "restricted",
                    "conditions": "冲洗类 ≤3%，驻留类 ≤2%，洗发水 ≤3% / Rinse-off ≤3%, leave-on ≤2%, shampoo ≤3%",
                    "restrictions": "3 岁以下儿童禁用 / Not for use on children under 3 years",
                    "rationale": "角质溶解剂，需年龄和浓度限制 / Keratolytic agent with age and concentration restrictions"
                },
                {
                    "serial_number": "9",
                    "name_chinese": "硼酸",
                    "name_english": "Boric Acid",
                    "cas_no": "10043-35-3",
                    "inci": "Boric Acid",
                    "maximum_concentration": "3%",
                    "category": "restricted",
                    "conditions": "最高浓度 3%（以酸计）/ ≤3% (as acid)",
                    "restrictions": "不得用于破损皮肤或 3 岁以下儿童 / Not for use on damaged skin or children under 3 years",
                    "rationale": "抗菌剂，需浓度和使用限制 / Antimicrobial agent with concentration and usage restrictions"
                }
            ]

        elif catalog_key == "preservatives":
            return [
                {
                    "serial_number": "1",
                    "name_chinese": "苯甲酸及其盐类",
                    "name_english": "Benzoic Acid and its salts",
                    "cas_no": "65-85-0",
                    "inci": "Benzoic Acid",
                    "maximum_concentration": "0.5%",
                    "category": "preservative",
                    "conditions": "以酸计 / As acid",
                    "rationale": "准用防腐剂 / Permitted preservative"
                },
                {
                    "serial_number": "3",
                    "name_chinese": "水杨酸及其盐类",
                    "name_english": "Salicylic Acid and its salts",
                    "cas_no": "69-72-7",
                    "inci": "Salicylic Acid",
                    "maximum_concentration": "0.5%",
                    "category": "preservative",
                    "conditions": "以酸计，3 岁以下儿童产品中禁用 / As acid. Not in products for children under 3",
                    "restrictions": "洗发水除外 / Except in shampoos",
                    "rationale": "准用防腐剂 / Permitted preservative"
                },
                {
                    "serial_number": "10",
                    "name_chinese": "苯氧乙醇",
                    "name_english": "Phenoxyethanol",
                    "cas_no": "122-99-6",
                    "inci": "Phenoxyethanol",
                    "maximum_concentration": "1.0%",
                    "category": "preservative",
                    "conditions": "最高浓度 1.0% / Maximum concentration 1.0%",
                    "rationale": "准用防腐剂 / Permitted preservative"
                }
            ]

        elif catalog_key == "colorants":
            return [
                {
                    "serial_number": "1",
                    "name_chinese": "氧化铁",
                    "name_english": "Iron Oxides",
                    "cas_no": "1309-37-1",
                    "inci": "CI 77491, CI 77492, CI 77499",
                    "category": "colorant",
                    "conditions": "无限制 / No restrictions",
                    "restrictions": "准用于所有化妆品 / Approved for all cosmetic uses",
                    "rationale": "准用着色剂 / Permitted colorant"
                },
                {
                    "serial_number": "5",
                    "name_chinese": "二氧化钛",
                    "name_english": "Titanium Dioxide",
                    "cas_no": "13463-67-7",
                    "inci": "CI 77891",
                    "category": "colorant",
                    "conditions": "无限制 / No restrictions",
                    "restrictions": "准用于所有化妆品 / Approved for all cosmetic uses",
                    "rationale": "准用着色剂和防晒剂 / Permitted colorant and UV filter"
                },
                {
                    "serial_number": "20",
                    "name_chinese": "焦糖",
                    "name_english": "Caramel",
                    "cas_no": "8028-89-5",
                    "inci": "Caramel",
                    "category": "colorant",
                    "conditions": "无限制 / No restrictions",
                    "restrictions": "准用于所有化妆品 / Approved for all cosmetic uses",
                    "rationale": "准用着色剂 / Permitted colorant"
                }
            ]

        elif catalog_key == "uv_filters":
            return [
                {
                    "serial_number": "2",
                    "name_chinese": "水杨酸乙基己酯",
                    "name_english": "Ethylhexyl Salicylate",
                    "cas_no": "118-60-5",
                    "inci": "Ethylhexyl Salicylate",
                    "maximum_concentration": "5%",
                    "category": "uv_filter",
                    "conditions": "最高浓度 5% / Maximum concentration 5%",
                    "rationale": "准用防晒剂 / Permitted UV filter"
                },
                {
                    "serial_number": "5",
                    "name_chinese": "甲氧基肉桂酸乙基己酯",
                    "name_english": "Ethylhexyl Methoxycinnamate",
                    "cas_no": "5466-77-3",
                    "inci": "Ethylhexyl Methoxycinnamate",
                    "maximum_concentration": "10%",
                    "category": "uv_filter",
                    "conditions": "最高浓度 10% / Maximum concentration 10%",
                    "rationale": "准用防晒剂 / Permitted UV filter"
                }
            ]

        return []

    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw China data"""
        last_update_str = raw_data.get("last_update", "")
        last_update = parse_date(last_update_str) if last_update_str else None

        # Count total ingredients across all catalogs
        total_ingredients = 0
        catalogs = raw_data.get("catalogs", {})
        for catalog in catalogs.values():
            total_ingredients += len(catalog) if isinstance(catalog, list) else 0

        return {
            "source": raw_data.get("source"),
            "regulation": raw_data.get("regulation"),
            "published_at": raw_data.get("published_date"),
            "effective_date": raw_data.get("effective_date"),
            "last_update": last_update_str,
            "total_ingredients": total_ingredients,
            "fetch_timestamp": raw_data.get("fetch_timestamp"),
            "is_sample_data": raw_data.get("is_sample_data", False)
        }
