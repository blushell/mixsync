"""
Utility functions for the Audio Fetcher application.
Contains helpers for string formatting, validation, and other common operations.
"""

import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse


def format_search_query(artist: str, title: str, album: Optional[str] = None) -> str:
    """
    Format a search query for yt-dlp from Spotify track information.
    
    Args:
        artist: Track artist name
        title: Track title
        album: Optional album name
        
    Returns:
        Formatted search query string
    """
    # Clean up artist and title strings
    artist_clean = clean_string(artist)
    title_clean = clean_string(title)
    
    # Basic format: "artist - title"
    query = f"{artist_clean} - {title_clean}"
    
    # Add album if provided and different from title
    if album and clean_string(album) != title_clean:
        query += f" {clean_string(album)}"
    
    return query


def clean_string(text: str) -> str:
    """
    Clean a string by removing special characters and extra whitespace.
    
    Args:
        text: Input string to clean
        
    Returns:
        Cleaned string
    """
    if not text:
        return ""
    
    # Remove common problematic characters and patterns
    text = re.sub(r'\(feat\..*?\)', '', text, flags=re.IGNORECASE)  # Remove featuring
    text = re.sub(r'\(ft\..*?\)', '', text, flags=re.IGNORECASE)    # Remove ft.
    text = re.sub(r'\[.*?\]', '', text)                             # Remove brackets
    text = re.sub(r'\(.*?remix.*?\)', '', text, flags=re.IGNORECASE)  # Remove remix info
    text = re.sub(r'[^\w\s-]', '', text)                           # Remove special chars
    text = re.sub(r'\s+', ' ', text)                               # Normalize whitespace
    
    return text.strip()


def validate_media_url(url: str) -> bool:
    """
    Validate if a URL is from a supported media platform.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and supported
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Supported domains
        supported_domains = [
            'youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com',
            'soundcloud.com', 'www.soundcloud.com',
            'bandcamp.com', 'www.bandcamp.com'
        ]
        
        # Check for direct MP3 links
        if url.lower().endswith('.mp3'):
            return True
        
        # Check supported domains
        return any(domain.endswith(supported) for supported in supported_domains)
        
    except Exception:
        return False


def get_safe_filename(text: str, max_length: int = 100) -> str:
    """
    Generate a safe filename from text.
    
    Args:
        text: Input text
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    if not text:
        return "unknown"
    
    # Remove or replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '', text)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('._')
    
    # Truncate if too long
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip('._')
    
    return safe_name or "unknown"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger("audio_fetcher")


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "3:45")
    """
    if seconds < 60:
        return f"0:{seconds:02d}"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}:{remaining_seconds:02d}"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}:{remaining_minutes:02d}:{remaining_seconds:02d}"


def extract_track_info(track_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant track information from Spotify track data.
    
    Args:
        track_data: Spotify track data dictionary
        
    Returns:
        Dictionary with extracted track information
    """
    try:
        track = track_data.get('track', track_data)
        
        # Extract basic info
        title = track.get('name', 'Unknown Title')
        artists = track.get('artists', [])
        artist = ', '.join([artist['name'] for artist in artists]) if artists else 'Unknown Artist'
        album = track.get('album', {}).get('name', '')
        duration_ms = track.get('duration_ms', 0)
        
        return {
            'title': title,
            'artist': artist,
            'album': album,
            'duration': format_duration(duration_ms // 1000),
            'id': track.get('id', ''),
            'uri': track.get('uri', '')
        }
    except Exception as e:
        logging.error(f"Error extracting track info: {e}")
        return {
            'title': 'Unknown Title',
            'artist': 'Unknown Artist',
            'album': '',
            'duration': '0:00',
            'id': '',
            'uri': ''
        } 
