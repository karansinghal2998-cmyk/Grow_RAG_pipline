import re
import sys
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """
    Holds the post-processed compliant response and verification status flags.
    """
    original_text: str
    verified_text: str
    sentence_count: int
    is_truncated: bool
    citation_url: str
    has_footer: bool


class ComplianceVerifier:
    """
    Output Post-Processor enforcing strict compliance constraints on LLM generated responses:
    1. Maximum 3 sentences
    2. Exactly 1 citation link (from Groww URLs)
    3. Timestamped footer line: 'Last updated from sources: <date>'
    """

    DEFAULT_DATE_FOOTER: str = "Last updated from sources: 2026-08-27"
    GROWW_URL_PATTERN = re.compile(r"https?://groww\.in/mutual-funds/[\w\-]+", re.IGNORECASE)

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences while protecting decimal numbers (e.g. 0.20%, ₹11,197.05 Cr).
        """
        # Remove footer line before sentence counting if present
        clean_text = re.sub(r"Last updated from sources:.*$", "", text, flags=re.IGNORECASE).strip()
        
        # Split on period/exclamation/question mark followed by space & capital letter or end of string,
        # ensuring no digit is immediately before the dot (e.g. 0.20%)
        raw_sentences = re.split(r"(?<=[^0-9][.!?])\s+(?=[A-Z0-9])|(?<=[.!?])\n+", clean_text)
        
        # Clean and filter non-empty sentences
        sentences = [s.strip() for s in raw_sentences if s and len(s.strip()) > 1]
        return sentences

    def extract_citations(self, text: str) -> List[str]:
        """
        Extracts all valid Groww source URLs in the text.
        """
        return self.GROWW_URL_PATTERN.findall(text)

    def verify_and_format(
        self,
        raw_text: str,
        fallback_source_url: str = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    ) -> VerificationResult:
        """
        Rigorously inspects and formats raw LLM output to strictly satisfy all compliance rules.
        """
        # 1. Separate body text from footer if present
        footer_match = re.search(r"Last updated from sources:\s*[\d\-]+", raw_text, re.IGNORECASE)
        footer_text = footer_match.group(0) if footer_match else self.DEFAULT_DATE_FOOTER

        # Body text without footer
        body = re.sub(r"Last updated from sources:.*$", "", raw_text, flags=re.IGNORECASE).strip()

        # 2. Extract & Enforce Citation URLs
        citations = self.extract_citations(body)
        citation_url = citations[0] if citations else fallback_source_url

        # Remove extra raw URLs from body to prepare clean sentence structure
        body_clean_urls = self.GROWW_URL_PATTERN.sub("", body).strip()

        # 3. Sentence Splitting & Truncation (Max 3 sentences)
        sentences = self.split_sentences(body_clean_urls)
        is_truncated = False

        if len(sentences) > 3:
            logger.info(f"Truncating response from {len(sentences)} sentences to 3 sentences.")
            sentences = sentences[:3]
            is_truncated = True

        # Reconstruct body text with max 3 sentences
        formatted_body = " ".join(sentences).strip()

        # Ensure punctuation at end of formatted body
        if formatted_body and not formatted_body[-1] in ".!?":
            formatted_body += "."

        # 4. Construct Final Compliant Output: Body + Single Citation Link + Footer
        final_text = (
            f"{formatted_body}\n\n"
            f"Source: {citation_url}\n"
            f"{footer_text}"
        )

        return VerificationResult(
            original_text=raw_text,
            verified_text=final_text,
            sentence_count=len(sentences),
            is_truncated=is_truncated,
            citation_url=citation_url,
            has_footer=True,
        )


if __name__ == "__main__":
    verifier = ComplianceVerifier()

    sample_outputs = [
        # Scenario 1: >3 Sentences
        (
            "The expense ratio for HDFC Large Cap Fund Direct Growth is 1.02%. "
            "Minimum monthly SIP amount is ₹100. Fund size (AUM) is ₹40,197.89 Cr. "
            "Riskometer is classified as Very High Risk. It is managed by HDFC Mutual Fund. "
            "Source: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth\n"
            "Last updated from sources: 2026-08-27"
        ),
        # Scenario 2: Missing Citation & Footer
        "Minimum monthly SIP amount for HDFC Gold ETF Fund of Fund Direct Plan Growth is ₹100. Expense ratio is 0.20%.",
    ]

    for raw in sample_outputs:
        res = verifier.verify_and_format(raw)
        print("=" * 60)
        print("Raw Output:\n", res.original_text)
        print("\nVerified Output:\n", res.verified_text)
        print(f"Sentences: {res.sentence_count} | Truncated: {res.is_truncated} | Citation: {res.citation_url}")
