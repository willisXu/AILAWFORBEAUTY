"""Fuzzy matching utilities for ingredient names"""

import re
from typing import Optional, List, Tuple, Dict
from rapidfuzz import fuzz, process
from .text_utils import normalize_text, clean_ingredient_name
from .logger import setup_logger

logger = setup_logger(__name__)


def normalize_inci_name(name: str) -> str:
    """
    Normalize INCI name for matching

    Args:
        name: INCI name

    Returns:
        Normalized INCI name
    """
    name = clean_ingredient_name(name)

    # Convert to lowercase for matching
    name = name.lower()

    # Remove common prefixes/suffixes that don't affect identity
    prefixes_to_remove = [
        r'^aqua\s+',
        r'^water\s+',
    ]

    for prefix in prefixes_to_remove:
        name = re.sub(prefix, '', name, flags=re.IGNORECASE)

    return name


def fuzzy_match_ingredient(
    query: str,
    candidates: List[str],
    threshold: float = 0.90,
    limit: int = 5
) -> List[Tuple[str, float]]:
    """
    Fuzzy match ingredient name against candidates

    Args:
        query: Query ingredient name
        candidates: List of candidate names
        threshold: Minimum similarity threshold (0-1)
        limit: Maximum number of results

    Returns:
        List of (candidate, score) tuples sorted by score
    """
    query_norm = normalize_inci_name(query)

    # Use token_sort_ratio for better matching of reordered words
    results = process.extract(
        query_norm,
        candidates,
        scorer=fuzz.token_sort_ratio,
        limit=limit
    )

    # Filter by threshold and convert score to 0-1 range
    filtered = [
        (candidate, score / 100.0)
        for candidate, score, _ in results
        if score / 100.0 >= threshold
    ]

    if filtered:
        logger.debug(f"Fuzzy matched '{query}' -> {filtered[0][0]} ({filtered[0][1]:.2f})")
    else:
        logger.debug(f"No fuzzy match found for '{query}' above threshold {threshold}")

    return filtered


def extract_salt_base(name: str) -> Optional[str]:
    """
    Extract base compound from salt name

    Args:
        name: Chemical name (possibly a salt)

    Returns:
        Base compound name or None

    Examples:
        "Sodium benzoate" -> "benzoic acid"
        "Potassium sorbate" -> "sorbic acid"
    """
    # Common salt patterns
    salt_patterns = {
        r'sodium\s+(\w+)ate': r'\1ic acid',
        r'potassium\s+(\w+)ate': r'\1ic acid',
        r'calcium\s+(\w+)ate': r'\1ic acid',
        r'(\w+)\s+sodium\s+salt': r'\1',
        r'(\w+)\s+potassium\s+salt': r'\1',
    }

    name_lower = name.lower()

    for pattern, replacement in salt_patterns.items():
        match = re.search(pattern, name_lower)
        if match:
            base = re.sub(pattern, replacement, name_lower)
            return base.strip()

    return None


def is_polymer_variant(name1: str, name2: str) -> bool:
    """
    Check if two names represent the same polymer with different molecular weights

    Args:
        name1: First name
        name2: Second name

    Returns:
        True if they appear to be polymer variants

    Examples:
        "PEG-40" and "PEG-100" -> True
        "Polyethylene Glycol" and "PEG-8" -> True
    """
    # Remove numbers and dashes
    base1 = re.sub(r'[-\d]+', '', name1.lower()).strip()
    base2 = re.sub(r'[-\d]+', '', name2.lower()).strip()

    # Check if bases match
    if base1 == base2 and base1:
        return True

    # Check for PEG/Polyethylene glycol equivalence
    peg_variants = ['peg', 'polyethylene glycol', 'polyethyleneglycol']
    if base1 in peg_variants and base2 in peg_variants:
        return True

    return False


def match_with_family_rules(
    query: str,
    ingredient_db: Dict[str, Dict],
    threshold: float = 0.90
) -> Optional[Dict]:
    """
    Match ingredient considering family rules (salts, esters, polymers)

    Args:
        query: Query ingredient name
        ingredient_db: Dictionary of ingredients with family info
        threshold: Matching threshold

    Returns:
        Matched ingredient dict or None
    """
    query_norm = normalize_inci_name(query)

    # Try exact match first
    for ing_id, ing_data in ingredient_db.items():
        if normalize_inci_name(ing_data.get('inci', '')) == query_norm:
            return ing_data

        # Check synonyms
        for synonym in ing_data.get('synonyms', []):
            if normalize_inci_name(synonym) == query_norm:
                return ing_data

    # Try fuzzy match
    candidates = [ing['inci'] for ing in ingredient_db.values() if 'inci' in ing]
    fuzzy_results = fuzzy_match_ingredient(query, candidates, threshold=threshold, limit=1)

    if fuzzy_results:
        matched_inci = fuzzy_results[0][0]
        for ing_data in ingredient_db.values():
            if ing_data.get('inci') == matched_inci:
                return ing_data

    # Try salt matching
    salt_base = extract_salt_base(query)
    if salt_base:
        for ing_data in ingredient_db.values():
            family = ing_data.get('family', {})
            if family.get('salts_of') and normalize_inci_name(family['salts_of']) == salt_base:
                return ing_data

    # Try polymer matching
    for ing_data in ingredient_db.values():
        if is_polymer_variant(query, ing_data.get('inci', '')):
            family = ing_data.get('family', {})
            if family.get('polymer_range'):
                return ing_data

    return None
