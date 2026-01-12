"""
Prompt Enhancement API Endpoints

This module provides API endpoints for prompt enhancement, including:
- LLM-based enhancement (NEW - 2026 best practices)
- Hybrid enhancement with validation (RECOMMENDED)
- Legacy rule-based enhancement (fallback)
- Knowledge base queries
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import structlog

from app.services.hybrid_prompt_enhancer import (
    get_hybrid_enhancer,
    HybridEnhancementResult
)
from app.services.prompt_enhancer import (
    get_prompt_enhancer,
    KnowledgeBase
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/prompt", tags=["Prompt Enhancement"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class EnhanceRequest(BaseModel):
    """Request for prompt enhancement."""
    prompt: str = Field(..., description="Original user prompt", min_length=5, max_length=2000)
    duration: float = Field(10.0, description="Video duration in seconds", ge=1.0, le=60.0)
    enhancement_method: str = Field(
        "hybrid",
        description="Enhancement method: 'llm', 'hybrid', or 'rule_based'"
    )
    additional_context: Optional[Dict[str, str]] = Field(
        None,
        description="Additional context like style preferences"
    )


class AnalyzeRequest(BaseModel):
    """Request for quick prompt analysis."""
    prompt: str = Field(..., description="Prompt to analyze", min_length=5, max_length=2000)


# =============================================================================
# MAIN ENHANCEMENT ENDPOINTS
# =============================================================================

@router.post("/enhance")
async def enhance_prompt(request: EnhanceRequest):
    """
    Enhance a prompt using the specified method.

    **Methods:**
    - `hybrid` (RECOMMENDED): LLM enhancement + rule-based validation
    - `llm`: Pure LLM-based enhancement (Claude Sonnet 4)
    - `rule_based`: Legacy rule-based enhancement

    **Example:**
    ```json
    {
      "prompt": "Rama breaks Shiva's bow in the hall",
      "duration": 10.0,
      "enhancement_method": "hybrid"
    }
    ```

    **Returns:**
    - Enhanced prompt optimized for video generation
    - Negative prompt (what to avoid)
    - Frame-by-frame guidance for temporal consistency
    - Aesthetic quality scores
    - Cultural notes and validation warnings
    """
    try:
        logger.info(
            "enhance_request",
            prompt=request.prompt[:100],
            method=request.enhancement_method
        )

        # Get the appropriate enhancer
        if request.enhancement_method in ["hybrid", "llm"]:
            enhancer = get_hybrid_enhancer(use_llm=True)
            result = enhancer.enhance(
                request.prompt,
                request.duration,
                request.additional_context
            )

            return {
                "success": True,
                "method": result.enhancement_method,
                "enhanced_prompt": result.enhanced_prompt,
                "negative_prompt": result.negative_prompt,
                "frame_guidance": result.frame_guidance,
                "aesthetic_score": result.aesthetic_score,
                "concepts_detected": result.concepts_detected,
                "styles_detected": result.styles_detected,
                "cultural_notes": result.cultural_notes,
                "technical_specs": result.technical_specs,
                "validation": {
                    "passed": result.validation_passed,
                    "warnings": result.validation_warnings
                },
                "metadata": {
                    "original_prompt": result.original_prompt,
                    "llm_confidence": result.llm_confidence,
                    "llm_reasoning": result.llm_reasoning,
                    "processing_time_ms": result.processing_time_ms,
                    "tokens_used": result.tokens_used,
                    "model_used": result.model_used
                }
            }

        elif request.enhancement_method == "rule_based":
            enhancer = get_prompt_enhancer()
            result = enhancer.enhance(
                request.prompt,
                request.duration,
                request.additional_context
            )

            return {
                "success": True,
                "method": "rule_based",
                "enhanced_prompt": result.enhanced_prompt,
                "negative_prompt": result.negative_prompt,
                "frame_guidance": [
                    {
                        "time_range": f"{f.timestamp_start:.1f}-{f.timestamp_end:.1f}s",
                        "focus": ", ".join(f.focus_elements),
                        "motion": f.motion_direction,
                        "transition": f.transition_from_previous
                    }
                    for f in result.frame_prompts
                ],
                "aesthetic_score": {
                    "overall": result.aesthetic_score.overall_score,
                    "composition": result.aesthetic_score.composition_score,
                    "clarity": result.aesthetic_score.clarity_score,
                    "creativity": result.aesthetic_score.creativity_score,
                    "technical": result.aesthetic_score.technical_score,
                    "cultural": result.aesthetic_score.cultural_accuracy_score,
                    "motion": result.aesthetic_score.motion_potential_score,
                    "audio": result.aesthetic_score.audio_sync_score
                },
                "concepts_detected": [
                    {
                        "type": c.type.value,
                        "value": c.value,
                        "confidence": c.confidence
                    }
                    for c in result.concepts
                ],
                "styles_detected": [
                    {
                        "category": s.category.value,
                        "value": s.value,
                        "confidence": s.confidence
                    }
                    for s in result.styles
                ],
                "metadata": {
                    "original_prompt": result.original_prompt,
                    "enhancement_iterations": result.enhancement_iterations,
                    "final_confidence": result.final_confidence
                }
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enhancement_method: {request.enhancement_method}. "
                       f"Use 'hybrid', 'llm', or 'rule_based'."
            )

    except RuntimeError as e:
        # LLM not available, fallback to rule-based
        logger.warning("llm_unavailable_fallback", error=str(e))

        enhancer = get_prompt_enhancer()
        result = enhancer.enhance(
            request.prompt,
            request.duration,
            request.additional_context
        )

        return {
            "success": True,
            "method": "rule_based_fallback",
            "message": "LLM unavailable, used rule-based fallback",
            "enhanced_prompt": result.enhanced_prompt,
            "negative_prompt": result.negative_prompt,
            "aesthetic_score": {
                "overall": result.aesthetic_score.overall_score
            }
        }

    except Exception as e:
        logger.error("enhancement_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )


@router.post("/analyze")
async def analyze_prompt(request: AnalyzeRequest):
    """
    Quick prompt analysis without full enhancement.

    Provides:
    - Detected concepts and styles
    - Aesthetic quality prediction
    - Suggestions for improvement

    Useful for giving users feedback before generating video.
    """
    try:
        from app.services.prompt_enhancer import (
            ConceptExtractor,
            StyleExtractor,
            AestheticScorer
        )

        extractor = ConceptExtractor()
        style_extractor = StyleExtractor()
        scorer = AestheticScorer()

        # Extract and analyze
        concepts = extractor.extract(request.prompt)
        styles = style_extractor.extract(request.prompt, concepts)
        score = scorer.score(request.prompt, concepts, styles)

        return {
            "success": True,
            "concepts": [
                {
                    "type": c.type.value,
                    "value": c.value,
                    "confidence": c.confidence,
                    "cultural_context": c.cultural_context
                }
                for c in concepts
            ],
            "styles": [
                {
                    "category": s.category.value,
                    "value": s.value,
                    "confidence": s.confidence
                }
                for s in styles
            ],
            "aesthetic_score": {
                "overall": score.overall_score,
                "composition": score.composition_score,
                "clarity": score.clarity_score,
                "creativity": score.creativity_score,
                "technical": score.technical_score,
                "cultural": score.cultural_accuracy_score,
                "motion": score.motion_potential_score,
                "audio": score.audio_sync_score
            },
            "strengths": score.strengths,
            "suggestions": score.suggestions,
            "is_ready": score.overall_score >= 70
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# KNOWLEDGE BASE ENDPOINTS
# =============================================================================

@router.get("/knowledge/entities")
async def list_cultural_entities():
    """
    List all known cultural entities in the knowledge base.

    Useful for understanding what cultural references are recognized.
    """
    kb = KnowledgeBase()

    entities = {}
    for name, info in kb.CULTURAL_ENTITIES.items():
        entities[name] = {
            "culture": info.get("culture"),
            "type": info.get("type"),
            "visual_keywords": info.get("visual", [])[:5],
            "color_palette": info.get("color_palette", [])
        }

    return {
        "entities": entities,
        "total": len(entities),
        "cultures": list(set(e.get("culture") for e in kb.CULTURAL_ENTITIES.values()))
    }


@router.get("/knowledge/objects")
async def list_mythological_objects():
    """List all known mythological objects."""
    kb = KnowledgeBase()

    return {
        "objects": {
            name: {
                "culture": info.get("culture"),
                "visual": info.get("visual", [])[:5],
                "aliases": info.get("also_known_as", [])
            }
            for name, info in kb.MYTHOLOGICAL_OBJECTS.items()
        }
    }


@router.get("/knowledge/settings")
async def list_settings():
    """List all known settings/locations."""
    kb = KnowledgeBase()

    return {
        "settings": {
            name: {
                "visual": info.get("visual", [])[:5],
                "lighting": info.get("lighting"),
                "atmosphere": info.get("atmosphere"),
                "audio": info.get("audio")
            }
            for name, info in kb.SETTINGS.items()
        }
    }


@router.get("/knowledge/actions")
async def list_actions():
    """List all recognized actions and their visual interpretations."""
    kb = KnowledgeBase()

    return {
        "actions": {
            name: {
                "synonyms": info.get("synonyms", []),
                "visual_interpretation": info.get("visual_interpretation", [])[:3],
                "audio_cues": info.get("audio_cues", []),
                "camera_suggestions": info.get("camera_suggestions", [])
            }
            for name, info in kb.ACTIONS.items()
        }
    }


@router.get("/info")
async def enhancement_info():
    """
    Get information about available enhancement methods.

    Returns capabilities and recommendations.
    """
    try:
        from app.services.llm_prompt_enhancer import ANTHROPIC_AVAILABLE

        return {
            "available_methods": {
                "hybrid": {
                    "available": ANTHROPIC_AVAILABLE,
                    "recommended": True,
                    "description": "LLM enhancement with rule-based validation",
                    "pros": [
                        "Best quality",
                        "Unlimited cultural coverage",
                        "Semantic understanding",
                        "Cultural accuracy validation"
                    ],
                    "cons": ["Requires API key", "Higher latency (~1-2s)"]
                },
                "llm": {
                    "available": ANTHROPIC_AVAILABLE,
                    "recommended": False,
                    "description": "Pure LLM-based enhancement",
                    "pros": ["Creative", "Adaptive"],
                    "cons": ["No validation", "May miss cultural details"]
                },
                "rule_based": {
                    "available": True,
                    "recommended": False,
                    "description": "Legacy rule-based enhancement",
                    "pros": ["Fast", "Free", "Consistent"],
                    "cons": [
                        "Limited cultural coverage",
                        "No semantic understanding",
                        "Requires maintenance"
                    ]
                }
            },
            "recommendation": "hybrid" if ANTHROPIC_AVAILABLE else "rule_based",
            "llm_status": {
                "available": ANTHROPIC_AVAILABLE,
                "model": "claude-sonnet-4-20250514" if ANTHROPIC_AVAILABLE else None
            }
        }
    except Exception as e:
        logger.error("info_endpoint_failed", error=str(e))
        return {
            "available_methods": {
                "rule_based": {
                    "available": True,
                    "recommended": True,
                    "description": "Rule-based enhancement"
                }
            },
            "recommendation": "rule_based",
            "llm_status": {
                "available": False,
                "error": str(e)
            }
        }
