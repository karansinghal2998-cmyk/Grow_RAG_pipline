import pytest
from pathlib import Path
from scraper.fetcher import DocumentFetcher, FetchResult
from config import settings


def test_derive_scheme_id():
    url = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    scheme_id = DocumentFetcher.derive_scheme_id(url)
    assert scheme_id == "hdfc-large-cap-fund-direct-growth"


def test_cache_filepath_generation(tmp_path):
    fetcher = DocumentFetcher(raw_data_dir=tmp_path)
    cache_path = fetcher.get_cache_filepath("hdfc-small-cap-fund-direct-growth")
    assert cache_path == tmp_path / "hdfc-small-cap-fund-direct-growth.html"


def test_fetch_url_local_cache(tmp_path):
    fetcher = DocumentFetcher(raw_data_dir=tmp_path)
    url = "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    scheme_id = "hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    cache_file = tmp_path / f"{scheme_id}.html"

    # Pre-populate mock HTML cache
    mock_html = "<html><body><h1>HDFC Gold ETF Test Page</h1></body></html>"
    cache_file.write_text(mock_html, encoding="utf-8")

    # Perform fetch using cache
    result = fetcher.fetch_url(url, use_cache=True)

    assert result.success is True
    assert result.scheme_id == scheme_id
    assert result.html_content == mock_html
    assert result.status_code == 200
    assert result.file_path == cache_file


def test_batch_target_urls_list():
    assert len(settings.TARGET_SCHEME_URLS) == 5
    for url in settings.TARGET_SCHEME_URLS:
        assert url.startswith("https://groww.in/mutual-funds/hdfc-")
