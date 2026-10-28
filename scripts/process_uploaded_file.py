"""
Process uploaded regulation files
This script handles files uploaded via the web interface
"""

import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAW_DATA_DIR, JURISDICTIONS
from utils import setup_logger, save_json, load_json, PerformanceMonitor
from parsers.eu_parser_v2 import EUParserV2
from parsers.asean_parser_v2 import ASEANParserV2
from parsers.cn_parser_v2 import CNParserV2
from parsers.jp_parser_v2 import JPParserV2
from parsers.ca_parser_v2 import CAParserV2

logger = setup_logger(__name__)

# Parser mapping
PARSERS = {
    "EU": EUParserV2,
    "ASEAN": ASEANParserV2,
    "CN": CNParserV2,
    "JP": JPParserV2,
    "CA": CAParserV2,
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

VALID_EXTENSIONS = {
    "pdf": [".pdf"],
    "json": [".json"],
    "html": [".html", ".htm"],
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_file(file_path: Path, file_type: str) -> None:
    """
    Validate uploaded file

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is too large or its extension does not match file_type
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size / 1024 / 1024:.2f}MB (max: 50MB)")

    if file_type not in VALID_EXTENSIONS:
        raise ValueError(f"Invalid file type: {file_type}. Must be one of {list(VALID_EXTENSIONS)}")

    if file_path.suffix.lower() not in VALID_EXTENSIONS[file_type]:
        raise ValueError(f"File extension {file_path.suffix} doesn't match type {file_type}")

    logger.info(f"File validation passed: {file_path.name} ({file_size / 1024:.2f}KB)")


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
    perf = PerformanceMonitor()
    perf.start("total")

    logger.info(f"Processing uploaded file for {jurisdiction}: {file_path}")

    perf.start("validation")
    if jurisdiction not in JURISDICTIONS:
        raise ValueError(f"Invalid jurisdiction: {jurisdiction}. Must be one of {list(JURISDICTIONS.keys())}")

    validate_file(file_path, file_type)
    perf.end("validation")

    perf.start("data_loading")
    upload_dir = RAW_DATA_DIR / jurisdiction / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    if version is None:
        version = utc_now().strftime("%Y%m%d%H%M%S")

    jurisdiction_config = JURISDICTIONS[jurisdiction]
    stem = f"{version}_{annex if annex else 'regulation'}"

    if file_type == "json":
        try:
            raw_data = load_json(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {e}") from e
        logger.info(f"Loaded JSON file with keys: {list(raw_data.keys())}")
        raw_data_path = file_path
    else:
        # Copy the PDF/HTML into the versioned upload directory and write a
        # metadata JSON next to it; the V2 parsers consume that JSON.
        dest_path = upload_dir / f"{stem}{file_path.suffix}"
        shutil.copy2(file_path, dest_path)
        logger.info(f"Copied file to {dest_path}")

        raw_data = {
            "jurisdiction": jurisdiction,
            "file_path": str(dest_path),
            "file_type": file_type,
            "annex": annex,
            "version": version,
            "uploaded_at": utc_now().isoformat(),
            "metadata": {
                "source": "uploaded_file",
                "version": version,
                "published_at": jurisdiction_config.get("published_date"),
                "effective_date": jurisdiction_config.get("effective_date"),
                "regulation": jurisdiction_config.get("regulation"),
            }
        }

        raw_data_path = upload_dir / f"{stem}.json"
        save_json(raw_data, raw_data_path)
        logger.info(f"Saved raw data metadata to {raw_data_path}")
    perf.end("data_loading")

    parser_class = PARSERS.get(jurisdiction)
    if parser_class is None:
        raise ValueError(f"No parser available for jurisdiction: {jurisdiction}")

    parser = parser_class()
    logger.info(f"Initialized {jurisdiction} parser ({parser_class.__name__})")

    # Not parser.run(): it would save the tables itself and we save them again
    # below under the caller-supplied version.
    perf.start("parsing")
    try:
        parser.parse_all_tables(load_json(raw_data_path))
        logger.info("Successfully parsed data with V2 parser")
    except Exception as e:
        logger.error(f"Failed to parse data: {e}", exc_info=True)
        raise ValueError(f"Parsing failed: {e}") from e
    finally:
        perf.end("parsing")

    perf.start("saving")
    try:
        saved_paths = parser.save_tables(version)
        logger.info(f"Saved tables: {list(saved_paths.keys())}")
    except Exception as e:
        logger.error(f"Failed to save tables: {e}", exc_info=True)
        raise ValueError(f"Save failed: {e}") from e
    finally:
        perf.end("saving")

    statistics = parser.get_statistics()

    perf.end("total")
    perf.log_summary()

    result = {
        "success": True,
        "jurisdiction": jurisdiction,
        "version": version,
        "file_type": file_type,
        "annex": annex,
        "statistics": statistics,
        "tables_saved": {k: str(v) for k, v in saved_paths.items()},
        "processed_at": utc_now().isoformat(),
        "performance": perf.get_summary(),
    }

    logger.info(f"Processing complete: {json.dumps(result, indent=2, ensure_ascii=False, default=str)}")
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

        if args.output:
            save_json(result, Path(args.output))
            logger.info(f"Saved result to {args.output}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

        sys.exit(0)

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
            "processed_at": utc_now().isoformat(),
        }

        if args.output:
            save_json(result, Path(args.output))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

        sys.exit(1)


if __name__ == "__main__":
    main()
