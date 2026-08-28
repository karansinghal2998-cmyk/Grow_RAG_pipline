import time
import pytest
from pathlib import Path
from ingestion.scheduler import IngestionScheduler
from config import settings


@pytest.fixture
def scheduler():
    return IngestionScheduler(interval_seconds=1.0)


def test_scheduler_job_execution(scheduler):
    """
    Verifies that run_daily_ingestion_job executes successfully and logs to audit file.
    """
    res = scheduler.run_daily_ingestion_job()
    
    assert res["status"] == "SUCCESS"
    assert res["total_chunks"] == 25
    assert "elapsed_seconds" in res
    assert "timestamp" in res

    # Verify audit log creation
    log_file = settings.PROCESSED_DATA_DIR / "ingestion_cron.log"
    assert log_file.exists() is True
    
    log_content = log_file.read_text(encoding="utf-8")
    assert "Status: SUCCESS" in log_content
    assert "Chunks Indexed: 25" in log_content


def test_scheduler_daemon_start_stop(scheduler):
    """
    Verifies starting and stopping the background scheduler thread daemon.
    """
    scheduler.start(run_immediately=False)
    assert scheduler._is_running is True
    assert scheduler._timer is not None

    scheduler.stop()
    assert scheduler._is_running is False
    assert scheduler._timer is None
