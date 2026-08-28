import json
import sys
import logging
from pathlib import Path
from dataclasses import asdict

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from scraper.fetcher import DocumentFetcher
from scraper.parser import HTMLParser
from ingestion.chunker import SemanticChunker

logger = logging.getLogger(__name__)


def export_phase2_data():
    fetcher = DocumentFetcher()
    parser = HTMLParser()
    chunker = SemanticChunker()

    output_dir = settings.PROCESSED_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    all_metrics = []
    all_chunks = []

    md_content = [
        "# Phase 2 Extracted Mutual Fund Corpus & Chunk Review\n",
        "This document contains the structured financial metrics and chunked text data extracted from the 5 target Groww URLs for review.\n",
        "---\n"
    ]

    for url in settings.TARGET_SCHEME_URLS:
        res = fetcher.fetch_url(url, use_cache=True)
        if res.success and res.html_content:
            metrics = parser.parse(res.html_content, url)
            all_metrics.append(asdict(metrics))

            chunks = chunker.create_chunks(metrics)
            for c in chunks:
                all_chunks.append({
                    "chunk_id": c.chunk_id,
                    "scheme_id": c.scheme_id,
                    "scheme_name": c.scheme_name,
                    "category": c.category,
                    "sub_category": c.sub_category,
                    "source_url": c.source_url,
                    "text": c.text,
                    "metadata": c.metadata,
                })

            # Append to Markdown review document
            md_content.append(f"## Scheme: {metrics.scheme_name}\n")
            md_content.append(f"* **Category**: {metrics.category} ({metrics.sub_category})")
            md_content.append(f"* **Riskometer**: {metrics.riskometer}")
            md_content.append(f"* **Expense Ratio**: `{metrics.expense_ratio}`")
            md_content.append(f"* **Exit Load**: `{metrics.exit_load}`")
            md_content.append(f"* **Minimum SIP**: `{metrics.min_sip}`")
            md_content.append(f"* **Fund Size (AUM)**: `{metrics.fund_size}`")
            md_content.append(f"* **Source URL**: [{metrics.source_url}]({metrics.source_url})\n")

            md_content.append("### Chunks Indexed for Vector Search:\n")
            for idx, c in enumerate(chunks, 1):
                md_content.append(f"#### Chunk {idx}: `{c.chunk_id}` (Type: `{c.metadata['chunk_type']}`)")
                md_content.append("```text")
                md_content.append(c.text)
                md_content.append("```\n")
            
            md_content.append("---\n")

    # Save JSON 1: Structured Metrics
    json_metrics_path = output_dir / "extracted_metrics.json"
    json_metrics_path.write_text(json.dumps(all_metrics, indent=2), encoding="utf-8")
    logger.info(f"Saved extracted metrics to: {json_metrics_path}")

    # Save JSON 2: Indexed Chunks
    json_chunks_path = output_dir / "indexed_chunks.json"
    json_chunks_path.write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
    logger.info(f"Saved indexed chunks to: {json_chunks_path}")

    # Save Markdown 3: Human-Readable Review
    md_review_path = output_dir / "corpus_review.md"
    md_review_path.write_text("\n".join(md_content), encoding="utf-8")
    logger.info(f"Saved human-readable review to: {md_review_path}")

    print("\nPhase 2 Data Export Completed Successfully!")
    print(f"1. Metrics JSON   : {json_metrics_path}")
    print(f"2. Chunks JSON    : {json_chunks_path}")
    print(f"3. Markdown Review: {md_review_path}")


if __name__ == "__main__":
    export_phase2_data()
