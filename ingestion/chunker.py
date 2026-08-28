import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.parser import SchemeMetrics
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    chunk_id: str
    scheme_id: str
    scheme_name: str
    category: str
    sub_category: str
    source_url: str
    text: str
    metadata: Dict[str, Any]


class SemanticChunker:
    """
    Splits scheme metric summaries into semantically cohesive key-value chunks
    optimised for RAG vector retrieval while preserving metadata.
    """

    def __init__(self, chunk_size: int = 350, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def create_chunks(self, metrics: SchemeMetrics) -> List[Chunk]:
        """
        Generates semantically cohesive chunks for a parsed scheme,
        ensuring key metrics stay intact alongside metadata payload.
        """
        chunks: List[Chunk] = []
        base_metadata = {
            "scheme_id": metrics.scheme_id,
            "scheme_name": metrics.scheme_name,
            "category": metrics.category,
            "sub_category": metrics.sub_category,
            "source_url": metrics.source_url,
            "last_updated": "2026-08-27",
            "doc_type": "groww_scheme_page",
        }

        # 1. Overview Facts Chunk (Contains all core metrics together)
        overview_text = (
            f"Scheme Overview for {metrics.scheme_name}:\n"
            f"Category: {metrics.category} - {metrics.sub_category}\n"
            f"Riskometer: {metrics.riskometer}\n"
            f"Expense Ratio: {metrics.expense_ratio}\n"
            f"Minimum SIP Investment: {metrics.min_sip}\n"
            f"Fund Size (AUM): {metrics.fund_size}\n"
            f"Exit Load: {metrics.exit_load}\n"
            f"Source Citation Link: {metrics.source_url}"
        )
        chunks.append(
            Chunk(
                chunk_id=f"{metrics.scheme_id}_chunk_overview",
                scheme_id=metrics.scheme_id,
                scheme_name=metrics.scheme_name,
                category=metrics.category,
                sub_category=metrics.sub_category,
                source_url=metrics.source_url,
                text=overview_text,
                metadata={**base_metadata, "chunk_type": "overview"},
            )
        )

        # 2. Specific Metric Chunks (Expense Ratio, Exit Load, Min SIP, Statement Download)
        specific_chunks_data = [
            (
                "expense_ratio",
                f"{metrics.scheme_name} Expense Ratio:\n"
                f"The expense ratio for {metrics.scheme_name} is {metrics.expense_ratio}.\n"
                f"Expense ratio represents the annual fee charged by the fund house to manage the fund.\n"
                f"Source Citation Link: {metrics.source_url}"
            ),
            (
                "exit_load",
                f"{metrics.scheme_name} Exit Load Details:\n"
                f"The exit load for {metrics.scheme_name} is: {metrics.exit_load}.\n"
                f"Exit load is the fee levied if an investor redeems or switches out of fund units within the specified exit load tenure.\n"
                f"Source Citation Link: {metrics.source_url}"
            ),
            (
                "sip_and_nav",
                f"{metrics.scheme_name} Minimum SIP & Riskometer:\n"
                f"Minimum monthly SIP amount for {metrics.scheme_name} is {metrics.min_sip}.\n"
                f"Riskometer classification: {metrics.riskometer}.\n"
                f"Benchmark Index: {metrics.benchmark}.\n"
                f"Source Citation Link: {metrics.source_url}"
            ),
            (
                "statement_download",
                f"How to download Account Statement & Capital Gains Report on Groww for {metrics.scheme_name}:\n"
                f"1. Log in to your Groww account.\n"
                f"2. Go to Profile > Reports > Mutual Fund Statements.\n"
                f"3. Select Capital Gains Statement or Account Statement, choose the date range, and click Download/Email.\n"
                f"Source Citation Link: {metrics.source_url}"
            ),
        ]

        for idx, (chunk_type, text_content) in enumerate(specific_chunks_data, 1):
            chunks.append(
                Chunk(
                    chunk_id=f"{metrics.scheme_id}_chunk_{chunk_type}",
                    scheme_id=metrics.scheme_id,
                    scheme_name=metrics.scheme_name,
                    category=metrics.category,
                    sub_category=metrics.sub_category,
                    source_url=metrics.source_url,
                    text=text_content,
                    metadata={**base_metadata, "chunk_type": chunk_type},
                )
            )

        logger.info(f"Generated {len(chunks)} chunks for '{metrics.scheme_id}'")
        return chunks


if __name__ == "__main__":
    from scraper.fetcher import DocumentFetcher
    from scraper.parser import HTMLParser

    fetcher = DocumentFetcher()
    parser = HTMLParser()
    chunker = SemanticChunker()

    sample_url = settings.TARGET_SCHEME_URLS[0]
    res = fetcher.fetch_url(sample_url)
    if res.success and res.html_content:
        metrics = parser.parse(res.html_content, sample_url)
        chunks = chunker.create_chunks(metrics)
        for c in chunks:
            print("=" * 50)
            print(f"ID: {c.chunk_id} | Type: {c.metadata['chunk_type']}")
            print(c.text)
