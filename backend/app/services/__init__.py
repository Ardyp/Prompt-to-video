"""Service modules for AI providers."""

from app.services.language_service import get_language_detector
from app.services.media_processor import get_media_processor
from app.services.video_service import get_video_service
from app.services.voice_service import get_voice_service

__all__ = [
    "get_language_detector",
    "get_voice_service",
    "get_video_service",
    "get_media_processor",
]
