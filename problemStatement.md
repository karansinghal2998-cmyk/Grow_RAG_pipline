# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer **objective, verifiable queries** related to mutual funds by retrieving information exclusively from **official public sources**, such as Asset Management Company (AMC) websites, AMFI (Association of Mutual Funds in India), and SEBI (Securities and Exchange Board of India).

The system must strictly **avoid providing investment advice, opinions, or recommendations**. Every response must include a **single, clear source link** and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)-based assistant** that:
* Answers **factual queries** about mutual fund schemes.
* Uses a **curated corpus of official documents**.
* Provides **concise, source-backed responses**.

---

## Target Users

* **Retail investors** comparing mutual fund schemes.
* **Customer support and content teams** handling repetitive mutual fund queries.

---

## Scope of Work

### 1. Corpus Definition
* **Selected AMC**: **HDFC Mutual Fund (HDFC AMC)**
* **Defined Target Scheme Corpus (5 Provided Schemes)**:
  1. **HDFC Gold ETF Fund of Fund Direct Plan Growth**
     - Category: Commodity / Fund of Funds (FoF)
     - Source URL: `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth`
  2. **HDFC Large Cap Fund Direct Growth**
     - Category: Equity (Large Cap)
     - Source URL: `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth`
  3. **HDFC Small Cap Fund Direct Growth**
     - Category: Equity (Small Cap)
     - Source URL: `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth`
  4. **HDFC Silver ETF FoF Direct Growth**
     - Category: Commodity / Fund of Funds (FoF - Silver)
     - Source URL: `https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth`
  5. **HDFC Mid Cap Fund Direct Growth**
     - Category: Equity (Mid Cap)
     - Source URL: `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`
* **Corpus Sources & Exclusive Data Scope**:
  The RAG pipeline ingests and indexes data exclusively from the 5 provided Groww scheme URLs above. No external PDF files, secondary AMC sites, or third-party aggregator sources are used.

### 2. FAQ Assistant Requirements
The assistant must:
* Answer **facts-only queries**, such as:
  * Expense ratio of a scheme
  * Exit load details
  * Minimum SIP amount
  * ELSS lock-in period
  * Riskometer classification
  * Benchmark index
  * Process to download statements or capital gains reports
* Ensure response criteria:
  * Each response is **limited to a maximum of 3 sentences**.
  * Each response includes **exactly one citation link**.
  * Each response includes the footer:  
    `"Last updated from sources: <date>"`

### 3. Refusal Handling
The assistant must **refuse non-factual or advisory queries**, such as:
* *"Should I invest in this fund?"*
* *"Which fund is better?"*

Refusal responses should:
* Be **polite and clearly worded**.
* Reinforce the **facts-only limitation**.
* Provide a **relevant educational link** (e.g., AMFI or SEBI resource).

### 4. User Interface (Minimal)
The solution should include a simple interface featuring:
* A **welcome message**.
* **Three example questions**.
* A visible disclaimer:  
  `"Facts-only. No investment advice."`

---

## Constraints

> [!IMPORTANT]
> Strict compliance rules apply to source data, content output, and user data security.

### Data and Sources
* Use **only official public sources** (AMC, AMFI, SEBI).
* **Do not** use third-party blogs or aggregator websites.

### Privacy and Security
* **Do not** collect, store, or process sensitive PII or authentication data:
  * PAN or Aadhaar numbers
  * Account numbers
  * OTPs
  * Email addresses or phone numbers

### Content Restrictions
* **No investment advice or recommendations**.
* **No performance comparisons or return calculations**.
* For performance-related queries, provide a **link to the official factsheet only**.

### Transparency
* Responses must be **short, factual, and verifiable**.
* Every answer must include a **source link and last updated date**.

---

## Expected Deliverables

### 1. README Document
* Setup instructions
* Selected AMC and schemes
* Architecture overview (RAG approach)
* Known limitations

### 2. Disclaimer Snippet
* `"Facts-only. No investment advice."`

---

## Success Criteria

* **Accurate Retrieval**: Precise extraction of factual mutual fund information.
* **Facts-Only Adherence**: Zero advisory, speculative, or opinionated output.
* **Valid Citations**: Consistent inclusion of exact source links.
* **Effective Refusals**: Polite handling and redirect for advisory queries.
* **Clean UI**: Simple, minimal, and user-friendly interface.

---

## Summary

The goal is to build a **trustworthy, transparent, and compliant mutual fund FAQ assistant** that prioritizes **accuracy over intelligence**. The system should ensure that users receive only **verified, source-backed financial information**, without any advisory bias or speculative content.
