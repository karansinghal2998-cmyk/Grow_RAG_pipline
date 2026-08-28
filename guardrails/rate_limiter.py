import sys
import time
import logging
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass, field

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitStatus:
    """
    Current health status of Groq API rate limits and token budget.
    """
    allowed: bool
    reason: str
    requests_last_minute: int
    requests_today: int
    tokens_last_minute: int
    tokens_today: int


class GroqRateLimiter:
    """
    Guardrail manager enforcing Groq API rate limits and token budgets for llama-3.3-70b-versatile:
    - 30 Requests Per Minute (RPM)
    - 1,000 Requests Per Day (RPD)
    - 12,000 Tokens Per Minute (TPM)
    - 100,000 Tokens Per Day (TPD)
    - Minimum 2.0s inter-request delay
    """

    def __init__(
        self,
        rpm_limit: int = settings.GROQ_RPM_LIMIT,
        rpd_limit: int = settings.GROQ_RPD_LIMIT,
        tpm_limit: int = settings.GROQ_TPM_LIMIT,
        tpd_limit: int = settings.GROQ_TPD_LIMIT,
        min_delay: float = settings.GROQ_MIN_REQUEST_DELAY,
    ):
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpm_limit = tpm_limit
        self.tpd_limit = tpd_limit
        self.min_delay = min_delay

        self.last_request_time: float = 0.0
        self.request_history: List[Tuple[float, int]] = []  # List of (timestamp, token_count)

    def _clean_history(self, now: float):
        """
        Purges historical entries older than 24 hours (86,400 seconds).
        """
        cutoff_day = now - 86400.0
        self.request_history = [entry for entry in self.request_history if entry[0] >= cutoff_day]

    def check_status(self, estimated_tokens: int = 600) -> RateLimitStatus:
        """
        Inspects sliding windows for RPM, RPD, TPM, and TPD quotas.
        """
        now = time.time()
        self._clean_history(now)

        cutoff_minute = now - 60.0

        requests_minute = sum(1 for ts, _ in self.request_history if ts >= cutoff_minute)
        requests_day = len(self.request_history)

        tokens_minute = sum(tk for ts, tk in self.request_history if ts >= cutoff_minute)
        tokens_day = sum(tk for ts, tk in self.request_history)

        if requests_minute >= self.rpm_limit:
            return RateLimitStatus(
                allowed=False,
                reason=f"RPM limit reached ({requests_minute}/{self.rpm_limit}).",
                requests_last_minute=requests_minute,
                requests_today=requests_day,
                tokens_last_minute=tokens_minute,
                tokens_today=tokens_day,
            )

        if requests_day >= self.rpd_limit:
            return RateLimitStatus(
                allowed=False,
                reason=f"Daily request quota reached ({requests_day}/{self.rpd_limit} RPD).",
                requests_last_minute=requests_minute,
                requests_today=requests_day,
                tokens_last_minute=tokens_minute,
                tokens_today=tokens_day,
            )

        if tokens_minute + estimated_tokens > self.tpm_limit:
            return RateLimitStatus(
                allowed=False,
                reason=f"TPM token budget limit reached ({tokens_minute}/{self.tpm_limit} TPM).",
                requests_last_minute=requests_minute,
                requests_today=requests_day,
                tokens_last_minute=tokens_minute,
                tokens_today=tokens_day,
            )

        if tokens_day + estimated_tokens > self.tpd_limit:
            return RateLimitStatus(
                allowed=False,
                reason=f"Daily token quota reached ({tokens_day}/{self.tpd_limit} TPD).",
                requests_last_minute=requests_minute,
                requests_today=requests_day,
                tokens_last_minute=tokens_minute,
                tokens_today=tokens_day,
            )

        return RateLimitStatus(
            allowed=True,
            reason="Within Groq API rate and token quotas.",
            requests_last_minute=requests_minute,
            requests_today=requests_day,
            tokens_last_minute=tokens_minute,
            tokens_today=tokens_day,
        )

    def acquire(self, estimated_tokens: int = 600) -> bool:
        """
        Enforces inter-request delay and records request token quota allocation.
        Returns True if request can proceed, or False if quota is exceeded.
        """
        now = time.time()
        status = self.check_status(estimated_tokens)

        if not status.allowed:
            logger.warning(f"Groq API Guardrail Intercept: {status.reason}")
            return False

        # Enforce minimum delay between calls to guarantee <= 30 RPM
        elapsed = now - self.last_request_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            logger.info(f"Rate Limiter: Pausing {sleep_time:.2f}s to maintain <= 30 RPM...")
            time.sleep(sleep_time)
            now = time.time()

        self.last_request_time = now
        self.request_history.append((now, estimated_tokens))
        return True


if __name__ == "__main__":
    limiter = GroqRateLimiter(rpm_limit=3, min_delay=0.1)
    for i in range(5):
        can_proceed = limiter.acquire(estimated_tokens=500)
        status = limiter.check_status()
        print(f"Request {i+1}: Allowed={can_proceed} | Reason={status.reason} | RPM={status.requests_last_minute}")
