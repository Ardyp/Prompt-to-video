"""
LLM-Based Prompt Enhancement System

This module provides state-of-the-art prompt enhancement using Large Language Models.
It follows best practices from 2026 research:
- Prompt-A-Video: LLM-driven automatic prompt adaptation
- VPO: Prompt optimization for harmlessness, accuracy, and helpfulness
- Meta-Prompting: Self-optimization techniques

The system uses Claude Sonnet 4 for high-quality prompt enhancement while preserving
user intent and ensuring cultural sensitivity.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# Try to import Anthropic SDK
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not installed - LLM enhancement will be disabled")


@dataclass
class LLMEnhancementResult:
    """Result from LLM-based prompt enhancement."""
    enhanced_prompt: str
    negative_prompt: str
    frame_guidance: List[Dict[str, Any]]
    cultural_notes: List[str]
    technical_specs: Dict[str, Any]
    reasoning: str
    confidence: float
    processing_time_ms: float
    model_used: str
    tokens_used: int


@dataclass
class EnhancementConfig:
    """Configuration for LLM enhancement."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2000
    temperature: float = 0.7
    preserve_intent: bool = True
    cultural_sensitivity: bool = True
    add_technical_details: bool = True
    include_frame_guidance: bool = True
    output_format: str = "structured"  # or "simple"


ENHANCEMENT_SYSTEM_PROMPT = """You are an expert text-to-video prompt enhancement AI. Your expertise includes:
- Cinematic storytelling and visual composition
- Cultural authenticity and sensitivity across global traditions
- Technical aspects of video generation (lighting, camera work, motion)
- Temporal consistency and frame-by-frame narrative structure

YOUR CORE PRINCIPLES:
1. PRESERVE USER INTENT - Never change the fundamental meaning or story
2. ENHANCE VISUAL RICHNESS - Add specific details about setting, lighting, colors, camera angles
3. ENSURE CULTURAL ACCURACY - Research and respect authentic cultural representations
4. AVOID STEREOTYPES - Use nuanced, respectful descriptions of all cultures
5. OPTIMIZE FOR VIDEO GENERATION - Structure prompts for temporal consistency

TASK: Transform user prompts into detailed, cinematically rich descriptions optimized for AI video generation.

OUTPUT REQUIREMENTS:
- Enhanced Prompt: Detailed visual description (3-5 sentences)
- Negative Prompt: What to avoid (comma-separated)
- Frame Guidance: Temporal breakdown for smooth video (JSON array)
- Cultural Notes: Any cultural context or sensitivity considerations
- Technical Specs: Camera, lighting, color palette recommendations
- Reasoning: Brief explanation of enhancement choices

FORMAT YOUR RESPONSE AS JSON:
{
  "enhanced_prompt": "...",
  "negative_prompt": "...",
  "frame_guidance": [
    {"time_range": "0-2s", "focus": "...", "motion": "...", "transition": "..."},
    ...
  ],
  "cultural_notes": ["...", "..."],
  "technical_specs": {
    "camera_work": "...",
    "lighting": "...",
    "color_palette": ["...", "..."],
    "mood": "..."
  },
  "reasoning": "..."
}"""


class LLMPromptEnhancer:
    """
    LLM-based prompt enhancer using Claude Sonnet 4.

    This class provides state-of-the-art prompt enhancement using Large Language Models,
    following 2026 best practices for text-to-video generation.

    Usage:
        enhancer = LLMPromptEnhancer(api_key="your_key")
        result = await enhancer.enhance("Rama breaks Shiva's bow")
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[EnhancementConfig] = None):
        """
        Initialize the LLM prompt enhancer.

        Args:
            api_key: Anthropic API key (if None, will try to get from environment)
            config: Enhancement configuration
        """
        self.config = config or EnhancementConfig()

        if not ANTHROPIC_AVAILABLE:
            logger.error("anthropic package not available - install with: pip install anthropic")
            self.client = None
            return

        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            # Will use ANTHROPIC_API_KEY environment variable
            try:
                self.client = anthropic.Anthropic()
            except Exception as e:
                logger.error("failed_to_initialize_anthropic_client", error=str(e))
                self.client = None

    async def enhance(
        self,
        prompt: str,
        duration: float = 10.0,
        additional_context: Optional[Dict[str, str]] = None
    ) -> LLMEnhancementResult:
        """
        Enhance a prompt using Claude Sonnet 4.

        Args:
            prompt: The user's original prompt
            duration: Video duration in seconds
            additional_context: Optional additional context (e.g., style preferences)

        Returns:
            LLMEnhancementResult with enhanced prompt and metadata

        Raises:
            RuntimeError: If Anthropic client is not available
            ValueError: If the LLM response is invalid
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized - check API key and installation")

        start_time = datetime.now()

        # Build user message
        user_message = self._build_user_message(prompt, duration, additional_context)

        try:
            logger.info("llm_enhancement_started", prompt=prompt[:100], duration=duration)

            # Call Claude API
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=ENHANCEMENT_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            # Parse response
            result = self._parse_response(response, prompt)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time
            result.model_used = self.config.model
            result.tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(
                "llm_enhancement_complete",
                processing_time_ms=processing_time,
                tokens=result.tokens_used,
                confidence=result.confidence
            )

            return result

        except anthropic.APIError as e:
            logger.error("anthropic_api_error", error=str(e))
            raise RuntimeError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error("llm_enhancement_failed", error=str(e))
            raise ValueError(f"Failed to enhance prompt: {str(e)}")

    def _build_user_message(
        self,
        prompt: str,
        duration: float,
        additional_context: Optional[Dict[str, str]]
    ) -> str:
        """Build the user message for Claude."""
        message_parts = [
            f"Original Prompt: {prompt}",
            f"Video Duration: {duration} seconds",
        ]

        if additional_context:
            message_parts.append("\nAdditional Context:")
            for key, value in additional_context.items():
                message_parts.append(f"- {key}: {value}")

        message_parts.append("\nPlease enhance this prompt following the guidelines above.")
        message_parts.append("Return your response as valid JSON.")

        return "\n".join(message_parts)

    def _parse_response(
        self,
        response: Any,
        original_prompt: str
    ) -> LLMEnhancementResult:
        """Parse Claude's response into a structured result."""
        try:
            # Get the text content
            content = response.content[0].text

            # Try to extract JSON from the response
            json_str = content

            # If wrapped in code blocks, extract
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            data = json.loads(json_str)

            # Extract fields with defaults
            enhanced_prompt = data.get("enhanced_prompt", "")
            negative_prompt = data.get("negative_prompt", "")
            frame_guidance = data.get("frame_guidance", [])
            cultural_notes = data.get("cultural_notes", [])
            technical_specs = data.get("technical_specs", {})
            reasoning = data.get("reasoning", "")

            # Calculate confidence based on completeness
            confidence = self._calculate_confidence(data)

            return LLMEnhancementResult(
                enhanced_prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                frame_guidance=frame_guidance,
                cultural_notes=cultural_notes,
                technical_specs=technical_specs,
                reasoning=reasoning,
                confidence=confidence,
                processing_time_ms=0.0,  # Will be set by caller
                model_used=self.config.model,
                tokens_used=0  # Will be set by caller
            )

        except json.JSONDecodeError as e:
            logger.warning("failed_to_parse_json_response", error=str(e), content=content[:200])
            # Fallback: use the raw text as enhanced prompt
            return LLMEnhancementResult(
                enhanced_prompt=content,
                negative_prompt="blurry, low quality, distorted",
                frame_guidance=[],
                cultural_notes=[],
                technical_specs={},
                reasoning="Fallback: JSON parsing failed",
                confidence=0.5,
                processing_time_ms=0.0,
                model_used=self.config.model,
                tokens_used=0
            )
        except Exception as e:
            logger.error("failed_to_parse_response", error=str(e))
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on response completeness."""
        score = 0.0

        # Check each field
        if data.get("enhanced_prompt") and len(data["enhanced_prompt"]) > 50:
            score += 0.25
        if data.get("negative_prompt"):
            score += 0.15
        if data.get("frame_guidance") and len(data["frame_guidance"]) > 0:
            score += 0.20
        if data.get("cultural_notes"):
            score += 0.15
        if data.get("technical_specs") and len(data["technical_specs"]) > 0:
            score += 0.15
        if data.get("reasoning"):
            score += 0.10

        return min(1.0, score)

    def enhance_sync(
        self,
        prompt: str,
        duration: float = 10.0,
        additional_context: Optional[Dict[str, str]] = None
    ) -> LLMEnhancementResult:
        """
        Synchronous version of enhance() for non-async contexts.

        Args:
            prompt: The user's original prompt
            duration: Video duration in seconds
            additional_context: Optional additional context

        Returns:
            LLMEnhancementResult with enhanced prompt and metadata
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized - check API key and installation")

        start_time = datetime.now()

        # Build user message
        user_message = self._build_user_message(prompt, duration, additional_context)

        try:
            logger.info("llm_enhancement_started", prompt=prompt[:100], duration=duration)

            # Call Claude API (synchronous)
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=ENHANCEMENT_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            # Parse response
            result = self._parse_response(response, prompt)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time
            result.model_used = self.config.model
            result.tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(
                "llm_enhancement_complete",
                processing_time_ms=processing_time,
                tokens=result.tokens_used,
                confidence=result.confidence
            )

            return result

        except anthropic.APIError as e:
            logger.error("anthropic_api_error", error=str(e))
            raise RuntimeError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error("llm_enhancement_failed", error=str(e))
            raise ValueError(f"Failed to enhance prompt: {str(e)}")


# Singleton instance
_llm_enhancer: Optional[LLMPromptEnhancer] = None


def get_llm_enhancer(api_key: Optional[str] = None) -> LLMPromptEnhancer:
    """Get or create the global LLM enhancer instance."""
    global _llm_enhancer
    if _llm_enhancer is None:
        _llm_enhancer = LLMPromptEnhancer(api_key=api_key)
    return _llm_enhancer


# Example usage
if __name__ == "__main__":
    import asyncio
    import sys

    async def test_enhancement():
        test_prompt = sys.argv[1] if len(sys.argv) > 1 else \
            "Rama breaks the Shiva's bow in the hall. Theme is Ancient Hindu"

        print("=" * 80)
        print("LLM-BASED PROMPT ENHANCEMENT TEST")
        print("=" * 80)
        print(f"\nOriginal: {test_prompt}\n")

        enhancer = LLMPromptEnhancer()

        try:
            result = await enhancer.enhance(test_prompt, duration=10.0)

            print("-" * 80)
            print("ENHANCED PROMPT")
            print("-" * 80)
            print(result.enhanced_prompt)

            print("\n" + "-" * 80)
            print("NEGATIVE PROMPT")
            print("-" * 80)
            print(result.negative_prompt)

            print("\n" + "-" * 80)
            print("FRAME GUIDANCE")
            print("-" * 80)
            for frame in result.frame_guidance:
                print(f"  {frame}")

            print("\n" + "-" * 80)
            print("CULTURAL NOTES")
            print("-" * 80)
            for note in result.cultural_notes:
                print(f"  • {note}")

            print("\n" + "-" * 80)
            print("TECHNICAL SPECS")
            print("-" * 80)
            for key, value in result.technical_specs.items():
                print(f"  {key}: {value}")

            print("\n" + "-" * 80)
            print("METADATA")
            print("-" * 80)
            print(f"  Model: {result.model_used}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Processing Time: {result.processing_time_ms:.1f}ms")
            print(f"  Tokens Used: {result.tokens_used}")

            print("\n" + "-" * 80)
            print("REASONING")
            print("-" * 80)
            print(result.reasoning)

            print("\n" + "=" * 80)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            return 1

        return 0

    exit_code = asyncio.run(test_enhancement())
    sys.exit(exit_code)
