"""
Provider Registry - Quality-First Model Selection

This module provides:
1. Auto-registration of AI providers
2. Quality-based ranking and selection
3. Automatic fallback chains
4. A/B testing support
5. Cost tracking per provider

Design Philosophy: Always use the BEST available model, with graceful degradation.
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
    PREMIUM = "premium"      # Best quality, highest cost
    STANDARD = "standard"    # Good quality, moderate cost
    BUDGET = "budget"        # Acceptable quality, low cost
    EXPERIMENTAL = "experimental"  # New/beta models


@dataclass
class ProviderInfo:
    """Information about a registered provider."""
    name: str
    category: ProviderCategory
    quality_tier: QualityTier
    quality_score: float  # 0-100, higher is better
    cost_per_unit: float  # Cost per second (video) or per 1k chars (voice)
    max_duration: Optional[int] = None  # Max video duration in seconds
    supports_audio: bool = False  # Native audio generation
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
    
    Handles:
    - Provider registration and discovery
    - Quality-based selection
    - Automatic fallbacks
    - Health monitoring
    - Cost tracking
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
        """Register all known providers with their quality rankings."""
        
        # ============================================================
        # VIDEO PROVIDERS - Ranked by quality (Dec 2025)
        # ============================================================
        
        # Tier: PREMIUM
        self.register_provider(ProviderInfo(
            name="veo3",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.PREMIUM,
            quality_score=95,
            cost_per_unit=0.40,  # per second
            max_duration=60,
            supports_audio=True,  # Native audio!
            features={
                "resolutions": ["720p", "1080p"],
                "aspect_ratios": ["16:9", "9:16", "1:1"],
                "style_control": True,
                "native_audio": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="sora2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.PREMIUM,
            quality_score=96,  # Best physics/realism
            cost_per_unit=0.30,
            max_duration=20,
            supports_audio=True,
            features={
                "resolutions": ["720p", "1080p"],
                "physics_accuracy": "best",
                "character_consistency": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="veo3_fast",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=88,
            cost_per_unit=0.15,
            max_duration=60,
            supports_audio=True,
            features={
                "resolutions": ["720p"],
                "fast_generation": True,
            }
        ))
        
        # Tier: STANDARD
        self.register_provider(ProviderInfo(
            name="runway_gen3",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=85,
            cost_per_unit=0.05,
            max_duration=10,
            supports_audio=False,
            features={
                "resolutions": ["720p", "1080p"],
                "editing_suite": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="kling_2.1",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=82,
            cost_per_unit=0.11,  # ~$0.90 per 8s
            max_duration=10,
            supports_audio=False,
            features={
                "resolutions": ["720p", "1080p"],
                "motion_fidelity": "high",
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="luma_ray2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=80,
            cost_per_unit=0.18,
            max_duration=9,
            supports_audio=False,
            features={
                "physics_simulation": True,
                "realistic_motion": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="pika_2.2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.BUDGET,
            quality_score=75,
            cost_per_unit=0.08,
            max_duration=5,
            supports_audio=False,
            features={
                "style_variety": True,
                "free_tier": True,
            }
        ))
        
        # Open Source
        self.register_provider(ProviderInfo(
            name="wan2.2",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=78,
            cost_per_unit=0.0,  # Self-hosted
            max_duration=30,
            supports_audio=False,
            features={
                "open_source": True,
                "self_hosted": True,
                "moe_architecture": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="hunyuan",
            category=ProviderCategory.VIDEO,
            quality_tier=QualityTier.STANDARD,
            quality_score=80,
            cost_per_unit=0.0,
            max_duration=30,
            supports_audio=False,
            features={
                "open_source": True,
                "13b_parameters": True,
            }
        ))
        
        # ============================================================
        # VOICE PROVIDERS - Ranked by quality
        # ============================================================
        
        self.register_provider(ProviderInfo(
            name="elevenlabs",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=95,
            cost_per_unit=0.30,  # per 1k chars
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "hi", "ar"] + ["+" * 20],
            features={
                "voice_cloning": True,
                "clone_time": "60s",
                "emotion_control": True,
                "multilingual": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="fish_audio",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=94,  # #1 on TTS-Arena
            cost_per_unit=0.015,  # Much cheaper!
            languages=["en", "zh", "ja", "ko", "es", "fr", "de"] + ["+" * 40],
            features={
                "voice_cloning": True,
                "clone_time": "15s",
                "emotion_tags": True,
                "tts_arena_rank": 1,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="cartesia",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=92,
            cost_per_unit=0.025,
            features={
                "voice_cloning": True,
                "low_latency": True,
                "streaming": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="resemble_ai",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=91,
            cost_per_unit=0.02,
            features={
                "voice_cloning": True,
                "clone_time": "10s",
                "on_premise": True,
                "speech_to_speech": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="playht",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.STANDARD,
            quality_score=85,
            cost_per_unit=0.02,
            languages=["142+ languages"],
            features={
                "voice_cloning": True,
                "900_voices": True,
            }
        ))
        
        # Open Source
        self.register_provider(ProviderInfo(
            name="chatterbox",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.STANDARD,
            quality_score=88,  # Beats ElevenLabs in blind tests
            cost_per_unit=0.0,
            languages=["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th"],
            features={
                "open_source": True,
                "mit_license": True,
                "clone_time": "5s",
                "self_hosted": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="xtts_v2",
            category=ProviderCategory.VOICE,
            quality_tier=QualityTier.BUDGET,
            quality_score=78,
            cost_per_unit=0.0,
            features={
                "open_source": True,
                "clone_time": "6s",
            }
        ))
        
        # ============================================================
        # LANGUAGE DETECTION PROVIDERS
        # ============================================================
        
        self.register_provider(ProviderInfo(
            name="lingua",
            category=ProviderCategory.LANGUAGE,
            quality_tier=QualityTier.PREMIUM,
            quality_score=95,  # Best for short text
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
            quality_score=90,
            cost_per_unit=0.00002,  # per character
            languages=["120+ languages"],
            features={
                "enterprise": True,
                "batch_support": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="aws_comprehend",
            category=ProviderCategory.LANGUAGE,
            quality_tier=QualityTier.STANDARD,
            quality_score=85,
            cost_per_unit=0.0001,
            features={
                "enterprise": True,
                "large_documents": True,
            }
        ))
        
        self.register_provider(ProviderInfo(
            name="fasttext",
            category=ProviderCategory.LANGUAGE,
            quality_tier=QualityTier.STANDARD,
            quality_score=82,
            cost_per_unit=0.0,
            languages=["157 languages"],
            features={
                "open_source": True,
                "fastest": True,
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
        exclude: Optional[List[str]] = None
    ) -> Optional[ProviderInfo]:
        """
        Get the best available provider for a category.
        
        Args:
            category: Provider category
            min_quality: Minimum quality score (0-100)
            max_cost: Maximum cost per unit
            required_features: Features the provider must support
            exclude: Provider names to exclude
        
        Returns:
            Best matching provider or None
        """
        providers = list(self._providers[category].values())
        
        # Filter by availability
        providers = [p for p in providers if p.is_available]
        
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
        # Implementation would ping the provider's health endpoint
        # For now, return the stored availability
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


# Global registry instance
registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return registry
