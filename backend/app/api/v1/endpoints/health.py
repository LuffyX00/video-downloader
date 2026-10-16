import shutil

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "ffmpeg": shutil.which("ffmpeg") is not None}
