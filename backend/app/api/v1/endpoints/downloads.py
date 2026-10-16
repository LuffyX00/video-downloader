import mimetypes
from typing import Annotated

from fastapi import APIRouter, Path, Response
from fastapi.responses import FileResponse

from app.api.deps import JobsDep, SettingsDep
from app.schemas.download import DownloadRequest, JobResponse
from app.utils.validators import ensure_allowed_url

router = APIRouter(prefix="/downloads", tags=["downloads"])

JobId = Annotated[str, Path(pattern=r"^[a-f0-9]{32}$")]


@router.post("", response_model=JobResponse, status_code=202)
def create_download(payload: DownloadRequest, settings: SettingsDep, jobs: JobsDep) -> JobResponse:
    ensure_allowed_url(payload.url, settings.allowed_hosts)
    job = jobs.submit(payload.url, payload.height, payload.profile)
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
def get_download(job_id: JobId, jobs: JobsDep) -> JobResponse:
    return JobResponse.model_validate(jobs.get(job_id))


@router.get("/{job_id}/file")
def get_download_file(job_id: JobId, jobs: JobsDep) -> FileResponse:
    path, filename = jobs.get_file(job_id)
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.delete("/{job_id}", status_code=204)
def delete_download(job_id: JobId, jobs: JobsDep) -> Response:
    jobs.delete(job_id)
    return Response(status_code=204)
