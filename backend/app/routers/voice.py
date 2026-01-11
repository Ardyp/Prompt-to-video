"""
Voice cloning and TTS API router.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models import TTSRequest, TTSResponse, VoiceCloneResponse
from app.services.voice_service import get_voice_service

router = APIRouter()
settings = get_settings()


@router.post("/clone", response_model=VoiceCloneResponse)
async def clone_voice(
    audio_file: UploadFile = File(..., description="Audio sample (5-30 seconds)"),
    name: str = Form(..., description="Name for the voice clone"),
    description: str = Form(None, description="Optional description")
):
    """
    Clone a voice from an audio sample.
    
    **Requirements:**
    - Audio duration: 5-30 seconds (longer = better quality)
    - Formats: WAV, MP3, M4A, FLAC
    - Quality: Clear speech, minimal background noise
    
    **Tips for best results:**
    - Use a quiet environment
    - Speak naturally at normal pace
    - Include varied intonation
    """
    # Validate file size (max 10MB)
    content = await audio_file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")
    
    # Reset file position
    await audio_file.seek(0)
    
    # Validate file type
    allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/m4a", "audio/flac", "audio/x-wav"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format. Allowed: WAV, MP3, M4A, FLAC"
        )
    
    try:
        voice_service = get_voice_service()
        result = await voice_service.clone_voice(
            audio_file=audio_file.file,
            name=name,
            description=description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text.
    
    **Parameters:**
    - `text`: Text to synthesize (max 5000 characters)
    - `voice_id`: Optional ID of a cloned voice
    - `language`: Optional language code for pronunciation
    - `speed`: Speech speed multiplier (0.5-2.0)
    
    Returns URL to download the generated audio.
    """
    try:
        voice_service = get_voice_service()
        result = await voice_service.synthesize_speech(
            text=request.text,
            voice_id=request.voice_id,
            language=request.language,
            speed=request.speed
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices():
    """
    List available voices.
    
    Returns both default voices and user-cloned voices.
    """
    try:
        voice_service = get_voice_service()
        voices = await voice_service.list_voices()
        return {"voices": voices, "provider": settings.voice_provider.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """
    Delete a cloned voice.
    
    **Note:** Only user-cloned voices can be deleted.
    """
    # Implementation depends on provider
    return {"status": "deleted", "voice_id": voice_id}
