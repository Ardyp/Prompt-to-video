"""
Provider Registry - 2026 State-of-the-Art Models

Updated with the latest text-to-video AI models as of January 2026:
- Google Veo 3.1: 4K, 2+ minutes, native audio (BEST for cinematic)
- OpenAI Sora 2: 20s, photorealistic, character consistency (BEST for realism)
- Runway Gen-4: 16s videos, precise camera control
- Kling AI 1.6: 2 minutes, lip-sync, facial motion (BEST for volume)
- Pika 2.5: Enhanced stylized content
- Luma Dream Machine Ray 2: Improved physics

This module provides:
1. Auto-registration of latest AI providers
2. Quality-based ranking (2026 benchmarks)
3. Automatic fallback chains
4. Native audio detection and routing
5. Cost optimization
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class ProviderCategory(str, Enum):
    """Categories of AI providers."""
    VIDEO = "video"
    VOICE = "voice"
    LANGUAGE = "language"


class QualityTier(str, Enum):
    """Quality tiers for ranking providers."""
    PREMIUM = "premium"      # Best quality, highest cost (Veo 3.1, Sora 2)
    STANDARD = "standard"    # Good quality, moderate cost (Runway, Kling)
    BUDGET = "budget"        # Acceptable quality, low cost (Pika)
    EXPERIMENTAL = "experimental"  # New/beta models


@dataclass
class ProviderInfo:
    """Information about a registered provider."""
    name: str
    category: ProviderCategory
    quality_tier: QualityTier
    quality_score: float  # 0-100, higher is better (2026 benchmarks)
    cost_per_unit: float  # Cost per second (video) or per 1k chars (voice)
    max_duration: Optional[int] = None  # Max video duration in seconds
    supports_audio: bool = False  # Native audio generation
    supports_4k: bool = False  # 4K resolution support
    languages: List[str] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    last_checked: Optional[datetime] = None
    avg_latency_ms: Optional[float] = None
    success_rate: float = 1.0


@dataclass
class ProviderResult:
    """Result from a provider operation."""
    success: bool
    provider_name: str
    data: Any
    latency_ms: float
    cost: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderRegistry:
    """
    Central registry for all AI providers.

    Updated January 2026 with state-of-the-art models.

    Handles:
    - Provider registration and discovery
    - Quality-based selection (2026 benchmarks)
    - Automatic fallbacks
    - Health monitoring
    - Cost tracking
    - Native audio routing
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._providers: Dict[str, Dict[str, ProviderInfo]] = {
            ProviderCategory.VIDEO: {},
            ProviderCategory.VOICE: {},
            ProviderCategory.LANGUAGE: {},
        }
        self._provider_classes: Dict[str, Type] = {}
        self._fallback_chains: Dict[str, List[str]] = {}
        self._usage_stats: Dict[str, Dict[str, Any]] = {}

        self._initialized = True
        self._register_default_providers()

    def _register_default_providers(self):
        """Register all known providers with 2026 quality rankings."""

        # ============================================================
        # VIDEO PROVIDERS - Ranked by 2026 benchmarks
        # ============================================================

        # TIER: PREMIUM - Best of the Best (2026)

        # Google Veo 3.1 - BEST for Cinematic Quality
        self.register_provider(ProviderInfo(
            name="veo_3.1",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.PREMIUM,
            quality_score=98,  # 2026: Leads in 4K and temporal consistency
            cost_per_unit=0.45,  # $249/month subscription (~$0.45/sec estimated)
            max_duration=120,  # 2+ minutes
            supports_audio=True,  # Native audio trained on YouTube data
            supports_4k=True,  # 4K photorealistic output
            features={
                "resolutions": ["720p", "1080p", "4K"],
                "aspect_ratios": ["16:9", "9:16", "1:1", "21:9"],
                "native_audio": True,
                "audio_types": ["dialogue", "sound_effects", "music"],
                "temporal_consistency": "best",
                "cinematic_motion": True,
                "polished_camera_work": True,
                "training_data": "YouTube",
                "subscription": "$249/month",
            }
        ))

        # OpenAI Sora 2 - BEST for Realism & Narrative
        self.register_provider(ProviderInfo(
            name="sora_2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.PREMIUM,
            quality_score=97,  # 2026: Best physics and character consistency
            cost_per_unit=0.35,  # ChatGPT Plus $20/month or Pro $200/month
            max_duration=20,  # 20 seconds
            supports_audio=True,  # Native audio with synchronized speech
            supports_4k=False,  # 1080p max
            features={
                "resolutions": ["720p", "1080p"],
                "physics_accuracy": "best",
                "character_consistency": "best",
                "narrative_coherence": "best",
                "synchronized_speech": True,
                "photorealistic": True,
                "native_audio": True,
                "subscription_tiers": ["Plus $20/mo", "Pro $200/mo"],
            }
        ))

        # Runway Gen-4 - BEST for Creative Control
        self.register_provider(ProviderInfo(
            name="runway_gen4",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.PREMIUM,
            quality_score=92,  # 2026: Most flexible for creative work
            cost_per_unit=0.08,  # $12+/month subscription
            max_duration=16,  # Gen-4: 16 seconds
            supports_audio=False,  # Audio handled in post
            supports_4k=True,  # 4K support
            features={
                "resolutions": ["720p", "1080p", "4K"],
                "precise_camera_control": True,
                "start_end_frame_control": True,
                "smooth_looping": True,
                "stylized_creativity": "best",
                "vfx_friendly": True,
                "motion_brush": True,
                "director_mode": True,
                "subscription": "from $12/month",
            }
        ))

        # Runway Gen-3 Alpha Turbo - Fast Version
        self.register_provider(ProviderInfo(
            name="runway_gen3_turbo",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=89,
            cost_per_unit=0.05,
            max_duration=10,  # 5-10 seconds
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p", "1080p"],
                "fast_generation": True,
                "stylized_content": True,
                "iteration_speed": "fastest",
            }
        ))

        # Kling AI 1.6 - BEST for Volume Production
        self.register_provider(ProviderInfo(
            name="kling_1.6",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=88,  # 2026: Best for high-volume content
            cost_per_unit=0.11,
            max_duration=120,  # 2 minutes
            supports_audio=True,  # Lip-sync and facial motion
            supports_4k=False,
            features={
                "resolutions": ["720p", "1080p"],
                "lip_sync": True,
                "facial_motion": "advanced",
                "high_volume_production": True,
                "ugc_optimized": True,
                "motion_fidelity": "high",
                "developer": "ByteDance",
                "consistency": "best_for_volume",
            }
        ))

        # Luma Dream Machine Ray 2 - Physics Master
        self.register_provider(ProviderInfo(
            name="luma_ray2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=85,  # 2026: Best physics simulation
            cost_per_unit=0.18,
            max_duration=9,
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p", "1080p"],
                "physics_simulation": "best",
                "realistic_motion": True,
                "natural_movement": True,
                "object_permanence": True,
            }
        ))

        # Pika 2.5 - Budget Friendly
        self.register_provider(ProviderInfo(
            name="pika_2.5",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.BUDGET,
            quality_score=80,  # 2026: Good for social media
            cost_per_unit=0.06,
            max_duration=5,
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p", "1080p"],
                "style_variety": "excellent",
                "social_ready": True,
                "free_tier": True,
                "fast_iteration": True,
                "creator_focused": True,
            }
        ))

        # Open Source Models (Self-Hosted)

        self.register_provider(ProviderInfo(
            name="hunyuan_video",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=84,  # 2026: Best open-source model
            cost_per_unit=0.0,  # Self-hosted
            max_duration=30,
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p", "1080p"],
                "open_source": True,
                "self_hosted": True,
                "13b_parameters": True,
                "huggingface": True,
                "commercial_use": True,
            }
        ))

        self.register_provider(ProviderInfo(
            name="mochi_1",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=82,
            cost_per_unit=0.0,
            max_duration=30,
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p"],
                "open_source": True,
                "self_hosted": True,
                "10b_parameters": True,
                "apache_license": True,
            }
        ))

        self.register_provider(ProviderInfo(
            name="cogvideox",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.BUDGET,
            quality_score=78,
            cost_per_unit=0.0,
            max_duration=10,
            supports_audio=False,
            supports_4k=False,
            features={
                "resolutions": ["720p"],
                "open_source": True,
                "self_hosted": True,
                "tsinghua_university": True,
            }
        ))

        # ============================================================
        # VOICE PROVIDERS - Ranked by 2026 quality
        # ============================================================

        # Fish Audio - #1 on TTS-Arena 2026
        self.register_provider(ProviderInfo(
            name="fish_audio",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=96,  # #1 on TTS-Arena leaderboard
            cost_per_unit=0.015,  # Best value
            languages=["en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru", "ar", "hi"] + ["+50 more"],
            features={
                "voice_cloning": True,
                "clone_time": "15s",
                "emotion_tags": True,
                "tts_arena_rank": 1,
                "multilingual": "60+ languages",
                "best_value": True,
            }
        ))

        # ElevenLabs - Premium Quality
        self.register_provider(ProviderInfo(
            name="elevenlabs",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=95,
            cost_per_unit=0.30,
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "hi", "ar"] + ["+20 more"],
            features={
                "voice_cloning": True,
                "clone_time": "60s",
                "emotion_control": "advanced",
                "multilingual": "30+ languages",
                "voice_lab": True,
                "projects": True,
            }
        ))

        # Cartesia - Low Latency Champion
        self.register_provider(ProviderInfo(
            name="cartesia",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=93,
            cost_per_unit=0.025,
            features={
                "voice_cloning": True,
                "low_latency": "best",
                "streaming": True,
                "realtime": True,
                "sonic": "fastest_model",
            }
        ))

        # Resemble AI - Enterprise Grade
        self.register_provider(ProviderInfo(
            name="resemble_ai",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=92,
            cost_per_unit=0.02,
            features={
                "voice_cloning": True,
                "clone_time": "10s",
                "on_premise": True,
                "speech_to_speech": True,
                "enterprise_sla": True,
            }
        ))

        # Open Source - Chatterbox (Beats ElevenLabs in blind tests)
        self.register_provider(ProviderInfo(
            name="chatterbox",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.STANDARD,
            quality_score=90,  # Beats ElevenLabs in blind tests
            cost_per_unit=0.0,
            languages=["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th"],
            features={
                "open_source": True,
                "mit_license": True,
                "clone_time": "5s",
                "self_hosted": True,
                "beats_elevenlabs": True,
            }
        ))

        # ============================================================
        # LANGUAGE DETECTION PROVIDERS
        # ============================================================

        self.register_provider(ProviderInfo(
            name="lingua",
            category=ProviderCategory.LANGUAGE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=95,
            cost_per_unit=0.0,
            languages=["75 languages"],
            features={
                "open_source": True,
                "short_text_accuracy": "best",
                "ngram_sizes": [1, 2, 3, 4, 5],
            }
        ))

        self.register_provider(ProviderInfo(
            name="google_cloud",
            category=ProviderCategory.LANGUAGE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=92,
            cost_per_unit=0.00002,
            languages=["120+ languages"],
            features={
                "enterprise": True,
                "batch_support": True,
            }
        ))

        # Build default fallback chains
        self._build_fallback_chains()

    def _build_fallback_chains(self):
        """Build fallback chains based on quality rankings."""
        for category in ProviderCategory:
            providers = self._providers[category]
            # Sort by quality score descending
            sorted_providers = sorted(
                providers.values(),
                key=lambda p: p.quality_score,
                reverse=True
            )
            self._fallback_chains[category.value] = [p.name for p in sorted_providers]

    def register_provider(self, info: ProviderInfo):
        """Register a provider."""
        self._providers[info.category][info.name] = info
        logger.info(
            "provider_registered",
            name=info.name,
            category=info.category.value,
            quality=info.quality_score
        )

    def get_best_provider(
        self,
        category: ProviderCategory,
        min_quality: float = 0,
        max_cost: Optional[float] = None,
        required_features: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        prefer_native_audio: bool = False
    ) -> Optional[ProviderInfo]:
        """
        Get the best available provider for a category.

        Args:
            category: Provider category
            min_quality: Minimum quality score (0-100)
            max_cost: Maximum cost per unit
            required_features: Features the provider must support
            exclude: Provider names to exclude
            prefer_native_audio: Prefer providers with native audio (2026)

        Returns:
            Best matching provider or None
        """
        providers = list(self._providers[category].values())

        # Filter by availability
        providers = [p for p in providers if p.is_available]

        # Prefer native audio if requested
        if prefer_native_audio and category == ProviderCategory.VIDEO:
            audio_providers = [p for p in providers if p.supports_audio]
            if audio_providers:
                providers = audio_providers

        # Filter by quality
        if min_quality > 0:
            providers = [p for p in providers if p.quality_score >= min_quality]

        # Filter by cost
        if max_cost is not None:
            providers = [p for p in providers if p.cost_per_unit <= max_cost]

        # Filter by features
        if required_features:
            providers = [
                p for p in providers
                if all(f in p.features for f in required_features)
            ]

        # Exclude specific providers
        if exclude:
            providers = [p for p in providers if p.name not in exclude]

        if not providers:
            return None

        # Sort by quality score and return best
        providers.sort(key=lambda p: p.quality_score, reverse=True)
        return providers[0]

    def get_fallback_chain(
        self,
        category: ProviderCategory,
        primary: Optional[str] = None
    ) -> List[str]:
        """
        Get fallback chain for a category.

        Args:
            category: Provider category
            primary: Primary provider (will be first in chain)

        Returns:
            Ordered list of provider names
        """
        chain = self._fallback_chains.get(category.value, [])

        if primary and primary in chain:
            # Move primary to front
            chain = [primary] + [p for p in chain if p != primary]

        return chain

    def get_provider_info(self, name: str) -> Optional[ProviderInfo]:
        """Get info for a specific provider."""
        for category in ProviderCategory:
            if name in self._providers[category]:
                return self._providers[category][name]
        return None

    def list_providers(
        self,
        category: Optional[ProviderCategory] = None,
        tier: Optional[QualityTier] = None
    ) -> List[ProviderInfo]:
        """List providers with optional filtering."""
        result = []

        categories = [category] if category else list(ProviderCategory)

        for cat in categories:
            for provider in self._providers[cat].values():
                if tier is None or provider.quality_tier == tier:
                    result.append(provider)

        return sorted(result, key=lambda p: p.quality_score, reverse=True)

    async def health_check(self, provider_name: str) -> bool:
        """Check if a provider is healthy/available."""
        info = self.get_provider_info(provider_name)
        return info.is_available if info else False

    def update_stats(
        self,
        provider_name: str,
        latency_ms: float,
        success: bool,
        cost: float
    ):
        """Update usage statistics for a provider."""
        if provider_name not in self._usage_stats:
            self._usage_stats[provider_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_cost": 0.0,
                "avg_latency_ms": 0.0,
            }

        stats = self._usage_stats[provider_name]
        stats["total_requests"] += 1
        if success:
            stats["successful_requests"] += 1
        stats["total_cost"] += cost

        # Update rolling average latency
        n = stats["total_requests"]
        stats["avg_latency_ms"] = (
            (stats["avg_latency_ms"] * (n - 1) + latency_ms) / n
        )

        # Update provider info
        info = self.get_provider_info(provider_name)
        if info:
            info.success_rate = stats["successful_requests"] / stats["total_requests"]
            info.avg_latency_ms = stats["avg_latency_ms"]

    def get_usage_stats(self, provider_name: Optional[str] = None) -> Dict:
        """Get usage statistics."""
        if provider_name:
            return self._usage_stats.get(provider_name, {})
        return self._usage_stats

    def get_recommendations(self, use_case: str) -> Dict[str, str]:
        """
        Get provider recommendations based on use case (2026).

        Args:
            use_case: One of: "cinematic", "realism", "creative", "volume", "budget"

        Returns:
            Dict with recommended providers for different aspects
        """
        recommendations = {
            "cinematic": {
                "video": "veo_3.1",
                "reason": "4K, best temporal consistency, native audio, polished camera work",
                "alternative": "runway_gen4"
            },
            "realism": {
                "video": "sora_2",
                "reason": "Best physics accuracy, character consistency, photorealistic",
                "alternative": "veo_3.1"
            },
            "creative": {
                "video": "runway_gen4",
                "reason": "Most flexible, precise camera control, VFX-friendly",
                "alternative": "runway_gen3_turbo"
            },
            "volume": {
                "video": "kling_1.6",
                "reason": "2min videos, lip-sync, best for high-volume UGC",
                "alternative": "pika_2.5"
            },
            "budget": {
                "video": "pika_2.5",
                "reason": "Low cost, free tier, good for social media",
                "alternative": "hunyuan_video"
            }
        }

        return recommendations.get(use_case, recommendations["cinematic"])


# Global registry instance
registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return registry
