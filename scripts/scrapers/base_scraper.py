"""Base scraper class for regulation data"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RAW_DATA_DIR, JURISDICTIONS, get_version_info
from utils import setup_logger, save_json, compute_hash

logger = setup_logger(__name__)


class BaseScraper(ABC):
    """Base class for jurisdiction-specific scrapers"""

    def __init__(self, jurisdiction_code: str):
        """
        Initialize scraper

        Args:
            jurisdiction_code: Jurisdiction code (EU, JP, CN, CA, ASEAN)
        """
        self.jurisdiction_code = jurisdiction_code
        self.jurisdiction_config = JURISDICTIONS.get(jurisdiction_code)

        if not self.jurisdiction_config:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction_code}")

        self.logger = setup_logger(f"{__name__}.{jurisdiction_code}")
        self.output_dir = RAW_DATA_DIR / jurisdiction_code
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch regulation data from source

        Returns:
            Dictionary containing raw data and metadata
        """
        pass

    @abstractmethod
    def parse_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from raw data

        Args:
            raw_data: Raw data from fetch()

        Returns:
            Metadata dictionary with keys like:
            - published_at: Publication date
            - effective_date: Effective date
            - version: Version identifier
        """
        pass

    def save_raw_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """
        Save raw data to file

        Args:
            data: Data to save
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.jurisdiction_code}_{timestamp}.json"

        output_path = self.output_dir / filename
        save_json(data, output_path)

        return output_path

    def create_version_snapshot(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a version snapshot with metadata

        Args:
            raw_data: Raw regulation data

        Returns:
            Snapshot dictionary with version info
        """
        metadata = self.parse_metadata(raw_data)
        version_info = get_version_info()

        # Compute hash of data
        data_hash = compute_hash(self.output_dir / "latest.json") if (self.output_dir / "latest.json").exists() else None

        snapshot = {
            "jurisdiction": self.jurisdiction_code,
            "fetched_at": version_info["timestamp"],
            "version": version_info["version"],
            "metadata": metadata,
            "data_hash": data_hash,
            "raw_data": raw_data,
        }

        return snapshot

    def run(self) -> Dict[str, Any]:
        """
        Run the complete scraping process

        Returns:
            Version snapshot
        """
        self.logger.info(f"Starting scraper for {self.jurisdiction_code}")

        try:
            # Fetch data
            raw_data = self.fetch()
            self.logger.info(f"Successfully fetched data for {self.jurisdiction_code}")

            # Create snapshot
            snapshot = self.create_version_snapshot(raw_data)

            # Save to latest.json
            latest_path = self.output_dir / "latest.json"
            save_json(snapshot, latest_path)

            # Save versioned copy
            version_filename = f"{self.jurisdiction_code}_{snapshot['version']}.json"
            self.save_raw_data(snapshot, version_filename)

            self.logger.info(f"Completed scraper for {self.jurisdiction_code}")

            return snapshot

        except Exception as e:
            self.logger.error(f"Error in scraper for {self.jurisdiction_code}: {e}", exc_info=True)
            raise
