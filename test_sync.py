#!/usr/bin/env python3
"""Simple test script for Spotify playlist sync functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.config import config
from app.spotify_watcher import SpotifyWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_sync():
    """Test the Spotify sync functionality."""
    logger.info("=== Audio Fetcher Sync Test ===")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed!")
        logger.error("Please make sure you have a .env file with the required variables.")
        logger.error("See env_example.txt for the required format.")
        return
    
    logger.info("Configuration validated successfully")
    
    # Initialize Spotify watcher
    logger.info("Initializing Spotify watcher...")
    watcher = SpotifyWatcher()
    
    if not watcher.spotify_client:
        logger.error("Failed to initialize Spotify client!")
        logger.error("Please check your Spotify API credentials.")
        return
    
    # Get playlist info
    logger.info("Getting playlist information...")
    playlist_info = watcher.get_playlist_info()
    
    if playlist_info:
        logger.info(f"Playlist: {playlist_info['name']}")
        logger.info(f"Owner: {playlist_info['owner']}")
        logger.info(f"Total tracks: {playlist_info['tracks_total']}")
        logger.info(f"URL: {playlist_info['url']}")
    else:
        logger.error("Could not fetch playlist information!")
        return
    
    # Get current tracks
    logger.info("Fetching current tracks...")
    tracks = watcher.get_playlist_tracks()
    logger.info(f"Found {len(tracks)} tracks in playlist")
    
    # Show first few tracks
    if tracks:
        logger.info("First few tracks:")
        for i, track_data in enumerate(tracks[:3]):
            track = track_data['track_info']
            artists = ', '.join([artist['name'] for artist in track['artists']])
            logger.info(f"  {i+1}. {artists} - {track['name']}")
    
    # Get new tracks (tracks that haven't been processed)
    logger.info("Checking for new tracks...")
    new_tracks = watcher.get_new_tracks()
    logger.info(f"Found {len(new_tracks)} new tracks to process")
    
    if new_tracks:
        logger.info("New tracks to be downloaded:")
        for track_data in new_tracks[:5]:  # Show first 5
            track = track_data['track_info']
            artists = ', '.join([artist['name'] for artist in track['artists']])
            logger.info(f"  - {artists} - {track['name']}")
        
        # Ask user if they want to proceed with sync
        if len(new_tracks) > 0:
            response = input(f"\nDo you want to sync {len(new_tracks)} tracks? (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                logger.info("Starting sync...")
                stats = watcher.sync_playlist()
                
                logger.info("=== Sync Results ===")
                logger.info(f"New tracks found: {stats['new_tracks']}")
                logger.info(f"Successfully downloaded: {stats['downloaded']}")
                logger.info(f"Failed downloads: {stats['failed']}")
            else:
                logger.info("Sync cancelled by user")
    else:
        logger.info("No new tracks to process")
    
    logger.info("=== Test Complete ===")

def main():
    """Main function."""
    try:
        asyncio.run(test_sync())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")

if __name__ == "__main__":
    main() 
