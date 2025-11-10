"""Base parser class for regulation data"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..config import PARSED_DATA_DIR, RULES_DATA_DIR
from ..utils import setup_logger, save_json, load_json, compute_data_hash

logger = setup_logger(__name__)


class BaseParser(ABC):
    """Base class for parsing regulation data"""

    def __init__(self, jurisdiction_code: str):
        """
        Initialize parser

        Args:
            jurisdiction_code: Jurisdiction code (EU, JP, CN, CA, ASEAN)
        """
        self.jurisdiction_code = jurisdiction_code
        self.logger = setup_logger(f"{__name__}.{jurisdiction_code}")
        self.parsed_dir = PARSED_DATA_DIR / jurisdiction_code
        self.rules_dir = RULES_DATA_DIR / jurisdiction_code
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
        self.rules_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw data into structured format

        Args:
            raw_data: Raw data from scraper

        Returns:
            Parsed data dictionary
        """
        pass

    def extract_ingredients(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract ingredient list from parsed data

        Args:
            parsed_data: Parsed regulation data

        Returns:
            List of ingredient dictionaries
        """
        ingredients = []
        ingredient_ids = set()

        # This method should be overridden by subclasses if needed
        # Base implementation extracts from clauses

        clauses = parsed_data.get("clauses", [])
        for clause in clauses:
            ing_ref = clause.get("ingredient_ref")
            if ing_ref and ing_ref not in ingredient_ids:
                ingredients.append({
                    "id": ing_ref,
                    "inci": clause.get("inci", ing_ref),
                    "cas": clause.get("cas"),
                    "synonyms": clause.get("synonyms", []),
                    "family": clause.get("family", {}),
                })
                ingredient_ids.add(ing_ref)

        return ingredients

    def extract_clauses(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract clause list from parsed data

        Args:
            parsed_data: Parsed regulation data

        Returns:
            List of clause dictionaries
        """
        # Override in subclasses
        return parsed_data.get("clauses", [])

    def create_rule_structure(
        self,
        raw_data: Dict[str, Any],
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create final rule structure for consumption

        Args:
            raw_data: Original raw data
            parsed_data: Parsed data

        Returns:
            Rule structure dictionary
        """
        # Extract metadata from raw_data
        metadata = raw_data.get("metadata", {})

        # Extract ingredients and clauses
        ingredients = self.extract_ingredients(parsed_data)
        clauses = self.extract_clauses(parsed_data)

        # Create structure
        rules = {
            "jurisdiction": self.jurisdiction_code,
            "version": metadata.get("version"),
            "published_at": metadata.get("published_at"),
            "effective_date": metadata.get("effective_date"),
            "fetched_at": raw_data.get("fetched_at"),
            "source": metadata.get("source"),
            "regulation": metadata.get("regulation"),
            "data_hash": compute_data_hash(clauses),
            "statistics": {
                "total_ingredients": len(ingredients),
                "total_clauses": len(clauses),
                "banned": len([c for c in clauses if c.get("category") == "banned"]),
                "restricted": len([c for c in clauses if c.get("category") == "restricted"]),
                "allowed": len([c for c in clauses if c.get("category") in ["allowed", "colorant", "preservative", "uv_filter"]]),
            },
            "ingredients": ingredients,
            "clauses": clauses,
        }

        return rules

    def save_rules(self, rules: Dict[str, Any], version: Optional[str] = None) -> Path:
        """
        Save rules to file

        Args:
            rules: Rule data
            version: Optional version identifier

        Returns:
            Path to saved file
        """
        if version is None:
            version = rules.get("version", datetime.utcnow().strftime("%Y%m%d%H%M%S"))

        filename = f"{version}.json"
        output_path = self.rules_dir / filename
        save_json(rules, output_path)

        # Also save as latest.json
        latest_path = self.rules_dir / "latest.json"
        save_json(rules, latest_path)

        return output_path

    def run(self, raw_data_path: Path) -> Dict[str, Any]:
        """
        Run complete parsing process

        Args:
            raw_data_path: Path to raw data JSON

        Returns:
            Parsed rules
        """
        self.logger.info(f"Parsing {raw_data_path}")

        # Load raw data
        raw_data = load_json(raw_data_path)

        # Parse
        parsed_data = self.parse(raw_data)

        # Create rule structure
        rules = self.create_rule_structure(raw_data, parsed_data)

        # Save
        version = rules.get("version")
        output_path = self.save_rules(rules, version)

        self.logger.info(f"Saved rules to {output_path}")
        self.logger.info(f"Statistics: {rules['statistics']}")

        return rules
