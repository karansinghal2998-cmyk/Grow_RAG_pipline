import re
import sys
import logging
from pathlib import Path
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    FACTUAL = "FACTUAL"
    ADVISORY = "ADVISORY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    AMBIGUOUS_SCHEME = "AMBIGUOUS_SCHEME"
    JAILBREAK = "JAILBREAK"


@dataclass
class IntentResult:
    """
    Holds the output of intent classification and target scheme extraction.
    """
    intent: QueryIntent
    target_scheme_id: Optional[str]
    detected_scheme_name: Optional[str]
    confidence_score: float
    reasoning: str


class IntentClassifier:
    """
    Classifies user queries into FACTUAL vs ADVISORY/OUT_OF_SCOPE/AMBIGUOUS_SCHEME,
    identifying target scheme IDs and intercepting non-compliance financial advice requests.
    """

    # Supported Scheme Mappings (5 Exclusive HDFC Schemes)
    SUPPORTED_SCHEMES: Dict[str, Dict[str, Any]] = {
        "hdfc-gold-etf-fund-of-fund-direct-plan-growth": {
            "name": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
            "aliases": ["gold etf", "gold fof", "gold fund of fund", "hdfc gold", "hdfc gold etf"],
        },
        "hdfc-large-cap-fund-direct-growth": {
            "name": "HDFC Large Cap Fund Direct Growth",
            "aliases": ["large cap", "largecap", "hdfc large cap", "hdfc large-cap"],
        },
        "hdfc-small-cap-fund-direct-growth": {
            "name": "HDFC Small Cap Fund Direct Growth",
            "aliases": ["small cap", "smallcap", "hdfc small cap", "hdfc small-cap"],
        },
        "hdfc-silver-etf-fof-direct-growth": {
            "name": "HDFC Silver ETF FoF Direct Growth",
            "aliases": ["silver etf", "silver fof", "silver fund of fund", "hdfc silver", "hdfc silver etf"],
        },
        "hdfc-mid-cap-fund-direct-growth": {
            "name": "HDFC Mid Cap Fund Direct Growth",
            "aliases": ["mid cap", "midcap", "hdfc mid cap", "hdfc mid-cap"],
        },
    }

    # Common Non-Target AMC / Fund Keywords
    NON_TARGET_AMC_PATTERNS = re.compile(
        r"\b(?:sbi|axis|nippon|icici|parag\s+parikh|mirae|uti|quant|kotak|tata|bandhan|dsp|motilal|canara|sundaram|invesco|hsbc|edelweiss|franklin)\b",
        re.IGNORECASE
    )

    # Advisory / Speculative Keywords & Phrases
    ADVISORY_PATTERNS = [
        re.compile(r"\bshould\s+i\s+(?:invest|buy|sell|choose|switch|put)\b", re.IGNORECASE),
        re.compile(r"\bwhich\s+(?:fund|scheme)\s+is\s+(?:better|best|good|safer|more\s+profitable)\b", re.IGNORECASE),
        re.compile(r"\bis\s+(?:it|this|that|[\w\s]+)\s+(?:worth|safe|good\s+time|advisable|recommended)\b", re.IGNORECASE),
        re.compile(r"\bwhere\s+to\s+invest\b", re.IGNORECASE),
        re.compile(r"\bpredict|forecast|future\s+returns?|expected\s+returns?|target\s+nav|\d+%\s+returns?\b", re.IGNORECASE),
        re.compile(r"\b(?:vs|versus|compared\s+to)\b", re.IGNORECASE),
        re.compile(r"\brecommend\s+(?:a\s+fund|any\s+fund|me)\b", re.IGNORECASE),
        re.compile(r"\bhow\s+much\s+(?:profit|returns?)\s+will\s+i\s+(?:get|make|earn)\b", re.IGNORECASE),
        re.compile(r"\bworth\s+(?:paying|buying|investing)\b", re.IGNORECASE),
    ]

    # Factual Keyword Patterns
    FACTUAL_PATTERNS = [
        re.compile(r"\bexpense\s+ratio\b", re.IGNORECASE),
        re.compile(r"\bexit\s+load\b", re.IGNORECASE),
        re.compile(r"\bminimum\s+sip|min\s+sip|sip\s+amount\b", re.IGNORECASE),
        re.compile(r"\briskometer|risk\s+level|risk\s+category\b", re.IGNORECASE),
        re.compile(r"\bbenchmark|index\b", re.IGNORECASE),
        re.compile(r"\bnav|net\s+asset\s+value\b", re.IGNORECASE),
        re.compile(r"\bfund\s+size|aum\b", re.IGNORECASE),
        re.compile(r"\bcategory|asset\s+class\b", re.IGNORECASE),
        re.compile(r"\bstatement|capital\s+gains|download|tax\s+report\b", re.IGNORECASE),
    ]

    def extract_scheme(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Identifies if the query references one of the 5 target HDFC schemes.
        Returns (scheme_id, scheme_name).
        """
        text_lower = text.lower()
        matched_scheme_id = None
        matched_scheme_name = None
        longest_alias_len = 0

        for scheme_id, info in self.SUPPORTED_SCHEMES.items():
            aliases = info["aliases"] + [info["name"].lower()]
            for alias in aliases:
                if alias in text_lower:
                    if len(alias) > longest_alias_len:
                        longest_alias_len = len(alias)
                        matched_scheme_id = scheme_id
                        matched_scheme_name = info["name"]

        return matched_scheme_id, matched_scheme_name

    def classify(self, query: str, is_jailbreak: bool = False) -> IntentResult:
        """
        Classifies query intent and matches target scheme ID.
        """
        # 1. Jailbreak Check
        if is_jailbreak:
            return IntentResult(
                intent=QueryIntent.JAILBREAK,
                target_scheme_id=None,
                detected_scheme_name=None,
                confidence_score=1.0,
                reasoning="Prompt injection / security override flag set."
            )

        # 2. Out of Scope AMC / Non-Target Fund Check
        if self.NON_TARGET_AMC_PATTERNS.search(query):
            non_target_match = self.NON_TARGET_AMC_PATTERNS.search(query).group(0)
            return IntentResult(
                intent=QueryIntent.OUT_OF_SCOPE,
                target_scheme_id=None,
                detected_scheme_name=None,
                confidence_score=0.95,
                reasoning=f"Query references non-indexed AMC/fund '{non_target_match}'. Scope is limited strictly to 5 HDFC schemes."
            )

        # 3. Advisory Intent Check
        for adv_pat in self.ADVISORY_PATTERNS:
            if adv_pat.search(query):
                adv_match = adv_pat.search(query).group(0)
                scheme_id, scheme_name = self.extract_scheme(query)
                return IntentResult(
                    intent=QueryIntent.ADVISORY,
                    target_scheme_id=scheme_id,
                    detected_scheme_name=scheme_name,
                    confidence_score=0.95,
                    reasoning=f"Advisory/speculative pattern detected: '{adv_match}'."
                )

        # 4. Extract Target Scheme
        scheme_id, scheme_name = self.extract_scheme(query)

        # 5. Statement / General Process Query Check (Can be scheme-agnostic)
        is_statement_query = bool(re.search(r"\b(?:statement|capital\s+gains|download|groww)\b", query, re.IGNORECASE))

        # 6. Scheme Ambiguity Check
        if not scheme_id and not is_statement_query:
            # Check if it's a factual question that needs a scheme
            is_factual_term = any(pat.search(query) for pat in self.FACTUAL_PATTERNS)
            if is_factual_term:
                return IntentResult(
                    intent=QueryIntent.AMBIGUOUS_SCHEME,
                    target_scheme_id=None,
                    detected_scheme_name=None,
                    confidence_score=0.90,
                    reasoning="Factual query detected but target scheme is unspecified among the 5 supported HDFC schemes."
                )

        # 7. Default to FACTUAL Intent
        return IntentResult(
            intent=QueryIntent.FACTUAL,
            target_scheme_id=scheme_id,
            detected_scheme_name=scheme_name,
            confidence_score=0.90,
            reasoning="Objective factual financial query."
        )


if __name__ == "__main__":
    classifier = IntentClassifier()
    test_queries = [
        "What is the expense ratio of HDFC Large Cap Fund?",
        "Should I invest in HDFC Small Cap Fund?",
        "What is the expense ratio of SBI Bluechip Fund?",
        "What is the minimum SIP amount?",
        "How to download capital gains statement on Groww?",
        "HDFC Large Cap vs HDFC Mid Cap: which gives better returns?",
        "Will HDFC Gold ETF FoF give 20% returns next month?",
        "Is 1% exit load in HDFC Small Cap worth paying?",
    ]

    for q in test_queries:
        res = classifier.classify(q)
        print("=" * 60)
        print(f"Query: {q}")
        print(f"Intent: {res.intent.value} | Scheme ID: {res.target_scheme_id}")
        print(f"Reason: {res.reasoning}")
