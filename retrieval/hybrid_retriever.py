import re
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from rank_bm25 import BM25Okapi

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from ingestion.chunker import Chunk, SemanticChunker
from ingestion.vector_store import VectorStoreManager
from scraper.fetcher import DocumentFetcher
from scraper.parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """
    Structured payload representing a context chunk retrieved via Hybrid Search.
    """
    chunk_id: str
    scheme_id: str
    scheme_name: str
    category: str
    source_url: str
    text: str
    rrf_score: float
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """
    Hybrid Search Engine combining Sparse Keyword Search (BM25) and
    Dense Vector Search (BAAI BGE Embeddings via ChromaDB) fused with
    Reciprocal Rank Fusion (RRF).
    """

    # Financial Synonyms for Sparse Query Expansion
    SYNONYMS: Dict[str, List[str]] = {
        "lock-in": ["redemption tenure", "exit load", "lockin"],
        "lockin": ["redemption tenure", "exit load"],
        "fee": ["expense ratio", "exit load", "charge"],
        "charge": ["expense ratio", "exit load"],
        "cost": ["expense ratio"],
        "sip": ["minimum monthly sip", "min sip"],
        "return": ["nav", "benchmark index"],
        "benchmark": ["nifty", "bse"],
        "download": ["capital gains", "account statement", "reports"],
    }

    def __init__(self, vector_store: Optional[VectorStoreManager] = None, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.vector_store = vector_store or VectorStoreManager()

        # Load or build chunk corpus for BM25
        self.chunks: List[Dict[str, Any]] = self._load_all_chunks()
        self.tokenized_corpus: List[List[str]] = [self._tokenize(c["text"]) for c in self.chunks]
        
        logger.info(f"Building BM25 Index over {len(self.chunks)} financial chunks...")
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _load_all_chunks(self) -> List[Dict[str, Any]]:
        """
        Loads all chunks from processed JSON cache or generates them from raw HTML.
        """
        json_chunks_path = settings.PROCESSED_DATA_DIR / "indexed_chunks.json"
        if json_chunks_path.exists():
            try:
                data = json.loads(json_chunks_path.read_text(encoding="utf-8"))
                logger.info(f"Loaded {len(data)} chunks from {json_chunks_path}")
                return data
            except Exception as e:
                logger.warning(f"Error loading {json_chunks_path}: {e}")

        # Fallback: Parse & Chunk on the fly
        logger.info("Generating chunks on the fly for BM25 indexing...")
        fetcher = DocumentFetcher()
        parser = HTMLParser()
        chunker = SemanticChunker()

        chunks = []
        for url in settings.TARGET_SCHEME_URLS:
            res = fetcher.fetch_url(url, use_cache=True)
            if res.success and res.html_content:
                metrics = parser.parse(res.html_content, url)
                c_list = chunker.create_chunks(metrics)
                for c in c_list:
                    chunks.append({
                        "chunk_id": c.chunk_id,
                        "scheme_id": c.scheme_id,
                        "scheme_name": c.scheme_name,
                        "category": c.category,
                        "sub_category": c.sub_category,
                        "source_url": c.source_url,
                        "text": c.text,
                        "metadata": c.metadata,
                    })
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizes text into lowercase alphanumeric tokens.
        """
        return re.findall(r"\w+", text.lower())

    def _expand_query(self, query: str) -> str:
        """
        Appends financial synonyms to the query string to enhance sparse BM25 recall.
        """
        query_lower = query.lower()
        expanded_tokens = query_lower.split()

        for term, syns in self.SYNONYMS.items():
            if term in query_lower:
                expanded_tokens.extend(syns)

        return " ".join(expanded_tokens)

    def _search_bm25(self, query: str, top_k: int = 10, target_scheme_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes BM25 sparse keyword search with optional scheme filtering.
        """
        expanded_query = self._expand_query(query)
        query_tokens = self._tokenize(expanded_query)
        
        scores = self.bm25.get_scores(query_tokens)

        # Pair scores with chunk objects
        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            
            # Apply Scheme Metadata Filtering
            if target_scheme_id and chunk.get("scheme_id") != target_scheme_id:
                continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "scheme_id": chunk.get("scheme_id", ""),
                "scheme_name": chunk.get("scheme_name", ""),
                "category": chunk.get("category", ""),
                "source_url": chunk.get("source_url", ""),
                "metadata": chunk.get("metadata", {}),
                "score": float(score),
            })

        # Sort by BM25 score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _search_dense(self, query: str, top_k: int = 10, target_scheme_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes BGE dense vector search via ChromaDB with optional scheme filtering.
        """
        filter_dict = {"scheme_id": target_scheme_id} if target_scheme_id else None
        return self.vector_store.search(query, top_k=top_k, filter_dict=filter_dict)

    def search(self, query: str, top_k: int = 3, target_scheme_id: Optional[str] = None) -> List[RetrievedChunk]:
        """
        Performs Hybrid Search using Reciprocal Rank Fusion (RRF) to combine BM25 and Dense BGE results.
        """
        fetch_k = max(top_k * 3, 10)

        # 1. Execute Sparse & Dense Retrievals
        sparse_results = self._search_bm25(query, top_k=fetch_k, target_scheme_id=target_scheme_id)
        dense_results = self._search_dense(query, top_k=fetch_k, target_scheme_id=target_scheme_id)

        # 2. Track Ranks per Chunk ID
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}

        # Process Dense Ranks
        for rank, item in enumerate(dense_results, 1):
            cid = item["chunk_id"]
            dense_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item

        # Process Sparse Ranks
        for rank, item in enumerate(sparse_results, 1):
            cid = item["chunk_id"]
            sparse_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item

        # 3. Sort by Combined RRF Score Descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        # 4. Construct Final RetrievedChunk Output Objects
        final_retrieved: List[RetrievedChunk] = []
        for cid in sorted_cids[:top_k]:
            item = chunk_map[cid]
            meta = item.get("metadata", {})

            final_retrieved.append(
                RetrievedChunk(
                    chunk_id=cid,
                    scheme_id=meta.get("scheme_id") or item.get("scheme_id", ""),
                    scheme_name=meta.get("scheme_name") or item.get("scheme_name", ""),
                    category=meta.get("category") or item.get("category", ""),
                    source_url=meta.get("source_url") or item.get("source_url", ""),
                    text=item.get("text", ""),
                    rrf_score=rrf_scores[cid],
                    dense_rank=dense_ranks.get(cid),
                    sparse_rank=sparse_ranks.get(cid),
                    metadata=meta,
                )
            )

        logger.info(f"Hybrid Search for '{query}' returned {len(final_retrieved)} top chunks (Target Scheme: {target_scheme_id}).")
        return final_retrieved


if __name__ == "__main__":
    retriever = HybridRetriever()

    test_queries = [
        ("What is the expense ratio of HDFC Large Cap Fund?", "hdfc-large-cap-fund-direct-growth"),
        ("What is the exit load for HDFC Small Cap Fund?", "hdfc-small-cap-fund-direct-growth"),
        ("How to download capital gains statement on Groww?", None),
        ("Minimum SIP amount for HDFC Gold ETF FoF", "hdfc-gold-etf-fund-of-fund-direct-plan-growth"),
    ]

    for q, scheme_id in test_queries:
        print("=" * 70)
        print(f"Query: {q} | Filter Scheme ID: {scheme_id}")
        results = retriever.search(q, top_k=2, target_scheme_id=scheme_id)
        for idx, r in enumerate(results, 1):
            print(f"\nResult #{idx} (RRF Score: {r.rrf_score:.5f} | Dense Rank: {r.dense_rank} | Sparse Rank: {r.sparse_rank}):")
            print(f"ID: {r.chunk_id} | Scheme: {r.scheme_name}")
            print(r.text)
