import sys
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from ingestion.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class IngestionScheduler:
    """
    Automated Daily Ingestion Scheduler Engine (Phase 5.5).
    Triggers web scraping, parsing, semantic chunking, and ChromaDB vector store
    re-indexing every 24 hours (or customizable interval) to ensure corpus freshness.
    """

    def __init__(self, interval_seconds: float = 86400.0):  # 86400s = 24 Hours
        self.interval_seconds = interval_seconds
        self.log_file = settings.PROCESSED_DATA_DIR / "ingestion_cron.log"
        self._timer: Optional[threading.Timer] = None
        self._is_running: bool = False
        self.last_run_timestamp: Optional[datetime] = None

    def _log_audit_entry(self, message: str, total_chunks: int, status: str = "SUCCESS"):
        """
        Appends timestamped audit log to data/processed/ingestion_cron.log.
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp_str}] Status: {status} | Chunks Indexed: {total_chunks} | Info: {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
        
        logger.info(f"Cron Audit Logged: {log_line.strip()}")

    def run_daily_ingestion_job(self) -> Dict[str, Any]:
        """
        Executes the full data ingestion and vector store re-indexing pipeline.
        """
        start_time = time.time()
        logger.info("=" * 70)
        logger.info("STARTING AUTOMATED DAILY DATA INGESTION CRON JOB")
        logger.info("=" * 70)

        try:
            vdb = VectorStoreManager()
            total_chunks = vdb.ingest_all_target_schemes()
            
            elapsed = time.time() - start_time
            self.last_run_timestamp = datetime.now()
            
            success_msg = f"Re-indexed {total_chunks} chunks across 5 Groww URLs in {elapsed:.2f}s."
            self._log_audit_entry(success_msg, total_chunks, status="SUCCESS")

            return {
                "status": "SUCCESS",
                "total_chunks": total_chunks,
                "elapsed_seconds": round(elapsed, 2),
                "timestamp": self.last_run_timestamp.isoformat(),
            }
        except Exception as e:
            error_msg = f"Daily ingestion failed: {e}"
            logger.error(error_msg, exc_info=True)
            self._log_audit_entry(error_msg, total_chunks=0, status="ERROR")
            return {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _schedule_next_run(self):
        """
        Schedules the next execution via background timer thread.
        """
        if self._is_running:
            self._timer = threading.Timer(self.interval_seconds, self._worker_loop)
            self._timer.daemon = True
            self._timer.start()
            logger.info(f"Next automated ingestion scheduled in {self.interval_seconds / 3600:.1f} hours.")

    def _worker_loop(self):
        """
        Internal worker executed on each interval trigger.
        """
        self.run_daily_ingestion_job()
        self._schedule_next_run()

    def start(self, run_immediately: bool = False):
        """
        Starts the background scheduler daemon.
        """
        if self._is_running:
            logger.warning("Ingestion Scheduler is already running.")
            return

        self._is_running = True
        logger.info("Ingestion Scheduler Daemon Started.")

        if run_immediately:
            self.run_daily_ingestion_job()

        self._schedule_next_run()

    def stop(self):
        """
        Stops the background scheduler daemon.
        """
        self._is_running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        logger.info("Ingestion Scheduler Daemon Stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automated Ingestion Scheduler Daemon")
    parser.add_argument("--once", action="store_true", help="Run ingestion job once and exit (for CI/CD / GitHub Actions)")
    args = parser.parse_args()

    scheduler = IngestionScheduler(interval_seconds=86400.0)
    if args.once:
        print("Executing single ingestion run for GitHub Actions / CI pipeline...")
        result = scheduler.run_daily_ingestion_job()
        print("Scheduler Job Result:", result)
    else:
        print("Testing Daily Ingestion Scheduler Job Execution...")
        result = scheduler.run_daily_ingestion_job()
        print("Scheduler Job Result:", result)
