import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    scheme_id: str
    success: bool
    status_code: Optional[int] = None
    html_content: Optional[str] = None
    file_path: Optional[Path] = None
    error_message: Optional[str] = None
    fetched_at: float = field(default_factory=time.time)


class DocumentFetcher:
    """
    Document Fetcher module for retrieving and caching HTML content
    from the target Groww Mutual Fund URLs.
    """

    def __init__(self, raw_data_dir: Optional[Path] = None):
        self.raw_data_dir = raw_data_dir or settings.RAW_DATA_DIR
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    @staticmethod
    def derive_scheme_id(url: str) -> str:
        """Extract a clean scheme identifier slug from the URL."""
        slug = url.rstrip("/").split("/")[-1]
        return slug

    def get_cache_filepath(self, scheme_id: str) -> Path:
        """Returns local path for cached HTML file."""
        return self.raw_data_dir / f"{scheme_id}.html"

    def fetch_url(
        self,
        url: str,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> FetchResult:
        """
        Fetch HTML content for a single Groww URL with retry and disk caching support.
        """
        scheme_id = self.derive_scheme_id(url)
        cache_path = self.get_cache_filepath(scheme_id)

        # Check local cache first if enabled and not forcing refresh
        if use_cache and not force_refresh and cache_path.exists():
            try:
                logger.info(f"Loading cached HTML for '{scheme_id}' from {cache_path}")
                content = cache_path.read_text(encoding="utf-8")
                return FetchResult(
                    url=url,
                    scheme_id=scheme_id,
                    success=True,
                    status_code=200,
                    html_content=content,
                    file_path=cache_path,
                )
            except Exception as e:
                logger.warning(f"Failed to read cache for {scheme_id}: {e}. Proceeding with live fetch.")

        # Execute HTTP Request with retry logic
        retries = settings.MAX_RETRIES
        delay = 1.0

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Fetching URL (Attempt {attempt}/{retries}): {url}")
                with httpx.Client(timeout=settings.REQUEST_TIMEOUT, follow_redirects=True) as client:
                    response = client.get(url, headers=self.headers)
                    response.raise_for_status()
                    
                    html_text = response.text
                    
                    # Persist to local disk cache
                    cache_path.write_text(html_text, encoding="utf-8")
                    logger.info(f"Successfully fetched and cached '{scheme_id}' ({len(html_text)} bytes)")

                    return FetchResult(
                        url=url,
                        scheme_id=scheme_id,
                        success=True,
                        status_code=response.status_code,
                        html_content=html_text,
                        file_path=cache_path,
                    )
            except httpx.HTTPStatusError as exc:
                logger.error(f"HTTP Status Error for {url}: {exc.response.status_code}")
                if exc.response.status_code == 429:
                    logger.warning("Rate limited (429). Exponential backoff...")
                    time.sleep(delay * 2)
                if attempt == retries:
                    return FetchResult(
                        url=url,
                        scheme_id=scheme_id,
                        success=False,
                        status_code=exc.response.status_code,
                        error_message=str(exc),
                    )
            except Exception as exc:
                logger.error(f"Network error on attempt {attempt} for {url}: {exc}")
                if attempt == retries:
                    return FetchResult(
                        url=url,
                        scheme_id=scheme_id,
                        success=False,
                        error_message=str(exc),
                    )
            
            time.sleep(delay)
            delay *= 2

        return FetchResult(
            url=url,
            scheme_id=scheme_id,
            success=False,
            error_message="Unknown fetch failure",
        )

    def fetch_all_target_schemes(
        self,
        urls: Optional[List[str]] = None,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> List[FetchResult]:
        """
        Batch fetch all 5 target Groww mutual fund URLs with rate limiting.
        """
        target_urls = urls or settings.TARGET_SCHEME_URLS
        results: List[FetchResult] = []

        logger.info(f"Starting batch fetch for {len(target_urls)} scheme URLs...")
        for idx, url in enumerate(target_urls, 1):
            logger.info(f"[{idx}/{len(target_urls)}] Processing: {url}")
            result = self.fetch_url(url, use_cache=use_cache, force_refresh=force_refresh)
            results.append(result)
            
            # Apply rate limiting delay between network requests if live fetching
            if not result.file_path or force_refresh:
                time.sleep(settings.RATE_LIMIT_DELAY)

        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch fetch completed: {successful}/{len(target_urls)} succeeded.")
        return results


if __name__ == "__main__":
    fetcher = DocumentFetcher()
    results = fetcher.fetch_all_target_schemes()
    for res in results:
        print(f"Scheme ID: {res.scheme_id} | Success: {res.success} | File: {res.file_path}")
