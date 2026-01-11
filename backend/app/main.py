"""
Prompt-to-Video API - Main Application Entry Point

A comprehensive API for converting text prompts into AI-generated videos
with voice narration support.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import generation, health, language, prompt, providers, voice

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)
settings = get_settings()


# WebSocket connection manager for real-time updates
class ConnectionManager:
    """Manage WebSocket connections for real-time progress updates."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info("websocket_connected", job_id=job_id)
    
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info("websocket_disconnected", job_id=job_id)
    
    async def send_progress(self, job_id: str, data: dict[str, Any]):
        if job_id in self.active_connections:
            await self.active_connections[job_id].send_json(data)
    
    async def broadcast(self, message: dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        video_provider=settings.video_provider.value,
        voice_provider=settings.voice_provider.value,
    )
    
    # Create storage directories
    storage_path = Path(settings.local_storage_path)
    (storage_path / "uploads").mkdir(parents=True, exist_ok=True)
    (storage_path / "outputs").mkdir(parents=True, exist_ok=True)
    (storage_path / "temp").mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("app_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Prompt-to-Video API
    
    Convert text prompts into AI-generated videos with voice narration.
    
    ### Features
    - 🌍 Automatic language detection (75+ languages)
    - 🎤 Voice cloning from audio samples
    - 🎥 AI video generation from text
    - 🔊 Text-to-speech synthesis
    - 🎬 Audio/video merging
    
    ### Supported Providers
    
    **Video Generation:**
    - Google Veo 3.1 (recommended)
    - Runway Gen-3
    - Kling 2.1
    - OpenAI Sora 2
    
    **Voice/TTS:**
    - Fish Audio
    - ElevenLabs
    - Chatterbox (open source)
    
    **Language Detection:**
    - Lingua (open source, recommended)
    - Google Cloud
    - AWS Comprehend
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated content
app.mount(
    "/static",
    StaticFiles(directory=settings.local_storage_path),
    name="static",
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(language.router, prefix="/api/language", tags=["Language Detection"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice & TTS"])
app.include_router(prompt.router, prefix="/api/prompt", tags=["Prompt Enhancement"])
app.include_router(generation.router, prefix="/api/generation", tags=["Video Generation"])
app.include_router(providers.router, prefix="/api/providers", tags=["Provider Management"])


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Connect to receive live updates about video generation progress.
    """
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(job_id)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "providers": {
            "video": settings.video_provider.value,
            "voice": settings.voice_provider.value,
            "language": settings.language_provider.value,
        },
    }


# Export for Celery and testing
def get_connection_manager() -> ConnectionManager:
    """Get the WebSocket connection manager instance."""
    return manager
