import pytest
from pathlib import Path
from config import settings
from scraper.fetcher import DocumentFetcher
from scraper.parser import HTMLParser, SchemeMetrics
from ingestion.chunker import SemanticChunker, Chunk
from ingestion.vector_store import VectorStoreManager


def test_html_parser_on_cached_files():
    fetcher = DocumentFetcher()
    parser = HTMLParser()

    for url in settings.TARGET_SCHEME_URLS:
        res = fetcher.fetch_url(url, use_cache=True)
        assert res.success is True
        assert res.html_content is not None

        metrics = parser.parse(res.html_content, url)
        assert isinstance(metrics, SchemeMetrics)
        assert metrics.scheme_name.startswith("HDFC")
        assert metrics.source_url == url
        assert len(metrics.raw_text_summary) > 100


def test_semantic_chunker():
    fetcher = DocumentFetcher()
    parser = HTMLParser()
    chunker = SemanticChunker()

    sample_url = settings.TARGET_SCHEME_URLS[0]
    res = fetcher.fetch_url(sample_url, use_cache=True)
    metrics = parser.parse(res.html_content, sample_url)

    chunks = chunker.create_chunks(metrics)
    assert len(chunks) == 5  # Overview, expense_ratio, exit_load, sip_and_nav, statement_download
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.source_url == sample_url
        assert "chunk_type" in c.metadata


def test_vector_store_search(tmp_path):
    vdb = VectorStoreManager(vector_db_dir=tmp_path)
    
    # Ingest 1 test scheme
    fetcher = DocumentFetcher()
    parser = HTMLParser()
    chunker = SemanticChunker()

    sample_url = settings.TARGET_SCHEME_URLS[0]
    res = fetcher.fetch_url(sample_url, use_cache=True)
    metrics = parser.parse(res.html_content, sample_url)
    chunks = chunker.create_chunks(metrics)

    added_count = vdb.add_chunks(chunks)
    assert added_count == 5

    # Test Search Query
    results = vdb.search("What is the exit load?", top_k=2)
    assert len(results) > 0
    assert "exit_load" in results[0]["chunk_id"] or "text" in results[0]
    assert results[0]["similarity_score"] > 0.0
