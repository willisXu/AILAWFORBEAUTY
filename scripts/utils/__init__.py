"""Utility functions for scraping and parsing"""

from .logger import setup_logger
from .http import fetch_url, download_file
from .file_utils import save_json, load_json, compute_hash
from .text_utils import normalize_text, extract_percentage, parse_date
from .fuzzy_match import fuzzy_match_ingredient, normalize_inci_name

__all__ = [
    "setup_logger",
    "fetch_url",
    "download_file",
    "save_json",
    "load_json",
    "compute_hash",
    "normalize_text",
    "extract_percentage",
    "parse_date",
    "fuzzy_match_ingredient",
    "normalize_inci_name",
]
