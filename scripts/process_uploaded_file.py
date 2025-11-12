"""
Process uploaded regulation files
This script handles files uploaded via the web interface
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAW_DATA_DIR, RULES_DATA_DIR, JURISDICTIONS
from utils import setup_logger, save_json, load_json, compute_data_hash
from parsers.eu_parser import EUParser
from parsers.asean_parser import ASEANParser
from parsers.cn_parser import CNParser
from parsers.jp_parser import JPParser
from parsers.ca_parser import CAParser

logger = setup_logger(__name__)

# Parser mapping
PARSERS = {
    "EU": EUParser,
    "ASEAN": ASEANParser,
    "CN": CNParser,
    "JP": JPParser,
    "CA": CAParser,
}


def process_uploaded_file(
    file_path: Path,
    jurisdiction: str,
    file_type: str = "pdf",
    annex: Optional[str] = None,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an uploaded regulation file

    Args:
        file_path: Path to uploaded file
        jurisdiction: Jurisdiction code (EU, JP, CN, CA, ASEAN)
        file_type: Type of file (pdf, html, json)
        annex: Annex identifier (for EU/ASEAN)
        version: Version identifier (defaults to timestamp)

    Returns:
        Processing result dictionary
    """
    logger.info(f"Processing uploaded file for {jurisdiction}: {file_path}")

    # Validate jurisdiction
    if jurisdiction not in JURISDICTIONS:
        raise ValueError(f"Invalid jurisdiction: {jurisdiction}. Must be one of {list(JURISDICTIONS.keys())}")

    # Validate file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Create upload directory structure
    upload_dir = RAW_DATA_DIR / jurisdiction / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate version if not provided
    if version is None:
        version = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # Create raw data structure
    jurisdiction_config = JURISDICTIONS[jurisdiction]

    # For JSON files, load directly
    if file_type == "json":
        try:
            raw_data = load_json(file_path)
            logger.info(f"Loaded JSON file with keys: {list(raw_data.keys())}")
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {e}")
    else:
        # For PDF/HTML files, create a raw_data structure pointing to the file
        # The parser will need to handle the actual PDF/HTML parsing
        raw_data = {
            "jurisdiction": jurisdiction,
            "file_path": str(file_path),
            "file_type": file_type,
            "annex": annex,
            "version": version,
            "uploaded_at": datetime.utcnow().isoformat(),
            "metadata": {
                "source": "uploaded_file",
                "version": version,
                "published_at": jurisdiction_config.get("published_date"),
                "effective_date": jurisdiction_config.get("effective_date"),
                "regulation": jurisdiction_config.get("regulation"),
            }
        }

        # Copy file to upload directory with versioned name
        file_ext = file_path.suffix
        dest_filename = f"{version}_{annex if annex else 'regulation'}{file_ext}"
        dest_path = upload_dir / dest_filename

        import shutil
        shutil.copy2(file_path, dest_path)
        logger.info(f"Copied file to {dest_path}")

        # Update file path in raw_data
        raw_data["file_path"] = str(dest_path)

        # Save raw data metadata
        raw_json_path = upload_dir / f"{version}_{annex if annex else 'regulation'}.json"
        save_json(raw_data, raw_json_path)
        logger.info(f"Saved raw data metadata to {raw_json_path}")

    # Get appropriate parser
    parser_class = PARSERS.get(jurisdiction)
    if parser_class is None:
        raise ValueError(f"No parser available for jurisdiction: {jurisdiction}")

    parser = parser_class()

    # Parse the data
    try:
        parsed_data = parser.parse(raw_data)
        logger.info(f"Successfully parsed data")
    except Exception as e:
        logger.error(f"Failed to parse data: {e}", exc_info=True)
        raise

    # Create rule structure
    rules = parser.create_rule_structure(raw_data, parsed_data)

    # Save rules
    rules_path = parser.save_rules(rules, version)
    logger.info(f"Saved rules to {rules_path}")

    # Return result
    result = {
        "success": True,
        "jurisdiction": jurisdiction,
        "version": version,
        "statistics": rules["statistics"],
        "rules_path": str(rules_path),
        "processed_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Processing complete: {result}")
    return result


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Process uploaded regulation file")
    parser.add_argument("file", type=str, help="Path to uploaded file")
    parser.add_argument("jurisdiction", type=str, help="Jurisdiction code (EU, JP, CN, CA, ASEAN)")
    parser.add_argument("--type", type=str, default="pdf", help="File type (pdf, html, json)")
    parser.add_argument("--annex", type=str, help="Annex identifier (for EU/ASEAN)")
    parser.add_argument("--version", type=str, help="Version identifier (defaults to timestamp)")
    parser.add_argument("--output", type=str, help="Output result to JSON file")

    args = parser.parse_args()

    try:
        result = process_uploaded_file(
            Path(args.file),
            args.jurisdiction,
            args.type,
            args.annex,
            args.version
        )

        # Output result
        if args.output:
            output_path = Path(args.output)
            save_json(result, output_path)
            logger.info(f"Saved result to {args.output}")
        else:
            print(json.dumps(result, indent=2))

        sys.exit(0)

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
            "processed_at": datetime.utcnow().isoformat(),
        }

        if args.output:
            save_json(result, Path(args.output))
        else:
            print(json.dumps(result, indent=2))

        sys.exit(1)


if __name__ == "__main__":
    main()
