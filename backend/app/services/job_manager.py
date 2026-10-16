"""In-process download job manager.

Jobs run on a bounded thread pool so heavy downloads never block the API.
The store is in-memory behind a small interface: to scale horizontally, swap it
(and the executor) for Redis + a worker queue such as arq/Celery without
touching the API layer.
"""
from __future__ import annotations

import logging
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path

from app.core.config import Settings
from app.exceptions import (
    AppError,
    JobNotFoundError,
    JobNotReadyError,
    QueueFullError,
)
from app.schemas.download import JobStatus, Profile
from app.services.ytdlp_service import YtDlpService

logger = logging.getLogger(__name__)

_ACTIVE = {JobStatus.queued, JobStatus.downloading, JobStatus.processing}


@dataclass
class Job:
    id: str
    url: str
    height: int | None
    profile: Profile
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    speed_bytes_per_sec: float | None = None
    eta_seconds: int | None = None
    title: str | None = None
    filename: str | None = None
    filepath: Path | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None


class JobManager:
    def __init__(self, settings: Settings, service: YtDlpService):
        self._settings = settings
        self._service = service
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=settings.max_concurrent_downloads, thread_name_prefix="download"
        )
        settings.download_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------- public API
    def submit(self, url: str, height: int | None, profile: Profile) -> Job:
        with self._lock:
            active = sum(1 for j in self._jobs.values() if j.status in _ACTIVE)
            if active >= self._settings.max_active_jobs:
                raise QueueFullError()
            job = Job(id=uuid.uuid4().hex, url=url, height=height, profile=profile)
            self._jobs[job.id] = job
            snapshot = replace(job)
        self._executor.submit(self._run, job.id)
        return snapshot

    def get(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError()
            return replace(job)

    def get_file(self, job_id: str) -> tuple[Path, str]:
        job = self.get(job_id)
        if job.status is not JobStatus.completed or not job.filepath or not job.filepath.exists():
            raise JobNotReadyError()
        return job.filepath, job.filename or job.filepath.name

    def delete(self, job_id: str) -> None:
        job = self.get(job_id)
        if job.status in _ACTIVE:
            raise JobNotReadyError("This download is still running.")
        self._discard(job_id)

    def cleanup_expired(self) -> int:
        cutoff = time.time() - self._settings.file_ttl_seconds
        with self._lock:
            expired = [
                jid
                for jid, j in self._jobs.items()
                if j.finished_at is not None and j.finished_at < cutoff
            ]
        for jid in expired:
            self._discard(jid)
        if expired:
            logger.info("Cleaned up %d expired download(s)", len(expired))
        return len(expired)

    def purge_all(self) -> None:
        """Remove leftovers from a previous run."""
        for child in self._settings.download_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    # ---------------------------------------------------------- internals
    def _update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in fields.items():
                    setattr(job, key, value)

    def _discard(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)
        shutil.rmtree(self._settings.download_dir / job_id, ignore_errors=True)

    def _run(self, job_id: str) -> None:
        job = self.get(job_id)
        self._update(job_id, status=JobStatus.downloading)
        try:
            path = self._service.download(
                url=job.url,
                job_dir=self._settings.download_dir / job_id,
                height=job.height,
                profile=job.profile,
                on_progress=lambda p, speed, eta: self._update(
                    job_id,
                    status=JobStatus.downloading,
                    progress=p,
                    speed_bytes_per_sec=speed,
                    eta_seconds=eta,
                ),
                on_processing=lambda: self._update(
                    job_id, status=JobStatus.processing, speed_bytes_per_sec=None, eta_seconds=None
                ),
                on_title=lambda title: self._update(job_id, title=title),
            )
            self._update(
                job_id,
                status=JobStatus.completed,
                progress=1.0,
                filepath=path,
                filename=path.name,
                speed_bytes_per_sec=None,
                eta_seconds=None,
                finished_at=time.time(),
            )
        except AppError as exc:
            self._fail(job_id, exc.message)
        except Exception:  # noqa: BLE001 - never let a worker thread die silently
            logger.exception("Unexpected error in download job %s", job_id)
            self._fail(job_id, "Unexpected server error. Please try again.")

    def _fail(self, job_id: str, message: str) -> None:
        self._update(job_id, status=JobStatus.failed, error=message, finished_at=time.time())
        shutil.rmtree(self._settings.download_dir / job_id, ignore_errors=True)
