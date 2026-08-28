import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from guardrails.pii_redactor import PIIRedactor, RedactionResult
from guardrails.intent_classifier import IntentClassifier, QueryIntent, IntentResult
from guardrails.refusal_handler import RefusalHandler, RefusalResponse
from guardrails.rate_limiter import GroqRateLimiter
from retrieval.hybrid_retriever import HybridRetriever, RetrievedChunk
from generation.compliance_verifier import ComplianceVerifier, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class AssistantResponse:
    """
    Final structured response payload returned to the caller / UI layer.
    """
    query: str
    sanitized_query: str
    response_text: str
    intent: QueryIntent
    target_scheme_id: Optional[str]
    retrieved_chunks: List[RetrievedChunk]
    is_refusal: bool
    verification_info: Optional[VerificationResult] = None


class ResponseGenerator:
    """
    End-to-End LLM Response Generation & Compliance Pipeline.
    Orchestrates PII Redaction -> Intent Classification -> Groq Rate Limiting ->
    Hybrid Retrieval -> Groq LLM Generation -> Compliance Verification.
    """

    def __init__(
        self,
        pii_redactor: Optional[PIIRedactor] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        refusal_handler: Optional[RefusalHandler] = None,
        hybrid_retriever: Optional[HybridRetriever] = None,
        compliance_verifier: Optional[ComplianceVerifier] = None,
        rate_limiter: Optional[GroqRateLimiter] = None,
    ):
        self.redactor = pii_redactor or PIIRedactor()
        self.classifier = intent_classifier or IntentClassifier()
        self.refusal_handler = refusal_handler or RefusalHandler()
        self.retriever = hybrid_retriever or HybridRetriever()
        self.verifier = compliance_verifier or ComplianceVerifier()
        self.rate_limiter = rate_limiter or GroqRateLimiter()

        # Initialize Groq Client
        self.groq_api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.groq_client = None
        
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Groq LLM Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}. Will use grounded fallback.")

    def _build_system_prompt(self) -> str:
        return (
            "You are a facts-only Mutual Fund FAQ Assistant for HDFC Mutual Fund schemes.\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Answer strictly using ONLY the provided context facts. Do NOT add investment advice, recommendations, opinions, or forecasts.\n"
            "2. Keep your response brief, accurate, and factual (AT MOST 3 SENTENCES).\n"
            "3. Include EXACTLY ONE source citation URL link from the context.\n"
            "4. Append a footer line at the end: 'Last updated from sources: 2026-08-27'."
        )

    def _build_user_prompt(self, query: str, chunks: List[RetrievedChunk]) -> str:
        context_blocks = []
        for idx, c in enumerate(chunks, 1):
            context_blocks.append(
                f"--- Fact Context #{idx} (Scheme: {c.scheme_name}) ---\n"
                f"{c.text}\n"
                f"Source Citation URL: {c.source_url}"
            )
        context_str = "\n\n".join(context_blocks)

        return (
            f"Fact Context:\n{context_str}\n\n"
            f"User Question: {query}\n\n"
            f"Provide a factual answer in 1-3 sentences with exact citation link."
        )

    def _generate_fallback_response(self, chunks: List[RetrievedChunk]) -> str:
        """
        Deterministic grounded generator used when Groq API key is unconfigured, offline, or rate-limited.
        """
        if not chunks:
            return (
                "No verified factual details found in the official Groww source pages.\n\n"
                "Source: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth\n"
                "Last updated from sources: 2026-08-27"
            )

        top_chunk = chunks[0]
        lines = [line.strip() for line in top_chunk.text.split("\n") if line.strip() and not line.startswith("Source Citation Link")]
        fact_summary = " ".join(lines[:2])

        return (
            f"{fact_summary}\n\n"
            f"Source: {top_chunk.source_url}\n"
            f"Last updated from sources: 2026-08-27"
        )

    def generate(self, user_query: str) -> AssistantResponse:
        """
        Executes complete RAG pipeline for a user query.
        """
        # Step 1: PII Redaction & Security Check
        redaction_res = self.redactor.redact(user_query)
        sanitized_query = redaction_res.sanitized_text

        # Step 2: Intent Classification & Target Scheme Extraction
        intent_res = self.classifier.classify(sanitized_query, is_jailbreak=redaction_res.is_jailbreak)

        # Step 3: Handle Non-Factual / Refusal Queries
        if intent_res.intent != QueryIntent.FACTUAL:
            refusal_res: RefusalResponse = self.refusal_handler.handle(intent_res)
            return AssistantResponse(
                query=user_query,
                sanitized_query=sanitized_query,
                response_text=refusal_res.to_formatted_text(),
                intent=intent_res.intent,
                target_scheme_id=intent_res.target_scheme_id,
                retrieved_chunks=[],
                is_refusal=True,
                verification_info=None,
            )

        # Step 4: Hybrid Search Context Retrieval
        chunks = self.retriever.search(
            query=sanitized_query,
            top_k=3,
            target_scheme_id=intent_res.target_scheme_id
        )

        fallback_url = chunks[0].source_url if chunks else "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"

        # Step 5: LLM Generation with Groq Rate Limit Protection
        raw_llm_output = ""
        if self.groq_client and self.rate_limiter.acquire(estimated_tokens=600):
            try:
                system_prompt = self._build_system_prompt()
                user_prompt = self._build_user_prompt(sanitized_query, chunks)
                
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=settings.GROQ_MODEL_NAME,
                    temperature=0.1,  # Low temperature for deterministic grounding
                    max_tokens=250,
                )
                raw_llm_output = chat_completion.choices[0].message.content.strip()
                logger.info("Successfully generated response via Groq LLM API.")
            except Exception as e:
                logger.error(f"Groq API generation error: {e}. Switching to grounded fallback.")
                raw_llm_output = self._generate_fallback_response(chunks)
        else:
            logger.info("Groq API unconfigured or Rate Limit Guardrail intercepted. Generating grounded fallback response.")
            raw_llm_output = self._generate_fallback_response(chunks)

        # Step 6: Output Post-Processing Compliance Verification
        verification_res = self.verifier.verify_and_format(raw_llm_output, fallback_source_url=fallback_url)

        return AssistantResponse(
            query=user_query,
            sanitized_query=sanitized_query,
            response_text=verification_res.verified_text,
            intent=intent_res.intent,
            target_scheme_id=intent_res.target_scheme_id,
            retrieved_chunks=chunks,
            is_refusal=False,
            verification_info=verification_res,
        )


if __name__ == "__main__":
    generator = ResponseGenerator()

    sample_queries = [
        "What is the expense ratio of HDFC Large Cap Fund?",
        "Should I invest in HDFC Small Cap Fund?",
        "What is the minimum SIP amount for HDFC Gold ETF FoF?",
    ]

    for q in sample_queries:
        print("=" * 70)
        print(f"User Query: {q}")
        resp = generator.generate(q)
        print(f"Intent    : {resp.intent.value} | Refusal: {resp.is_refusal}")
        print("\nFinal Assistant Output:")
        print(resp.response_text)
