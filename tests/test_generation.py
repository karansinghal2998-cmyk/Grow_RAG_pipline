import pytest
from generation.compliance_verifier import ComplianceVerifier
from generation.generator import ResponseGenerator
from guardrails.intent_classifier import QueryIntent


@pytest.fixture
def verifier():
    return ComplianceVerifier()


@pytest.fixture(scope="module")
def generator():
    return ResponseGenerator()


# =====================================================================
# 1. Compliance Verifier Unit Tests
# =====================================================================

def test_truncate_long_response(verifier):
    raw_text = (
        "Sentence one is here. Sentence two is here. Sentence three is here. "
        "Sentence four should be stripped out. Sentence five should also be stripped out. "
        "Source: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth\n"
        "Last updated from sources: 2026-08-27"
    )
    res = verifier.verify_and_format(raw_text)
    assert res.is_truncated is True
    assert res.sentence_count == 3
    assert "Sentence four" not in res.verified_text
    assert "Last updated from sources: 2026-08-27" in res.verified_text


def test_citation_url_injection(verifier):
    raw_text = "Minimum monthly SIP amount for HDFC Gold ETF Fund of Fund is ₹100."
    res = verifier.verify_and_format(raw_text, fallback_source_url="https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth")
    assert res.citation_url == "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    assert "Source: https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth" in res.verified_text


def test_date_footer_enforcement(verifier):
    raw_text = "The expense ratio is 0.75%. Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
    res = verifier.verify_and_format(raw_text)
    assert res.has_footer is True
    assert "Last updated from sources: 2026-08-27" in res.verified_text


# =====================================================================
# 2. Response Generator End-to-End Unit Tests
# =====================================================================

def test_factual_query_rag_flow(generator):
    query = "What is the expense ratio of HDFC Large Cap Fund?"
    res = generator.generate(query)
    assert res.intent == QueryIntent.FACTUAL
    assert res.is_refusal is False
    assert res.target_scheme_id == "hdfc-large-cap-fund-direct-growth"
    assert "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth" in res.response_text
    assert "Last updated from sources: 2026-08-27" in res.response_text


def test_advisory_query_interception(generator):
    query = "Should I invest in HDFC Small Cap Fund?"
    res = generator.generate(query)
    assert res.intent == QueryIntent.ADVISORY
    assert res.is_refusal is True
    assert "facts-only" in res.response_text
    assert "https://www.amfiindia.com/investor-corner/knowledge-center" in res.response_text


def test_pii_query_sanitization(generator):
    query = "My PAN is ABCDE1234F, what is the minimum SIP for HDFC Mid Cap Fund?"
    res = generator.generate(query)
    assert res.sanitized_query != query
    assert "[REDACTED_PAN]" in res.sanitized_query
    assert res.intent == QueryIntent.FACTUAL
    assert res.target_scheme_id == "hdfc-mid-cap-fund-direct-growth"
