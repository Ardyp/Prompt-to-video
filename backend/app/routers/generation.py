"""
Video generation API router.

Orchestrates the full prompt-to-video pipeline:
1. Language detection
2. Voice synthesis (TTS)
3. Video generation
4. Audio/video merging
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config import get_settings
from app.models import (
    FullGenerationRequest,
    FullGenerationResponse,
    GenerationResult,
    JobProgress,
    JobStatus,
    VideoGenerationRequest,
    VideoGenerationResponse,
)
from app.services.language_service import get_language_detector
from app.services.media_processor import get_media_processor
from app.services.video_service import get_video_service
from app.services.voice_service import get_voice_service

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()

# In-memory job storage (use Redis in production)
_jobs: dict[str, JobProgress] = {}
_results: dict[str, GenerationResult] = {}


async def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: float,
    current_step: str,
    message: Optional[str] = None,
    error: Optional[str] = None
):
    """Update job progress status."""
    if job_id in _jobs:
        _jobs[job_id].status = status
        _jobs[job_id].progress = progress
        _jobs[job_id].current_step = current_step
        _jobs[job_id].message = message
        _jobs[job_id].error = error
        _jobs[job_id].updated_at = datetime.utcnow()
    
    logger.info(
        "job_progress",
        job_id=job_id,
        status=status.value,
        progress=progress,
        step=current_step
    )


async def run_full_pipeline(
    job_id: str,
    request: FullGenerationRequest
):
    """
    Execute the full prompt-to-video pipeline.
    
    Steps:
    1. Detect language (if enabled)
    2. Generate speech from prompt
    3. Generate video from prompt
    4. Merge audio and video (if video has no audio)
    """
    start_time = datetime.utcnow()
    storage_path = Path(settings.local_storage_path)
    
    try:
        detected_language = None
        
        # Step 1: Language Detection
        if request.detect_language:
            await update_job_status(
                job_id, JobStatus.DETECTING_LANGUAGE, 10,
                "Detecting language...",
                "Analyzing your prompt"
            )
            
            detector = get_language_detector()
            lang_result = await detector.detect(request.prompt)
            detected_language = lang_result.detected_language
            
            logger.info(
                "language_detected",
                job_id=job_id,
                language=detected_language.code,
                confidence=detected_language.confidence
            )
        
        # Step 2: Generate Speech
        await update_job_status(
            job_id, JobStatus.GENERATING_SPEECH, 25,
            "Generating voice narration...",
            f"Creating speech in {detected_language.name if detected_language else 'detected language'}"
        )
        
        voice_service = get_voice_service()
        tts_result = await voice_service.synthesize_speech(
            text=request.prompt,
            voice_id=request.voice_id,
            language=detected_language.code if detected_language else None
        )
        
        audio_path = str(storage_path / tts_result.audio_url.lstrip("/static/"))
        
        logger.info(
            "speech_generated",
            job_id=job_id,
            duration=tts_result.duration_seconds
        )
        
        # Step 3: Generate Video
        await update_job_status(
            job_id, JobStatus.GENERATING_VIDEO, 50,
            "Generating video...",
            "This may take 2-5 minutes"
        )
        
        # Enhance prompt for video generation
        video_prompt = request.prompt
        if request.video_style:
            video_prompt = f"{request.video_style} style. {video_prompt}"
        
        video_service = get_video_service()
        video_result = await video_service.generate_video(
            prompt=video_prompt,
            duration=request.video_duration,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            style=request.video_style
        )
        
        video_path = str(storage_path / video_result.video_url.lstrip("/static/"))
        final_video_url = video_result.video_url
        
        logger.info(
            "video_generated",
            job_id=job_id,
            has_audio=video_result.has_audio
        )
        
        # Step 4: Merge Audio/Video (if needed)
        if not video_result.has_audio:
            await update_job_status(
                job_id, JobStatus.MERGING, 85,
                "Merging audio and video...",
                "Almost done!"
            )
            
            processor = get_media_processor()
            
            # Adjust audio length to match video
            adjusted_audio = await processor.adjust_audio_length(
                audio_path,
                request.video_duration
            )
            
            # Merge
            output_filename = f"final_{job_id}.mp4"
            output_path = str(storage_path / "outputs" / output_filename)
            
            await processor.merge_audio_video(
                video_path=video_path,
                audio_path=adjusted_audio,
                output_path=output_path
            )
            
            final_video_url = f"/static/outputs/{output_filename}"
            
            logger.info("audio_video_merged", job_id=job_id)
        
        # Generate thumbnail
        processor = get_media_processor()
        thumb_path = await processor.generate_thumbnail(video_path)
        thumb_url = f"/static/outputs/{Path(thumb_path).name}"
        
        # Calculate processing time and cost
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Estimate cost (simplified)
        cost = request.video_duration * 0.40  # Veo 3.1 pricing
        
        # Store result
        result = GenerationResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            video_url=final_video_url,
            audio_url=tts_result.audio_url,
            thumbnail_url=thumb_url,
            duration_seconds=float(request.video_duration),
            detected_language=detected_language,
            processing_time_seconds=processing_time,
            cost_estimate=cost,
            metadata={
                "video_provider": settings.video_provider.value,
                "voice_provider": settings.voice_provider.value,
                "resolution": request.resolution,
                "aspect_ratio": request.aspect_ratio,
            }
        )
        _results[job_id] = result
        
        # Update final status
        await update_job_status(
            job_id, JobStatus.COMPLETED, 100,
            "Complete!",
            f"Video generated in {processing_time:.1f} seconds"
        )
        
        logger.info(
            "pipeline_completed",
            job_id=job_id,
            processing_time=processing_time,
            cost=cost
        )
        
    except Exception as e:
        logger.error("pipeline_failed", job_id=job_id, error=str(e))
        await update_job_status(
            job_id, JobStatus.FAILED, 0,
            "Failed",
            error=str(e)
        )


@router.post("/create", response_model=FullGenerationResponse)
async def create_video(
    request: FullGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a video from a text prompt with voice narration.
    
    This endpoint starts the full pipeline:
    1. **Language Detection** - Automatically detects the prompt language
    2. **Speech Synthesis** - Generates voice narration using TTS
    3. **Video Generation** - Creates video from the text prompt
    4. **Audio Merging** - Combines voice with video
    
    **WebSocket Updates:**
    Connect to `/ws/progress/{job_id}` to receive real-time progress updates.
    
    **Example Request:**
    ```json
    {
        "prompt": "A serene mountain landscape at sunrise with mist rolling through the valleys",
        "video_duration": 10,
        "aspect_ratio": "16:9",
        "resolution": "720p",
        "video_style": "cinematic"
    }
    ```
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job
    job = JobProgress(
        job_id=job_id,
        status=JobStatus.PENDING,
        progress=0,
        current_step="Initializing...",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    _jobs[job_id] = job
    
    # Start background task
    background_tasks.add_task(run_full_pipeline, job_id, request)
    
    logger.info("generation_started", job_id=job_id, prompt_length=len(request.prompt))
    
    return FullGenerationResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Video generation started. Use the WebSocket URL for real-time updates.",
        websocket_url=f"/ws/progress/{job_id}"
    )


@router.get("/status/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str):
    """
    Get the current status of a generation job.
    
    Returns progress percentage, current step, and any error messages.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _jobs[job_id]


@router.get("/result/{job_id}", response_model=GenerationResult)
async def get_job_result(job_id: str):
    """
    Get the result of a completed generation job.
    
    Only available for jobs with status `completed`.
    """
    if job_id not in _results:
        if job_id in _jobs:
            job = _jobs[job_id]
            if job.status == JobStatus.FAILED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job failed: {job.error}"
                )
            raise HTTPException(
                status_code=400,
                detail=f"Job not yet completed. Status: {job.status.value}"
            )
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _results[job_id]


@router.post("/video-only", response_model=VideoGenerationResponse)
async def generate_video_only(request: VideoGenerationRequest):
    """
    Generate a video without voice narration.
    
    Use this endpoint when you only need video generation
    without the full TTS pipeline.
    """
    try:
        video_service = get_video_service()
        result = await video_service.generate_video(
            prompt=request.prompt,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            style=request.style,
            negative_prompt=request.negative_prompt
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job.
    
    **Note:** Already completed jobs cannot be cancelled.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _jobs[job_id]
    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")
    
    # Mark as failed/cancelled
    await update_job_status(
        job_id, JobStatus.FAILED, 0,
        "Cancelled",
        error="Job cancelled by user"
    )
    
    return {"status": "cancelled", "job_id": job_id}


@router.get("/estimate")
async def estimate_cost(
    duration: int = 8,
    resolution: str = "720p"
):
    """
    Estimate the cost of generating a video.
    
    Returns estimated cost based on current provider pricing.
    """
    from app.config import PRICING, VideoProvider, VoiceProvider
    
    video_pricing = PRICING.get(settings.video_provider, {})
    voice_pricing = PRICING.get(settings.voice_provider, {})
    
    video_cost = video_pricing.get("per_second", 0.40) * duration
    voice_cost = voice_pricing.get("per_minute", 0.05) * (duration / 60)
    
    total = video_cost + voice_cost
    
    return {
        "video_cost": round(video_cost, 2),
        "voice_cost": round(voice_cost, 2),
        "total_cost": round(total, 2),
        "duration_seconds": duration,
        "providers": {
            "video": settings.video_provider.value,
            "voice": settings.voice_provider.value
        }
    }
