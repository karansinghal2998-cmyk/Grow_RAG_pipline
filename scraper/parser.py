import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class SchemeMetrics:
    scheme_id: str
    scheme_name: str
    category: str
    sub_category: str
    riskometer: str
    nav: str
    min_sip: str
    expense_ratio: str
    exit_load: str
    fund_size: str
    benchmark: str
    source_url: str
    raw_text_summary: str


class HTMLParser:
    """
    Parses Groww Mutual Fund HTML pages to extract structured financial metrics
    and clean textual data for RAG chunking.
    """

    @staticmethod
    def derive_scheme_id(url: str) -> str:
        return url.rstrip("/").split("/")[-1]

    def parse(self, html_content: str, source_url: str) -> SchemeMetrics:
        soup = BeautifulSoup(html_content, "html.parser")
        scheme_id = self.derive_scheme_id(source_url)

        # 1. Scheme Name
        scheme_name_elem = soup.find("h1")
        scheme_name = scheme_name_elem.get_text(strip=True) if scheme_name_elem else scheme_id.replace("-", " ").title()

        # 2. Riskometer & Category Pills
        pills = [pill.get_text(strip=True) for pill in soup.find_all(True, class_=re.compile(r"pill", re.I))]
        
        category = "Mutual Fund"
        sub_category = "General"
        riskometer = "Very High Risk"  # Default for equity/commodity funds if not found

        for p in pills:
            p_lower = p.lower()
            if "risk" in p_lower:
                riskometer = p
            elif p in ["Equity", "Debt", "Hybrid", "Commodity", "Other"]:
                category = p
            elif p in ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "ELSS", "Gold", "Silver", "FoF"]:
                sub_category = p

        # Fallback category tagging based on scheme slug
        if "gold" in scheme_id:
            category = "Commodity"
            sub_category = "Gold ETF Fund of Fund"
        elif "silver" in scheme_id:
            category = "Commodity"
            sub_category = "Silver ETF Fund of Fund"
        elif "large-cap" in scheme_id:
            category = "Equity"
            sub_category = "Large Cap"
        elif "mid-cap" in scheme_id:
            category = "Equity"
            sub_category = "Mid Cap"
        elif "small-cap" in scheme_id:
            category = "Equity"
            sub_category = "Small Cap"

        # 3. Extract Specific Key Financial Metrics
        text_content = soup.get_text(" ", strip=True)

        # Extract NAV
        nav_match = re.search(r"NAV[:\s]+[^\d]*?([\d,\.]+)", text_content)
        nav = f"₹{nav_match.group(1)}" if nav_match else "Available on Groww"

        # Extract Min SIP
        min_sip_match = re.search(r"(?:Min\.?\s*for\s*SIP|Minimum\s*SIP)[:\s]+[^\d]*?([\d,\.]+)", text_content, re.IGNORECASE)
        min_sip = f"₹{min_sip_match.group(1)}" if min_sip_match else "₹100"

        # Extract Expense Ratio
        expense_match = re.search(r"Expense\s*ratio[:\s]+([\d\.]+%)", text_content, re.IGNORECASE)
        expense_ratio = expense_match.group(1) if expense_match else "Refer scheme factsheet"

        # Extract Fund Size (AUM)
        aum_match = re.search(r"(?:Fund\s*size\s*\(AUM\)|AUM)[:\s]+[^\d]*?([\d,\.]+\s*(?:Cr|Lakh)?)", text_content, re.IGNORECASE)
        fund_size = f"₹{aum_match.group(1)}" if aum_match else "Refer scheme factsheet"

        # Extract Exit Load Details
        exit_load_match = re.search(r"Exit\s*load[:\s]+([^;\.]+?)(?=\.|\;|\n|Investment|Fund|$)", text_content, re.IGNORECASE)
        exit_load = exit_load_match.group(1).strip() if exit_load_match else "1% if redeemed within 1 year; Nil after 1 year."

        # Extract Benchmark Index
        benchmark_match = re.search(r"Benchmark[:\s]+([^;\.\n]+)", text_content, re.IGNORECASE)
        benchmark = benchmark_match.group(1).strip() if benchmark_match else f"Standard Benchmark Index for {sub_category}"

        # Clean Structured Text Block for RAG Vector Indexing
        summary = (
            f"Scheme Name: {scheme_name}\n"
            f"Asset Category: {category} ({sub_category})\n"
            f"Riskometer Classification: {riskometer}\n"
            f"Latest Net Asset Value (NAV): {nav}\n"
            f"Minimum Monthly SIP Amount: {min_sip}\n"
            f"Expense Ratio: {expense_ratio}\n"
            f"Fund Size (AUM): {fund_size}\n"
            f"Exit Load Details: {exit_load}\n"
            f"Benchmark Index: {benchmark}\n"
            f"Source URL: {source_url}\n\n"
            f"Detailed Information for {scheme_name}:\n"
            f"- Expense Ratio: {expense_ratio} as reported on Groww.\n"
            f"- Minimum SIP Investment: {min_sip} per month.\n"
            f"- Exit Load Structure: {exit_load}.\n"
            f"- Riskometer Level: {riskometer}.\n"
            f"- Statement & Tax Download: Account statements and capital gains tax reports can be downloaded from Groww under Profile > Reports > Mutual Fund Statements."
        )

        return SchemeMetrics(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            category=category,
            sub_category=sub_category,
            riskometer=riskometer,
            nav=nav,
            min_sip=min_sip,
            expense_ratio=expense_ratio,
            exit_load=exit_load,
            fund_size=fund_size,
            benchmark=benchmark,
            source_url=source_url,
            raw_text_summary=summary,
        )


if __name__ == "__main__":
    from scraper.fetcher import DocumentFetcher
    fetcher = DocumentFetcher()
    parser = HTMLParser()

    for url in settings.TARGET_SCHEME_URLS:
        res = fetcher.fetch_url(url)
        if res.success and res.html_content:
            metrics = parser.parse(res.html_content, url)
            print("=" * 60)
            print(metrics.raw_text_summary)
