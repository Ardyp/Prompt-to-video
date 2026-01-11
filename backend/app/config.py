"""
Configuration settings for the Prompt-to-Video application.
Supports multiple AI providers with easy switching.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VideoProvider(str, Enum):
    """Supported video generation providers."""
    VEO3 = "veo3"
    VEO3_FAST = "veo3_fast"
    RUNWAY = "runway"
    KLING = "kling"
    SORA = "sora"
    WAN2 = "wan2"  # Open source - self hosted


class VoiceProvider(str, Enum):
    """Supported voice cloning/TTS providers."""
    FISH_AUDIO = "fish_audio"
    ELEVENLABS = "elevenlabs"
    CHATTERBOX = "chatterbox"  # Open source
    RESEMBLE = "resemble"
    CARTESIA = "cartesia"


class LanguageProvider(str, Enum):
    """Supported language detection providers."""
    LINGUA = "lingua"  # Open source - recommended
    GOOGLE = "google"
    AWS = "aws"
    FASTTEXT = "fasttext"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application Settings
    app_name: str = "Prompt to Video"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Provider Selection
    video_provider: VideoProvider = VideoProvider.VEO3
    voice_provider: VoiceProvider = VoiceProvider.FISH_AUDIO
    language_provider: LanguageProvider = LanguageProvider.LINGUA
    
    # Google AI (Veo 3.1)
    google_api_key: Optional[SecretStr] = None
    google_project_id: Optional[str] = None
    veo_model: str = "veo-3.0-generate-preview"
    veo_resolution: str = "720p"  # 720p or 1080p
    veo_duration: int = 8  # seconds per generation
    
    # OpenAI (Sora 2)
    openai_api_key: Optional[SecretStr] = None
    sora_model: str = "sora-2"
    
    # Runway
    runway_api_key: Optional[SecretStr] = None
    runway_model: str = "gen3a_turbo"
    
    # Kling
    kling_api_key: Optional[SecretStr] = None
    kling_model: str = "kling-v2.1"
    
    # Fish Audio
    fish_audio_api_key: Optional[SecretStr] = None
    fish_audio_model: str = "speech-1.5"
    
    # ElevenLabs
    elevenlabs_api_key: Optional[SecretStr] = None
    elevenlabs_model: str = "eleven_multilingual_v2"
    
    # Resemble AI
    resemble_api_key: Optional[SecretStr] = None
    
    # AWS (Comprehend for language detection)
    aws_access_key_id: Optional[SecretStr] = None
    aws_secret_access_key: Optional[SecretStr] = None
    aws_region: str = "us-east-1"
    
    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"
    
    # Storage
    storage_backend: str = "local"  # local, s3
    local_storage_path: str = "./storage"
    s3_bucket: Optional[str] = None
    
    # Processing Settings
    max_prompt_length: int = 2000
    max_video_duration: int = 60  # seconds
    max_audio_sample_duration: int = 30  # seconds for voice cloning
    min_audio_sample_duration: int = 5  # minimum for voice cloning
    
    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    def get_video_api_key(self) -> Optional[str]:
        """Get the API key for the selected video provider."""
        key_map = {
            VideoProvider.VEO3: self.google_api_key,
            VideoProvider.VEO3_FAST: self.google_api_key,
            VideoProvider.RUNWAY: self.runway_api_key,
            VideoProvider.KLING: self.kling_api_key,
            VideoProvider.SORA: self.openai_api_key,
        }
        key = key_map.get(self.video_provider)
        return key.get_secret_value() if key else None
    
    def get_voice_api_key(self) -> Optional[str]:
        """Get the API key for the selected voice provider."""
        key_map = {
            VoiceProvider.FISH_AUDIO: self.fish_audio_api_key,
            VoiceProvider.ELEVENLABS: self.elevenlabs_api_key,
            VoiceProvider.RESEMBLE: self.resemble_api_key,
        }
        key = key_map.get(self.voice_provider)
        return key.get_secret_value() if key else None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Provider pricing information (per second/unit)
PRICING = {
    VideoProvider.VEO3: {"per_second": 0.40, "with_audio": True},
    VideoProvider.VEO3_FAST: {"per_second": 0.15, "with_audio": True},
    VideoProvider.RUNWAY: {"per_second": 0.05, "with_audio": False},
    VideoProvider.KLING: {"per_video_8s": 0.90, "with_audio": False},
    VideoProvider.SORA: {"per_second": 0.30, "with_audio": True},
    VideoProvider.WAN2: {"per_second": 0.0, "with_audio": False},  # Self-hosted
    
    VoiceProvider.FISH_AUDIO: {"per_minute": 0.05},
    VoiceProvider.ELEVENLABS: {"per_1k_chars": 0.30},
    VoiceProvider.CHATTERBOX: {"per_minute": 0.0},  # Open source
}
