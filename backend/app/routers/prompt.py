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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/knowledge/entities")
async def list_cultural_entities():
    """
    List all known cultural entities in the knowledge base.
    
    Useful for understanding what cultural references are recognized.
    """
    from app.services.prompt_enhancer import KnowledgeBase
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
    from app.services.prompt_enhancer import KnowledgeBase
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
    from app.services.prompt_enhancer import KnowledgeBase
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
    from app.services.prompt_enhancer import KnowledgeBase
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
