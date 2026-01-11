# 🎬 Prompt-to-Video Pipeline Architecture

## Complete System with Prompt Enhancement

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            USER INPUT                                            │
│  "Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu"              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PROMPT ENHANCEMENT PIPELINE                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        1. CONCEPT EXTRACTOR                              │   │
│  │  ┌──────────┬───────────┬──────────┬──────────┬──────────┬──────────┐  │   │
│  │  │ SUBJECT  │  ACTION   │ SETTING  │  OBJECT  │ EMOTION  │ CULTURAL │  │   │
│  │  │  Rama    │  breaks   │  Hall    │ Shiva's  │  epic    │  hindu   │  │   │
│  │  │  Shiva   │           │          │   Bow    │ ancient  │          │  │   │
│  │  └──────────┴───────────┴──────────┴──────────┴──────────┴──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        2. STYLE EXTRACTOR                                │   │
│  │  ┌────────────┬────────────┬──────────┬──────────┬────────────────┐    │   │
│  │  │ CINEMATIC  │  CULTURAL  │  COLOR   │ LIGHTING │    CAMERA      │    │   │
│  │  │ epic_myth  │   hindu    │ gold/red │ divine   │ slow-mo, wide  │    │   │
│  │  │ action_seq │ aesthetic  │ saffron  │ rays     │ close-up       │    │   │
│  │  └────────────┴────────────┴──────────┴──────────┴────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      3. DYNAMIC CONTEXT BUILDER                          │   │
│  │                                                                          │   │
│  │   SETTING: Hall: grand ceremonial hall, pillars, gathered crowd         │   │
│  │   CHARACTERS: Rama (divine blue skin, radiant aura, bow and arrow)      │   │
│  │   ACTION: breaks - dramatic splintering, shockwave emanating            │   │
│  │   ATMOSPHERE: bright ceremonial lighting; divine rays of light          │   │
│  │   AUDIO: thunderous crack; splintering wood; gasps; sitar; tabla        │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       4. AESTHETIC SCORER                                │   │
│  │                                                                          │   │
│  │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │   │  OVERALL: 90/100 ⭐⭐⭐⭐⭐                                       │   │   │
│  │   │  ├── Composition:  100  │ Creativity:   95  │ Motion:    80   │   │   │
│  │   │  ├── Clarity:       85  │ Technical:   100  │ Audio:     65   │   │   │
│  │   │  └── Cultural:      95  │                                      │   │   │
│  │   │                                                                 │   │   │
│  │   │  ✅ Strengths: Strong composition, Clear prompt, Rich cultural │   │   │
│  │   └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                              Score >= 70?                                        │
│                           ┌──────┴──────┐                                        │
│                          YES            NO                                       │
│                           │              │                                       │
│                           ▼              ▼                                       │
│                       PROCEED      5. FEEDBACK LOOP                              │
│                           │         (Refine & Retry)                             │
│                           │              │                                       │
│                           ◄──────────────┘                                       │
│                           │                                                      │
│                           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       6. FRAME SMOOTHER                                  │   │
│  │                                                                          │   │
│  │   Frame 0 (0-2s):  fade_in    │ slow push in     │ Focus: Hall, Rama   │   │
│  │   Frame 1 (2-4s):  smooth     │ steady approach  │ Focus: Hall, Rama   │   │
│  │   Frame 2 (4-6s):  smooth     │ action peak      │ Focus: Rama, Bow    │   │
│  │   Frame 3 (6-8s):  smash_cut  │ impact/reaction  │ Focus: Rama, Shiva  │   │
│  │   Frame 4 (8-10s): smooth     │ slow pull back   │ Focus: aftermath    │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ENHANCED PROMPT OUTPUT                                 │
│                                                                                  │
│   SETTING: Hall: grand ceremonial hall, pillars, gathered crowd                │
│   SCENE: Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu        │
│   CHARACTERS: Rama (divine blue skin, radiant aura, bow and arrow, royal crown) │
│   ACTION: breaks - dramatic splintering, shockwave emanating, pieces flying     │
│   ATMOSPHERE: bright ceremonial lighting; divine rays of light; ethereal glow   │
│   CINEMATIC: sweeping camera; grand scale; slow motion key moments              │
│   AUDIO: thunderous crack; gasps from crowd; sitar; tabla                       │
│                                                                                  │
│   NEGATIVE: blurry, modern buildings, western architecture, watermark           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            VIDEO GENERATION                                      │
│                                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐          │
│  │  VOICE SYNTHESIS │    │  VIDEO GENERATOR  │    │  AUDIO MERGE     │          │
│  │    Fish Audio    │    │     Veo 3.1       │    │     FFmpeg       │          │
│  │   (if no native) │    │  (with frame      │    │  (if needed)     │          │
│  │                  │    │   guidance)       │    │                  │          │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FINAL OUTPUT                                        │
│                                                                                  │
│   🎥 Video: 10 seconds, 1080p, 16:9                                             │
│   🔊 Audio: Native (synchronized with video)                                    │
│   📊 Quality: 90/100                                                            │
│   💰 Cost: ~$4.00 (Veo 3.1)                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Prompt Enhancement
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prompt/enhance` | POST | Full enhancement with all components |
| `/api/prompt/analyze` | POST | Quick analysis without full enhancement |
| `/api/prompt/knowledge/entities` | GET | List cultural entities in knowledge base |
| `/api/prompt/knowledge/objects` | GET | List mythological objects |
| `/api/prompt/knowledge/settings` | GET | List recognized settings |
| `/api/prompt/knowledge/actions` | GET | List action patterns |

### Generation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generation/create` | POST | Create video with enhanced prompt |
| `/api/generation/status/{id}` | GET | Check job status |
| `/api/generation/result/{id}` | GET | Get final result |

### Providers
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET | List all providers |
| `/api/providers/compare` | GET | Compare providers |
| `/api/providers/recommendations` | GET | Get recommendations |

## Component Breakdown

### 1. Concept Extractor
Identifies semantic elements from the prompt:
- **SUBJECT**: Main characters/deities (Rama, Shiva, Krishna...)
- **ACTION**: What's happening (breaks, fights, flies...)
- **SETTING**: Location (temple, palace, battlefield...)
- **OBJECT**: Mythological items (Shiva's bow, Sudarshana Chakra...)
- **EMOTION**: Mood/feeling (epic, serene, fierce...)
- **CULTURAL**: Cultural context (hindu, greek, norse...)

### 2. Style Extractor
Determines visual style elements:
- **CINEMATIC**: Film style (epic_mythology, action_sequence...)
- **CULTURAL**: Cultural aesthetics (hindu_aesthetic, greek_aesthetic...)
- **COLOR**: Color palette (gold, saffron, royal blue...)
- **LIGHTING**: Lighting style (divine rays, oil lamp glow...)
- **CAMERA**: Camera work (slow motion, wide shot, close-up...)

### 3. Aesthetic Scorer
Predicts video quality (0-100):
- Composition (scene structure)
- Clarity (prompt specificity)
- Creativity (visual interest)
- Technical (camera/lighting specs)
- Cultural (authenticity)
- Motion (animation potential)
- Audio (sound sync quality)

### 4. Dynamic Context Builder
Creates rich, detailed prompt by combining all extracted elements.

### 5. Feedback Loop
Iteratively refines prompts if score < 70.

### 6. Frame Smoother
Generates per-segment guidance for temporal consistency:
- Motion direction
- Focus elements
- Transition type (fade, cut, smooth)

## Example Output

**Input:** `"Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu"`

**Enhanced Output:**
```
SETTING: Hall: grand ceremonial hall, pillars, gathered crowd, central stage

SCENE: Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu

CHARACTERS: Rama (divine blue skin, radiant aura, bow and arrow, royal crown, 
silk dhoti); Shiva (third eye, crescent moon, trident, sacred snake, matted locks)

ACTION: breaks - dramatic splintering, shockwave emanating, pieces flying

ATMOSPHERE: bright ceremonial lighting; divine rays of light; ethereal glow

CINEMATIC: sweeping camera; grand scale; slow motion key moments; dynamic angles

AUDIO: thunderous crack; splintering wood; gasps from crowd; sitar; tabla
```

**Negative Prompt:**
```
blurry, contemporary clothing, distorted, logo, low quality, modern buildings, 
text, watermark, western architecture
```

**Frame Guidance:**
| Frame | Time | Motion | Focus | Transition |
|-------|------|--------|-------|------------|
| 0 | 0-2s | slow push in | Hall, Rama | fade_in |
| 1 | 2-4s | steady approach | Hall, Rama | smooth |
| 2 | 4-6s | action peak | Rama, Bow | smooth |
| 3 | 6-8s | impact/reaction | Rama, Shiva | smash_cut |
| 4 | 8-10s | pull back | aftermath | smooth |
