"""
Configuration module for Audio Fetcher application.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pathlib import Path


class Config:
    """Application configuration class."""
    
    # Spotify API Configuration
    SPOTIPY_CLIENT_ID: str = os.getenv("SPOTIPY_CLIENT_ID", "")
    SPOTIPY_CLIENT_SECRET: str = os.getenv("SPOTIPY_CLIENT_SECRET", "")
    SPOTIPY_REDIRECT_URI: str = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
    SPOTIFY_PLAYLIST_ID: str = os.getenv("SPOTIFY_PLAYLIST_ID", "")
    
    # Application Settings
    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "10"))
    DOWNLOAD_PATH: Path = Path(os.getenv("DOWNLOAD_PATH", "/downloads"))
    
    # FastAPI Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "7860"))
    
    # yt-dlp Settings
    YTDLP_FORMAT: str = os.getenv("YTDLP_FORMAT", "bestaudio/best")
    YTDLP_AUDIO_FORMAT: str = os.getenv("YTDLP_AUDIO_FORMAT", "mp3")
    YTDLP_AUDIO_QUALITY: str = os.getenv("YTDLP_AUDIO_QUALITY", "192")
    
    # Debug Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate_spotify_config(cls) -> bool:
        """Validate that required Spotify configuration is present."""
        required_fields = [
            cls.SPOTIPY_CLIENT_ID,
            cls.SPOTIPY_CLIENT_SECRET,
            cls.SPOTIFY_PLAYLIST_ID
        ]
        return all(required_fields)
    
    @classmethod
    def get_download_path(cls) -> Path:
        """Get the download path and ensure it exists."""
        download_path = cls.DOWNLOAD_PATH
        download_path.mkdir(parents=True, exist_ok=True)
        return download_path


# Global config instance
config = Config() 
