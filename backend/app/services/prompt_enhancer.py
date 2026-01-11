"""
Prompt Enhancement Pipeline - Complete System

Components:
1. CONCEPT EXTRACTOR - Identifies subjects, actions, settings, emotions, cultural elements
2. STYLE EXTRACTOR - Detects artistic style, mood, genre, cultural aesthetics
3. AESTHETIC SCORER - Predicts visual quality (0-100) with detailed breakdown
4. DYNAMIC CONTEXT BUILDER - Enriches prompts with extracted concepts/styles
5. FEEDBACK LOOP - Learns from generations to improve future prompts
6. FRAME SMOOTHER - Ensures temporal consistency in video frames
"""

import json
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# ENUMS AND DATA MODELS
# =============================================================================

class ConceptType(str, Enum):
    SUBJECT = "subject"
    ACTION = "action"
    SETTING = "setting"
    TIME = "time"
    EMOTION = "emotion"
    OBJECT = "object"
    RELATIONSHIP = "relationship"
    NARRATIVE = "narrative"
    CULTURAL = "cultural"


class StyleCategory(str, Enum):
    CINEMATIC = "cinematic"
    ARTISTIC = "artistic"
    CULTURAL = "cultural"
    GENRE = "genre"
    MOOD = "mood"
    TECHNICAL = "technical"
    COLOR = "color"
    LIGHTING = "lighting"
    CAMERA = "camera"


@dataclass
class ExtractedConcept:
    """A concept extracted from the prompt."""
    type: ConceptType
    value: str
    confidence: float
    expansions: List[str] = field(default_factory=list)
    cultural_context: Optional[str] = None
    visual_keywords: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)


@dataclass
class ExtractedStyle:
    """A style element extracted from the prompt."""
    category: StyleCategory
    value: str
    confidence: float
    modifiers: List[str] = field(default_factory=list)
    technical_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AestheticScore:
    """Detailed aesthetic quality prediction."""
    overall_score: float
    composition_score: float
    clarity_score: float
    creativity_score: float
    technical_score: float
    cultural_accuracy_score: float
    motion_potential_score: float
    audio_sync_score: float
    suggestions: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class FramePrompt:
    """Prompt for a specific frame/segment of the video."""
    frame_number: int
    timestamp_start: float
    timestamp_end: float
    prompt: str
    transition_from_previous: str
    motion_direction: str
    focus_elements: List[str]


@dataclass
class EnhancedPrompt:
    """The complete enhanced prompt package."""
    original_prompt: str
    enhanced_prompt: str
    negative_prompt: str
    concepts: List[ExtractedConcept]
    styles: List[ExtractedStyle]
    aesthetic_score: AestheticScore
    frame_prompts: List[FramePrompt]
    context_additions: Dict[str, str]
    enhancement_iterations: int
    final_confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# KNOWLEDGE BASE
# =============================================================================

class KnowledgeBase:
    """Comprehensive knowledge base for concept and style extraction."""
    
    CULTURAL_ENTITIES = {
        # Hindu Mythology
        "rama": {
            "type": "deity", "culture": "hindu", "era": "treta_yuga",
            "visual": ["divine blue skin", "radiant aura", "bow and arrow", "royal crown", 
                      "silk dhoti", "sacred tilak", "lotus eyes", "serene expression"],
            "settings": ["ayodhya palace", "forest hermitage", "battlefield", "royal court"],
            "associated_objects": ["kodanda bow", "arrow", "royal chariot"],
            "emotions": ["divine calm", "righteous anger", "compassion", "valor"],
            "color_palette": ["royal blue", "gold", "saffron", "white"],
        },
        "shiva": {
            "type": "deity", "culture": "hindu", "era": "timeless",
            "visual": ["third eye", "crescent moon", "trident", "sacred snake", 
                      "matted locks", "blue throat", "tiger skin", "ash covered body"],
            "settings": ["mount kailash", "cremation ground", "himalayan peaks"],
            "associated_objects": ["trident (trishul)", "damaru", "rudraksha"],
            "color_palette": ["ash grey", "blue", "white", "orange flames"],
        },
        "krishna": {
            "type": "deity", "culture": "hindu", "era": "dwapara_yuga",
            "visual": ["blue-black skin", "peacock feather crown", "yellow silk dhoti",
                      "divine flute", "enchanting smile", "lotus garland"],
            "settings": ["vrindavan", "gokul", "kurukshetra battlefield", "dwarka palace"],
            "color_palette": ["deep blue", "yellow gold", "peacock colors", "lotus pink"],
        },
        "hanuman": {
            "type": "deity", "culture": "hindu", "era": "treta_yuga",
            "visual": ["monkey form", "muscular build", "flying pose", "tail raised",
                      "mace (gada)", "mountain carrying", "saffron body"],
            "settings": ["lanka", "sky", "mountain", "rama's court"],
            "color_palette": ["saffron orange", "red", "gold"],
        },
        "sita": {
            "type": "deity", "culture": "hindu", "era": "treta_yuga",
            "visual": ["divine beauty", "graceful form", "silk saree", "gold jewelry",
                      "lotus in hand", "modest demeanor", "radiant skin"],
            "settings": ["mithila palace", "forest", "ashoka vatika"],
            "color_palette": ["red", "gold", "green", "white"],
        },
        "durga": {
            "type": "deity", "culture": "hindu", "era": "timeless",
            "visual": ["multiple arms (8-10)", "riding lion/tiger", "various weapons",
                      "fierce expression", "red saree", "divine radiance"],
            "settings": ["battlefield", "mountain", "celestial realm"],
            "color_palette": ["vermillion red", "gold", "orange"],
        },
        "ganesh": {
            "type": "deity", "culture": "hindu", "era": "timeless",
            "visual": ["elephant head", "single tusk", "large belly", "four arms",
                      "mouse vehicle", "modak sweet", "trunk curved"],
            "settings": ["temple", "home altar", "beginning ceremonies"],
            "color_palette": ["vermillion red", "saffron", "gold", "white"],
        },
        # Greek Mythology
        "zeus": {
            "type": "deity", "culture": "greek", "era": "ancient",
            "visual": ["muscular build", "flowing beard", "lightning bolt", "eagle",
                      "throne of olympus", "royal robes", "crown of laurels"],
            "settings": ["mount olympus", "stormy skies", "greek temple"],
            "color_palette": ["royal purple", "gold", "storm grey", "lightning white"],
        },
        "athena": {
            "type": "deity", "culture": "greek", "era": "ancient",
            "visual": ["warrior helmet", "aegis shield", "spear", "owl companion",
                      "intelligent eyes", "flowing robes", "olive branch"],
            "settings": ["acropolis", "battlefield", "library"],
            "color_palette": ["silver", "olive green", "royal blue", "gold"],
        },
        # Norse Mythology
        "thor": {
            "type": "deity", "culture": "norse", "era": "viking",
            "visual": ["mighty hammer mjolnir", "red beard", "viking armor", "lightning",
                      "muscular build", "winged helmet"],
            "settings": ["asgard", "bifrost bridge", "stormy skies"],
            "color_palette": ["thunder grey", "lightning blue", "red", "silver"],
        },
        "odin": {
            "type": "deity", "culture": "norse", "era": "viking",
            "visual": ["one eye", "two ravens", "spear gungnir", "wide-brimmed hat",
                      "grey beard", "wisdom lines"],
            "settings": ["throne of asgard", "world tree yggdrasil"],
            "color_palette": ["deep blue", "silver grey", "gold", "raven black"],
        },
    }
    
    MYTHOLOGICAL_OBJECTS = {
        "shiva's bow": {
            "also_known_as": ["pinaka", "shiva dhanush", "the divine bow"],
            "culture": "hindu",
            "visual": ["massive size", "ancient wood and divine metal", "intricate carvings",
                      "glowing aura", "celestial decorations", "impossible weight"],
        },
        "sudarshana chakra": {
            "culture": "hindu",
            "visual": ["spinning disc", "108 serrated edges", "flames", "golden glow"],
        },
        "trishul": {
            "also_known_as": ["trident", "shiva's trident"],
            "culture": "hindu",
            "visual": ["three-pronged spear", "divine metal", "glowing"],
        },
        "mjolnir": {
            "culture": "norse",
            "visual": ["short handle", "massive head", "lightning crackling", "runes engraved"],
        },
    }
    
    SETTINGS = {
        "palace": {
            "visual": ["grand pillars", "ornate ceilings", "throne room", "marble floors",
                      "tapestries", "oil lamps", "royal guards", "intricate carvings"],
            "lighting": "warm oil lamps with divine light rays",
            "atmosphere": "majestic and sacred",
        },
        "temple": {
            "visual": ["carved gopuram", "stone pillars", "deity sanctum", "oil lamps",
                      "flower garlands", "incense smoke", "devotees", "sacred bells"],
            "lighting": "dim interior with divine light from sanctum",
            "atmosphere": "sacred and mystical",
            "audio": "temple bells, chanting, conch shells",
        },
        "hall": {
            "visual": ["grand ceremonial hall", "pillars", "gathered crowd", "central stage",
                      "decorated with flowers", "oil lamps flickering"],
            "lighting": "bright ceremonial lighting",
            "atmosphere": "tense anticipation and ceremony",
        },
        "forest": {
            "visual": ["ancient trees", "dappled sunlight", "nature sounds", "wildlife"],
            "lighting": "dappled sunlight through canopy",
            "atmosphere": "peaceful and spiritual",
        },
        "battlefield": {
            "visual": ["armies", "dust clouds", "weapons", "chariots", "dramatic sky"],
            "lighting": "dramatic with sun rays through clouds",
            "atmosphere": "intense and epic",
            "audio": "war drums, conch shells, battle cries",
        },
        "mountain": {
            "visual": ["snow-capped peak", "clouds", "eternal ice", "majestic scale"],
            "lighting": "ethereal divine glow",
            "atmosphere": "transcendent and otherworldly",
        },
    }
    
    ACTIONS = {
        "breaks": {
            "synonyms": ["shatters", "snaps", "destroys", "splits", "cracks"],
            "visual_interpretation": [
                "dramatic splintering", "shockwave emanating", "pieces flying",
                "light burst at impact", "slow-motion fragments", "dust cloud"
            ],
            "audio_cues": ["thunderous crack", "splintering wood", "gasps from crowd"],
            "camera_suggestions": ["close-up at moment of break", "slow motion", "multiple angles"],
        },
        "lifts": {
            "synonyms": ["raises", "picks up", "hoists", "elevates"],
            "visual_interpretation": [
                "muscles tensing", "object rising smoothly", "effortless motion",
                "surprised onlookers", "divine strength evident"
            ],
            "audio_cues": ["intake of breath", "creaking", "amazed whispers"],
        },
        "fights": {
            "synonyms": ["battles", "combats", "clashes", "strikes"],
            "visual_interpretation": [
                "dynamic motion", "weapon clashing", "martial poses",
                "dust and debris", "dramatic expressions"
            ],
            "audio_cues": ["metal clashing", "battle cries", "impact sounds"],
        },
        "meditates": {
            "synonyms": ["contemplates", "focuses", "sits in peace"],
            "visual_interpretation": [
                "lotus position", "closed eyes", "serene expression",
                "aura forming", "nature responding"
            ],
            "audio_cues": ["om chanting", "nature sounds", "silence"],
        },
        "flies": {
            "synonyms": ["soars", "glides", "ascends", "floats"],
            "visual_interpretation": [
                "wind in hair/clothes", "clouds passing", "ground below",
                "arms spread", "divine vehicle"
            ],
            "audio_cues": ["whooshing wind", "celestial sounds"],
        },
        "dances": {
            "synonyms": ["performs", "moves gracefully", "cosmic dance"],
            "visual_interpretation": [
                "rhythmic movement", "flowing garments", "expressive gestures",
                "circular motion", "fire ring"
            ],
            "audio_cues": ["ankle bells", "drums", "rhythmic music"],
        },
    }
    
    EMOTIONS = {
        "epic": {
            "visual_style": "grand scale, dramatic angles, heroic poses",
            "lighting": "dramatic contrast, god rays",
            "music": "orchestral, brass heavy, timpani",
            "color_grading": "high contrast, saturated",
        },
        "serene": {
            "visual_style": "soft focus, gentle movements, peaceful composition",
            "lighting": "soft, diffused, golden hour",
            "music": "ambient, flute, nature sounds",
            "color_grading": "pastel, warm tones",
        },
        "fierce": {
            "visual_style": "intense close-ups, sharp movements, aggressive poses",
            "lighting": "harsh, high contrast, red accents",
            "music": "percussion heavy, intense strings",
            "color_grading": "desaturated with red highlights",
        },
        "mystical": {
            "visual_style": "ethereal effects, magical particles, glowing elements",
            "lighting": "otherworldly, divine rays",
            "music": "ethereal vocals, bells",
            "color_grading": "cool tones, purple/blue highlights",
        },
        "devotional": {
            "visual_style": "reverent poses, upward gazes, offering gestures",
            "lighting": "warm temple light, candle glow",
            "music": "bhajans, chanting",
            "color_grading": "warm, golden, soft",
        },
    }
    
    CINEMATIC_STYLES = {
        "epic_mythology": {
            "description": "Grand mythological epic style",
            "characteristics": [
                "sweeping camera movements", "grand scale establishing shots",
                "slow motion for key moments", "dramatic lighting", "orchestral score"
            ],
        },
        "action_sequence": {
            "description": "Dynamic action-oriented style",
            "characteristics": [
                "fast cuts", "multiple angles", "speed ramping",
                "impact frames", "motion blur"
            ],
        },
    }
    
    COLOR_PALETTES = {
        "ancient_hindu": {
            "primary": ["#D4AF37", "#8B0000", "#FF6B00"],
            "secondary": ["#1E3A5F", "#2E4A3E", "#F5DEB3"],
            "accent": ["#FFD700", "#FF4500", "#9932CC"],
        },
        "divine_celestial": {
            "primary": ["#FFD700", "#FFFFFF", "#87CEEB"],
            "secondary": ["#DDA0DD", "#E6E6FA", "#F0F8FF"],
            "accent": ["#FF69B4", "#00CED1", "#FFE4B5"],
        },
    }


# =============================================================================
# CONCEPT EXTRACTOR
# =============================================================================

class ConceptExtractor:
    """Extracts semantic concepts from user prompts."""
    
    def __init__(self):
        self.kb = KnowledgeBase()
    
    def extract(self, prompt: str) -> List[ExtractedConcept]:
        """Extract all concepts from a prompt."""
        concepts = []
        prompt_lower = prompt.lower()
        
        concepts.extend(self._extract_cultural_entities(prompt_lower))
        concepts.extend(self._extract_mythological_objects(prompt_lower))
        concepts.extend(self._extract_settings(prompt_lower))
        concepts.extend(self._extract_actions(prompt_lower))
        concepts.extend(self._extract_emotions(prompt_lower))
        concepts.extend(self._extract_temporal(prompt_lower))
        concepts = self._enrich_with_relationships(concepts)
        
        logger.info("concepts_extracted", num_concepts=len(concepts))
        return concepts
    
    def _extract_cultural_entities(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        for entity, info in self.kb.CULTURAL_ENTITIES.items():
            if entity in prompt:
                concepts.append(ExtractedConcept(
                    type=ConceptType.SUBJECT,
                    value=entity.title(),
                    confidence=0.95,
                    expansions=info.get("visual", []),
                    cultural_context=info.get("culture"),
                    visual_keywords=info.get("visual", [])[:5],
                    related_concepts=info.get("associated_objects", [])
                ))
                if info.get("culture"):
                    concepts.append(ExtractedConcept(
                        type=ConceptType.CULTURAL,
                        value=info["culture"],
                        confidence=0.90,
                        expansions=info.get("color_palette", [])
                    ))
        return concepts
    
    def _extract_mythological_objects(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        for obj, info in self.kb.MYTHOLOGICAL_OBJECTS.items():
            names_to_check = [obj] + info.get("also_known_as", [])
            for name in names_to_check:
                if name in prompt:
                    concepts.append(ExtractedConcept(
                        type=ConceptType.OBJECT,
                        value=obj.title(),
                        confidence=0.92,
                        expansions=info.get("visual", []),
                        cultural_context=info.get("culture"),
                        visual_keywords=info.get("visual", [])
                    ))
                    break
        return concepts
    
    def _extract_settings(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        for setting, info in self.kb.SETTINGS.items():
            if setting in prompt:
                concepts.append(ExtractedConcept(
                    type=ConceptType.SETTING,
                    value=setting.title(),
                    confidence=0.88,
                    expansions=info.get("visual", []),
                    visual_keywords=[info.get("lighting", ""), info.get("atmosphere", "")]
                ))
        return concepts
    
    def _extract_actions(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        for action, info in self.kb.ACTIONS.items():
            all_forms = [action] + info.get("synonyms", [])
            for form in all_forms:
                if form in prompt:
                    concepts.append(ExtractedConcept(
                        type=ConceptType.ACTION,
                        value=action,
                        confidence=0.90,
                        expansions=info.get("visual_interpretation", []),
                        visual_keywords=info.get("camera_suggestions", []),
                        related_concepts=info.get("audio_cues", [])
                    ))
                    break
        return concepts
    
    def _extract_emotions(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        for emotion, info in self.kb.EMOTIONS.items():
            if emotion in prompt:
                concepts.append(ExtractedConcept(
                    type=ConceptType.EMOTION,
                    value=emotion,
                    confidence=0.85,
                    expansions=[info.get("visual_style", ""), info.get("lighting", "")],
                    visual_keywords=[info.get("visual_style", "")]
                ))
        
        # Theme keywords
        themes = {"ancient": "historical aesthetic", "divine": "celestial glow", 
                  "epic": "grand scale", "sacred": "spiritual mood", "mythological": "legendary"}
        for keyword, expansion in themes.items():
            if keyword in prompt:
                concepts.append(ExtractedConcept(
                    type=ConceptType.EMOTION, value=keyword, confidence=0.80, expansions=[expansion]
                ))
        return concepts
    
    def _extract_temporal(self, prompt: str) -> List[ExtractedConcept]:
        concepts = []
        temporal = {"ancient": ("ancient era", 0.85), "dawn": ("golden morning light", 0.80),
                   "dusk": ("sunset colors", 0.80), "night": ("moonlit darkness", 0.80)}
        for keyword, (expansion, conf) in temporal.items():
            if keyword in prompt:
                concepts.append(ExtractedConcept(
                    type=ConceptType.TIME, value=keyword, confidence=conf, expansions=[expansion]
                ))
        return concepts
    
    def _enrich_with_relationships(self, concepts: List[ExtractedConcept]) -> List[ExtractedConcept]:
        subjects = [c for c in concepts if c.type == ConceptType.SUBJECT]
        objects = [c for c in concepts if c.type == ConceptType.OBJECT]
        actions = [c for c in concepts if c.type == ConceptType.ACTION]
        
        if subjects and actions and objects:
            concepts.append(ExtractedConcept(
                type=ConceptType.RELATIONSHIP,
                value=f"{subjects[0].value} {actions[0].value} {objects[0].value}",
                confidence=0.88,
                expansions=["dramatic interaction", "key moment", "pivotal scene"]
            ))
        return concepts


# =============================================================================
# STYLE EXTRACTOR
# =============================================================================

class StyleExtractor:
    """Extracts visual style elements from prompts."""
    
    def __init__(self):
        self.kb = KnowledgeBase()
    
    def extract(self, prompt: str, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        styles = []
        prompt_lower = prompt.lower()
        
        styles.extend(self._extract_cinematic_style(concepts))
        styles.extend(self._extract_cultural_style(concepts))
        styles.extend(self._extract_mood_style(concepts))
        styles.extend(self._extract_color_style(concepts))
        styles.extend(self._extract_lighting_style(concepts))
        styles.extend(self._extract_technical_style(concepts))
        
        logger.info("styles_extracted", num_styles=len(styles))
        return styles
    
    def _extract_cinematic_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        styles = []
        has_mythology = any(c.cultural_context for c in concepts)
        has_action = any(c.type == ConceptType.ACTION for c in concepts)
        
        if has_mythology:
            styles.append(ExtractedStyle(
                category=StyleCategory.CINEMATIC,
                value="epic_mythology",
                confidence=0.90,
                modifiers=["sweeping camera", "grand scale", "slow motion key moments", 
                          "dramatic lighting", "orchestral score"]
            ))
        if has_action:
            styles.append(ExtractedStyle(
                category=StyleCategory.CINEMATIC,
                value="action_sequence",
                confidence=0.85,
                modifiers=["dynamic angles", "speed ramping", "impact frames"]
            ))
        return styles
    
    def _extract_cultural_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        styles = []
        cultures = set(c.cultural_context for c in concepts if c.cultural_context)
        
        cultural_mods = {
            "hindu": ["traditional Indian aesthetics", "ornate carvings", "sacred symbols",
                     "rich fabrics", "temple architecture", "oil lamp lighting"],
            "greek": ["classical Greek aesthetics", "marble columns", "Mediterranean"],
            "norse": ["Viking aesthetics", "runic decorations", "Nordic landscape"],
        }
        
        for culture in cultures:
            if culture in cultural_mods:
                styles.append(ExtractedStyle(
                    category=StyleCategory.CULTURAL,
                    value=f"{culture}_aesthetic",
                    confidence=0.92,
                    modifiers=cultural_mods[culture],
                    technical_params={"avoid": ["modern elements", "anachronistic items"]}
                ))
        return styles
    
    def _extract_mood_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        styles = []
        emotions = [c for c in concepts if c.type == ConceptType.EMOTION]
        for emotion in emotions:
            if emotion.value in self.kb.EMOTIONS:
                info = self.kb.EMOTIONS[emotion.value]
                styles.append(ExtractedStyle(
                    category=StyleCategory.MOOD,
                    value=emotion.value,
                    confidence=0.88,
                    modifiers=[info.get("visual_style", ""), info.get("color_grading", "")]
                ))
        return styles
    
    def _extract_color_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        styles = []
        if any(c.cultural_context == "hindu" for c in concepts):
            styles.append(ExtractedStyle(
                category=StyleCategory.COLOR,
                value="ancient_hindu_palette",
                confidence=0.90,
                modifiers=["gold", "deep red", "saffron", "royal blue"],
                technical_params={"palette": self.kb.COLOR_PALETTES["ancient_hindu"]}
            ))
        if any("divine" in str(c.expansions).lower() for c in concepts):
            styles.append(ExtractedStyle(
                category=StyleCategory.COLOR,
                value="divine_celestial_palette",
                confidence=0.85,
                modifiers=["golden glow", "ethereal white", "celestial blue"]
            ))
        return styles
    
    def _extract_lighting_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        suggestions = []
        settings = [c for c in concepts if c.type == ConceptType.SETTING]
        for setting in settings:
            if setting.value.lower() in self.kb.SETTINGS:
                lighting = self.kb.SETTINGS[setting.value.lower()].get("lighting", "")
                if lighting:
                    suggestions.append(lighting)
        
        if any(c.cultural_context for c in concepts):
            suggestions.extend(["divine rays of light", "ethereal glow"])
        
        if suggestions:
            return [ExtractedStyle(
                category=StyleCategory.LIGHTING,
                value="scene_lighting",
                confidence=0.88,
                modifiers=suggestions
            )]
        return []
    
    def _extract_technical_style(self, concepts: List[ExtractedConcept]) -> List[ExtractedStyle]:
        camera_suggestions = []
        for c in concepts:
            if c.type == ConceptType.ACTION and c.value in self.kb.ACTIONS:
                camera_suggestions.extend(self.kb.ACTIONS[c.value].get("camera_suggestions", []))
        
        if any(c.cultural_context for c in concepts):
            camera_suggestions.extend(["establishing wide shot", "dramatic low angle", 
                                       "close-up emotions", "slow motion"])
        
        styles = []
        if camera_suggestions:
            styles.append(ExtractedStyle(
                category=StyleCategory.CAMERA,
                value="camera_work",
                confidence=0.85,
                modifiers=list(set(camera_suggestions))
            ))
        
        styles.append(ExtractedStyle(
            category=StyleCategory.TECHNICAL,
            value="quality_settings",
            confidence=0.95,
            modifiers=["high detail", "cinematic depth of field", "film grain"],
            technical_params={"resolution": "1080p", "fps": "24", "aspect_ratio": "16:9"}
        ))
        return styles


# =============================================================================
# AESTHETIC SCORER
# =============================================================================

class AestheticScorer:
    """Predicts aesthetic quality of a prompt with detailed breakdown."""
    
    def __init__(self):
        self.kb = KnowledgeBase()
    
    def score(self, prompt: str, concepts: List[ExtractedConcept], 
              styles: List[ExtractedStyle]) -> AestheticScore:
        
        composition = self._score_composition(concepts)
        clarity = self._score_clarity(prompt, concepts)
        creativity = self._score_creativity(concepts)
        technical = self._score_technical(styles)
        cultural = self._score_cultural_accuracy(concepts)
        motion = self._score_motion_potential(concepts)
        audio = self._score_audio_sync(prompt, concepts)
        
        # Weighted overall
        overall = (composition * 0.15 + clarity * 0.20 + creativity * 0.15 +
                  technical * 0.15 + cultural * 0.15 + motion * 0.10 + audio * 0.10)
        
        suggestions, weaknesses, strengths = self._generate_feedback(
            composition, clarity, creativity, technical, cultural, motion, audio
        )
        
        return AestheticScore(
            overall_score=round(overall, 1),
            composition_score=round(composition, 1),
            clarity_score=round(clarity, 1),
            creativity_score=round(creativity, 1),
            technical_score=round(technical, 1),
            cultural_accuracy_score=round(cultural, 1),
            motion_potential_score=round(motion, 1),
            audio_sync_score=round(audio, 1),
            suggestions=suggestions,
            weaknesses=weaknesses,
            strengths=strengths
        )
    
    def _score_composition(self, concepts: List[ExtractedConcept]) -> float:
        score = 50.0
        if any(c.type == ConceptType.SUBJECT for c in concepts): score += 15
        if any(c.type == ConceptType.SETTING for c in concepts): score += 15
        if any(c.type == ConceptType.ACTION for c in concepts): score += 10
        if any(c.type == ConceptType.RELATIONSHIP for c in concepts): score += 10
        return min(100, max(0, score))
    
    def _score_clarity(self, prompt: str, concepts: List[ExtractedConcept]) -> float:
        score = 50.0
        word_count = len(prompt.split())
        if 20 <= word_count <= 100: score += 15
        elif word_count < 10: score -= 20
        score += min(20, len(concepts) * 4)
        score += min(15, sum(1 for c in concepts if c.confidence > 0.85) * 3)
        return min(100, max(0, score))
    
    def _score_creativity(self, concepts: List[ExtractedConcept]) -> float:
        score = 60.0
        if any(c.cultural_context for c in concepts): score += 15
        if any("divine" in str(c.expansions).lower() for c in concepts): score += 10
        dramatic = ["breaks", "fights", "flies", "dances"]
        if any(c.type == ConceptType.ACTION and c.value in dramatic for c in concepts): score += 10
        return min(100, max(0, score))
    
    def _score_technical(self, styles: List[ExtractedStyle]) -> float:
        score = 50.0
        if any(s.category == StyleCategory.CINEMATIC for s in styles): score += 15
        if any(s.category == StyleCategory.LIGHTING for s in styles): score += 15
        if any(s.category == StyleCategory.CAMERA for s in styles): score += 10
        if any(s.category == StyleCategory.COLOR for s in styles): score += 10
        return min(100, max(0, score))
    
    def _score_cultural_accuracy(self, concepts: List[ExtractedConcept]) -> float:
        cultural = [c for c in concepts if c.cultural_context]
        if not cultural: return 50.0
        score = 70.0
        for c in cultural:
            if len(c.visual_keywords) > 3: score += 10; break
        for c in cultural:
            if c.value.lower() in self.kb.CULTURAL_ENTITIES: score += 15; break
        return min(100, max(0, score))
    
    def _score_motion_potential(self, concepts: List[ExtractedConcept]) -> float:
        score = 50.0
        actions = [c for c in concepts if c.type == ConceptType.ACTION]
        if actions:
            score += 20
            dynamic = ["breaks", "fights", "flies", "runs", "dances"]
            if any(a.value in dynamic for a in actions): score += 10
        return min(100, max(0, score))
    
    def _score_audio_sync(self, prompt: str, concepts: List[ExtractedConcept]) -> float:
        score = 50.0
        audio_words = ["thunder", "crack", "music", "chanting", "bells", "drums"]
        for word in audio_words:
            if word in prompt.lower(): score += 10
        for c in concepts:
            if c.type == ConceptType.ACTION and c.related_concepts: score += 15; break
        return min(100, max(0, score))
    
    def _generate_feedback(self, comp, clarity, creative, tech, cultural, motion, audio):
        suggestions, weaknesses, strengths = [], [], []
        
        if comp >= 80: strengths.append("Strong scene composition")
        elif comp < 60: weaknesses.append("Unclear composition"); suggestions.append("Add setting details")
        
        if clarity >= 80: strengths.append("Clear and specific prompt")
        elif clarity < 60: weaknesses.append("Lacks specificity"); suggestions.append("Add descriptive details")
        
        if tech >= 80: strengths.append("Good technical specs")
        elif tech < 60: suggestions.append("Add camera/lighting direction")
        
        if cultural >= 80: strengths.append("Rich cultural context")
        elif cultural < 60: suggestions.append("Add authentic cultural details")
        
        if motion >= 80: strengths.append("Strong motion potential")
        elif motion < 60: suggestions.append("Describe specific movements")
        
        if audio >= 70: strengths.append("Good audio sync potential")
        elif audio < 50: suggestions.append("Add sound descriptions")
        
        return suggestions[:5], weaknesses, strengths


# =============================================================================
# DYNAMIC CONTEXT BUILDER
# =============================================================================

class DynamicContextBuilder:
    """Builds rich contextual prompts from extracted elements."""
    
    def __init__(self):
        self.kb = KnowledgeBase()
    
    def build_enhanced_prompt(self, original: str, concepts: List[ExtractedConcept],
                              styles: List[ExtractedStyle]) -> Tuple[str, str, Dict[str, str]]:
        context = {}
        
        # Build subject description
        subjects = [c for c in concepts if c.type == ConceptType.SUBJECT]
        if subjects:
            desc_parts = []
            for s in subjects:
                entity = s.value.lower()
                if entity in self.kb.CULTURAL_ENTITIES:
                    visuals = ", ".join(self.kb.CULTURAL_ENTITIES[entity].get("visual", [])[:5])
                    desc_parts.append(f"{s.value} ({visuals})")
                else:
                    desc_parts.append(s.value)
            context["subject"] = "; ".join(desc_parts)
        
        # Build action description
        actions = [c for c in concepts if c.type == ConceptType.ACTION]
        if actions:
            desc_parts = []
            for a in actions:
                if a.value in self.kb.ACTIONS:
                    interp = ", ".join(self.kb.ACTIONS[a.value].get("visual_interpretation", [])[:3])
                    desc_parts.append(f"{a.value} - {interp}")
            context["action"] = "; ".join(desc_parts)
        
        # Build setting description
        settings = [c for c in concepts if c.type == ConceptType.SETTING]
        if settings:
            desc_parts = []
            for s in settings:
                name = s.value.lower()
                if name in self.kb.SETTINGS:
                    info = self.kb.SETTINGS[name]
                    visuals = ", ".join(info.get("visual", [])[:4])
                    desc_parts.append(f"{s.value}: {visuals}")
            context["setting"] = "; ".join(desc_parts)
        
        # Build atmosphere
        mood_styles = [s for s in styles if s.category == StyleCategory.MOOD]
        light_styles = [s for s in styles if s.category == StyleCategory.LIGHTING]
        atmo_parts = []
        for m in mood_styles: atmo_parts.extend(m.modifiers)
        for l in light_styles: atmo_parts.extend(l.modifiers)
        if atmo_parts: context["atmosphere"] = "; ".join(atmo_parts)
        
        # Build technical
        cin_styles = [s for s in styles if s.category == StyleCategory.CINEMATIC]
        cam_styles = [s for s in styles if s.category == StyleCategory.CAMERA]
        tech_parts = []
        for c in cin_styles: tech_parts.extend(c.modifiers[:3])
        for c in cam_styles: tech_parts.extend(c.modifiers[:3])
        if tech_parts: context["technical"] = "; ".join(tech_parts)
        
        # Build audio
        audio_parts = []
        for c in concepts:
            if c.type == ConceptType.ACTION and c.value in self.kb.ACTIONS:
                audio_parts.extend(self.kb.ACTIONS[c.value].get("audio_cues", []))
        if any(c.cultural_context == "hindu" for c in concepts):
            audio_parts.extend(["traditional Indian instruments", "tabla", "sitar"])
        if audio_parts: context["audio"] = "; ".join(audio_parts)
        
        # Synthesize enhanced prompt
        parts = []
        if context.get("setting"): parts.append(f"SETTING: {context['setting']}")
        parts.append(f"\nSCENE: {original}")
        if context.get("subject"): parts.append(f"\nCHARACTERS: {context['subject']}")
        if context.get("action"): parts.append(f"\nACTION: {context['action']}")
        if context.get("atmosphere"): parts.append(f"\nATMOSPHERE: {context['atmosphere']}")
        if context.get("technical"): parts.append(f"\nCINEMATIC: {context['technical']}")
        if context.get("audio"): parts.append(f"\nAUDIO: {context['audio']}")
        
        enhanced = "\n".join(parts)
        
        # Build negative prompt
        negatives = {"blurry", "low quality", "distorted", "watermark", "text", "logo"}
        if any(c.cultural_context == "hindu" for c in concepts):
            negatives.update(["modern buildings", "western architecture", "contemporary clothing"])
        negative = ", ".join(sorted(negatives))
        
        return enhanced, negative, context


# =============================================================================
# FRAME SMOOTHER
# =============================================================================

class FrameSmoother:
    """Generates frame-by-frame prompts for temporal consistency."""
    
    def __init__(self):
        self.kb = KnowledgeBase()
    
    def generate_frame_prompts(self, enhanced_prompt: str, concepts: List[ExtractedConcept],
                               styles: List[ExtractedStyle], duration: float, fps: int = 24) -> List[FramePrompt]:
        frames = []
        segment_duration = 2.0
        num_segments = max(1, int(duration / segment_duration))
        
        narrative = self._analyze_narrative(concepts)
        
        for i in range(num_segments):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration)
            beat = self._get_narrative_beat(i, num_segments, narrative)
            segment_prompt = self._generate_segment_prompt(enhanced_prompt, beat)
            motion = self._get_motion_direction(i, num_segments, concepts)
            transition = self._get_transition(i, narrative)
            focus = self._get_focus_elements(i, num_segments, concepts)
            
            frames.append(FramePrompt(
                frame_number=i,
                timestamp_start=start,
                timestamp_end=end,
                prompt=segment_prompt,
                transition_from_previous=transition,
                motion_direction=motion,
                focus_elements=focus
            ))
        
        logger.info("frame_prompts_generated", num_frames=len(frames))
        return frames
    
    def _analyze_narrative(self, concepts: List[ExtractedConcept]) -> Dict[str, Any]:
        has_action = any(c.type == ConceptType.ACTION for c in concepts)
        has_subject = any(c.type == ConceptType.SUBJECT for c in concepts)
        has_object = any(c.type == ConceptType.OBJECT for c in concepts)
        
        if has_subject and has_action and has_object:
            return {"type": "action_climax", "beats": ["establish", "approach", "build", "climax", "aftermath"]}
        elif has_subject and has_action:
            return {"type": "action_focus", "beats": ["establish", "build", "action", "resolve"]}
        return {"type": "scenic", "beats": ["establish", "explore", "detail", "conclude"]}
    
    def _get_narrative_beat(self, idx: int, total: int, narrative: Dict) -> str:
        beats = narrative.get("beats", ["establish", "develop", "conclude"])
        progress = idx / max(1, total - 1)
        return beats[min(int(progress * len(beats)), len(beats) - 1)]
    
    def _generate_segment_prompt(self, base: str, beat: str) -> str:
        mods = {
            "establish": "wide establishing shot, setting the scene",
            "approach": "camera moves closer, anticipation building",
            "build": "tension rising, dramatic angles",
            "climax": "peak moment, slow motion, maximum impact",
            "aftermath": "aftermath, settling dust, emotional resonance",
            "explore": "camera pans, revealing details",
            "detail": "close-up on important elements",
            "conclude": "final composition, satisfying closure",
            "resolve": "resolution, calm after action"
        }
        return f"{base}\n\n[SEGMENT: {mods.get(beat, '')}]"
    
    def _get_motion_direction(self, idx: int, total: int, concepts: List[ExtractedConcept]) -> str:
        progress = idx / max(1, total - 1)
        if progress < 0.2: return "slow push in, establishing"
        elif progress < 0.4: return "steady approach, building"
        elif progress < 0.6: return "dynamic motion, action peak"
        elif progress < 0.8: return "impact and reaction"
        return "slow pull back, resolution"
    
    def _get_transition(self, idx: int, narrative: Dict) -> str:
        if idx == 0: return "fade_in"
        if narrative.get("type") == "action_climax" and idx == 3: return "smash_cut"
        return "smooth_continuation"
    
    def _get_focus_elements(self, idx: int, total: int, concepts: List[ExtractedConcept]) -> List[str]:
        progress = idx / max(1, total - 1)
        subjects = [c.value for c in concepts if c.type == ConceptType.SUBJECT]
        objects = [c.value for c in concepts if c.type == ConceptType.OBJECT]
        settings = [c.value for c in concepts if c.type == ConceptType.SETTING]
        
        if progress < 0.3: return settings + subjects[:1]
        elif progress < 0.6: return subjects + objects
        return subjects + [c.value for c in concepts if c.type == ConceptType.EMOTION]


# =============================================================================
# FEEDBACK LOOP
# =============================================================================

class FeedbackLoop:
    """Learns from generation results to improve future prompts."""
    
    def __init__(self):
        self.successful_patterns: Dict[str, float] = {}
        self.failed_patterns: Dict[str, float] = {}
        self.history: List[Dict] = []
    
    def record_result(self, concepts: List[ExtractedConcept], styles: List[ExtractedStyle],
                     score: AestheticScore, success: bool, rating: Optional[float] = None):
        record = {
            "timestamp": datetime.now().isoformat(),
            "concept_types": [c.type.value for c in concepts],
            "score": score.overall_score,
            "success": success,
            "rating": rating
        }
        
        if success and score.overall_score >= 80:
            for c in concepts:
                self.successful_patterns[c.type.value] = self.successful_patterns.get(c.type.value, 0) + 0.1
        elif not success or score.overall_score < 60:
            for c in concepts:
                self.failed_patterns[c.type.value] = self.failed_patterns.get(c.type.value, 0) + 0.1
        
        self.history.append(record)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    def should_refine(self, score: AestheticScore) -> bool:
        if score.overall_score < 70: return True
        if len(score.weaknesses) >= 3: return True
        return False
    
    def refine_prompt(self, prompt: str, score: AestheticScore,
                     concepts: List[ExtractedConcept]) -> str:
        refinements = []
        for suggestion in score.suggestions:
            if "setting" in suggestion.lower(): refinements.append("Add environmental details")
            elif "motion" in suggestion.lower(): refinements.append("Emphasize movement")
            elif "cultural" in suggestion.lower(): refinements.append("Add cultural elements")
        
        if refinements:
            return prompt + f"\n[REFINEMENTS: {'; '.join(refinements[:3])}]"
        return prompt
    
    def get_suggestions(self, concepts: List[ExtractedConcept]) -> List[str]:
        suggestions = []
        current = set(c.type.value for c in concepts)
        for pattern, rate in self.successful_patterns.items():
            if rate > 0.8 and pattern not in current:
                suggestions.append(f"Consider adding {pattern} for better results")
        return suggestions[:5]


# =============================================================================
# MAIN PROMPT ENHANCER
# =============================================================================

class PromptEnhancer:
    """
    Main orchestrator for the prompt enhancement pipeline.
    
    Usage:
        enhancer = PromptEnhancer()
        result = enhancer.enhance("Rama breaks Shiva's bow in the hall. Theme is Ancient Hindu")
        print(result.enhanced_prompt)
        print(result.aesthetic_score.overall_score)
    """
    
    def __init__(self, min_score: float = 70.0, max_iterations: int = 3):
        self.concept_extractor = ConceptExtractor()
        self.style_extractor = StyleExtractor()
        self.aesthetic_scorer = AestheticScorer()
        self.context_builder = DynamicContextBuilder()
        self.frame_smoother = FrameSmoother()
        self.feedback_loop = FeedbackLoop()
        self.min_score = min_score
        self.max_iterations = max_iterations
    
    def enhance(self, prompt: str, duration: float = 10.0,
                extra_context: Optional[Dict[str, str]] = None) -> EnhancedPrompt:
        """Main enhancement method - runs the full pipeline."""
        logger.info("enhancement_started", prompt=prompt[:100])
        
        # Step 1: Extract concepts
        concepts = self.concept_extractor.extract(prompt)
        
        # Step 2: Extract styles
        styles = self.style_extractor.extract(prompt, concepts)
        
        # Step 3: Build enhanced prompt
        enhanced, negative, context = self.context_builder.build_enhanced_prompt(
            prompt, concepts, styles
        )
        
        # Add extra user context
        if extra_context:
            for key, value in extra_context.items():
                context[f"user_{key}"] = value
                enhanced += f"\n[USER: {key.upper()}: {value}]"
        
        # Step 4: Score aesthetics
        score = self.aesthetic_scorer.score(prompt, concepts, styles)
        
        # Step 5: Feedback loop refinement
        iterations = 0
        while self.feedback_loop.should_refine(score) and iterations < self.max_iterations:
            enhanced = self.feedback_loop.refine_prompt(enhanced, score, concepts)
            score = self.aesthetic_scorer.score(prompt, concepts, styles)
            iterations += 1
            logger.info("prompt_refined", iteration=iterations, score=score.overall_score)
        
        # Step 6: Generate frame prompts for smooth video
        frame_prompts = self.frame_smoother.generate_frame_prompts(
            enhanced, concepts, styles, duration
        )
        
        # Calculate confidence
        confidence = min(
            score.overall_score / 100,
            sum(c.confidence for c in concepts) / max(1, len(concepts))
        )
        
        result = EnhancedPrompt(
            original_prompt=prompt,
            enhanced_prompt=enhanced,
            negative_prompt=negative,
            concepts=concepts,
            styles=styles,
            aesthetic_score=score,
            frame_prompts=frame_prompts,
            context_additions=context,
            enhancement_iterations=iterations,
            final_confidence=confidence,
            metadata={
                "duration": duration,
                "num_concepts": len(concepts),
                "num_styles": len(styles),
                "num_frames": len(frame_prompts),
                "version": "1.0.0"
            }
        )
        
        # Record for learning
        self.feedback_loop.record_result(concepts, styles, score, True)
        
        logger.info("enhancement_complete", 
                   original_len=len(prompt),
                   enhanced_len=len(enhanced),
                   score=score.overall_score)
        
        return result
    
    def enhance_for_model(self, prompt: str, model: str = "veo3",
                         duration: float = 10.0) -> Dict[str, Any]:
        """Format enhanced prompt for specific video model."""
        result = self.enhance(prompt, duration)
        
        if model in ["veo3", "veo3.1"]:
            return {
                "prompt": result.enhanced_prompt,
                "negativePrompt": result.negative_prompt,
                "duration": duration,
                "aspectRatio": "16:9",
                "metadata": {
                    "aesthetic_score": result.aesthetic_score.overall_score,
                    "concepts": [c.value for c in result.concepts],
                    "frame_guidance": [
                        {"time": f.timestamp_start, "focus": f.focus_elements}
                        for f in result.frame_prompts
                    ]
                }
            }
        return {
            "prompt": result.enhanced_prompt,
            "negative_prompt": result.negative_prompt,
            "duration": duration
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_enhancer: Optional[PromptEnhancer] = None

def get_prompt_enhancer() -> PromptEnhancer:
    """Get global PromptEnhancer instance."""
    global _enhancer
    if _enhancer is None:
        _enhancer = PromptEnhancer()
    return _enhancer

def enhance_prompt(prompt: str, duration: float = 10.0) -> EnhancedPrompt:
    """Quick function to enhance a prompt."""
    return get_prompt_enhancer().enhance(prompt, duration)


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    test_prompt = sys.argv[1] if len(sys.argv) > 1 else \
        "Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu"
    
    print("=" * 80)
    print("PROMPT ENHANCEMENT PIPELINE")
    print("=" * 80)
    print(f"\nOriginal: {test_prompt}\n")
    
    enhancer = PromptEnhancer()
    result = enhancer.enhance(test_prompt, duration=10.0)
    
    print("-" * 80)
    print("CONCEPTS EXTRACTED")
    print("-" * 80)
    for c in result.concepts:
        print(f"  [{c.type.value.upper()}] {c.value} ({c.confidence:.0%})")
        if c.visual_keywords:
            print(f"    Visuals: {', '.join(c.visual_keywords[:3])}")
    
    print("\n" + "-" * 80)
    print("STYLES EXTRACTED")
    print("-" * 80)
    for s in result.styles:
        print(f"  [{s.category.value.upper()}] {s.value}")
        if s.modifiers:
            print(f"    Modifiers: {', '.join(s.modifiers[:3])}")
    
    print("\n" + "-" * 80)
    print("AESTHETIC SCORE")
    print("-" * 80)
    s = result.aesthetic_score
    print(f"  Overall: {s.overall_score}/100")
    print(f"  ├── Composition:  {s.composition_score}")
    print(f"  ├── Clarity:      {s.clarity_score}")
    print(f"  ├── Creativity:   {s.creativity_score}")
    print(f"  ├── Technical:    {s.technical_score}")
    print(f"  ├── Cultural:     {s.cultural_accuracy_score}")
    print(f"  ├── Motion:       {s.motion_potential_score}")
    print(f"  └── Audio:        {s.audio_sync_score}")
    print(f"\n  Strengths: {', '.join(s.strengths)}")
    print(f"  Suggestions: {', '.join(s.suggestions)}")
    
    print("\n" + "-" * 80)
    print("ENHANCED PROMPT")
    print("-" * 80)
    print(result.enhanced_prompt)
    
    print("\n" + "-" * 80)
    print("NEGATIVE PROMPT")
    print("-" * 80)
    print(result.negative_prompt)
    
    print("\n" + "-" * 80)
    print("FRAME PROMPTS")
    print("-" * 80)
    for f in result.frame_prompts:
        print(f"  Frame {f.frame_number}: {f.timestamp_start:.1f}s-{f.timestamp_end:.1f}s")
        print(f"    Motion: {f.motion_direction}")
        print(f"    Focus: {', '.join(f.focus_elements)}")
    
    print("\n" + "=" * 80)
    print(f"Enhancement complete! Score: {result.aesthetic_score.overall_score}/100")
    print("=" * 80)
