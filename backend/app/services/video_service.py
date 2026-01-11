"""
Video Generation Service

Supports multiple providers:
- Google Veo 3.1 (recommended - native audio, 60s duration)
- OpenAI Sora 2 (best physics/realism)
- Runway Gen-3 (professional workflows)
- Kling 2.1 (cost-effective)
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import aiohttp
import structlog

from app.config import VideoProvider, get_settings
from app.models import VideoGenerationRequest, VideoGenerationResponse

logger = structlog.get_logger(__name__)
settings = get_settings()


class BaseVideoService(ABC):
    """Abstract base class for video generation services."""
    
    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None
    ) -> VideoGenerationResponse:
        """Generate a video from a text prompt."""
        pass
    
    @abstractmethod
    async def check_status(self, job_id: str) -> dict:
        """Check the status of a video generation job."""
        pass


class GoogleVeoService(BaseVideoService):
    """
    Google Veo 3.1 video generation service.
    
    Features:
    - Native audio generation (synchronized dialogue, SFX, music)
    - Up to 60 seconds duration
    - 720p/1080p resolution
    - 9:16 vertical format support
    - $0.15-$0.40 per second
    """
    
    def __init__(self):
        import google.generativeai as genai
        
        api_key = settings.google_api_key.get_secret_value() if settings.google_api_key else None
        genai.configure(api_key=api_key)
        
        self._client = genai
        self.storage_path = Path(settings.local_storage_path)
        self._pending_jobs: dict[str, dict] = {}
        
        logger.info("google_veo_service_initialized", model=settings.veo_model)
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None
    ) -> VideoGenerationResponse:
        """Generate a video using Google Veo 3.1."""
        job_id = str(uuid.uuid4())
        output_filename = f"video_{job_id}.mp4"
        output_path = self.storage_path / "outputs" / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the enhanced prompt
        full_prompt = prompt
        if style:
            full_prompt = f"{style} style. {full_prompt}"
        
        try:
            # Initialize the video generation
            from google.genai import types
            
            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio.replace(":", "x"),
                resolution=resolution,
            )
            
            if negative_prompt:
                config.negative_prompt = negative_prompt
            
            # Start generation
            operation = self._client.models.generate_videos(
                model=settings.veo_model,
                prompt=full_prompt,
                config=config
            )
            
            # Store for status checking
            self._pending_jobs[job_id] = {
                "operation": operation,
                "output_path": str(output_path),
                "started_at": time.time()
            }
            
            # Wait for completion (with timeout)
            timeout = 300  # 5 minutes
            poll_interval = 10
            elapsed = 0
            
            while not operation.done and elapsed < timeout:
                await asyncio.sleep(poll_interval)
                operation = self._client.operations.get(operation)
                elapsed += poll_interval
                logger.info("veo_generation_progress", job_id=job_id, elapsed=elapsed)
            
            if not operation.done:
                raise Exception("Video generation timed out")
            
            # Download the video
            result = operation.result
            if result.generated_videos:
                video = result.generated_videos[0]
                self._client.files.download(file=video.video)
                video.video.save(str(output_path))
                
                return VideoGenerationResponse(
                    video_url=f"/static/outputs/{output_filename}",
                    duration_seconds=float(duration),
                    resolution=resolution,
                    format="mp4",
                    has_audio=True  # Veo 3.1 generates audio
                )
            else:
                raise Exception("No video generated")
                
        except Exception as e:
            logger.error("veo_generation_failed", error=str(e), job_id=job_id)
            raise
    
    async def check_status(self, job_id: str) -> dict:
        """Check generation status."""
        if job_id not in self._pending_jobs:
            return {"status": "not_found"}
        
        job = self._pending_jobs[job_id]
        operation = job["operation"]
        
        if operation.done:
            return {"status": "completed", "output_path": job["output_path"]}
        
        elapsed = time.time() - job["started_at"]
        return {"status": "processing", "elapsed_seconds": elapsed}


class SoraService(BaseVideoService):
    """
    OpenAI Sora 2 video generation service.
    
    Features:
    - Best physics/realism simulation
    - Up to 20 seconds duration
    - Native audio support
    - $0.10-$0.50 per second
    """
    
    def __init__(self):
        from openai import AsyncOpenAI
        
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        self._client = AsyncOpenAI(api_key=api_key)
        self.storage_path = Path(settings.local_storage_path)
        
        logger.info("sora_service_initialized", model=settings.sora_model)
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None
    ) -> VideoGenerationResponse:
        """Generate a video using OpenAI Sora 2."""
        job_id = str(uuid.uuid4())
        output_filename = f"video_{job_id}.mp4"
        output_path = self.storage_path / "outputs" / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        full_prompt = prompt
        if style:
            full_prompt = f"{style}. {full_prompt}"
        
        try:
            # Sora API call (API structure may vary - this is estimated)
            response = await self._client.videos.generate(
                model=settings.sora_model,
                prompt=full_prompt,
                duration=min(duration, 20),  # Sora max 20s
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            )
            
            # Download video
            video_url = response.video_url
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as resp:
                    video_data = await resp.read()
                    with open(output_path, "wb") as f:
                        f.write(video_data)
            
            return VideoGenerationResponse(
                video_url=f"/static/outputs/{output_filename}",
                duration_seconds=float(duration),
                resolution=resolution,
                format="mp4",
                has_audio=True
            )
            
        except Exception as e:
            logger.error("sora_generation_failed", error=str(e), job_id=job_id)
            raise
    
    async def check_status(self, job_id: str) -> dict:
        """Check generation status."""
        # Implementation depends on Sora API
        return {"status": "unknown"}


class RunwayService(BaseVideoService):
    """
    Runway Gen-3 Alpha video generation service.
    
    Features:
    - Professional-grade output
    - Integrated editing suite
    - Up to 10 seconds per generation
    - ~$0.05 per second
    """
    
    BASE_URL = "https://api.runwayml.com/v1"
    
    def __init__(self):
        self.api_key = settings.runway_api_key.get_secret_value() if settings.runway_api_key else None
        self.storage_path = Path(settings.local_storage_path)
        
        logger.info("runway_service_initialized", model=settings.runway_model)
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None
    ) -> VideoGenerationResponse:
        """Generate a video using Runway Gen-3."""
        job_id = str(uuid.uuid4())
        output_filename = f"video_{job_id}.mp4"
        output_path = self.storage_path / "outputs" / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": settings.runway_model,
                "prompt": prompt,
                "duration": min(duration, 10),
                "aspect_ratio": aspect_ratio,
            }
            
            # Start generation
            async with session.post(
                f"{self.BASE_URL}/generations",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Runway generation failed: {error}")
                
                result = await response.json()
                generation_id = result["id"]
            
            # Poll for completion
            timeout = 300
            poll_interval = 5
            elapsed = 0
            
            while elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                async with session.get(
                    f"{self.BASE_URL}/generations/{generation_id}",
                    headers=headers
                ) as response:
                    status_result = await response.json()
                    
                    if status_result["status"] == "completed":
                        video_url = status_result["output"]["video_url"]
                        
                        # Download
                        async with session.get(video_url) as video_resp:
                            video_data = await video_resp.read()
                            with open(output_path, "wb") as f:
                                f.write(video_data)
                        
                        return VideoGenerationResponse(
                            video_url=f"/static/outputs/{output_filename}",
                            duration_seconds=float(duration),
                            resolution=resolution,
                            format="mp4",
                            has_audio=False  # Runway doesn't include audio
                        )
                    
                    elif status_result["status"] == "failed":
                        raise Exception("Runway generation failed")
            
            raise Exception("Runway generation timed out")
    
    async def check_status(self, job_id: str) -> dict:
        """Check generation status."""
        return {"status": "unknown"}


class KlingService(BaseVideoService):
    """
    Kling 2.1 video generation service.
    
    Features:
    - Cost-effective ($0.25-$2.80 per video)
    - Good motion fidelity
    - 5-10 second videos
    - 720p/1080p
    """
    
    BASE_URL = "https://api.kling.ai/v1"
    
    def __init__(self):
        self.api_key = settings.kling_api_key.get_secret_value() if settings.kling_api_key else None
        self.storage_path = Path(settings.local_storage_path)
        
        logger.info("kling_service_initialized", model=settings.kling_model)
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None
    ) -> VideoGenerationResponse:
        """Generate a video using Kling 2.1."""
        job_id = str(uuid.uuid4())
        output_filename = f"video_{job_id}.mp4"
        output_path = self.storage_path / "outputs" / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": settings.kling_model,
                "prompt": prompt,
                "duration": min(duration, 10),
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
            }
            
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            
            # Generate
            async with session.post(
                f"{self.BASE_URL}/videos/generate",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Kling generation failed: {error}")
                
                result = await response.json()
                task_id = result["task_id"]
            
            # Poll for completion
            timeout = 600  # Kling can take longer
            poll_interval = 10
            elapsed = 0
            
            while elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                async with session.get(
                    f"{self.BASE_URL}/videos/status/{task_id}",
                    headers=headers
                ) as response:
                    status_result = await response.json()
                    
                    if status_result["status"] == "completed":
                        video_url = status_result["video_url"]
                        
                        async with session.get(video_url) as video_resp:
                            video_data = await video_resp.read()
                            with open(output_path, "wb") as f:
                                f.write(video_data)
                        
                        return VideoGenerationResponse(
                            video_url=f"/static/outputs/{output_filename}",
                            duration_seconds=float(duration),
                            resolution=resolution,
                            format="mp4",
                            has_audio=False
                        )
                    
                    elif status_result["status"] == "failed":
                        raise Exception("Kling generation failed")
            
            raise Exception("Kling generation timed out")
    
    async def check_status(self, job_id: str) -> dict:
        """Check generation status."""
        return {"status": "unknown"}


# Factory function
_video_service_instance: Optional[BaseVideoService] = None


def get_video_service() -> BaseVideoService:
    """Get the configured video service instance."""
    global _video_service_instance
    
    if _video_service_instance is None:
        provider = settings.video_provider
        
        if provider in (VideoProvider.VEO3, VideoProvider.VEO3_FAST):
            _video_service_instance = GoogleVeoService()
        elif provider == VideoProvider.SORA:
            _video_service_instance = SoraService()
        elif provider == VideoProvider.RUNWAY:
            _video_service_instance = RunwayService()
        elif provider == VideoProvider.KLING:
            _video_service_instance = KlingService()
        else:
            # Default to Veo
            _video_service_instance = GoogleVeoService()
        
        logger.info("video_service_created", provider=provider.value)
    
    return _video_service_instance
