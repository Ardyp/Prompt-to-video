"""
Hybrid Prompt Enhancement System

This module combines LLM-based enhancement with rule-based validation to provide
the best of both worlds:

1. LLM Enhancement (Primary):
   - Creative, adaptive prompt enhancement
   - Unlimited cultural context understanding
   - Semantic comprehension

2. Rule-Based Validation (Secondary):
   - Cultural accuracy verification
   - Safety and sensitivity checks
   - Technical quality scoring
   - Knowledge base enrichment

This hybrid approach follows 2026 best practices while maintaining quality guardrails.
"""

import structlog
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .llm_prompt_enhancer import (
    LLMPromptEnhancer,
    LLMEnhancementResult,
    EnhancementConfig,
    get_llm_enhancer,
    ANTHROPIC_AVAILABLE
)
from .prompt_enhancer import (
    PromptEnhancer as RuleBasedEnhancer,
    EnhancedPrompt,
    ConceptExtractor,
    StyleExtractor,
    AestheticScorer,
    KnowledgeBase,
    ExtractedConcept,
    ConceptType
)

logger = structlog.get_logger(__name__)


@dataclass
class HybridEnhancementResult:
    """Complete result from hybrid enhancement."""
    # Final outputs
    enhanced_prompt: str
    negative_prompt: str
    frame_guidance: List[Dict[str, Any]]

    # LLM results
    llm_enhanced: str
    llm_confidence: float
    llm_reasoning: str
    cultural_notes: List[str]
    technical_specs: Dict[str, Any]

    # Rule-based validation
    concepts_detected: List[Dict[str, Any]]
    styles_detected: List[Dict[str, Any]]
    aesthetic_score: Dict[str, float]
    validation_passed: bool
    validation_warnings: List[str]

    # Metadata
    enhancement_method: str  # "llm_only", "hybrid", "fallback_rule_based"
    original_prompt: str
    processing_time_ms: float
    tokens_used: int
    model_used: str


class CulturalValidator:
    """Validates cultural accuracy and sensitivity."""

    def __init__(self):
        self.kb = KnowledgeBase()
        self.concept_extractor = ConceptExtractor()

    def validate(
        self,
        enhanced_prompt: str,
        cultural_notes: List[str],
        original_prompt: str
    ) -> tuple[bool, List[str]]:
        """
        Validate cultural accuracy and sensitivity.

        Returns:
            (passed, warnings) - True if validation passed, list of warnings
        """
        warnings = []

        # Extract concepts to check cultural entities
        concepts = self.concept_extractor.extract(enhanced_prompt)

        # Check for cultural entities in knowledge base
        cultural_entities = [c for c in concepts if c.cultural_context]

        for entity in cultural_entities:
            entity_name = entity.value.lower()

            # Check if entity is in our knowledge base
            if entity_name in self.kb.CULTURAL_ENTITIES:
                kb_info = self.kb.CULTURAL_ENTITIES[entity_name]

                # Verify visual keywords are appropriate
                expected_visuals = set(kb_info.get("visual", []))
                if expected_visuals:
                    # Check if LLM included some of the expected visual elements
                    found_visuals = sum(
                        1 for visual in expected_visuals
                        if any(word in enhanced_prompt.lower() for word in visual.lower().split())
                    )
                    if found_visuals < len(expected_visuals) * 0.3:  # At least 30% match
                        warnings.append(
                            f"Cultural entity '{entity.value}' may lack authentic visual details. "
                            f"Expected elements like: {', '.join(list(expected_visuals)[:3])}"
                        )

        # Check for stereotypical language
        stereotypes = [
            ("exotic", "Use more specific cultural descriptions instead of 'exotic'"),
            ("mysterious orient", "Avoid orientalist stereotypes"),
            ("primitive", "Use culturally sensitive terminology"),
            ("savage", "Use culturally sensitive terminology"),
        ]

        for stereotype, warning in stereotypes:
            if stereotype in enhanced_prompt.lower():
                warnings.append(warning)

        # Check intent preservation
        original_keywords = set(original_prompt.lower().split())
        enhanced_keywords = set(enhanced_prompt.lower().split())

        # Key entities should be preserved
        key_terms = []
        for concept in concepts:
            if concept.type in [ConceptType.SUBJECT, ConceptType.OBJECT, ConceptType.ACTION]:
                key_terms.append(concept.value.lower())

        missing_terms = [term for term in key_terms if term not in enhanced_prompt.lower()]
        if missing_terms:
            warnings.append(f"Original key terms may be missing: {', '.join(missing_terms)}")

        # Validation passes if no critical warnings
        passed = len(warnings) == 0 or all("may" in w for w in warnings)

        return passed, warnings


class HybridPromptEnhancer:
    """
    Hybrid prompt enhancement system combining LLM and rule-based approaches.

    Architecture:
    1. LLM Enhancement (Primary) - Creative, adaptive enhancement
    2. Rule-Based Validation - Cultural accuracy and safety checks
    3. Knowledge Base Enrichment - Add verified cultural details
    4. Quality Scoring - Predict final video quality

    Usage:
        enhancer = HybridPromptEnhancer()
        result = enhancer.enhance("Rama breaks Shiva's bow")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_llm: bool = True,
        fallback_to_rules: bool = True
    ):
        """
        Initialize hybrid enhancer.

        Args:
            api_key: Anthropic API key for LLM enhancement
            use_llm: Whether to use LLM enhancement (True) or only rule-based (False)
            fallback_to_rules: If LLM fails, fall back to rule-based enhancement
        """
        self.use_llm = use_llm and ANTHROPIC_AVAILABLE
        self.fallback_to_rules = fallback_to_rules

        # Initialize LLM enhancer
        if self.use_llm:
            try:
                self.llm_enhancer = get_llm_enhancer(api_key)
                logger.info("llm_enhancer_initialized", model="claude-sonnet-4")
            except Exception as e:
                logger.warning("llm_enhancer_init_failed", error=str(e))
                self.use_llm = False
                self.llm_enhancer = None
        else:
            self.llm_enhancer = None

        # Initialize rule-based components
        self.rule_based_enhancer = RuleBasedEnhancer()
        self.cultural_validator = CulturalValidator()
        self.concept_extractor = ConceptExtractor()
        self.style_extractor = StyleExtractor()
        self.aesthetic_scorer = AestheticScorer()

        logger.info(
            "hybrid_enhancer_initialized",
            use_llm=self.use_llm,
            fallback=self.fallback_to_rules
        )

    def enhance(
        self,
        prompt: str,
        duration: float = 10.0,
        additional_context: Optional[Dict[str, str]] = None
    ) -> HybridEnhancementResult:
        """
        Enhance a prompt using the hybrid approach.

        Args:
            prompt: Original user prompt
            duration: Video duration in seconds
            additional_context: Optional context (style preferences, etc.)

        Returns:
            HybridEnhancementResult with complete enhancement data
        """
        start_time = datetime.now()

        logger.info("hybrid_enhancement_started", prompt=prompt[:100])

        # Strategy 1: Try LLM enhancement first
        if self.use_llm and self.llm_enhancer:
            try:
                result = self._enhance_with_llm(prompt, duration, additional_context)
                logger.info("enhancement_method", method="llm_with_validation")
                return result
            except Exception as e:
                logger.warning("llm_enhancement_failed", error=str(e))
                if not self.fallback_to_rules:
                    raise

        # Strategy 2: Fallback to rule-based enhancement
        logger.info("enhancement_method", method="rule_based_fallback")
        return self._enhance_with_rules(prompt, duration, additional_context)

    def _enhance_with_llm(
        self,
        prompt: str,
        duration: float,
        additional_context: Optional[Dict[str, str]]
    ) -> HybridEnhancementResult:
        """Enhance using LLM with rule-based validation."""
        start_time = datetime.now()

        # Step 1: LLM Enhancement
        llm_result = self.llm_enhancer.enhance_sync(prompt, duration, additional_context)

        # Step 2: Cultural Validation
        validation_passed, warnings = self.cultural_validator.validate(
            llm_result.enhanced_prompt,
            llm_result.cultural_notes,
            prompt
        )

        # Step 3: Extract concepts and styles for enrichment
        concepts = self.concept_extractor.extract(llm_result.enhanced_prompt)
        styles = self.style_extractor.extract(llm_result.enhanced_prompt, concepts)

        # Step 4: Aesthetic scoring
        aesthetic_score = self.aesthetic_scorer.score(
            llm_result.enhanced_prompt,
            concepts,
            styles
        )

        # Step 5: Enrich with knowledge base if needed
        enhanced_prompt = llm_result.enhanced_prompt
        if not validation_passed and concepts:
            # Add authentic cultural details from knowledge base
            enhanced_prompt = self._enrich_with_knowledge_base(
                llm_result.enhanced_prompt,
                concepts,
                warnings
            )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return HybridEnhancementResult(
            enhanced_prompt=enhanced_prompt,
            negative_prompt=llm_result.negative_prompt,
            frame_guidance=llm_result.frame_guidance,
            llm_enhanced=llm_result.enhanced_prompt,
            llm_confidence=llm_result.confidence,
            llm_reasoning=llm_result.reasoning,
            cultural_notes=llm_result.cultural_notes,
            technical_specs=llm_result.technical_specs,
            concepts_detected=[
                {
                    "type": c.type.value,
                    "value": c.value,
                    "confidence": c.confidence,
                    "cultural_context": c.cultural_context
                }
                for c in concepts
            ],
            styles_detected=[
                {
                    "category": s.category.value,
                    "value": s.value,
                    "confidence": s.confidence
                }
                for s in styles
            ],
            aesthetic_score={
                "overall": aesthetic_score.overall_score,
                "composition": aesthetic_score.composition_score,
                "clarity": aesthetic_score.clarity_score,
                "creativity": aesthetic_score.creativity_score,
                "technical": aesthetic_score.technical_score,
                "cultural": aesthetic_score.cultural_accuracy_score,
                "motion": aesthetic_score.motion_potential_score,
                "audio": aesthetic_score.audio_sync_score
            },
            validation_passed=validation_passed,
            validation_warnings=warnings,
            enhancement_method="hybrid" if not validation_passed else "llm_only",
            original_prompt=prompt,
            processing_time_ms=processing_time,
            tokens_used=llm_result.tokens_used,
            model_used=llm_result.model_used
        )

    def _enhance_with_rules(
        self,
        prompt: str,
        duration: float,
        additional_context: Optional[Dict[str, str]]
    ) -> HybridEnhancementResult:
        """Fallback to pure rule-based enhancement."""
        start_time = datetime.now()

        # Use original rule-based enhancer
        result = self.rule_based_enhancer.enhance(prompt, duration, additional_context)

        # Convert to hybrid result format
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Convert frame prompts to dict format
        frame_guidance = [
            {
                "time_range": f"{f.timestamp_start:.1f}-{f.timestamp_end:.1f}s",
                "focus": ", ".join(f.focus_elements),
                "motion": f.motion_direction,
                "transition": f.transition_from_previous
            }
            for f in result.frame_prompts
        ]

        return HybridEnhancementResult(
            enhanced_prompt=result.enhanced_prompt,
            negative_prompt=result.negative_prompt,
            frame_guidance=frame_guidance,
            llm_enhanced="",
            llm_confidence=0.0,
            llm_reasoning="Rule-based fallback used",
            cultural_notes=[],
            technical_specs={},
            concepts_detected=[
                {
                    "type": c.type.value,
                    "value": c.value,
                    "confidence": c.confidence,
                    "cultural_context": c.cultural_context
                }
                for c in result.concepts
            ],
            styles_detected=[
                {
                    "category": s.category.value,
                    "value": s.value,
                    "confidence": s.confidence
                }
                for s in result.styles
            ],
            aesthetic_score={
                "overall": result.aesthetic_score.overall_score,
                "composition": result.aesthetic_score.composition_score,
                "clarity": result.aesthetic_score.clarity_score,
                "creativity": result.aesthetic_score.creativity_score,
                "technical": result.aesthetic_score.technical_score,
                "cultural": result.aesthetic_score.cultural_accuracy_score,
                "motion": result.aesthetic_score.motion_potential_score,
                "audio": result.aesthetic_score.audio_sync_score
            },
            validation_passed=True,
            validation_warnings=[],
            enhancement_method="fallback_rule_based",
            original_prompt=prompt,
            processing_time_ms=processing_time,
            tokens_used=0,
            model_used="rule_based"
        )

    def _enrich_with_knowledge_base(
        self,
        enhanced_prompt: str,
        concepts: List[ExtractedConcept],
        warnings: List[str]
    ) -> str:
        """Enrich LLM output with verified knowledge base details."""
        kb = KnowledgeBase()
        enrichments = []

        # Add cultural visual details that may be missing
        cultural_entities = [c for c in concepts if c.cultural_context]

        for entity in cultural_entities:
            entity_name = entity.value.lower()
            if entity_name in kb.CULTURAL_ENTITIES:
                kb_info = kb.CULTURAL_ENTITIES[entity_name]
                visual_details = kb_info.get("visual", [])

                # Add top 2-3 visual details that aren't already in the prompt
                for detail in visual_details[:3]:
                    if detail.lower() not in enhanced_prompt.lower():
                        enrichments.append(detail)

        # Append enrichments if any
        if enrichments:
            enhanced_prompt += f" Additional authentic details: {', '.join(enrichments[:3])}."

        return enhanced_prompt


# Singleton instance
_hybrid_enhancer: Optional[HybridPromptEnhancer] = None


def get_hybrid_enhancer(
    api_key: Optional[str] = None,
    use_llm: bool = True
) -> HybridPromptEnhancer:
    """Get or create the global hybrid enhancer instance."""
    global _hybrid_enhancer
    if _hybrid_enhancer is None:
        _hybrid_enhancer = HybridPromptEnhancer(api_key=api_key, use_llm=use_llm)
    return _hybrid_enhancer


# Example usage
if __name__ == "__main__":
    import sys

    test_prompt = sys.argv[1] if len(sys.argv) > 1 else \
        "Rama breaks the Shiva's bow in the hall. Theme is Ancient Hindu"

    print("=" * 80)
    print("HYBRID PROMPT ENHANCEMENT TEST")
    print("=" * 80)
    print(f"\nOriginal: {test_prompt}\n")

    enhancer = HybridPromptEnhancer(use_llm=True, fallback_to_rules=True)

    try:
        result = enhancer.enhance(test_prompt, duration=10.0)

        print("-" * 80)
        print(f"ENHANCEMENT METHOD: {result.enhancement_method.upper()}")
        print("-" * 80)

        print("\n" + "-" * 80)
        print("ENHANCED PROMPT")
        print("-" * 80)
        print(result.enhanced_prompt)

        print("\n" + "-" * 80)
        print("NEGATIVE PROMPT")
        print("-" * 80)
        print(result.negative_prompt)

        print("\n" + "-" * 80)
        print("AESTHETIC SCORE")
        print("-" * 80)
        for key, value in result.aesthetic_score.items():
            print(f"  {key:12s}: {value:.1f}/100")

        if result.validation_warnings:
            print("\n" + "-" * 80)
            print("VALIDATION WARNINGS")
            print("-" * 80)
            for warning in result.validation_warnings:
                print(f"  ⚠️  {warning}")

        if result.cultural_notes:
            print("\n" + "-" * 80)
            print("CULTURAL NOTES")
            print("-" * 80)
            for note in result.cultural_notes:
                print(f"  • {note}")

        print("\n" + "-" * 80)
        print("METADATA")
        print("-" * 80)
        print(f"  Model: {result.model_used}")
        print(f"  Processing Time: {result.processing_time_ms:.1f}ms")
        print(f"  Tokens Used: {result.tokens_used}")
        print(f"  Validation: {'✅ PASSED' if result.validation_passed else '⚠️  WARNINGS'}")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
