# 🎬 Prompt-to-Video App

A full-stack application that converts user prompts into AI-generated videos with voice narration.

## Features

- 🌍 **Automatic Language Detection** - Detects 75+ languages from user input
- 🎤 **Voice Cloning** - Clone user's voice from 5-15 seconds of audio
- 🎥 **AI Video Generation** - Generate cinematic videos from text prompts
- 🔊 **Audio Sync** - Automatically sync generated speech with video
- 📱 **Modern UI** - Beautiful, responsive web interface

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  React + TypeScript + TailwindCSS                               │
│  • Voice Recording Component                                     │
│  • Prompt Input with Language Badge                              │
│  • Video Player with Progress                                    │
│  • Generation Status Dashboard                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API / WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  • /api/detect-language - Language detection endpoint            │
│  • /api/clone-voice - Voice cloning from audio sample            │
│  • /api/generate-video - Text-to-video generation                │
│  • /api/generate-speech - TTS with cloned voice                  │
│  • /api/merge-av - Merge audio and video                         │
│  • /ws/status - WebSocket for real-time progress                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Language   │   │   Voice     │   │   Video     │
│  Service    │   │   Service   │   │   Service   │
│             │   │             │   │             │
│ • lingua-py │   │ • Fish Audio│   │ • Veo 3.1   │
│ • fastText  │   │ • ElevenLabs│   │ • Runway    │
│ • Google    │   │ • Chatterbox│   │ • Kling     │
└─────────────┘   └─────────────┘   └─────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - High-performance async Python web framework
- **Celery + Redis** - Background task processing
- **FFmpeg** - Audio/video processing
- **lingua-py** - Language detection
- **Multiple AI Provider SDKs**

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Framer Motion** - Animations
- **React Query** - Data fetching

### AI Services (Configurable)
- **Language Detection**: lingua-py (free), Google Cloud, AWS Comprehend
- **Voice Cloning**: Fish Audio, ElevenLabs, Chatterbox (open source)
- **Video Generation**: Google Veo 3.1, Runway Gen-3, Kling, Wan2.2 (open source)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis
- FFmpeg

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/prompt-to-video-app.git
cd prompt-to-video-app

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the App

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
cd backend
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Start Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 4: Start Frontend
cd frontend
npm run dev
```

Visit `http://localhost:5173` to use the app.

## Configuration

See `.env.example` for all configuration options:

```env
# AI Service Selection
VIDEO_PROVIDER=veo3          # veo3, runway, kling, wan2
VOICE_PROVIDER=fish_audio    # fish_audio, elevenlabs, chatterbox
LANGUAGE_PROVIDER=lingua     # lingua, google, aws

# API Keys
GOOGLE_API_KEY=your_key
FISH_AUDIO_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
RUNWAY_API_KEY=your_key
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Cost Estimation

| Provider Combination | Cost per 10s Video |
|---------------------|-------------------|
| Veo 3.1 + Fish Audio | ~$2-4 |
| Kling + Fish Audio | ~$1-2 |
| Runway + ElevenLabs | ~$3-5 |
| Wan2.2 + Chatterbox (self-hosted) | GPU costs only |

## License

MIT License - see LICENSE file for details.
