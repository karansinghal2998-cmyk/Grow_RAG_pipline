import pytest
from retrieval.hybrid_retriever import HybridRetriever, RetrievedChunk


@pytest.fixture(scope="module")
def retriever():
    return HybridRetriever()


# =====================================================================
# 1. Sparse BM25 Search Unit Tests
# =====================================================================

def test_bm25_exact_keyword_matching(retriever):
    results = retriever._search_bm25("expense ratio", top_k=3, target_scheme_id="hdfc-large-cap-fund-direct-growth")
    assert len(results) > 0
    assert any("expense_ratio" in r["chunk_id"] for r in results)


def test_bm25_synonym_expansion(retriever):
    results = retriever._search_bm25("lock-in period", top_k=3, target_scheme_id="hdfc-small-cap-fund-direct-growth")
    assert len(results) > 0
    # Should match exit load chunk via synonym expansion
    assert any("exit_load" in r["chunk_id"] for r in results)


# =====================================================================
# 2. Dense Vector Search Unit Tests
# =====================================================================

def test_dense_vector_search(retriever):
    results = retriever._search_dense("annual management fee", top_k=3, target_scheme_id="hdfc-mid-cap-fund-direct-growth")
    assert len(results) > 0
    assert any("expense_ratio" in r["chunk_id"] for r in results)


# =====================================================================
# 3. Hybrid RRF Retrieval Unit Tests
# =====================================================================

def test_hybrid_retrieval_rrf(retriever):
    results = retriever.search(
        query="What is the exit load for HDFC Small Cap Fund?",
        top_k=3,
        target_scheme_id="hdfc-small-cap-fund-direct-growth"
    )
    assert len(results) > 0
    assert isinstance(results[0], RetrievedChunk)
    assert "exit_load" in results[0].chunk_id
    assert results[0].scheme_id == "hdfc-small-cap-fund-direct-growth"
    assert results[0].rrf_score > 0.0


def test_hybrid_retrieval_scheme_filter(retriever):
    target_id = "hdfc-silver-etf-fof-direct-growth"
    results = retriever.search(
        query="What is the expense ratio?",
        top_k=3,
        target_scheme_id=target_id
    )
    assert len(results) > 0
    # Strict metadata filter check: every single result MUST match target_scheme_id
    for r in results:
        assert r.scheme_id == target_id


def test_hybrid_retrieval_statement_download(retriever):
    results = retriever.search(
        query="How to download capital gains statement on Groww?",
        top_k=2,
        target_scheme_id=None
    )
    assert len(results) > 0
    assert any("statement_download" in r.chunk_id for r in results)
