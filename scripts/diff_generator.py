"""Generate diff reports between regulation versions"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RULES_DATA_DIR, DIFF_DATA_DIR
from utils import setup_logger, save_json, load_json

logger = setup_logger(__name__)


class DiffGenerator:
    """Generate diffs between regulation versions"""

    def __init__(self, jurisdiction: str):
        self.jurisdiction = jurisdiction
        self.rules_dir = RULES_DATA_DIR / jurisdiction
        self.diff_dir = DIFF_DATA_DIR / jurisdiction
        self.diff_dir.mkdir(parents=True, exist_ok=True)

    def compare_versions(
        self,
        old_version: Dict[str, Any],
        new_version: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two versions and generate diff

        Args:
            old_version: Old version rules
            new_version: New version rules

        Returns:
            Diff dictionary
        """
        old_clauses = {c["id"]: c for c in old_version.get("clauses", [])}
        new_clauses = {c["id"]: c for c in new_version.get("clauses", [])}

        old_ids = set(old_clauses.keys())
        new_ids = set(new_clauses.keys())

        # Find additions, removals, and modifications
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids

        added = [new_clauses[id] for id in added_ids]
        removed = [old_clauses[id] for id in removed_ids]

        modified = []
        for id in common_ids:
            old_clause = old_clauses[id]
            new_clause = new_clauses[id]

            changes = self._compare_clauses(old_clause, new_clause)
            if changes:
                modified.append({
                    "clause_id": id,
                    "ingredient": new_clause.get("ingredient_ref"),
                    "changes": changes,
                    "old": old_clause,
                    "new": new_clause,
                })

        # Identify affected ingredients
        affected_ingredients = self._get_affected_ingredients(added, removed, modified)

        diff = {
            "jurisdiction": self.jurisdiction,
            "from_version": old_version.get("version"),
            "to_version": new_version.get("version"),
            "from_date": old_version.get("published_at"),
            "to_date": new_version.get("published_at"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_changes": len(added) + len(removed) + len(modified),
                "added": len(added),
                "removed": len(removed),
                "modified": len(modified),
                "affected_ingredients": len(affected_ingredients),
            },
            "changes": {
                "added": added,
                "removed": removed,
                "modified": modified,
            },
            "affected_ingredients": list(affected_ingredients),
        }

        return diff

    def _compare_clauses(
        self,
        old_clause: Dict[str, Any],
        new_clause: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare two clauses and identify changes

        Args:
            old_clause: Old clause
            new_clause: New clause

        Returns:
            List of changes
        """
        changes = []

        # Compare category
        if old_clause.get("category") != new_clause.get("category"):
            changes.append({
                "field": "category",
                "old_value": old_clause.get("category"),
                "new_value": new_clause.get("category"),
                "severity": "high",
            })

        # Compare conditions
        old_conditions = old_clause.get("conditions", {})
        new_conditions = new_clause.get("conditions", {})

        # Compare max_pct
        old_pct = old_conditions.get("max_pct")
        new_pct = new_conditions.get("max_pct")
        if old_pct != new_pct:
            severity = "high" if (new_pct is not None and old_pct is not None and new_pct < old_pct) else "medium"
            changes.append({
                "field": "max_pct",
                "old_value": old_pct,
                "new_value": new_pct,
                "severity": severity,
            })

        # Compare warnings
        if old_clause.get("warnings") != new_clause.get("warnings"):
            changes.append({
                "field": "warnings",
                "old_value": old_clause.get("warnings"),
                "new_value": new_clause.get("warnings"),
                "severity": "medium",
            })

        return changes

    def _get_affected_ingredients(
        self,
        added: List[Dict],
        removed: List[Dict],
        modified: List[Dict]
    ) -> Set[str]:
        """Get set of affected ingredient names"""
        ingredients = set()

        for clause in added:
            ing = clause.get("ingredient_ref")
            if ing:
                ingredients.add(ing)

        for clause in removed:
            ing = clause.get("ingredient_ref")
            if ing:
                ingredients.add(ing)

        for change in modified:
            ing = change.get("ingredient")
            if ing:
                ingredients.add(ing)

        return ingredients

    def generate_changelog(self, diff: Dict[str, Any]) -> str:
        """
        Generate human-readable changelog

        Args:
            diff: Diff dictionary

        Returns:
            Markdown changelog
        """
        lines = []

        lines.append(f"# Regulation Changes: {self.jurisdiction}")
        lines.append("")
        lines.append(f"**From Version:** {diff['from_version']} ({diff['from_date']})")
        lines.append(f"**To Version:** {diff['to_version']} ({diff['to_date']})")
        lines.append("")

        summary = diff["summary"]
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Changes:** {summary['total_changes']}")
        lines.append(f"- **Added Clauses:** {summary['added']}")
        lines.append(f"- **Removed Clauses:** {summary['removed']}")
        lines.append(f"- **Modified Clauses:** {summary['modified']}")
        lines.append(f"- **Affected Ingredients:** {summary['affected_ingredients']}")
        lines.append("")

        changes = diff["changes"]

        if changes["added"]:
            lines.append("## Added Clauses")
            lines.append("")
            for clause in changes["added"]:
                lines.append(f"- **{clause.get('ingredient_ref')}** ({clause.get('category')})")
                lines.append(f"  - Source: {clause.get('source_ref')}")
            lines.append("")

        if changes["removed"]:
            lines.append("## Removed Clauses")
            lines.append("")
            for clause in changes["removed"]:
                lines.append(f"- **{clause.get('ingredient_ref')}** ({clause.get('category')})")
                lines.append(f"  - Source: {clause.get('source_ref')}")
            lines.append("")

        if changes["modified"]:
            lines.append("## Modified Clauses")
            lines.append("")
            for mod in changes["modified"]:
                lines.append(f"- **{mod.get('ingredient')}** (Clause: {mod.get('clause_id')})")
                for change in mod["changes"]:
                    lines.append(f"  - {change['field']}: `{change['old_value']}` → `{change['new_value']}` (severity: {change['severity']})")
            lines.append("")

        if diff["affected_ingredients"]:
            lines.append("## Affected Ingredients")
            lines.append("")
            for ing in sorted(diff["affected_ingredients"]):
                lines.append(f"- {ing}")
            lines.append("")

        return "\n".join(lines)

    def save_diff(self, diff: Dict[str, Any]) -> Path:
        """Save diff to file"""
        from_ver = diff["from_version"]
        to_ver = diff["to_version"]
        filename = f"{from_ver}_to_{to_ver}.json"
        output_path = self.diff_dir / filename
        save_json(diff, output_path)

        # Save changelog
        changelog = self.generate_changelog(diff)
        changelog_path = self.diff_dir / f"{from_ver}_to_{to_ver}.md"
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(changelog)

        logger.info(f"Saved diff to {output_path}")
        logger.info(f"Saved changelog to {changelog_path}")

        return output_path


def main():
    """Generate diffs for all jurisdictions"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate regulation diff reports")
    parser.add_argument("--jurisdiction", type=str, help="Jurisdiction code (EU, JP, CN, CA, ASEAN)")
    parser.add_argument("--old", type=str, help="Path to old version JSON")
    parser.add_argument("--new", type=str, help="Path to new version JSON")

    args = parser.parse_args()

    if args.jurisdiction and args.old and args.new:
        # Generate specific diff
        generator = DiffGenerator(args.jurisdiction)

        old_version = load_json(Path(args.old))
        new_version = load_json(Path(args.new))

        diff = generator.compare_versions(old_version, new_version)
        generator.save_diff(diff)

        logger.info(f"Generated diff: {diff['summary']}")

    else:
        logger.error("Please provide --jurisdiction, --old, and --new arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
