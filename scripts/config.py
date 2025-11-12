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
        "published_date": "2024-04-04",
        "effective_date": "2024-04-24",
        "regulation": "Regulation (EC) No 1223/2009",
        "sources": [
            {
                "name": "EC Cosmetics Regulation 2024/996",
                "url": "https://eur-lex.europa.eu/eli/reg/2024/996/oj",
                "annexes_url": "https://ec.europa.eu/growth/tools-databases/cosing/reference/annexes",
                "type": "html",
                "update_freq": "weekly",
                "description": "Annexes II-VI: Prohibited, Restricted, Colorants, Preservatives, UV filters. Note: Currently uses sample data due to PDF/CSV access restrictions."
            }
        ]
    },
    "JP": {
        "code": "JP",
        "name": "Japan",
        "timezone": "Asia/Tokyo",
        "published_date": "2000-09-29",
        "effective_date": "2001-04-01",
        "regulation": "Standards for Cosmetics (化粧品基準)",
        "sources": [
            {
                "name": "MHLW Cosmetics Standards",
                "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/index.html",
                "type": "html",
                "update_freq": "weekly",
                "description": "Standards for Cosmetics and Active Ingredients List"
            }
        ]
    },
    "CN": {
        "code": "CN",
        "name": "China",
        "timezone": "Asia/Shanghai",
        "published_date": "2015-12-23",
        "effective_date": "2016-12-01",
        "regulation": "化妝品安全技術規範（2015年版）",
        "sources": [
            {
                "name": "NMPA Safety Technical Standards for Cosmetics (2015)",
                "url": "https://www.nmpa.gov.cn/directory/web/nmpa/images/MjAxNcTqtdoyNji6xbmruOa4vbz+LnBkZg==.pdf",
                "type": "pdf",
                "update_freq": "monthly",
                "description": "Safety and Technical Standards for Cosmetics (2015 Edition) - Tables 1-3 for prohibited and restricted ingredients"
            },
            {
                "name": "NMPA Cosmetics Database (Backup)",
                "url": "https://www.nmpa.gov.cn/datasearch/search-result.html?searchCtg=cosmetics",
                "type": "html",
                "update_freq": "weekly",
                "description": "Catalog of Used Cosmetic Ingredients (2021 Edition)"
            }
        ]
    },
    "CA": {
        "code": "CA",
        "name": "Canada",
        "timezone": "America/Toronto",
        "published_date": "2025-02",
        "effective_date": "2025-02-28",
        "regulation": "Cosmetic Ingredient Hotlist",
        "sources": [
            {
                "name": "Health Canada Cosmetic Ingredient Hotlist",
                "url": "https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics/cosmetic-ingredient-hotlist-prohibited-restricted-ingredients.html",
                "type": "html",
                "update_freq": "weekly",
                "description": "Prohibited and Restricted Ingredients List"
            }
        ]
    },
    "ASEAN": {
        "code": "ASEAN",
        "name": "ASEAN",
        "timezone": "Asia/Singapore",
        "published_date": "2024-12-06",
        "effective_date": "2024-12-06",
        "regulation": "ASEAN Cosmetic Directive (Version 2024-2)",
        "sources": [
            {
                "name": "ASEAN Cosmetic Directive - Annex II (December 2024)",
                "url": "https://asean.org/wp-content/uploads/2024/12/Annex-II-Release_6_Dec_2024.pdf",
                "annex": "II",
                "type": "pdf",
                "description": "Prohibited substances - December 2024 release"
            },
            {
                "name": "HSA ASEAN Cosmetic Directive (Backup)",
                "url": "https://www.hsa.gov.sg/cosmetic-products/asean-cosmetic-directive",
                "type": "html",
                "description": "ASEAN Cosmetic Directive overview and additional annexes"
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
