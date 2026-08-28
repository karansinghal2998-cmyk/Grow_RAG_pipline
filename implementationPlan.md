# Phase-Wise Implementation Plan: Mutual Fund Facts-Only FAQ Assistant (RAG Pipeline)

Build a compliance-first, facts-only Retrieval-Augmented Generation (RAG) assistant for 5 HDFC Mutual Fund schemes indexed exclusively from Groww URLs, enforcing strict non-advisory guardrails, 3-sentence response limits, single citation links, and PII masking.

---

## 1. Project Overview & Tech Stack Confirmation

* **Target AMC**: HDFC Mutual Fund (HDFC AMC)
* **Exclusive Source Data**: 5 Groww Scheme URLs (No external PDFs or secondary AMC sites):
  1. `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth`
  2. `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth`
  3. `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth`
  4. `https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth`
  5. `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`
* **Core Machine Learning Models**:
  - **LLM Inference Engine**: **Groq API** (`groq` / `langchain-groq` with `llama-3.3-70b-versatile` or `mixtral-8x7b`)
  - **Embedding Model**: **BAAI BGE Model** (`BAAI/bge-small-en-v1.5` via HuggingFace `sentence-transformers` / `fastembed`)

---

## 2. Phase-Wise Implementation Breakdown

### Phase 1: Environment Setup & Project Foundation
* **Goal**: Establish project directory structure, environment variables, configuration files, and dependency manifests.
* **Deliverables**:
  - Python virtual environment setup (`python 3.10+`)
  - Modular project structure: `config/`, `scraper/`, `ingestion/`, `guardrails/`, `retrieval/`, `generation/`, `ui/`, `tests/`
  - `config.py` holding scheme URLs, Groq API key configuration, BGE embedding parameters, and strict output constraints
  - `requirements.txt` containing dependencies (`groq`, `langchain-groq`, `sentence-transformers`, `fastapi`, `streamlit`, `beautifulsoup4`, `chromadb`, `rank-bm25`, `spacy`, `pytest`)

---

### Phase 2: Web Scraping & Ingestion Pipeline (5 Groww URLs + BGE Embeddings)
* **Goal**: Ingest HTML content from the 5 target Groww URLs, parse key financial metrics, chunk text using a domain-specific key-value semantic chunking strategy, and store BGE embeddings in ChromaDB with structured metadata.
* **Deliverables**:
  - `scraper/scraper.py` & `scraper/parser.py`: HTML scraper and parser using `BeautifulSoup4` / `httpx` to parse Groww scheme detail pages and extract structured `SchemeMetrics`.
  - Key financial metrics extractor: Expense Ratio, Exit Load, Minimum SIP, Riskometer, Benchmark Index, NAV, Fund Size (AUM), Fund Category/Sub-Category.
  - `ingestion/chunker.py`: **Domain-Specific Key-Value & Fact-Centric Chunker** replacing naive fixed-token character splitting (256–512 tokens) with 5 atomic, self-contained semantic chunk types per scheme:
    1. **`overview`**: Comprehensive Overview Fact Sheet chunk combining all core metrics (Name, Category, Riskometer, Expense Ratio, Min SIP, Fund Size, Exit Load, Source Citation URL).
    2. **`expense_ratio`**: Dedicated chunk isolating Expense Ratio percentage, fee definition, and exact Groww source URL citation.
    3. **`exit_load`**: Dedicated chunk isolating Exit Load fee structure, redemption tenure rules, and source URL citation.
    4. **`sip_and_nav`**: Dedicated chunk focusing on Minimum Monthly SIP (`₹100`), NAV info, Riskometer classification, Benchmark Index, and source URL citation.
    5. **`statement_download`**: Procedural chunk covering step-by-step account statement and capital gains report download steps on Groww (`Profile > Reports > Mutual Fund Statements`).
  - **Self-Contained Citation & Metadata Injection**: Every chunk embeds explicit inline citation links (`Source Citation Link: <url>`) and rich metadata (`scheme_id`, `scheme_name`, `category`, `sub_category`, `source_url`, `last_updated`, `doc_type`, `chunk_type`) to eliminate context fragmentation and guarantee zero-hallucination citation grounding.
  - `ingestion/vector_store.py`: **Chunk-Aware BGE Embedding Strategy & Persistent Vector Store**:
    - **Dense Embedding Model**: **BAAI BGE Small** (`BAAI/bge-small-en-v1.5`, 384-dimensional dense vectors) via `sentence-transformers` / `fastembed`.
    - **Vector Space & Metric**: Cosine Similarity metric (`"hnsw:space": "cosine"` in persistent ChromaDB collection `hdfc_mutual_funds`).
    - **Normalized Vector Encoding (`normalize_embeddings=True`)**: Enforces L2 unit vector norm on all embedded chunk text blocks to optimize cosine nearest-neighbor search.
    - **Fact-Dense Payload Vector Encoding**: Instead of embedding raw unstructured HTML, BGE embeddings are computed directly over the 5 atomic, self-contained chunk text payloads (`overview`, `expense_ratio`, `exit_load`, `sip_and_nav`, `statement_download`), tightly clustering vectors around financial key-values and scheme entity names.
    - **Metadata-Filtered Cosine Retrieval**: Embeddings are indexed with rich metadata (`scheme_id`, `chunk_type`, `category`, `sub_category`, `source_url`, `last_updated`). Enables query-time filtering (`where={"scheme_id": target_scheme_id}`), guaranteeing zero cross-scheme vector score contamination.

---

### Phase 3: Input Security & Advisory Guardrails
* **Goal**: Sanitize incoming user queries for sensitive PII, intercept advisory/speculative financial requests, and enforce Groq API rate & token budget guardrails.
* **Deliverables**:
  - `guardrails/pii_redactor.py`: Regex & NER masker for PAN (`[A-Z]{5}[0-9]{4}[A-Z]{1}`), Aadhaar, Account Numbers, OTPs, Phone/Email.
  - `guardrails/intent_classifier.py`: Zero-shot/rule-based query classifier (`FACTUAL` vs `ADVISORY`).
  - `guardrails/refusal_handler.py`: Refusal response module delivering polite non-advisory statements + AMFI educational reference link.
  - `guardrails/rate_limiter.py`: **Groq API Rate & Token Budget Guardrail (`llama-3.3-70b-versatile`)**:
    1. **RPM & RPD Request Quotas**: Enforces minimum `2.0s` delay between API calls to guarantee staying strictly under **30 RPM** (Requests Per Minute) and **1,000 RPD** (Requests Per Day).
    2. **TPM & TPD Token Budgets**: Restricts input context to Top K=3 chunks (~350 tokens) and caps `max_tokens=250`, keeping average query token consumption at ~600 tokens—well below **12,000 TPM** (Tokens Per Minute) and **100,000 TPD** (Tokens Per Day) limits.
    3. **Quota Interception & Fallback**: Intercepts queries when quotas are exhausted and transitions seamlessly to the deterministic grounded response generator.

---

### Phase 4: Hybrid Search Retrieval Engine
* **Goal**: Retrieve the most accurate context chunks for factual financial queries using sparse BM25 and BGE dense vector search fused via Reciprocal Rank Fusion (RRF).
* **Chunk & Embedding-Informed Retrieval Strategy**:
  - **Embedding Cluster Alignment**: Our 384-dimensional BGE vector verification demonstrated high intra-type similarity (~0.93–0.96) across the 5 atomic chunk types (`overview`, `expense_ratio`, `exit_load`, `sip_and_nav`, `statement_download`). Specific metric queries map directly to topic-focused chunks, while broad scheme queries hit the aggregate `overview` chunk.
  - **Stage 1 (Sparse BM25 Keyword Search)**: Fits `BM25Okapi` over tokenized chunk texts with financial query synonym expansion (`lock-in` $\leftrightarrow$ `redemption tenure`, `fee` $\leftrightarrow$ `expense ratio`, `charge` $\leftrightarrow$ `exit load`, `sip` $\leftrightarrow$ `minimum monthly sip`).
  - **Stage 2 (Dense BGE Vector Search)**: Cosine similarity vector search on ChromaDB using 384-dimensional normalized BGE embeddings (`normalize_embeddings=True`).
  - **Stage 3 (Metadata Scheme Filtering)**: Strict `where={"scheme_id": target_scheme_id}` filtering derived from `IntentClassifier` to guarantee zero cross-scheme context contamination.
  - **Stage 4 (Reciprocal Rank Fusion - RRF)**: Merges sparse BM25 ranks and dense vector ranks via $RRF(d) = \frac{1}{60 + R_{dense}(d)} + \frac{1}{60 + R_{sparse}(d)}$ to return the Top K=3 context chunks.
  - **Stage 5 (Distance Threshold Cutoff)**: Cosine distance threshold cutoff ($>0.65$) to detect low-relevance queries and prevent LLM hallucinations.
* **Deliverables**:
  - `retrieval/hybrid_retriever.py`: Hybrid Search Engine implementing BM25, BGE dense search, metadata scheme filtering, and RRF rank fusion.
  - `tests/test_retrieval.py`: Test suite verifying BM25 keyword matching, synonym expansion, dense vector retrieval, scheme-filtered hybrid search, and RRF score ranking.

---

### Phase 5: LLM Generation (Groq API) & Output Compliance Post-Processor
* **Goal**: Generate factual, grounded responses via **Groq LLM** (`llama-3.3-70b-versatile`) and rigorously enforce formatting constraints.
* **Deliverables**:
  - `generation/generator.py`: **End-to-End RAG Response Generator**:
    1. **Groq LLM Client**: System prompt builder with zero-advisory grounding instructions for Groq API (`llama-3.3-70b-versatile`).
    2. **Grounded Fallback Engine**: Deterministic summary generator built from top retrieved chunks when API key is unconfigured or offline.
    3. **Full RAG Pipeline Orchestration**: PII Redaction -> Intent Classification -> Hybrid Retrieval -> LLM Generation -> Compliance Post-Processing.
  - `generation/compliance_verifier.py`: **Output Compliance Post-Processor**:
    1. **Sentence Limit Enforcement**: Truncates LLM responses strictly to $\le 3$ sentences while preserving decimal numbers (`0.20%`, `₹40,197.89 Cr`).
    2. **Single Citation URL Guarantee**: Extracts and deduplicates Groww scheme URLs to guarantee **exactly 1 citation link**.
    3. **Timestamped Footer**: Enforces mandatory `"Last updated from sources: 2026-08-27"` footer on all outputs.
  - `tests/test_generation.py`: Test suite verifying sentence truncation, URL injection, date footer enforcement, advisory query interception, and end-to-end RAG pipeline responses.

---

### Phase 5.5: Automated Data Ingestion Scheduler Engine & GitHub Actions Workflow
* **Goal**: Automate daily web scraping, metric extraction, semantic chunking, and ChromaDB vector store re-indexing via a serverless **GitHub Actions Workflow** and python background daemon so that the RAG pipeline corpus stays 100% up-to-date with live Groww source data every 24 hours.
* **Deliverables**:
  - `.github/workflows/daily_ingestion.yml`: **Serverless GitHub Actions Daily Ingestion Workflow**:
    1. **Automated Cron Schedule**: Configured with `schedule: - cron: '0 5 * * *'` (runs every day at **10:30 AM IST** / 05:00 UTC) and `workflow_dispatch` for manual triggers.
    2. **Automated Environment Setup**: Provisions Python 3.10+, installs dependencies from `requirements.txt`, and caches HuggingFace BGE model artifacts.
    3. **Ingestion & Verification Execution**: Runs `python export_extracted_data.py` and `python verify_embeddings.py` to re-fetch the 5 Groww URLs and update ChromaDB vector embeddings.
    4. **Automated Dataset Commit & Push**: Commits updated `extracted_metrics.json`, `indexed_chunks.json`, `corpus_review.md`, and `ingestion_cron.log` back to the GitHub repository automatically when changes occur.
  - `ingestion/scheduler.py`: Python Ingestion Scheduler Daemon providing `--once` CLI execution for CI/CD runners and local background thread scheduling.
  - `tests/test_scheduler.py`: Test suite verifying automated scheduler job execution, audit logging, and thread daemon control.

---

### Phase 6: Minimal User Interface (UI) Development
* **Goal**: Deliver a clean, minimal user interface adhering to compliance requirements.
* **Deliverables**:
  - `ui/app.py`: Streamlit / Web UI featuring:
    - Sticky Disclaimer Header: `"Facts-only. No investment advice."`
    - Welcome Banner & 3 Interactive Sample Questions
    - Chat History Window rendering source URL citations and footer timestamps

---

### Phase 7: Verification & Testing
* **Goal**: Rigorously test compliance, retrieval accuracy, and guardrail interception.
* **Deliverables**:
  - `tests/test_guardrails.py`: Unit tests for PII redaction and advisory refusal handling
  - `tests/test_rag_pipeline.py`: Automated tests verifying 3-sentence limits, single citation links, and answer accuracy across 30+ factual test queries

---

## 3. Timeline & Execution Roadmap Matrix

| Phase | Description | Key Modules Created / Touched | Output Artifacts |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Project Setup & Config | `config/config.py`, `requirements.txt` | Virtual environment & dependencies |
| **Phase 2** | Ingestion & Vector DB | `scraper/scraper.py`, `ingestion/vector_store.py` | ChromaDB vector index of 5 Groww URLs |
| **Phase 3** | PII & Advisory Guardrails | `guardrails/pii_redactor.py`, `guardrails/intent_classifier.py` | Sanitized & safe query pipeline |
| **Phase 4** | Hybrid Retrieval Engine | `retrieval/hybrid_retriever.py` | BM25 + Vector Dense RRF retriever |
| **Phase 5** | LLM Generation & Formatter | `generation/generator.py`, `generation/compliance_verifier.py` | Verified 3-sentence + citation output |
| **Phase 5.5**| GitHub Actions Daily Scheduler | `.github/workflows/daily_ingestion.yml`, `ingestion/scheduler.py` | Automated 24h GitHub Actions Cron & Audit Log |
| **Phase 6** | Minimal User Interface | `ui/app.py` | Streamlit chat UI with disclaimer banner |
| **Phase 7** | Testing & Verification | `tests/test_guardrails.py`, `tests/test_rag_pipeline.py` | Automated test suite & audit results |
