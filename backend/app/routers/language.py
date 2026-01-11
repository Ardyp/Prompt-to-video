"""
Language detection API router.
"""

from fastapi import APIRouter, HTTPException

from app.models import LanguageDetectionRequest, LanguageDetectionResponse
from app.services.language_service import get_language_detector

router = APIRouter()


@router.post("/detect", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect the language of the provided text.
    
    Supports 75+ languages with high accuracy, even for short text.
    
    Returns the most likely language along with alternatives and confidence scores.
    """
    try:
        detector = get_language_detector()
        result = await detector.detect(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported")
async def get_supported_languages():
    """
    Get list of supported languages for detection.
    """
    # Common languages supported by most providers
    languages = [
        {"code": "en", "name": "English"},
        {"code": "es", "name": "Spanish"},
        {"code": "fr", "name": "French"},
        {"code": "de", "name": "German"},
        {"code": "it", "name": "Italian"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "nl", "name": "Dutch"},
        {"code": "ru", "name": "Russian"},
        {"code": "zh", "name": "Chinese"},
        {"code": "ja", "name": "Japanese"},
        {"code": "ko", "name": "Korean"},
        {"code": "ar", "name": "Arabic"},
        {"code": "hi", "name": "Hindi"},
        {"code": "tr", "name": "Turkish"},
        {"code": "pl", "name": "Polish"},
        {"code": "vi", "name": "Vietnamese"},
        {"code": "th", "name": "Thai"},
        {"code": "id", "name": "Indonesian"},
        {"code": "sv", "name": "Swedish"},
        {"code": "da", "name": "Danish"},
        {"code": "no", "name": "Norwegian"},
        {"code": "fi", "name": "Finnish"},
        {"code": "cs", "name": "Czech"},
        {"code": "el", "name": "Greek"},
        {"code": "he", "name": "Hebrew"},
        {"code": "uk", "name": "Ukrainian"},
        {"code": "ro", "name": "Romanian"},
        {"code": "hu", "name": "Hungarian"},
        {"code": "bn", "name": "Bengali"},
        {"code": "ta", "name": "Tamil"},
    ]
    return {"languages": languages, "total": len(languages)}
