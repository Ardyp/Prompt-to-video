"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Status of a generation job."""
    PENDING = "pending"
    ENHANCING_PROMPT = "enhancing_prompt"
    DETECTING_LANGUAGE = "detecting_language"
    CLONING_VOICE = "cloning_voice"
    GENERATING_SPEECH = "generating_speech"
    GENERATING_VIDEO = "generating_video"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# PROMPT ENHANCEMENT MODELS
# =============================================================================

class ConceptInfo(BaseModel):
    """Extracted concept from prompt."""
    type: str = Field(..., description="Concept type: subject, action, setting, etc.")
    value: str = Field(..., description="The concept value")
    confidence: float = Field(..., ge=0, le=1)
    visual_keywords: list[str] = Field(default_factory=list)
    cultural_context: Optional[str] = None


class StyleInfo(BaseModel):
    """Extracted style from prompt."""
    category: str = Field(..., description="Style category: cinematic, cultural, mood, etc.")
    value: str
    confidence: float = Field(..., ge=0, le=1)
    modifiers: list[str] = Field(default_factory=list)


class AestheticScoreInfo(BaseModel):
    """Aesthetic quality prediction."""
    overall_score: float = Field(..., ge=0, le=100)
    composition_score: float = Field(..., ge=0, le=100)
    clarity_score: float = Field(..., ge=0, le=100)
    creativity_score: float = Field(..., ge=0, le=100)
    technical_score: float = Field(..., ge=0, le=100)
    cultural_accuracy_score: float = Field(..., ge=0, le=100)
    motion_potential_score: float = Field(..., ge=0, le=100)
    audio_sync_score: float = Field(..., ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class FrameGuidance(BaseModel):
    """Guidance for a specific video frame/segment."""
    frame_number: int
    timestamp_start: float
    timestamp_end: float
    motion_direction: str
    focus_elements: list[str]
    transition: str


class PromptEnhancementResult(BaseModel):
    """Result of prompt enhancement pipeline."""
    original_prompt: str
    enhanced_prompt: str
    negative_prompt: str
    concepts: list[ConceptInfo]
    styles: list[StyleInfo]
    aesthetic_score: AestheticScoreInfo
    frame_guidance: list[FrameGuidance]
    enhancement_iterations: int
    final_confidence: float


class LanguageInfo(BaseModel):
    """Detected language information."""
    code: str = Field(..., description="ISO 639-1 language code", example="en")
    name: str = Field(..., description="Language name", example="English")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence", example=0.98)


class LanguageDetectionRequest(BaseModel):
    """Request to detect language of text."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    
    @field_validator("text")
    @classmethod
    def clean_text(cls, v: str) -> str:
        return v.strip()


class LanguageDetectionResponse(BaseModel):
    """Response from language detection."""
    detected_language: LanguageInfo
    alternatives: list[LanguageInfo] = Field(default_factory=list)
    processing_time_ms: float


class VoiceCloneRequest(BaseModel):
    """Request to clone a voice from audio sample."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the voice clone")
    description: Optional[str] = Field(None, max_length=500)


class VoiceCloneResponse(BaseModel):
    """Response from voice cloning."""
    voice_id: str = Field(..., description="Unique ID for the cloned voice")
    name: str
    status: str = Field(..., description="Clone status: processing, ready, failed")
    created_at: datetime


class TTSRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: Optional[str] = Field(None, description="ID of cloned voice to use")
    language: Optional[str] = Field(None, description="Target language code")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier")


class TTSResponse(BaseModel):
    """Response from text-to-speech synthesis."""
    audio_url: str = Field(..., description="URL to download the audio file")
    duration_seconds: float
    format: str = Field("mp3", description="Audio format")


class VideoGenerationRequest(BaseModel):
    """Request to generate a video from text prompt."""
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Text prompt describing the video",
        example="A serene mountain landscape at sunrise with clouds rolling through the valleys"
    )
    duration: int = Field(
        8,
        ge=4,
        le=60,
        description="Video duration in seconds"
    )
    aspect_ratio: str = Field(
        "16:9",
        pattern=r"^\d+:\d+$",
        description="Aspect ratio (16:9, 9:16, 1:1)"
    )
    resolution: str = Field(
        "720p",
        description="Video resolution (720p, 1080p)"
    )
    style: Optional[str] = Field(
        None,
        description="Visual style (cinematic, anime, realistic, etc.)"
    )
    negative_prompt: Optional[str] = Field(
        None,
        max_length=500,
        description="What to avoid in the video"
    )


class VideoGenerationResponse(BaseModel):
    """Response from video generation."""
    video_url: str = Field(..., description="URL to download the video")
    thumbnail_url: Optional[str] = None
    duration_seconds: float
    resolution: str
    format: str = Field("mp4")
    has_audio: bool = Field(False)


class FullGenerationRequest(BaseModel):
    """
    Complete request to generate a video with voice narration.
    This is the main endpoint that orchestrates the full pipeline.
    """
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Text prompt that will be narrated and visualized"
    )
    voice_id: Optional[str] = Field(
        None,
        description="ID of previously cloned voice. If not provided, uses default voice."
    )
    video_duration: int = Field(
        8,
        ge=4,
        le=60,
        description="Target video duration in seconds"
    )
    aspect_ratio: str = Field("16:9")
    resolution: str = Field("720p")
    video_style: Optional[str] = Field(None, description="Visual style for the video")
    detect_language: bool = Field(True, description="Auto-detect prompt language")
    
    @field_validator("prompt")
    @classmethod
    def clean_prompt(cls, v: str) -> str:
        return v.strip()


class JobProgress(BaseModel):
    """Progress update for a generation job."""
    job_id: str
    status: JobStatus
    progress: float = Field(..., ge=0, le=100, description="Completion percentage")
    current_step: str = Field(..., description="Current processing step")
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None


class FullGenerationResponse(BaseModel):
    """Response from the full generation pipeline."""
    job_id: str = Field(..., description="Job ID to track progress")
    status: JobStatus
    message: str
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")


class GenerationResult(BaseModel):
    """Final result of a completed generation."""
    job_id: str
    status: JobStatus
    video_url: str
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: float
    detected_language: Optional[LanguageInfo] = None
    prompt_enhancement: Optional[PromptEnhancementResult] = None
    processing_time_seconds: float
    cost_estimate: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    providers: dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
