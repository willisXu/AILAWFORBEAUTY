"""Parse all raw regulation data"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import EUParser, JPParser, CNParser, CAParser, ASEANParser
from config import RAW_DATA_DIR
from utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Run all parsers"""
    parsers = [
        (EUParser(), "EU"),
        (JPParser(), "JP"),
        (CNParser(), "CN"),
        (CAParser(), "CA"),
        (ASEANParser(), "ASEAN"),
    ]

    results = {}
    failed = []

    for parser, jurisdiction in parsers:
        try:
            # Find latest raw data file
            raw_dir = RAW_DATA_DIR / jurisdiction
            latest_file = raw_dir / "latest.json"

            if not latest_file.exists():
                logger.warning(f"No raw data found for {jurisdiction} at {latest_file}")
                continue

            logger.info(f"Parsing {jurisdiction}")
            rules = parser.run(latest_file)
            results[jurisdiction] = rules
            logger.info(f"Successfully parsed {jurisdiction}")

        except Exception as e:
            logger.error(f"Failed to parse {jurisdiction}: {e}", exc_info=True)
            failed.append(jurisdiction)

    # Summary
    logger.info("=" * 60)
    logger.info("Parse Summary:")
    logger.info(f"  Successful: {len(results)} / {len(parsers)}")
    logger.info(f"  Failed: {len(failed)}")

    if failed:
        logger.error(f"  Failed jurisdictions: {', '.join(failed)}")

    for jurisdiction, rules in results.items():
        stats = rules.get("statistics", {})
        logger.info(f"  {jurisdiction}: {stats}")

    if failed:
        sys.exit(1)
    else:
        logger.info("All parsers completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
