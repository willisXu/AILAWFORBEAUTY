"""Data scrapers for cosmetics regulations"""

from .base_scraper import BaseScraper
from .eu_scraper import EUScraper
from .jp_scraper import JPScraper
from .cn_scraper import CNScraper
from .ca_scraper import CAScraper
from .asean_scraper import ASEANScraper

__all__ = [
    "BaseScraper",
    "EUScraper",
    "JPScraper",
    "CNScraper",
    "CAScraper",
    "ASEANScraper",
]
