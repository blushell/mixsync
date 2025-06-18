"""Configuration module for audio fetcher application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Spotify API credentials
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
    
    # Spotify playlist configuration
    SPOTIFY_PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
    
    # Polling configuration
    POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "10"))
    
    # Download configuration
    DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")
    
    # Ensure download directory exists
    def __init__(self):
        Path(self.DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required_vars = [
            cls.SPOTIPY_CLIENT_ID,
            cls.SPOTIPY_CLIENT_SECRET,
            cls.SPOTIFY_PLAYLIST_ID
        ]
        
        missing_vars = [var for var in required_vars if not var]
        
        if missing_vars:
            print("Missing required environment variables:")
            for var in missing_vars:
                print(f"  - {var}")
            return False
        
        return True

# Global config instance
config = Config() 
