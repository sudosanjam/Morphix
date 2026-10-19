"""Job Queue and Concurrency Management."""

import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from app.core.planner import plan_conversion, PlannedJob
from app.core.converter import execute_conversion, ConversionResult
from app.core.errors import JobCancelledError
from app.config import config


class JobState:
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_path: str
    target_format: str
    target_path: Optional[str] = None
    status: str = JobState.PENDING
    progress: int = 0
    progress_message: str = "Queued"
    engine: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = Field(default=None)
    created_at: float = Field(default_factory=time.time)
    duration_seconds: Optional[float] = None
    source_size_bytes: Optional[int] = None
    output_size_bytes: Optional[int] = None
    output_files: List[str] = Field(default_factory=list)


class JobManager:
    """Thread-safe background conversion job manager."""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or config.settings.max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="morphix-worker")
        self._jobs: Dict[str, JobItem] = {}
        self._cancel_flags: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self._on_job_completed_callbacks: List[Callable[[JobItem], None]] = []

    def register_completion_callback(self, cb: Callable[[JobItem], None]):
        self._on_job_completed_callbacks.append(cb)

    def submit_job(
        self,
        source_path: str | Path,
        target_format: str,
        output_destination: Optional[str | Path] = None,
        settings: Optional[Dict[str, Any]] = None,
        overwrite_policy: Optional[str] = None
    ) -> JobItem:
        """Create and queue a new conversion job."""
        job_id = str(uuid.uuid4())
        src_path = str(Path(source_path).resolve())

        job = JobItem(
            id=job_id,
            source_path=src_path,
            target_format=target_format,
            settings=settings or {},
            status=JobState.PENDING,
            progress=0,
            progress_message="Pending..."
        )

        with self._lock:
            self._jobs[job_id] = job
            self._cancel_flags[job_id] = False

        # Submit to thread pool
        self.executor.submit(
            self._run_job,
            job_id,
            src_path,
            target_format,
            output_destination,
            settings or {},
            overwrite_policy
        )

        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            job = self._jobs[job_id]
            if job.status in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED):
                return False

            self._cancel_flags[job_id] = True
            job.status = JobState.CANCELLED
            job.progress_message = "Cancelled by user"
            return True

    def get_job(self, job_id: str) -> Optional[JobItem]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[JobItem]:
        with self._lock:
            return list(self._jobs.values())

    def clear_finished(self):
        with self._lock:
            self._jobs = {
                k: v for k, v in self._jobs.items()
                if v.status in (JobState.PENDING, JobState.RUNNING, JobState.PREPARING)
            }

    def _run_job(
        self,
        job_id: str,
        source_path: str,
        target_format: str,
        output_destination: Optional[str | Path],
        settings: Dict[str, Any],
        overwrite_policy: Optional[str]
    ):
        job = self._jobs[job_id]

        def is_cancelled() -> bool:
            return self._cancel_flags.get(job_id, False)

        def update_progress(pct: int, msg: str):
            with self._lock:
                job.progress = pct
                job.progress_message = msg
                if pct < 10:
                    job.status = JobState.PREPARING
                elif pct >= 95:
                    job.status = JobState.VALIDATING
                else:
                    job.status = JobState.RUNNING

        try:
            if is_cancelled():
                raise JobCancelledError(job_id)

            update_progress(5, "Planning conversion...")
            planned = plan_conversion(
                source_path=source_path,
                target_format=target_format,
                output_destination=output_destination,
                raw_settings=settings,
                overwrite_policy=overwrite_policy
            )

            with self._lock:
                job.engine = planned.route.engine_name
                job.target_path = str(planned.target_path)
                job.warnings = planned.warnings

            result = execute_conversion(
                planned_job=planned,
                progress_callback=update_progress,
                is_cancelled_callback=is_cancelled
            )

            with self._lock:
                job.status = JobState.COMPLETED
                job.progress = 100
                job.progress_message = "Completed"
                job.duration_seconds = result.duration_seconds
                job.source_size_bytes = result.source_size_bytes
                job.output_size_bytes = result.output_size_bytes
                job.target_path = str(result.output_path)
                job.output_files = [str(f) for f in result.output_files]

        except JobCancelledError:
            with self._lock:
                job.status = JobState.CANCELLED
                job.progress_message = "Cancelled"
        except Exception as e:
            with self._lock:
                job.status = JobState.FAILED
                job.error_message = str(e)
                job.progress_message = f"Failed: {str(e)}"
        finally:
            for cb in self._on_job_completed_callbacks:
                try:
                    cb(job)
                except Exception:
                    pass


# Singleton job manager instance
jobs = JobManager()
