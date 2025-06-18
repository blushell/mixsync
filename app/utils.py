"""Utility functions for the audio fetcher application."""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_search_query(track_info: Dict[str, Any]) -> str:
    """
    Format a Spotify track into a search query for YouTube.
    
    Args:
        track_info: Dictionary containing track information from Spotify API
        
    Returns:
        Formatted search string for YouTube
    """
    try:
        # Extract artist names (handle multiple artists)
        artists = track_info.get('artists', [])
        if artists:
            artist_names = [artist['name'] for artist in artists]
            artist_string = ', '.join(artist_names)
        else:
            artist_string = "Unknown Artist"
        
        # Extract track name
        track_name = track_info.get('name', 'Unknown Track')
        
        # Create search query
        search_query = f"{artist_string} - {track_name}"
        
        # Clean up the search query (remove special characters that might interfere)
        search_query = re.sub(r'[^\w\s\-]', '', search_query)
        search_query = re.sub(r'\s+', ' ', search_query).strip()
        
        logger.info(f"Formatted search query: {search_query}")
        return search_query
        
    except Exception as e:
        logger.error(f"Error formatting search query: {e}")
        return "Unknown Track"

def clean_track_title(title: str) -> str:
    """
    Clean up track titles by removing common video-specific suffixes and prefixes.
    
    Args:
        title: Raw video title from YouTube
        
    Returns:
        Cleaned title suitable for music files
    """
    if not title:
        return "Unknown Track"
    
    # Remove common video suffixes (case insensitive)
    # Use broader patterns first, then specific ones
    patterns_to_remove = [
        # Broad patterns that catch variations
        r'\[.*Official.*Music.*Video.*\]',  # [Monstercat Official Music Video], [Official Music Video], etc.
        r'\[.*Official.*Video.*\]',         # [Official Video], [Label Official Video], etc.
        r'\[.*Music.*Video.*\]',            # [Music Video], [HD Music Video], etc.
        r'\[.*Official.*Audio.*\]',         # [Official Audio], [Label Official Audio], etc.
        r'\(.*Official.*Music.*Video.*\)',  # (Monstercat Official Music Video), etc.
        r'\(.*Official.*Video.*\)',         # (Official Video), (Label Official Video), etc.
        r'\(.*Music.*Video.*\)',            # (Music Video), (HD Music Video), etc.
        r'\(.*Official.*Audio.*\)',         # (Official Audio), etc.
        
        # Specific common patterns
        r'\[Official Music Video\]',
        r'\[Official Video\]',
        r'\[Music Video\]',
        r'\[Official Audio\]',
        r'\[Audio\]',
        r'\[Official\]',
        r'\[HD\]',
        r'\[4K\]',
        r'\[Lyric Video\]',
        r'\[Lyrics\]',
        r'\[Visualizer\]',
        r'\[Live\]',
        r'\[Acoustic\]',
        r'\[Remix\]',
        r'\[Extended Mix\]',
        r'\[Radio Edit\]',
        r'\(Official Music Video\)',
        r'\(Official Video\)',
        r'\(Music Video\)',
        r'\(Official Audio\)',
        r'\(Audio\)',
        r'\(Official\)',
        r'\(HD\)',
        r'\(4K\)',
        r'\(Lyric Video\)',
        r'\(Lyrics\)',
        r'\(Visualizer\)',
        r'\(Live\)',
        r'\(Acoustic\)',
        r'\(Remix\)',
        r'\(Extended Mix\)',
        r'\(Radio Edit\)',
        
        # Remove common prefixes
        r'^Official\s*-\s*',
        r'^Official:\s*',
        # Remove extra whitespace and separators
        r'\s*-\s*$',  # Trailing dash
        r'^\s*-\s*',  # Leading dash
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove extra dashes and separators
    cleaned = re.sub(r'\s*-\s*-\s*', ' - ', cleaned)  # Multiple dashes
    cleaned = re.sub(r'^-\s*|\s*-$', '', cleaned)  # Leading/trailing dashes
    
    # Ensure we have something left
    if not cleaned or len(cleaned.strip()) < 3:
        cleaned = title  # Fall back to original if we cleaned too much
    
    return cleaned.strip()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename: The filename to sanitize (should be pre-cleaned)
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace invalid filesystem characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores and whitespace
    sanitized = sanitized.strip('_').strip()
    
    # Ensure filename isn't empty
    if not sanitized:
        sanitized = "unknown_file"
    
    return sanitized

def get_track_id_from_uri(spotify_uri: str) -> Optional[str]:
    """
    Extract track ID from Spotify URI.
    
    Args:
        spotify_uri: Spotify URI in format spotify:track:id
        
    Returns:
        Track ID or None if invalid format
    """
    try:
        if spotify_uri.startswith('spotify:track:'):
            return spotify_uri.split(':')[-1]
        return None
    except Exception as e:
        logger.error(f"Error extracting track ID from URI {spotify_uri}: {e}")
        return None

def log_track_info(track_info: Dict[str, Any], action: str = "Processing") -> None:
    """
    Log track information in a readable format.
    
    Args:
        track_info: Track information dictionary
        action: Action being performed (e.g., "Downloading", "Removing")
    """
    try:
        artists = [artist['name'] for artist in track_info.get('artists', [])]
        artist_string = ', '.join(artists) if artists else "Unknown Artist"
        track_name = track_info.get('name', 'Unknown Track')
        
        logger.info(f"{action} track: {artist_string} - {track_name}")
        
    except Exception as e:
        logger.error(f"Error logging track info: {e}") 
