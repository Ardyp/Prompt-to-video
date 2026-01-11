"""
Smart Orchestrator - Quality-First Generation Pipeline

This orchestrator:
1. Always selects the BEST available model
2. Automatically falls back if primary fails
3. Tracks quality/cost metrics
4. Supports A/B testing between providers
5. Handles model versioning for reproducibility
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog

from app.config import get_settings
from app.models import (
    FullGenerationRequest,
    GenerationResult,
    JobProgress,
    JobStatus,
    LanguageInfo,
)
from app.services.provider_registry import (
    ProviderCategory,
    ProviderInfo,
    ProviderResult,
    QualityTier,
    get_registry,
)
from app.services.prompt_enhancer import (
    PromptEnhancer,
    EnhancedPrompt,
    get_prompt_enhancer,
)
from app.services.language_service import get_language_detector
from app.services.voice_service import get_voice_service
from app.services.video_service import get_video_service
from app.services.media_processor import get_media_processor

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class GenerationPlan:
    """Plan for executing a generation request."""
    job_id: str
    request: FullGenerationRequest
    
    # Enhanced prompt from the enhancer pipeline
    enhanced_prompt: Optional[EnhancedPrompt] = None
    
    # Selected providers (best available)
    video_provider: ProviderInfo = None
    voice_provider: ProviderInfo = None
    language_provider: ProviderInfo = None
    
    # Fallback chains
    video_fallbacks: List[str] = field(default_factory=list)
    voice_fallbacks: List[str] = field(default_factory=list)
    
    # Estimated costs
    estimated_video_cost: float = 0.0
    estimated_voice_cost: float = 0.0
    estimated_total_cost: float = 0.0
    
    # Quality expectations
    expected_quality_score: float = 0.0
    
    # Flags
    needs_audio_merge: bool = True  # True if video provider doesn't have native audio


class SmartOrchestrator:
    """
    Intelligent orchestrator for the generation pipeline.
    
    Philosophy: Always deliver the highest quality possible.
    """
    
    def __init__(self):
        self.registry = get_registry()
        self.prompt_enhancer = get_prompt_enhancer()
        self._active_jobs: Dict[str, GenerationPlan] = {}
    
    def create_plan(self, request: FullGenerationRequest) -> GenerationPlan:
        """
        Create an optimized execution plan for the request.
        
        Includes:
        1. Prompt Enhancement (concept/style extraction, aesthetic scoring)
        2. Provider Selection (best quality with fallbacks)
        3. Cost Estimation
        """
        job_id = str(uuid.uuid4())
        
        # ================================================================
        # STEP 1: ENHANCE THE PROMPT
        # ================================================================
        enhanced_prompt = self.prompt_enhancer.enhance(
            prompt=request.prompt,
            duration=float(request.video_duration),
            extra_context={"style": request.video_style} if request.video_style else None
        )
        
        logger.info(
            "prompt_enhanced",
            job_id=job_id,
            aesthetic_score=enhanced_prompt.aesthetic_score.overall_score,
            num_concepts=len(enhanced_prompt.concepts),
            num_styles=len(enhanced_prompt.styles),
            num_frames=len(enhanced_prompt.frame_prompts)
        )
        
        # ================================================================
        # STEP 2: SELECT BEST PROVIDERS
        # ================================================================
        
        # Select best video provider
        video_requirements = []
        if request.video_duration > 20:
            video_requirements.append("long_duration")
        
        # Prefer providers with native audio to avoid merge step
        video_provider = self.registry.get_best_provider(
            ProviderCategory.VIDEO,
            min_quality=80,  # Minimum acceptable quality
            required_features=["native_audio"] if not request.voice_id else None
        )
        
        # Fallback: get any high-quality video provider
        if not video_provider:
            video_provider = self.registry.get_best_provider(
                ProviderCategory.VIDEO,
                min_quality=75
            )
        
        if not video_provider:
            raise ValueError("No video providers available")
        
        # Select best voice provider
        voice_provider = self.registry.get_best_provider(
            ProviderCategory.VOICE,
            min_quality=85,
            required_features=["voice_cloning"] if request.voice_id else None
        )
        
        if not voice_provider:
            voice_provider = self.registry.get_best_provider(ProviderCategory.VOICE)
        
        if not voice_provider:
            raise ValueError("No voice providers available")
        
        # Select best language provider (always use best, it's usually free)
        language_provider = self.registry.get_best_provider(
            ProviderCategory.LANGUAGE,
            min_quality=80
        )
        
        if not language_provider:
            language_provider = self.registry.get_best_provider(ProviderCategory.LANGUAGE)
        
        # Get fallback chains
        video_fallbacks = self.registry.get_fallback_chain(
            ProviderCategory.VIDEO,
            primary=video_provider.name
        )
        voice_fallbacks = self.registry.get_fallback_chain(
            ProviderCategory.VOICE,
            primary=voice_provider.name
        )
        
        # Calculate costs
        video_cost = video_provider.cost_per_unit * request.video_duration
        voice_cost = voice_provider.cost_per_unit * (len(request.prompt) / 1000)
        
        # Determine if we need to merge audio
        needs_merge = not video_provider.supports_audio
        
        # Calculate expected quality (weighted average)
        quality_score = (
            video_provider.quality_score * 0.6 +  # Video is most important
            voice_provider.quality_score * 0.3 +  # Voice quality matters
            (language_provider.quality_score if language_provider else 90) * 0.1
        )
        
        plan = GenerationPlan(
            job_id=job_id,
            request=request,
            enhanced_prompt=enhanced_prompt,
            video_provider=video_provider,
            voice_provider=voice_provider,
            language_provider=language_provider,
            video_fallbacks=video_fallbacks,
            voice_fallbacks=voice_fallbacks,
            estimated_video_cost=video_cost,
            estimated_voice_cost=voice_cost,
            estimated_total_cost=video_cost + voice_cost,
            expected_quality_score=quality_score,
            needs_audio_merge=needs_merge,
        )
        
        self._active_jobs[job_id] = plan
        
        logger.info(
            "generation_plan_created",
            job_id=job_id,
            video_provider=video_provider.name,
            voice_provider=voice_provider.name,
            language_provider=language_provider.name if language_provider else None,
            expected_quality=quality_score,
            estimated_cost=video_cost + voice_cost,
            needs_audio_merge=needs_merge,
            prompt_aesthetic_score=enhanced_prompt.aesthetic_score.overall_score,
            prompt_concepts=[c.value for c in enhanced_prompt.concepts],
        )
        
        return plan
    
    async def execute_with_fallback(
        self,
        category: ProviderCategory,
        operation: str,
        fallback_chain: List[str],
        execute_fn,
        **kwargs
    ) -> ProviderResult:
        """
        Execute an operation with automatic fallback.
        
        Tries each provider in the fallback chain until one succeeds.
        """
        last_error = None
        
        for provider_name in fallback_chain:
            provider_info = self.registry.get_provider_info(provider_name)
            if not provider_info or not provider_info.is_available:
                continue
            
            start_time = time.perf_counter()
            
            try:
                logger.info(
                    f"{operation}_attempting",
                    provider=provider_name,
                    category=category.value
                )
                
                result = await execute_fn(provider_name, **kwargs)
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                cost = provider_info.cost_per_unit * kwargs.get("duration", 1)
                
                # Update stats
                self.registry.update_stats(provider_name, latency_ms, True, cost)
                
                logger.info(
                    f"{operation}_success",
                    provider=provider_name,
                    latency_ms=latency_ms
                )
                
                return ProviderResult(
                    success=True,
                    provider_name=provider_name,
                    data=result,
                    latency_ms=latency_ms,
                    cost=cost,
                    metadata={"quality_score": provider_info.quality_score}
                )
                
            except Exception as e:
                last_error = str(e)
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # Update stats
                self.registry.update_stats(provider_name, latency_ms, False, 0)
                
                logger.warning(
                    f"{operation}_failed",
                    provider=provider_name,
                    error=last_error,
                    trying_next=True
                )
                continue
        
        # All providers failed
        return ProviderResult(
            success=False,
            provider_name="none",
            data=None,
            latency_ms=0,
            cost=0,
            error=last_error or "All providers failed"
        )
    
    async def execute_plan(
        self,
        plan: GenerationPlan,
        progress_callback=None
    ) -> GenerationResult:
        """
        Execute a generation plan.
        
        This is the main pipeline that:
        1. Detects language
        2. Generates speech
        3. Generates video
        4. Merges if needed
        """
        start_time = datetime.utcnow()
        
        detected_language = None
        audio_path = None
        video_path = None
        final_video_url = None
        
        try:
            # Step 1: Language Detection
            if plan.request.detect_language and progress_callback:
                await progress_callback(JobStatus.DETECTING_LANGUAGE, 10, "Detecting language...")
            
            if plan.request.detect_language:
                detector = get_language_detector()
                lang_result = await detector.detect(plan.request.prompt)
                detected_language = lang_result.detected_language
                
                logger.info(
                    "language_detected",
                    language=detected_language.code,
                    confidence=detected_language.confidence,
                    provider=plan.language_provider.name
                )
            
            # Step 2: Generate Speech
            if progress_callback:
                await progress_callback(
                    JobStatus.GENERATING_SPEECH, 25,
                    f"Generating speech with {plan.voice_provider.name}..."
                )
            
            async def generate_speech(provider_name: str, **kwargs):
                voice_service = get_voice_service()
                return await voice_service.synthesize_speech(
                    text=plan.request.prompt,
                    voice_id=plan.request.voice_id,
                    language=detected_language.code if detected_language else None
                )
            
            speech_result = await self.execute_with_fallback(
                ProviderCategory.VOICE,
                "speech_generation",
                plan.voice_fallbacks,
                generate_speech,
                duration=len(plan.request.prompt) / 15
            )
            
            if not speech_result.success:
                raise Exception(f"Speech generation failed: {speech_result.error}")
            
            audio_url = speech_result.data.audio_url
            
            # Step 3: Generate Video (using enhanced prompt)
            if progress_callback:
                await progress_callback(
                    JobStatus.GENERATING_VIDEO, 50,
                    f"Generating video with {plan.video_provider.name}... (2-5 min)"
                )
            
            # Use the enhanced prompt for video generation
            video_prompt = plan.enhanced_prompt.enhanced_prompt if plan.enhanced_prompt else plan.request.prompt
            negative_prompt = plan.enhanced_prompt.negative_prompt if plan.enhanced_prompt else ""
            
            async def generate_video(provider_name: str, **kwargs):
                video_service = get_video_service()
                return await video_service.generate_video(
                    prompt=video_prompt,
                    negative_prompt=negative_prompt,
                    duration=plan.request.video_duration,
                    aspect_ratio=plan.request.aspect_ratio,
                    resolution=plan.request.resolution,
                    style=plan.request.video_style
                )
            
            video_result = await self.execute_with_fallback(
                ProviderCategory.VIDEO,
                "video_generation",
                plan.video_fallbacks,
                generate_video,
                duration=plan.request.video_duration
            )
            
            if not video_result.success:
                raise Exception(f"Video generation failed: {video_result.error}")
            
            video_url = video_result.data.video_url
            has_native_audio = video_result.data.has_audio
            
            # Step 4: Merge Audio/Video (if needed)
            if plan.needs_audio_merge and not has_native_audio:
                if progress_callback:
                    await progress_callback(
                        JobStatus.MERGING, 85,
                        "Merging audio and video..."
                    )
                
                processor = get_media_processor()
                
                # Get actual file paths from URLs
                storage_path = settings.local_storage_path
                video_file = f"{storage_path}/{video_url.lstrip('/static/')}"
                audio_file = f"{storage_path}/{audio_url.lstrip('/static/')}"
                
                # Adjust audio length
                adjusted_audio = await processor.adjust_audio_length(
                    audio_file,
                    plan.request.video_duration
                )
                
                # Merge
                output_filename = f"final_{plan.job_id}.mp4"
                output_path = f"{storage_path}/outputs/{output_filename}"
                
                await processor.merge_audio_video(
                    video_path=video_file,
                    audio_path=adjusted_audio,
                    output_path=output_path
                )
                
                final_video_url = f"/static/outputs/{output_filename}"
            else:
                final_video_url = video_url
            
            # Generate thumbnail
            processor = get_media_processor()
            video_file = f"{settings.local_storage_path}/{video_url.lstrip('/static/')}"
            thumb_path = await processor.generate_thumbnail(video_file)
            thumb_url = f"/static/outputs/{thumb_path.split('/')[-1]}"
            
            # Calculate final metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            total_cost = speech_result.cost + video_result.cost
            
            # Mark job complete
            if progress_callback:
                await progress_callback(
                    JobStatus.COMPLETED, 100,
                    f"Complete! Generated with {video_result.provider_name}"
                )
            
            return GenerationResult(
                job_id=plan.job_id,
                status=JobStatus.COMPLETED,
                video_url=final_video_url,
                audio_url=audio_url,
                thumbnail_url=thumb_url,
                duration_seconds=float(plan.request.video_duration),
                detected_language=detected_language,
                processing_time_seconds=processing_time,
                cost_estimate=total_cost,
                metadata={
                    "video_provider": video_result.provider_name,
                    "video_provider_quality": video_result.metadata.get("quality_score"),
                    "voice_provider": speech_result.provider_name,
                    "voice_provider_quality": speech_result.metadata.get("quality_score"),
                    "language_provider": plan.language_provider.name if plan.language_provider else None,
                    "resolution": plan.request.resolution,
                    "aspect_ratio": plan.request.aspect_ratio,
                    "had_native_audio": has_native_audio if 'has_native_audio' in dir() else False,
                    "used_fallback": video_result.provider_name != plan.video_provider.name,
                }
            )
            
        except Exception as e:
            logger.error("generation_failed", job_id=plan.job_id, error=str(e))
            
            if progress_callback:
                await progress_callback(JobStatus.FAILED, 0, str(e))
            
            raise
    
    def get_plan(self, job_id: str) -> Optional[GenerationPlan]:
        """Get the plan for a job."""
        return self._active_jobs.get(job_id)
    
    def get_provider_recommendations(
        self,
        request: FullGenerationRequest
    ) -> Dict[str, List[Dict]]:
        """
        Get provider recommendations for a request.
        
        Useful for showing users their options before generating.
        """
        recommendations = {
            "video": [],
            "voice": [],
        }
        
        # Get video providers
        video_providers = self.registry.list_providers(ProviderCategory.VIDEO)
        for provider in video_providers[:5]:  # Top 5
            est_cost = provider.cost_per_unit * request.video_duration
            recommendations["video"].append({
                "name": provider.name,
                "quality_tier": provider.quality_tier.value,
                "quality_score": provider.quality_score,
                "estimated_cost": round(est_cost, 2),
                "has_native_audio": provider.supports_audio,
                "max_duration": provider.max_duration,
            })
        
        # Get voice providers
        voice_providers = self.registry.list_providers(ProviderCategory.VOICE)
        for provider in voice_providers[:5]:
            est_cost = provider.cost_per_unit * (len(request.prompt) / 1000)
            recommendations["voice"].append({
                "name": provider.name,
                "quality_tier": provider.quality_tier.value,
                "quality_score": provider.quality_score,
                "estimated_cost": round(est_cost, 2),
                "supports_cloning": provider.features.get("voice_cloning", False),
            })
        
        return recommendations


# Global orchestrator instance
_orchestrator: Optional[SmartOrchestrator] = None


def get_orchestrator() -> SmartOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartOrchestrator()
    return _orchestrator
