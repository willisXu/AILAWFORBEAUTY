"""File utilities for reading/writing data"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict
from ..config import OUTPUT_CONFIG
from .logger import setup_logger

logger = setup_logger(__name__)


def save_json(data: Any, file_path: Path, **kwargs) -> Path:
    """
    Save data as JSON file

    Args:
        data: Data to save
        file_path: Output file path
        **kwargs: Additional json.dump arguments

    Returns:
        Path to saved file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    json_kwargs = {
        "indent": OUTPUT_CONFIG["indent"],
        "ensure_ascii": OUTPUT_CONFIG["ensure_ascii"],
        **kwargs
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, **json_kwargs)

    logger.info(f"Saved JSON to {file_path}")
    return file_path


def load_json(file_path: Path) -> Any:
    """
    Load data from JSON file

    Args:
        file_path: Input file path

    Returns:
        Loaded data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded JSON from {file_path}")
    return data


def compute_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute hash of file

    Args:
        file_path: File to hash
        algorithm: Hash algorithm (sha256, md5, etc.)

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    hash_value = hasher.hexdigest()
    logger.debug(f"Computed {algorithm} hash for {file_path}: {hash_value}")

    return hash_value


def compute_data_hash(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute hash of data

    Args:
        data: Data to hash (will be JSON serialized)
        algorithm: Hash algorithm

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    hasher.update(json_str.encode('utf-8'))
    return hasher.hexdigest()
