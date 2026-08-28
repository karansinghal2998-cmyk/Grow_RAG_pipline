import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from config import settings
from generation.generator import ResponseGenerator, AssistantResponse

# =====================================================================
# 1. Page Configuration & Custom Dark Theme CSS
# =====================================================================
st.set_page_config(
    page_title="Groww Mutual Fund FAQ Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism & Dark Slate CSS
st.markdown("""
<style>
    /* Dark Theme Core Variables */
    :root {
        --bg-color: #0B0F19;
        --card-bg: #151C2C;
        --card-border: #232E42;
        --accent-emerald: #00D09C;
        --accent-emerald-glow: rgba(0, 208, 156, 0.25);
        --text-primary: #F3F4F6;
        --text-secondary: #9CA3AF;
        --warning-amber: #F59E0B;
    }

    /* Main Container Dark Styling */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Sticky Disclaimer Top Header */
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(90deg, #091E19 0%, #0F2D26 100%);
        border-bottom: 1px solid rgba(0, 208, 156, 0.4);
        padding: 10px 20px;
        margin: -50px -50px 25px -50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .disclaimer-badge {
        background-color: rgba(0, 208, 156, 0.15);
        color: var(--accent-emerald);
        border: 1px solid var(--accent-emerald);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
    }

    /* Hero Banner */
    .hero-card {
        background: radial-gradient(circle at top left, #1E293B 0%, #0F172A 100%);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        color: var(--accent-emerald);
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 14px;
        margin-bottom: 18px;
    }

    /* Sample Question Button Cards */
    div.stButton > button {
        background-color: var(--card-bg);
        color: var(--text-primary);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 14px 16px;
        width: 100%;
        text-align: left;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        border-color: var(--accent-emerald);
        background-color: rgba(0, 208, 156, 0.08);
        box-shadow: 0 0 16px var(--accent-emerald-glow);
        transform: translateY(-2px);
    }

    /* Chat Message Bubble Styling */
    .user-bubble {
        background: linear-gradient(135deg, #0F382C 0%, #134E3A 100%);
        color: #FFFFFF;
        border: 1px solid rgba(0, 208, 156, 0.3);
        border-radius: 16px 16px 4px 16px;
        padding: 14px 18px;
        margin: 10px 0 10px auto;
        max-width: 80%;
        font-size: 15px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    .assistant-bubble {
        background-color: var(--card-bg);
        color: var(--text-primary);
        border: 1px solid var(--card-border);
        border-radius: 16px 16px 16px 4px;
        padding: 18px 22px;
        margin: 10px auto 10px 0;
        max-width: 88%;
        font-size: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .citation-btn {
        display: inline-block;
        background-color: rgba(0, 208, 156, 0.12);
        color: var(--accent-emerald) !important;
        border: 1px solid var(--accent-emerald);
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none !important;
        margin-top: 12px;
        margin-bottom: 8px;
        transition: all 0.2s;
    }
    .citation-btn:hover {
        background-color: var(--accent-emerald);
        color: #0B0F19 !important;
    }
    .timestamp-footer {
        color: var(--text-secondary);
        font-size: 12px;
        border-top: 1px dashed var(--card-border);
        padding-top: 8px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. Sticky Compliance Header
# =====================================================================
st.markdown("""
<div class="sticky-header">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 20px;">🛡️</span>
        <span style="font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px;">COMPLIANCE MANDATE:</span>
        <span style="color: var(--text-secondary); font-size: 14px;">Facts-Only FAQ Assistant. No Investment Advice.</span>
    </div>
    <div class="disclaimer-badge">
        ✓ Verified Groww Corpus
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# 3. Pipeline Generator Initialization (Cached)
# =====================================================================
@st.cache_resource
def get_response_generator() -> ResponseGenerator:
    return ResponseGenerator()

generator = get_response_generator()

# Initialize Session Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# =====================================================================
# 4. Sidebar Corpus & Guardrails Breakdown
# =====================================================================
with st.sidebar:
    st.image("https://groww.in/groww-logo-210.png", width=140)
    st.markdown("<h2 style='color:#00D09C; font-size:20px; margin-top:10px;'>Groww RAG Assistant</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9CA3AF; font-size:12px;'>Facts-only compliance engine for 5 HDFC Mutual Fund schemes.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📚 Target Corpus Scope")

    schemes_info = [
        ("HDFC Gold ETF FoF", "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"),
        ("HDFC Large Cap Fund", "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"),
        ("HDFC Small Cap Fund", "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"),
        ("HDFC Silver ETF FoF", "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth"),
        ("HDFC Mid-Cap Opportunities", "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"),
    ]

    for name, url in schemes_info:
        st.markdown(f"• [{name}]({url})")

    st.markdown("---")
    st.markdown("### 🔒 Active Guardrails")
    st.markdown("• **PII Redaction**: PAN, Aadhaar, OTPs, Accounts")
    st.markdown("• **Advisory Intercept**: Non-factual queries blocked")
    st.markdown(r"• **Rate Limiter**: $\le 30$ RPM / 12,000 TPM Cap")
    st.markdown("• **Hybrid Search**: BM25 + BGE Dense RRF ($K=3$)")
    st.markdown("• **LLM Engine**: Groq `llama-3.3-70b-versatile`")

# =====================================================================
# 5. Welcome Hero & Interactive Sample Questions
# =====================================================================
st.markdown("""
<div class="hero-card">
    <div class="hero-title">Welcome to Groww Mutual Fund FAQ Assistant</div>
    <div class="hero-subtitle">Ask factual questions about expense ratios, exit loads, minimum SIPs, NAVs, and account statement downloads.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h4 style='color:#F3F4F6; margin-bottom:12px;'>Sample Questions (Click to Ask):</h4>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

sample_query = None

with col1:
    if st.button("What is the expense ratio of HDFC Large Cap Fund?", key="sample_1"):
        sample_query = "What is the expense ratio of HDFC Large Cap Fund?"

with col2:
    if st.button("What is the exit load for HDFC Small Cap Fund?", key="sample_2"):
        sample_query = "What is the exit load for HDFC Small Cap Fund?"

with col3:
    if st.button("How to download capital gains statement on Groww?", key="sample_3"):
        sample_query = "How to download capital gains statement on Groww?"

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 6. Render Chat History Stream
# =====================================================================
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">💬 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        resp: AssistantResponse = msg["resp"]
        st.markdown(f'<div class="assistant-bubble">🤖 {resp.response_text}</div>', unsafe_allow_html=True)

# =====================================================================
# 7. Query Input Handling
# =====================================================================
user_input = st.chat_input("Ask a factual question about HDFC Mutual Funds...")

query_to_process = sample_query or user_input

if query_to_process:
    # Append User Message
    st.session_state["messages"].append({"role": "user", "content": query_to_process})
    st.markdown(f'<div class="user-bubble">💬 {query_to_process}</div>', unsafe_allow_html=True)

    # Process RAG Response via Orchestrator Pipeline
    with st.spinner("Retrieving verified facts & generating response..."):
        resp: AssistantResponse = generator.generate(query_to_process)

    # Append Assistant Message
    st.session_state["messages"].append({"role": "assistant", "resp": resp})
    st.markdown(f'<div class="assistant-bubble">🤖 {resp.response_text}</div>', unsafe_allow_html=True)
    st.rerun()
