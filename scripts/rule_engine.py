"""Rule engine for cosmetics compliance checking"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RULES_DATA_DIR
from utils import setup_logger, load_json, normalize_inci_name, match_with_family_rules

logger = setup_logger(__name__)


class ComplianceResult:
    """Result of compliance check"""

    def __init__(
        self,
        ingredient_name: str,
        jurisdiction: str,
        status: str,
        matched_clauses: List[Dict[str, Any]],
        rationale: str = "",
        required_fields: List[str] = None,
        warnings: List[str] = None
    ):
        self.ingredient_name = ingredient_name
        self.jurisdiction = jurisdiction
        self.status = status  # compliant, restricted, banned, insufficient_info
        self.matched_clauses = matched_clauses
        self.rationale = rationale
        self.required_fields = required_fields or []
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "ingredient_name": self.ingredient_name,
            "jurisdiction": self.jurisdiction,
            "status": self.status,
            "matched_clauses": self.matched_clauses,
            "rationale": self.rationale,
            "required_fields": self.required_fields,
            "warnings": self.warnings,
        }


class RuleEngine:
    """Rule engine for compliance checking"""

    def __init__(self):
        self.rules_cache = {}
        self.ingredient_db = self._load_ingredient_db()

    def _load_ingredient_db(self) -> Dict[str, Dict]:
        """Load ingredient database"""
        db_path = Path(__file__).parent.parent / "data" / "ingredients_db.json"
        if db_path.exists():
            data = load_json(db_path)
            return data.get("ingredients", {})
        return {}

    def load_rules(self, jurisdiction: str) -> Dict[str, Any]:
        """
        Load rules for jurisdiction

        Args:
            jurisdiction: Jurisdiction code

        Returns:
            Rules data
        """
        if jurisdiction in self.rules_cache:
            return self.rules_cache[jurisdiction]

        rules_dir = RULES_DATA_DIR / jurisdiction
        latest_file = rules_dir / "latest.json"

        if not latest_file.exists():
            logger.warning(f"No rules found for {jurisdiction}")
            return {"clauses": []}

        rules = load_json(latest_file)
        self.rules_cache[jurisdiction] = rules
        return rules

    def check_ingredient(
        self,
        ingredient_name: str,
        jurisdiction: str,
        concentration: Optional[float] = None,
        product_type: Optional[str] = None,
        **kwargs
    ) -> ComplianceResult:
        """
        Check ingredient compliance

        Args:
            ingredient_name: Ingredient name
            jurisdiction: Jurisdiction code
            concentration: Concentration (% w/w)
            product_type: Product type (rinse-off, leave-on, etc.)
            **kwargs: Additional product info

        Returns:
            ComplianceResult
        """
        # Load rules
        rules = self.load_rules(jurisdiction)
        clauses = rules.get("clauses", [])

        # Normalize ingredient name
        normalized_name = normalize_inci_name(ingredient_name)

        # Find matching clauses
        matched_clauses = []
        for clause in clauses:
            if self._matches_ingredient(normalized_name, clause):
                matched_clauses.append(clause)

        # If no match, consider compliant
        if not matched_clauses:
            return ComplianceResult(
                ingredient_name=ingredient_name,
                jurisdiction=jurisdiction,
                status="compliant",
                matched_clauses=[],
                rationale="No restrictions found in database"
            )

        # Evaluate clauses
        return self._evaluate_clauses(
            ingredient_name,
            jurisdiction,
            matched_clauses,
            concentration,
            product_type,
            **kwargs
        )

    def _matches_ingredient(self, normalized_name: str, clause: Dict[str, Any]) -> bool:
        """Check if clause matches ingredient"""
        # Normalize clause ingredient
        clause_ing = clause.get("ingredient_ref", "")
        clause_inci = clause.get("inci", "")

        normalized_clause = normalize_inci_name(clause_ing)
        normalized_inci = normalize_inci_name(clause_inci)

        # Direct match
        if normalized_name == normalized_clause or normalized_name == normalized_inci:
            return True

        # Check CAS number
        clause_cas = clause.get("cas")
        if clause_cas:
            # Try to find CAS in ingredient DB
            for ing_id, ing_data in self.ingredient_db.items():
                if ing_data.get("cas") == clause_cas:
                    if normalize_inci_name(ing_data.get("inci", "")) == normalized_name:
                        return True

        # Check synonyms (if available)
        # In a full implementation, this would use the ingredient DB

        return False

    def _evaluate_clauses(
        self,
        ingredient_name: str,
        jurisdiction: str,
        clauses: List[Dict[str, Any]],
        concentration: Optional[float],
        product_type: Optional[str],
        **kwargs
    ) -> ComplianceResult:
        """
        Evaluate matched clauses

        Args:
            ingredient_name: Ingredient name
            jurisdiction: Jurisdiction code
            clauses: Matched clauses
            concentration: Concentration
            product_type: Product type
            **kwargs: Additional product info

        Returns:
            ComplianceResult
        """
        # Check for banned
        for clause in clauses:
            if clause.get("category") == "banned":
                return ComplianceResult(
                    ingredient_name=ingredient_name,
                    jurisdiction=jurisdiction,
                    status="banned",
                    matched_clauses=[clause],
                    rationale=f"Ingredient is banned. {clause.get('source_ref')}",
                    warnings=[clause.get("notes", "")]
                )

        # Check for restricted
        restricted_clauses = [c for c in clauses if c.get("category") == "restricted"]

        if restricted_clauses:
            return self._check_restrictions(
                ingredient_name,
                jurisdiction,
                restricted_clauses,
                concentration,
                product_type,
                **kwargs
            )

        # If only allowed categories (colorant, preservative, uv_filter)
        allowed_clauses = [
            c for c in clauses
            if c.get("category") in ["colorant", "preservative", "uv_filter", "allowed"]
        ]

        if allowed_clauses:
            return self._check_allowed(
                ingredient_name,
                jurisdiction,
                allowed_clauses,
                concentration,
                product_type,
                **kwargs
            )

        # Default to compliant
        return ComplianceResult(
            ingredient_name=ingredient_name,
            jurisdiction=jurisdiction,
            status="compliant",
            matched_clauses=clauses,
            rationale="Ingredient matches database but has no specific restrictions"
        )

    def _check_restrictions(
        self,
        ingredient_name: str,
        jurisdiction: str,
        clauses: List[Dict[str, Any]],
        concentration: Optional[float],
        product_type: Optional[str],
        **kwargs
    ) -> ComplianceResult:
        """Check restriction compliance"""
        required_fields = []
        warnings = []

        for clause in clauses:
            conditions = clause.get("conditions", {})
            max_pct = conditions.get("max_pct")

            # Check concentration
            if max_pct is not None:
                if concentration is None:
                    required_fields.append("concentration")
                elif concentration > max_pct:
                    return ComplianceResult(
                        ingredient_name=ingredient_name,
                        jurisdiction=jurisdiction,
                        status="non_compliant",
                        matched_clauses=[clause],
                        rationale=f"Concentration {concentration}% exceeds maximum {max_pct}%. {clause.get('source_ref')}",
                        warnings=[clause.get("warnings", "")]
                    )

            # Check product type
            allowed_types = conditions.get("product_type", [])
            if allowed_types:
                if product_type is None:
                    required_fields.append("product_type")
                elif product_type not in allowed_types:
                    return ComplianceResult(
                        ingredient_name=ingredient_name,
                        jurisdiction=jurisdiction,
                        status="non_compliant",
                        matched_clauses=[clause],
                        rationale=f"Product type '{product_type}' not allowed. Allowed types: {', '.join(allowed_types)}. {clause.get('source_ref')}",
                        warnings=[clause.get("warnings", "")]
                    )

            # Collect warnings
            if clause.get("warnings"):
                warnings.append(clause.get("warnings"))

        # If we need more info
        if required_fields:
            return ComplianceResult(
                ingredient_name=ingredient_name,
                jurisdiction=jurisdiction,
                status="insufficient_info",
                matched_clauses=clauses,
                rationale=f"Additional information required: {', '.join(required_fields)}",
                required_fields=required_fields,
                warnings=warnings
            )

        # If all checks pass
        return ComplianceResult(
            ingredient_name=ingredient_name,
            jurisdiction=jurisdiction,
            status="restricted_compliant",
            matched_clauses=clauses,
            rationale=f"Ingredient is restricted but complies with conditions. {clauses[0].get('source_ref')}",
            warnings=warnings
        )

    def _check_allowed(
        self,
        ingredient_name: str,
        jurisdiction: str,
        clauses: List[Dict[str, Any]],
        concentration: Optional[float],
        product_type: Optional[str],
        **kwargs
    ) -> ComplianceResult:
        """Check allowed category compliance (preservatives, colorants, UV filters)"""
        required_fields = []
        warnings = []

        for clause in clauses:
            conditions = clause.get("conditions", {})
            max_pct = conditions.get("max_pct")

            # Check concentration
            if max_pct is not None:
                if concentration is None:
                    required_fields.append("concentration")
                elif concentration > max_pct:
                    return ComplianceResult(
                        ingredient_name=ingredient_name,
                        jurisdiction=jurisdiction,
                        status="non_compliant",
                        matched_clauses=[clause],
                        rationale=f"Concentration {concentration}% exceeds maximum {max_pct}%. {clause.get('source_ref')}",
                        warnings=[clause.get("warnings", "")]
                    )

            # Collect warnings
            if clause.get("warnings"):
                warnings.append(clause.get("warnings"))

        # If we need more info
        if required_fields:
            return ComplianceResult(
                ingredient_name=ingredient_name,
                jurisdiction=jurisdiction,
                status="insufficient_info",
                matched_clauses=clauses,
                rationale=f"Additional information required: {', '.join(required_fields)}",
                required_fields=required_fields,
                warnings=warnings
            )

        # If all checks pass
        category = clauses[0].get("category")
        return ComplianceResult(
            ingredient_name=ingredient_name,
            jurisdiction=jurisdiction,
            status="compliant",
            matched_clauses=clauses,
            rationale=f"Ingredient is permitted as {category} and complies with conditions. {clauses[0].get('source_ref')}",
            warnings=warnings
        )

    def check_formulation(
        self,
        ingredients: List[Dict[str, Any]],
        jurisdictions: List[str],
        product_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check entire formulation against multiple jurisdictions

        Args:
            ingredients: List of ingredient dicts with name, concentration, etc.
            jurisdictions: List of jurisdiction codes
            product_info: Product information (type, application site, etc.)

        Returns:
            Dict with results for each jurisdiction
        """
        product_info = product_info or {}
        results = {}

        for jurisdiction in jurisdictions:
            jurisdiction_results = []

            for ing in ingredients:
                result = self.check_ingredient(
                    ingredient_name=ing.get("name", ""),
                    jurisdiction=jurisdiction,
                    concentration=ing.get("concentration"),
                    product_type=product_info.get("product_type"),
                    **product_info
                )
                jurisdiction_results.append(result.to_dict())

            # Summary for jurisdiction
            statuses = [r["status"] for r in jurisdiction_results]
            overall_status = "compliant"

            if "banned" in statuses or "non_compliant" in statuses:
                overall_status = "non_compliant"
            elif "restricted_compliant" in statuses:
                overall_status = "restricted_compliant"
            elif "insufficient_info" in statuses:
                overall_status = "insufficient_info"

            results[jurisdiction] = {
                "overall_status": overall_status,
                "total_ingredients": len(ingredients),
                "ingredient_results": jurisdiction_results,
            }

        return results


if __name__ == "__main__":
    # Test the rule engine
    engine = RuleEngine()

    # Test with formaldehyde
    result = engine.check_ingredient("Formaldehyde", "EU")
    print(f"Formaldehyde in EU: {result.status} - {result.rationale}")

    # Test with salicylic acid
    result = engine.check_ingredient("Salicylic Acid", "EU", concentration=1.5, product_type="leave-on")
    print(f"Salicylic Acid (1.5%) in EU: {result.status} - {result.rationale}")
