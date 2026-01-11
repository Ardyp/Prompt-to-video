"""
Health check router.
"""

from datetime import datetime

from fastapi import APIRouter

from app.config import get_settings
from app.models import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        providers={
            "video": settings.video_provider.value,
            "voice": settings.voice_provider.value,
            "language": settings.language_provider.value,
        },
        timestamp=datetime.utcnow()
    )
