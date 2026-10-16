import asyncio
import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.exceptions import AppError
from app.services.job_manager import JobManager
from app.services.ytdlp_service import YtDlpService

import os
from pathlib import Path


logger = logging.getLogger(__name__)

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
if BIN_DIR.is_dir():
    os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"

async def _cleanup_loop(manager: JobManager, interval: int) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(manager.cleanup_expired)
        except Exception:  # noqa: BLE001
            logger.exception("Cleanup task failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    if not shutil.which("ffmpeg"):
        logger.warning(
            "ffmpeg was not found on PATH. High-quality downloads need it to merge "
            "video and audio streams - install it before downloading."
        )

    service = YtDlpService(settings)
    manager = JobManager(settings, service)
    manager.purge_all()

    app.state.settings = settings
    app.state.ytdlp = service
    app.state.jobs = manager

    cleanup = asyncio.create_task(_cleanup_loop(manager, settings.cleanup_interval_seconds))
    try:
        yield
    finally:
        cleanup.cancel()
        manager.shutdown()


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
