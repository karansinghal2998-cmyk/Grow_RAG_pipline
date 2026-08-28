import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Core Application Settings
    APP_NAME: str = "Mutual Fund Facts-Only FAQ Assistant"
    DEBUG: bool = True
    
    # Storage Paths
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw_html"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    VECTOR_DB_DIR: Path = BASE_DIR / "data" / "vector_db"
    
    # Target Scheme URLs (Groww Exclusive Corpus)
    TARGET_SCHEME_URLS: list[str] = [
        "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    ]
    
    # HTTP Fetcher Settings
    USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    REQUEST_TIMEOUT: float = 15.0
    MAX_RETRIES: int = 3
    RATE_LIMIT_DELAY: float = 1.5  # Seconds between requests
    
    # Models & Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
    BGE_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

    # Groq API Rate & Token Limit Guardrails (llama-3.3-70b-versatile)
    GROQ_RPM_LIMIT: int = 30             # Requests Per Minute
    GROQ_RPD_LIMIT: int = 1000           # Requests Per Day
    GROQ_TPM_LIMIT: int = 12000          # Tokens Per Minute
    GROQ_TPD_LIMIT: int = 100000         # Tokens Per Day
    GROQ_MIN_REQUEST_DELAY: float = 2.0  # Minimum 2.0s delay to guarantee <= 30 RPM

settings = Settings()

# Ensure required directories exist
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
