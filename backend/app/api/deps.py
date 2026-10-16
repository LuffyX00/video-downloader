from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.services.job_manager import JobManager
from app.services.ytdlp_service import YtDlpService


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_ytdlp(request: Request) -> YtDlpService:
    return request.app.state.ytdlp


def get_jobs(request: Request) -> JobManager:
    return request.app.state.jobs


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
YtDlpDep = Annotated[YtDlpService, Depends(get_ytdlp)]
JobsDep = Annotated[JobManager, Depends(get_jobs)]
