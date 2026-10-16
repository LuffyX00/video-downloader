from pydantic import BaseModel, ConfigDict, Field


class VideoInfoRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=8, max_length=2048)


class QualityOption(BaseModel):
    height: int
    label: str
    fps: int | None = None
    codec: str | None = None  # codec of the best-quality stream at this height
    estimated_size_bytes: int | None = None  # best-quality profile (video + audio)
    compatible_size_bytes: int | None = None  # H.264 / MP4 profile (video + audio)


class VideoInfo(BaseModel):
    id: str
    title: str
    uploader: str | None = None
    duration: int | None = None
    thumbnail: str | None = None
    webpage_url: str
    audio_size_bytes: int | None = None
    qualities: list[QualityOption]
