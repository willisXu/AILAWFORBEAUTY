"""Fetch all regulation data from all jurisdictions"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers import EUScraper, JPScraper, CNScraper, CAScraper, ASEANScraper
from utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Run all scrapers"""
    scrapers = [
        EUScraper(),
        JPScraper(),
        CNScraper(),
        CAScraper(),
        ASEANScraper(),
    ]

    results = {}
    failed = []

    for scraper in scrapers:
        try:
            logger.info(f"Running scraper for {scraper.jurisdiction_code}")
            snapshot = scraper.run()
            results[scraper.jurisdiction_code] = snapshot
            logger.info(f"Successfully completed {scraper.jurisdiction_code}")
        except Exception as e:
            logger.error(f"Failed to fetch {scraper.jurisdiction_code}: {e}")
            failed.append(scraper.jurisdiction_code)

    # Summary
    logger.info("=" * 60)
    logger.info("Fetch Summary:")
    logger.info(f"  Successful: {len(results)} / {len(scrapers)}")
    logger.info(f"  Failed: {len(failed)}")

    if failed:
        logger.error(f"  Failed jurisdictions: {', '.join(failed)}")
        sys.exit(1)
    else:
        logger.info("All scrapers completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
