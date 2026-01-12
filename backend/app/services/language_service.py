"""
Language Detection Service

Supports multiple providers:
- Lingua (open source, recommended for accuracy)
- Google Cloud Language Detection
- AWS Comprehend
- FastText
"""

import time
from abc import ABC, abstractmethod
from typing import Optional

import structlog
import lingua
from lingua import LanguageDetectorBuilder

from app.config import LanguageProvider, get_settings
from app.models import LanguageDetectionResponse, LanguageInfo

logger = structlog.get_logger(__name__)
settings = get_settings()


# Language code mapping for Lingua
LINGUA_TO_ISO = {
    lingua.Language.ENGLISH: ("en", "English"),
    lingua.Language.SPANISH: ("es", "Spanish"),
    lingua.Language.FRENCH: ("fr", "French"),
    lingua.Language.GERMAN: ("de", "German"),
    lingua.Language.ITALIAN: ("it", "Italian"),
    lingua.Language.PORTUGUESE: ("pt", "Portuguese"),
    lingua.Language.DUTCH: ("nl", "Dutch"),
    lingua.Language.RUSSIAN: ("ru", "Russian"),
    lingua.Language.CHINESE: ("zh", "Chinese"),
    lingua.Language.JAPANESE: ("ja", "Japanese"),
    lingua.Language.KOREAN: ("ko", "Korean"),
    lingua.Language.ARABIC: ("ar", "Arabic"),
    lingua.Language.HINDI: ("hi", "Hindi"),
    lingua.Language.TURKISH: ("tr", "Turkish"),
    lingua.Language.POLISH: ("pl", "Polish"),
    lingua.Language.VIETNAMESE: ("vi", "Vietnamese"),
    lingua.Language.THAI: ("th", "Thai"),
    lingua.Language.INDONESIAN: ("id", "Indonesian"),
    lingua.Language.SWEDISH: ("sv", "Swedish"),
    lingua.Language.DANISH: ("da", "Danish"),
    lingua.Language.NORWEGIAN: ("no", "Norwegian"),
    lingua.Language.FINNISH: ("fi", "Finnish"),
    lingua.Language.CZECH: ("cs", "Czech"),
    lingua.Language.GREEK: ("el", "Greek"),
    lingua.Language.HEBREW: ("he", "Hebrew"),
    lingua.Language.UKRAINIAN: ("uk", "Ukrainian"),
    lingua.Language.ROMANIAN: ("ro", "Romanian"),
    lingua.Language.HUNGARIAN: ("hu", "Hungarian"),
    lingua.Language.BENGALI: ("bn", "Bengali"),
    lingua.Language.TAMIL: ("ta", "Tamil"),
    # Add more as needed
}


class BaseLanguageDetector(ABC):
    """Abstract base class for language detection."""
    
    @abstractmethod
    async def detect(self, text: str) -> LanguageDetectionResponse:
        """Detect the language of the given text."""
        pass


class LinguaDetector(BaseLanguageDetector):
    """
    Language detector using the Lingua library.
    
    Lingua is highly accurate for short text and supports 75 languages.
    It uses n-grams of sizes 1-5 for better accuracy on short phrases.
    """
    
    def __init__(self):
        # Build detector with all supported languages
        # Use low accuracy mode for faster detection, high for better accuracy
        self._detector = (
            LanguageDetectorBuilder
            .from_all_languages()
            .with_preloaded_language_models()
            .build()
        )
        logger.info("lingua_detector_initialized")
    
    async def detect(self, text: str) -> LanguageDetectionResponse:
        """Detect language using Lingua."""
        start_time = time.perf_counter()
        
        # Get confidence values for all languages
        confidence_values = self._detector.compute_language_confidence_values(text)
        
        if not confidence_values:
            # Fallback if no language detected
            return LanguageDetectionResponse(
                detected_language=LanguageInfo(
                    code="und",
                    name="Undetermined",
                    confidence=0.0
                ),
                alternatives=[],
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )
        
        # Convert to our format
        results = []
        for lang, confidence in confidence_values:
            if lang in LINGUA_TO_ISO:
                code, name = LINGUA_TO_ISO[lang]
                results.append(LanguageInfo(
                    code=code,
                    name=name,
                    confidence=round(confidence, 4)
                ))
        
        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return LanguageDetectionResponse(
            detected_language=results[0] if results else LanguageInfo(
                code="und", name="Undetermined", confidence=0.0
            ),
            alternatives=results[1:5] if len(results) > 1 else [],
            processing_time_ms=round(processing_time, 2)
        )


class GoogleLanguageDetector(BaseLanguageDetector):
    """
    Language detector using Google Cloud Translation API.
    Supports 120+ languages.
    """
    
    def __init__(self):
        from google.cloud import translate_v2 as translate
        self._client = translate.Client()
        logger.info("google_language_detector_initialized")
    
    async def detect(self, text: str) -> LanguageDetectionResponse:
        """Detect language using Google Cloud."""
        start_time = time.perf_counter()
        
        result = self._client.detect_language(text)
        
        # Google returns a single result with confidence
        detected = LanguageInfo(
            code=result["language"],
            name=self._get_language_name(result["language"]),
            confidence=result.get("confidence", 0.0)
        )
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return LanguageDetectionResponse(
            detected_language=detected,
            alternatives=[],
            processing_time_ms=round(processing_time, 2)
        )
    
    def _get_language_name(self, code: str) -> str:
        """Get language name from code."""
        # Simplified mapping - in production, use a full mapping
        names = {
            "en": "English", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
            "ar": "Arabic", "hi": "Hindi", "ru": "Russian",
        }
        return names.get(code, code.upper())


class AWSLanguageDetector(BaseLanguageDetector):
    """
    Language detector using AWS Comprehend.
    Good for enterprise use with large documents.
    """
    
    def __init__(self):
        import boto3
        self._client = boto3.client(
            "comprehend",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id.get_secret_value() if settings.aws_access_key_id else None,
            aws_secret_access_key=settings.aws_secret_access_key.get_secret_value() if settings.aws_secret_access_key else None,
        )
        logger.info("aws_comprehend_detector_initialized")
    
    async def detect(self, text: str) -> LanguageDetectionResponse:
        """Detect language using AWS Comprehend."""
        start_time = time.perf_counter()
        
        response = self._client.detect_dominant_language(Text=text[:5000])
        
        languages = response.get("Languages", [])
        
        if not languages:
            return LanguageDetectionResponse(
                detected_language=LanguageInfo(
                    code="und", name="Undetermined", confidence=0.0
                ),
                alternatives=[],
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )
        
        results = [
            LanguageInfo(
                code=lang["LanguageCode"],
                name=self._get_language_name(lang["LanguageCode"]),
                confidence=round(lang["Score"], 4)
            )
            for lang in languages
        ]
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return LanguageDetectionResponse(
            detected_language=results[0],
            alternatives=results[1:5],
            processing_time_ms=round(processing_time, 2)
        )
    
    def _get_language_name(self, code: str) -> str:
        """Get language name from code."""
        names = {
            "en": "English", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
            "ar": "Arabic", "hi": "Hindi", "ru": "Russian",
        }
        return names.get(code, code.upper())


class FastTextDetector(BaseLanguageDetector):
    """
    Language detector using FastText.
    Very fast, supports 157 languages.
    """
    
    def __init__(self):
        import fasttext
        # Download model if not exists
        model_path = "lid.176.bin"  # Compressed model
        self._model = fasttext.load_model(model_path)
        logger.info("fasttext_detector_initialized")
    
    async def detect(self, text: str) -> LanguageDetectionResponse:
        """Detect language using FastText."""
        start_time = time.perf_counter()
        
        # FastText expects single line
        clean_text = text.replace("\n", " ").strip()
        predictions = self._model.predict(clean_text, k=5)
        
        labels, confidences = predictions
        
        results = []
        for label, conf in zip(labels, confidences):
            # Labels are like "__label__en"
            code = label.replace("__label__", "")
            results.append(LanguageInfo(
                code=code,
                name=self._get_language_name(code),
                confidence=round(float(conf), 4)
            ))
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return LanguageDetectionResponse(
            detected_language=results[0] if results else LanguageInfo(
                code="und", name="Undetermined", confidence=0.0
            ),
            alternatives=results[1:] if len(results) > 1 else [],
            processing_time_ms=round(processing_time, 2)
        )
    
    def _get_language_name(self, code: str) -> str:
        """Get language name from code."""
        names = {
            "en": "English", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
            "ar": "Arabic", "hi": "Hindi", "ru": "Russian",
        }
        return names.get(code, code.upper())


# Factory function to get the appropriate detector
_detector_instance: Optional[BaseLanguageDetector] = None


def get_language_detector() -> BaseLanguageDetector:
    """Get the configured language detector instance."""
    global _detector_instance
    
    if _detector_instance is None:
        provider = settings.language_provider
        
        if provider == LanguageProvider.LINGUA:
            _detector_instance = LinguaDetector()
        elif provider == LanguageProvider.GOOGLE:
            _detector_instance = GoogleLanguageDetector()
        elif provider == LanguageProvider.AWS:
            _detector_instance = AWSLanguageDetector()
        elif provider == LanguageProvider.FASTTEXT:
            _detector_instance = FastTextDetector()
        else:
            # Default to Lingua
            _detector_instance = LinguaDetector()
        
        logger.info("language_detector_created", provider=provider.value)
    
    return _detector_instance
