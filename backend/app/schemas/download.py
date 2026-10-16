from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Profile(str, Enum):
    efficient = "efficient"  # best quality / smallest size: AV1 or VP9 + Opus -> MKV
    compatible = "compatible"  # H.264 + AAC -> MP4, plays everywhere
    audio = "audio"  # best audio -> MP3


class JobStatus(str, Enum):
    queued = "queued"
    downloading = "downloading"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class DownloadRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=8, max_length=2048)
    height: int | None = Field(default=None, ge=100, le=4320, description="None = best available")
    profile: Profile = Profile.efficient


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: JobStatus
    progress: float  # 0..1
    speed_bytes_per_sec: float | None = None
    eta_seconds: int | None = None
    title: str | None = None
    filename: str | None = None
    error: str | None = None
