"""
Audio/Video Processing Service

Handles merging, conversion, and processing using FFmpeg.
"""

import asyncio
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class MediaProcessor:
    """
    Media processing utilities using FFmpeg.
    
    Handles:
    - Merging audio and video
    - Audio format conversion
    - Video transcoding
    - Thumbnail generation
    """
    
    def __init__(self):
        self.storage_path = Path(settings.local_storage_path)
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Verify FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception("FFmpeg not working properly")
            logger.info("ffmpeg_available")
        except FileNotFoundError:
            logger.error("ffmpeg_not_found")
            raise Exception("FFmpeg is required but not found")
    
    async def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Merge audio and video files.
        
        Args:
            video_path: Path to the video file
            audio_path: Path to the audio file
            output_path: Optional output path (generated if not provided)
        
        Returns:
            Path to the merged output file
        """
        if output_path is None:
            output_filename = f"merged_{uuid.uuid4()}.mp4"
            output_path = str(self.storage_path / "outputs" / output_filename)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg command to merge audio and video
        # -c:v copy = copy video stream without re-encoding
        # -c:a aac = encode audio to AAC
        # -shortest = end when shortest input ends
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-map", "0:v:0",  # Take video from first input
            "-map", "1:a:0",  # Take audio from second input
            output_path
        ]
        
        logger.info(
            "merging_audio_video",
            video=video_path,
            audio=audio_path,
            output=output_path
        )
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(
                "merge_failed",
                returncode=process.returncode,
                stderr=stderr.decode()
            )
            raise Exception(f"FFmpeg merge failed: {stderr.decode()}")
        
        logger.info("merge_completed", output=output_path)
        return output_path
    
    async def replace_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Replace audio track in a video with new audio.
        
        Args:
            video_path: Path to the video file (may have existing audio)
            audio_path: Path to the new audio file
            output_path: Optional output path
        
        Returns:
            Path to the output file
        """
        if output_path is None:
            output_filename = f"replaced_{uuid.uuid4()}.mp4"
            output_path = str(self.storage_path / "outputs" / output_filename)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg replace audio failed: {stderr.decode()}")
        
        return output_path
    
    async def generate_thumbnail(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        timestamp: str = "00:00:01"
    ) -> str:
        """
        Generate a thumbnail from a video.
        
        Args:
            video_path: Path to the video file
            output_path: Optional output path
            timestamp: Time position to capture (HH:MM:SS)
        
        Returns:
            Path to the thumbnail image
        """
        if output_path is None:
            output_filename = f"thumb_{uuid.uuid4()}.jpg"
            output_path = str(self.storage_path / "outputs" / output_filename)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-q:v", "2",  # High quality JPEG
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg thumbnail failed: {stderr.decode()}")
        
        return output_path
    
    async def get_duration(self, file_path: str) -> float:
        """
        Get the duration of an audio or video file.
        
        Args:
            file_path: Path to the media file
        
        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFprobe failed: {stderr.decode()}")
        
        return float(stdout.decode().strip())
    
    async def convert_audio(
        self,
        input_path: str,
        output_format: str = "mp3",
        output_path: Optional[str] = None
    ) -> str:
        """
        Convert audio to a different format.
        
        Args:
            input_path: Path to input audio file
            output_format: Target format (mp3, wav, aac, etc.)
            output_path: Optional output path
        
        Returns:
            Path to converted audio
        """
        if output_path is None:
            output_filename = f"audio_{uuid.uuid4()}.{output_format}"
            output_path = str(self.storage_path / "outputs" / output_filename)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vn",  # No video
            output_path
        ]
        
        # Add format-specific options
        if output_format == "mp3":
            cmd.insert(-1, "-codec:a")
            cmd.insert(-1, "libmp3lame")
            cmd.insert(-1, "-b:a")
            cmd.insert(-1, "192k")
        elif output_format == "aac":
            cmd.insert(-1, "-codec:a")
            cmd.insert(-1, "aac")
            cmd.insert(-1, "-b:a")
            cmd.insert(-1, "192k")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg convert failed: {stderr.decode()}")
        
        return output_path
    
    async def adjust_audio_length(
        self,
        audio_path: str,
        target_duration: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Adjust audio length to match target duration.
        
        If audio is shorter, pad with silence.
        If audio is longer, trim it.
        
        Args:
            audio_path: Path to input audio
            target_duration: Target duration in seconds
            output_path: Optional output path
        
        Returns:
            Path to adjusted audio
        """
        if output_path is None:
            output_filename = f"adjusted_{uuid.uuid4()}.mp3"
            output_path = str(self.storage_path / "outputs" / output_filename)
        
        current_duration = await self.get_duration(audio_path)
        
        if current_duration >= target_duration:
            # Trim audio
            cmd = [
                "ffmpeg",
                "-y",
                "-i", audio_path,
                "-t", str(target_duration),
                "-c:a", "copy",
                output_path
            ]
        else:
            # Pad with silence
            silence_duration = target_duration - current_duration
            cmd = [
                "ffmpeg",
                "-y",
                "-i", audio_path,
                "-af", f"apad=pad_dur={silence_duration}",
                "-t", str(target_duration),
                output_path
            ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg adjust failed: {stderr.decode()}")
        
        return output_path


# Singleton instance
_processor_instance: Optional[MediaProcessor] = None


def get_media_processor() -> MediaProcessor:
    """Get the media processor instance."""
    global _processor_instance
    
    if _processor_instance is None:
        _processor_instance = MediaProcessor()
    
    return _processor_instance
