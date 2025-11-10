"""Text processing utilities"""

import re
import unicodedata
from datetime import datetime
from typing import Optional, List
from ..config import PARSING_CONFIG
from .logger import setup_logger

logger = setup_logger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text: strip whitespace, normalize unicode, lowercase

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Normalize unicode (NFD -> NFC)
    text = unicodedata.normalize('NFKC', text)

    # Strip and collapse whitespace
    text = ' '.join(text.split())

    return text.strip()


def extract_percentage(text: str) -> Optional[float]:
    """
    Extract percentage value from text

    Args:
        text: Text containing percentage

    Returns:
        Percentage as float (0-100) or None if not found

    Examples:
        "2.5%" -> 2.5
        "max 0.5 %" -> 0.5
        "≤ 10%" -> 10.0
    """
    if not text:
        return None

    # Patterns for percentage extraction
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%',  # "2.5%"
        r'≤\s*(\d+(?:\.\d+)?)\s*%',  # "≤ 2.5%"
        r'max\s*(\d+(?:\.\d+)?)\s*%',  # "max 2.5%"
        r'maximum\s*(\d+(?:\.\d+)?)\s*%',  # "maximum 2.5%"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue

    return None


def parse_date(date_str: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    """
    Parse date string using multiple formats

    Args:
        date_str: Date string
        formats: List of date formats to try

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None

    formats = formats or PARSING_CONFIG["date_formats"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse date: {date_str}")
    return None


def clean_ingredient_name(name: str) -> str:
    """
    Clean ingredient name by removing extra formatting

    Args:
        name: Ingredient name

    Returns:
        Cleaned name
    """
    if not name:
        return ""

    # Normalize
    name = normalize_text(name)

    # Remove parenthetical notes (but keep chemical notation)
    # Keep things like (CI 77491) but remove things like (derived from...)
    name = re.sub(r'\([^)]*derived[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\([^)]*origin[^)]*\)', '', name, flags=re.IGNORECASE)

    # Remove trailing dots, commas
    name = name.rstrip('.,;')

    # Collapse whitespace again
    name = ' '.join(name.split())

    return name.strip()


def extract_cas_number(text: str) -> Optional[str]:
    """
    Extract CAS registry number from text

    Args:
        text: Text containing CAS number

    Returns:
        CAS number or None

    Example:
        "Salicylic acid (CAS 69-72-7)" -> "69-72-7"
    """
    if not text:
        return None

    # CAS number format: XXXXXX-XX-X
    pattern = r'\b(\d{2,7}-\d{2}-\d)\b'
    match = re.search(pattern, text)

    if match:
        return match.group(1)

    return None
