from fastapi import APIRouter

from app.api.deps import SettingsDep, YtDlpDep
from app.schemas.video import VideoInfo, VideoInfoRequest
from app.utils.validators import ensure_allowed_url

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/info", response_model=VideoInfo)
def get_video_info(payload: VideoInfoRequest, settings: SettingsDep, ytdlp: YtDlpDep) -> VideoInfo:
    """Return title, thumbnail and the list of available qualities for a video."""
    ensure_allowed_url(payload.url, settings.allowed_hosts)
    return ytdlp.extract_info(payload.url)  # sync endpoint -> runs in FastAPI's threadpool
