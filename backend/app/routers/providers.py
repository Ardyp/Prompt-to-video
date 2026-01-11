"""
Provider Management API Router

Endpoints for:
- Listing available providers
- Checking provider health
- Getting recommendations
- Viewing usage statistics
- Admin: Enable/disable providers
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.provider_registry import (
    ProviderCategory,
    QualityTier,
    get_registry,
)
from app.services.orchestrator import get_orchestrator
from app.models import FullGenerationRequest

router = APIRouter()


@router.get("/providers")
async def list_providers(
    category: Optional[str] = Query(None, description="Filter by category: video, voice, language"),
    tier: Optional[str] = Query(None, description="Filter by tier: premium, standard, budget"),
    available_only: bool = Query(True, description="Only show available providers")
):
    """
    List all registered AI providers.
    
    Returns providers sorted by quality score (highest first).
    
    **Example Response:**
    ```json
    {
        "providers": [
            {
                "name": "veo3",
                "category": "video",
                "quality_tier": "premium",
                "quality_score": 95,
                "cost_per_unit": 0.40,
                "is_available": true,
                "features": {...}
            }
        ]
    }
    ```
    """
    registry = get_registry()
    
    # Parse filters
    cat_filter = ProviderCategory(category) if category else None
    tier_filter = QualityTier(tier) if tier else None
    
    providers = registry.list_providers(category=cat_filter, tier=tier_filter)
    
    if available_only:
        providers = [p for p in providers if p.is_available]
    
    return {
        "providers": [
            {
                "name": p.name,
                "category": p.category.value,
                "quality_tier": p.quality_tier.value,
                "quality_score": p.quality_score,
                "cost_per_unit": p.cost_per_unit,
                "max_duration": p.max_duration,
                "supports_audio": p.supports_audio,
                "is_available": p.is_available,
                "success_rate": p.success_rate,
                "avg_latency_ms": p.avg_latency_ms,
                "features": p.features,
            }
            for p in providers
        ],
        "total": len(providers)
    }


@router.get("/providers/{provider_name}")
async def get_provider_details(provider_name: str):
    """
    Get detailed information about a specific provider.
    """
    registry = get_registry()
    provider = registry.get_provider_info(provider_name)
    
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    return {
        "name": provider.name,
        "category": provider.category.value,
        "quality_tier": provider.quality_tier.value,
        "quality_score": provider.quality_score,
        "cost_per_unit": provider.cost_per_unit,
        "max_duration": provider.max_duration,
        "supports_audio": provider.supports_audio,
        "languages": provider.languages,
        "is_available": provider.is_available,
        "success_rate": provider.success_rate,
        "avg_latency_ms": provider.avg_latency_ms,
        "features": provider.features,
        "last_checked": provider.last_checked,
    }


@router.get("/providers/{provider_name}/health")
async def check_provider_health(provider_name: str):
    """
    Check the health status of a provider.
    """
    registry = get_registry()
    provider = registry.get_provider_info(provider_name)
    
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    is_healthy = await registry.health_check(provider_name)
    
    return {
        "provider": provider_name,
        "is_healthy": is_healthy,
        "is_available": provider.is_available,
        "success_rate": provider.success_rate,
        "avg_latency_ms": provider.avg_latency_ms,
    }


@router.get("/recommendations")
async def get_recommendations(
    prompt: str = Query(..., min_length=10, description="The prompt to generate"),
    duration: int = Query(8, ge=4, le=60, description="Video duration in seconds"),
    aspect_ratio: str = Query("16:9", description="Aspect ratio"),
    resolution: str = Query("720p", description="Resolution"),
):
    """
    Get provider recommendations for a generation request.
    
    Shows the top providers for video and voice, with estimated costs.
    """
    orchestrator = get_orchestrator()
    
    request = FullGenerationRequest(
        prompt=prompt,
        video_duration=duration,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        detect_language=True,
    )
    
    recommendations = orchestrator.get_provider_recommendations(request)
    
    # Calculate total estimates for best combination
    best_video = recommendations["video"][0] if recommendations["video"] else None
    best_voice = recommendations["voice"][0] if recommendations["voice"] else None
    
    total_cost = 0
    if best_video:
        total_cost += best_video["estimated_cost"]
    if best_voice:
        total_cost += best_voice["estimated_cost"]
    
    return {
        "recommendations": recommendations,
        "best_combination": {
            "video": best_video["name"] if best_video else None,
            "voice": best_voice["name"] if best_voice else None,
            "total_estimated_cost": round(total_cost, 2),
            "needs_audio_merge": not best_video.get("has_native_audio", False) if best_video else True,
        }
    }


@router.get("/fallback-chains")
async def get_fallback_chains():
    """
    Get the fallback chains for each category.
    
    Shows the order in which providers will be tried if the primary fails.
    """
    registry = get_registry()
    
    chains = {}
    for category in ProviderCategory:
        chain = registry.get_fallback_chain(category)
        chains[category.value] = chain
    
    return {"fallback_chains": chains}


@router.get("/stats")
async def get_usage_statistics(provider_name: Optional[str] = None):
    """
    Get usage statistics for providers.
    
    Shows total requests, success rates, costs, and latencies.
    """
    registry = get_registry()
    stats = registry.get_usage_stats(provider_name)
    
    return {"statistics": stats}


@router.get("/compare")
async def compare_providers(
    providers: str = Query(..., description="Comma-separated provider names"),
    duration: int = Query(10, description="Video duration for cost comparison"),
    prompt_length: int = Query(200, description="Prompt length for voice cost")
):
    """
    Compare multiple providers side-by-side.
    
    **Example:** `/compare?providers=veo3,sora2,runway_gen3&duration=10`
    """
    registry = get_registry()
    provider_names = [p.strip() for p in providers.split(",")]
    
    comparisons = []
    for name in provider_names:
        provider = registry.get_provider_info(name)
        if not provider:
            continue
        
        # Calculate costs based on category
        if provider.category == ProviderCategory.VIDEO:
            cost = provider.cost_per_unit * duration
        elif provider.category == ProviderCategory.VOICE:
            cost = provider.cost_per_unit * (prompt_length / 1000)
        else:
            cost = 0
        
        comparisons.append({
            "name": provider.name,
            "category": provider.category.value,
            "quality_score": provider.quality_score,
            "quality_tier": provider.quality_tier.value,
            "estimated_cost": round(cost, 2),
            "max_duration": provider.max_duration,
            "supports_audio": provider.supports_audio,
            "success_rate": provider.success_rate,
            "features": list(provider.features.keys()),
        })
    
    # Sort by quality score
    comparisons.sort(key=lambda x: x["quality_score"], reverse=True)
    
    return {
        "comparison": comparisons,
        "best_quality": comparisons[0]["name"] if comparisons else None,
        "best_value": min(comparisons, key=lambda x: x["estimated_cost"])["name"] if comparisons else None,
    }


@router.post("/providers/{provider_name}/enable")
async def enable_provider(provider_name: str):
    """
    Enable a provider (admin endpoint).
    """
    registry = get_registry()
    provider = registry.get_provider_info(provider_name)
    
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    provider.is_available = True
    
    return {"status": "enabled", "provider": provider_name}


@router.post("/providers/{provider_name}/disable")
async def disable_provider(provider_name: str):
    """
    Disable a provider (admin endpoint).
    """
    registry = get_registry()
    provider = registry.get_provider_info(provider_name)
    
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    provider.is_available = False
    
    return {"status": "disabled", "provider": provider_name}


@router.get("/quality-tiers")
async def get_quality_tiers():
    """
    Get information about quality tiers.
    """
    return {
        "tiers": [
            {
                "name": "premium",
                "description": "Highest quality output, best for production use",
                "quality_range": "90-100",
                "typical_cost": "Higher",
                "examples": ["veo3", "sora2", "elevenlabs", "fish_audio"]
            },
            {
                "name": "standard",
                "description": "Good quality, balanced cost-performance",
                "quality_range": "75-89",
                "typical_cost": "Moderate",
                "examples": ["runway_gen3", "kling_2.1", "playht", "chatterbox"]
            },
            {
                "name": "budget",
                "description": "Acceptable quality, lowest cost",
                "quality_range": "60-74",
                "typical_cost": "Low",
                "examples": ["pika_2.2", "xtts_v2"]
            },
            {
                "name": "experimental",
                "description": "New or beta models, quality may vary",
                "quality_range": "Variable",
                "typical_cost": "Variable",
                "examples": []
            }
        ]
    }
