#!/usr/bin/env python3
"""
Continuous playlist sync runner - no console prompts.
This script runs the playlist sync automatically without user interaction.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.config import config
from app.spotify_watcher import SpotifyWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mixsync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variable for graceful shutdown
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()

async def run_continuous_sync():
    """Run the Spotify sync continuously without prompts."""
    logger.info("=== Audio Fetcher Continuous Sync ===")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed!")
        logger.error("Please make sure you have a .env file with the required variables.")
        logger.error("See env_example.txt for the required format.")
        return False
    
    logger.info("Configuration validated successfully")
    
    # Initialize Spotify watcher
    logger.info("Initializing Spotify watcher...")
    watcher = SpotifyWatcher()
    
    if not watcher.spotify_client:
        logger.error("Failed to initialize Spotify client!")
        logger.error("Please check your Spotify API credentials.")
        return False
    
    # Get playlist info
    logger.info("Getting playlist information...")
    playlist_info = watcher.get_playlist_info()
    
    if playlist_info:
        logger.info(f"Monitoring playlist: {playlist_info['name']}")
        logger.info(f"Owner: {playlist_info['owner']}")
        logger.info(f"Total tracks: {playlist_info['tracks_total']}")
        logger.info(f"Poll interval: {config.POLL_INTERVAL_MINUTES} minutes")
        logger.info(f"Download path: {config.DOWNLOAD_PATH}")
    else:
        logger.error("Could not fetch playlist information!")
        return False
    
    # Start continuous monitoring
    logger.info("Starting continuous monitoring...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run initial sync
        logger.info("Running initial sync...")
        stats = watcher.sync_playlist()
        logger.info(f"Initial sync: {stats['downloaded']} downloaded, {stats['failed']} failed")
        
        # Start monitoring loop
        while not shutdown_event.is_set():
            try:
                # Wait for the poll interval or shutdown signal
                await asyncio.wait_for(
                    shutdown_event.wait(), 
                    timeout=config.POLL_INTERVAL_MINUTES * 60
                )
                break  # Shutdown signal received
                
            except asyncio.TimeoutError:
                # Time to run another sync
                logger.info("Running scheduled playlist sync...")
                stats = watcher.sync_playlist()
                
                if stats['new_tracks'] > 0:
                    logger.info(f"Sync completed: {stats['downloaded']} downloaded, {stats['failed']} failed")
                else:
                    logger.info("No new tracks found")
    
    except Exception as e:
        logger.error(f"Error in monitoring loop: {e}")
        return False
    
    logger.info("Continuous sync stopped")
    return True

def main():
    """Main function."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = asyncio.run(run_continuous_sync())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Sync failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
