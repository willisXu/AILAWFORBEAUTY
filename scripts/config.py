"""
Configuration for data scraping and parsing
"""

import os
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PARSED_DATA_DIR = DATA_DIR / "parsed"
RULES_DATA_DIR = DATA_DIR / "rules"
DIFF_DATA_DIR = DATA_DIR / "diff"

# Ensure directories exist
for directory in [RAW_DATA_DIR, PARSED_DATA_DIR, RULES_DATA_DIR, DIFF_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Jurisdiction configurations
JURISDICTIONS = {
    "EU": {
        "code": "EU",
        "name": "European Union",
        "timezone": "Europe/Brussels",
        "sources": [
            {
                "name": "EC Cosmetics Regulation",
                "url": "https://ec.europa.eu/growth/sectors/cosmetics/products_en",
                "annexes_url": "https://ec.europa.eu/growth/tools-databases/cosing/",
                "type": "html",
                "update_freq": "weekly"
            }
        ]
    },
    "JP": {
        "code": "JP",
        "name": "Japan",
        "timezone": "Asia/Tokyo",
        "sources": [
            {
                "name": "MHLW Cosmetics Standards",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/index.html",
                "type": "html",
                "update_freq": "weekly"
            }
        ]
    },
    "CN": {
        "code": "CN",
        "name": "China",
        "timezone": "Asia/Shanghai",
        "sources": [
            {
                "name": "NMPA Cosmetics Database",
                "url": "https://www.nmpa.gov.cn/directory/web/nmpa/xxgk/fgwj/gzwj/gzwjyhzp/index.html",
                "type": "html",
                "update_freq": "weekly"
            }
        ]
    },
    "CA": {
        "code": "CA",
        "name": "Canada",
        "timezone": "America/Toronto",
        "sources": [
            {
                "name": "Health Canada Cosmetics",
                "url": "https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics.html",
                "hotlist_url": "https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics/cosmetic-ingredient-hotlist-prohibited-restricted-ingredients.html",
                "type": "html",
                "update_freq": "weekly"
            }
        ]
    },
    "ASEAN": {
        "code": "ASEAN",
        "name": "ASEAN",
        "timezone": "Asia/Singapore",
        "sources": [
            {
                "name": "ASEAN Cosmetic Directive",
                "url": "https://asean.org/our-communities/economic-community/resilient-and-inclusive-asean/cosmetics/",
                "type": "html",
                "update_freq": "weekly"
            }
        ]
    }
}

# Scraping settings
SCRAPING_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "timeout": 30,
    "max_retries": 3,
    "retry_backoff": 2,
    "max_wait": 1800,  # 30 minutes
}

# Parsing settings
PARSING_CONFIG = {
    "min_confidence": 0.85,
    "fuzzy_match_threshold": 0.90,
    "date_formats": [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y年%m月%d日",
    ]
}

# Ingredient categories
INGREDIENT_CATEGORIES = [
    "banned",
    "restricted",
    "allowed",
    "colorant",
    "preservative",
    "uv_filter"
]

# Product types
PRODUCT_TYPES = [
    "rinse-off",
    "leave-on",
    "hair",
    "oral",
    "eye-area",
    "nail",
    "aerosol"
]

# Application sites
APPLICATION_SITES = [
    "face",
    "body",
    "hair",
    "scalp",
    "lips",
    "eyes",
    "nails",
    "mucous-membrane"
]

# Output settings
OUTPUT_CONFIG = {
    "indent": 2,
    "ensure_ascii": False,
    "date_format": "%Y-%m-%d",
    "datetime_format": "%Y-%m-%dT%H:%M:%SZ"
}

# Version info
def get_version_info():
    """Generate version information for data snapshots"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": datetime.utcnow().strftime("%Y%m%d%H%M%S")
    }
