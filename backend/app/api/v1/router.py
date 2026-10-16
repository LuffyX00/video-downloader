from fastapi import APIRouter

from app.api.v1.endpoints import downloads, health, videos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(videos.router)
api_router.include_router(downloads.router)
