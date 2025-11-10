"""HTTP utilities for fetching web resources"""

import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from ..config import SCRAPING_CONFIG
from .logger import setup_logger

logger = setup_logger(__name__)


def fetch_url(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
    retry_backoff: Optional[int] = None
) -> requests.Response:
    """
    Fetch URL with retry logic

    Args:
        url: URL to fetch
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers
        params: Optional query parameters
        data: Optional request body
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        retry_backoff: Backoff multiplier for retries

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    timeout = timeout or SCRAPING_CONFIG["timeout"]
    max_retries = max_retries or SCRAPING_CONFIG["max_retries"]
    retry_backoff = retry_backoff or SCRAPING_CONFIG["retry_backoff"]

    if headers is None:
        headers = {"User-Agent": SCRAPING_CONFIG["user_agent"]}

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout
            )

            response.raise_for_status()
            logger.info(f"Successfully fetched {url}")
            return response

        except requests.RequestException as e:
            wait_time = retry_backoff ** attempt

            if attempt < max_retries - 1:
                logger.warning(f"Failed to fetch {url}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                raise

    raise requests.RequestException(f"Failed to fetch {url}")


def download_file(url: str, output_path: Path, **kwargs) -> Path:
    """
    Download file from URL to local path

    Args:
        url: URL to download
        output_path: Local path to save file
        **kwargs: Additional arguments passed to fetch_url

    Returns:
        Path to downloaded file
    """
    logger.info(f"Downloading {url} to {output_path}")

    response = fetch_url(url, **kwargs)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        f.write(response.content)

    logger.info(f"Downloaded {url} to {output_path} ({len(response.content)} bytes)")

    return output_path
