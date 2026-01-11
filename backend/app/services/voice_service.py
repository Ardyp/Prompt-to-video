"""
Voice Cloning and Text-to-Speech Service

Supports multiple providers:
- Fish Audio (recommended - best value)
- ElevenLabs (premium quality)
- Chatterbox (open source)
- Resemble AI (enterprise)
"""

import asyncio
import base64
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional

import aiohttp
import structlog

from app.config import VoiceProvider, get_settings
from app.models import TTSResponse, VoiceCloneResponse

logger = structlog.get_logger(__name__)
settings = get_settings()


class BaseVoiceService(ABC):
    """Abstract base class for voice services."""
    
    @abstractmethod
    async def clone_voice(
        self,
        audio_file: BinaryIO,
        name: str,
        description: Optional[str] = None
    ) -> VoiceCloneResponse:
        """Clone a voice from an audio sample."""
        pass
    
    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> TTSResponse:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    async def list_voices(self) -> list[dict]:
        """List available voices."""
        pass


class FishAudioService(BaseVoiceService):
    """
    Fish Audio voice service.
    
    Features:
    - #1 ranked on TTS-Arena
    - Voice cloning from 15 seconds
    - Emotional speech support
    - 50+ languages
    - Very affordable ($9.99/mo for 200 min)
    """
    
    BASE_URL = "https://api.fish.audio/v1"
    
    def __init__(self):
        self.api_key = settings.fish_audio_api_key.get_secret_value() if settings.fish_audio_api_key else None
        self.storage_path = Path(settings.local_storage_path)
        logger.info("fish_audio_service_initialized")
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def clone_voice(
        self,
        audio_file: BinaryIO,
        name: str,
        description: Optional[str] = None
    ) -> VoiceCloneResponse:
        """Clone a voice using Fish Audio."""
        voice_id = str(uuid.uuid4())
        
        async with aiohttp.ClientSession() as session:
            # Read audio file
            audio_data = audio_file.read()
            
            form = aiohttp.FormData()
            form.add_field("file", audio_data, filename="voice_sample.wav")
            form.add_field("name", name)
            if description:
                form.add_field("description", description)
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with session.post(
                f"{self.BASE_URL}/voices/clone",
                data=form,
                headers=headers
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error("fish_audio_clone_failed", error=error)
                    raise Exception(f"Voice cloning failed: {error}")
                
                result = await response.json()
                voice_id = result.get("voice_id", voice_id)
        
        return VoiceCloneResponse(
            voice_id=voice_id,
            name=name,
            status="ready",
            created_at=datetime.utcnow()
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> TTSResponse:
        """Synthesize speech using Fish Audio."""
        output_filename = f"tts_{uuid.uuid4()}.mp3"
        output_path = self.storage_path / "outputs" / output_filename
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": text,
                "model": settings.fish_audio_model,
                "speed": speed,
            }
            
            if voice_id:
                payload["voice_id"] = voice_id
            if language:
                payload["language"] = language
            
            async with session.post(
                f"{self.BASE_URL}/tts",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error("fish_audio_tts_failed", error=error)
                    raise Exception(f"TTS failed: {error}")
                
                audio_data = await response.read()
                
                # Save to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                # Get duration (approximate based on text length)
                # In production, use actual audio analysis
                duration = len(text) / 15  # ~15 chars per second
        
        return TTSResponse(
            audio_url=f"/static/outputs/{output_filename}",
            duration_seconds=round(duration, 2),
            format="mp3"
        )
    
    async def list_voices(self) -> list[dict]:
        """List available voices."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/voices",
                headers=self._get_headers()
            ) as response:
                if response.status != 200:
                    return []
                return await response.json()


class ElevenLabsService(BaseVoiceService):
    """
    ElevenLabs voice service.
    
    Features:
    - Industry-leading voice quality
    - Voice cloning from 1-2 minutes of audio
    - 29 languages
    - Emotional expression
    """
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key.get_secret_value() if settings.elevenlabs_api_key else None
        self.storage_path = Path(settings.local_storage_path)
        logger.info("elevenlabs_service_initialized")
    
    def _get_headers(self) -> dict:
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def clone_voice(
        self,
        audio_file: BinaryIO,
        name: str,
        description: Optional[str] = None
    ) -> VoiceCloneResponse:
        """Clone a voice using ElevenLabs."""
        async with aiohttp.ClientSession() as session:
            audio_data = audio_file.read()
            
            form = aiohttp.FormData()
            form.add_field("files", audio_data, filename="voice_sample.wav")
            form.add_field("name", name)
            if description:
                form.add_field("description", description)
            
            headers = {"xi-api-key": self.api_key}
            
            async with session.post(
                f"{self.BASE_URL}/voices/add",
                data=form,
                headers=headers
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error("elevenlabs_clone_failed", error=error)
                    raise Exception(f"Voice cloning failed: {error}")
                
                result = await response.json()
        
        return VoiceCloneResponse(
            voice_id=result["voice_id"],
            name=name,
            status="ready",
            created_at=datetime.utcnow()
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> TTSResponse:
        """Synthesize speech using ElevenLabs."""
        output_filename = f"tts_{uuid.uuid4()}.mp3"
        output_path = self.storage_path / "outputs" / output_filename
        
        # Use default voice if none specified
        voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": text,
                "model_id": settings.elevenlabs_model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with session.post(
                f"{self.BASE_URL}/text-to-speech/{voice_id}",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error("elevenlabs_tts_failed", error=error)
                    raise Exception(f"TTS failed: {error}")
                
                audio_data = await response.read()
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                duration = len(text) / 15
        
        return TTSResponse(
            audio_url=f"/static/outputs/{output_filename}",
            duration_seconds=round(duration, 2),
            format="mp3"
        )
    
    async def list_voices(self) -> list[dict]:
        """List available voices."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/voices",
                headers=self._get_headers()
            ) as response:
                if response.status != 200:
                    return []
                result = await response.json()
                return result.get("voices", [])


class ChatterboxService(BaseVoiceService):
    """
    Chatterbox (open source) voice service.
    
    Features:
    - MIT licensed
    - Voice cloning from 5 seconds
    - 17 languages
    - Self-hosted (free)
    - Beats ElevenLabs in blind tests
    """
    
    def __init__(self):
        # Chatterbox runs locally - import and initialize
        try:
            from chatterbox import ChatterboxTTS
            self._tts = ChatterboxTTS()
            logger.info("chatterbox_service_initialized")
        except ImportError:
            logger.warning("chatterbox_not_installed")
            self._tts = None
        
        self.storage_path = Path(settings.local_storage_path)
        self._cloned_voices: dict[str, Path] = {}
    
    async def clone_voice(
        self,
        audio_file: BinaryIO,
        name: str,
        description: Optional[str] = None
    ) -> VoiceCloneResponse:
        """Clone a voice using Chatterbox (local processing)."""
        voice_id = str(uuid.uuid4())
        
        # Save the audio file for reference
        voice_path = self.storage_path / "voices" / f"{voice_id}.wav"
        voice_path.parent.mkdir(parents=True, exist_ok=True)
        
        audio_data = audio_file.read()
        with open(voice_path, "wb") as f:
            f.write(audio_data)
        
        self._cloned_voices[voice_id] = voice_path
        
        return VoiceCloneResponse(
            voice_id=voice_id,
            name=name,
            status="ready",
            created_at=datetime.utcnow()
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> TTSResponse:
        """Synthesize speech using Chatterbox."""
        if self._tts is None:
            raise Exception("Chatterbox not installed")
        
        output_filename = f"tts_{uuid.uuid4()}.wav"
        output_path = self.storage_path / "outputs" / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get reference audio if voice_id provided
        reference_audio = None
        if voice_id and voice_id in self._cloned_voices:
            reference_audio = str(self._cloned_voices[voice_id])
        
        # Run synthesis (this is CPU/GPU intensive, should be in background)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._tts.synthesize(
                text,
                output_path=str(output_path),
                reference_audio=reference_audio,
                speed=speed
            )
        )
        
        duration = len(text) / 15
        
        return TTSResponse(
            audio_url=f"/static/outputs/{output_filename}",
            duration_seconds=round(duration, 2),
            format="wav"
        )
    
    async def list_voices(self) -> list[dict]:
        """List cloned voices."""
        return [
            {"voice_id": vid, "name": f"Clone {vid[:8]}"}
            for vid in self._cloned_voices.keys()
        ]


# Factory function
_voice_service_instance: Optional[BaseVoiceService] = None


def get_voice_service() -> BaseVoiceService:
    """Get the configured voice service instance."""
    global _voice_service_instance
    
    if _voice_service_instance is None:
        provider = settings.voice_provider
        
        if provider == VoiceProvider.FISH_AUDIO:
            _voice_service_instance = FishAudioService()
        elif provider == VoiceProvider.ELEVENLABS:
            _voice_service_instance = ElevenLabsService()
        elif provider == VoiceProvider.CHATTERBOX:
            _voice_service_instance = ChatterboxService()
        else:
            # Default to Fish Audio
            _voice_service_instance = FishAudioService()
        
        logger.info("voice_service_created", provider=provider.value)
    
    return _voice_service_instance
