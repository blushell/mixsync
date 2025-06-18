#!/usr/bin/env python3
"""
Quiet continuous playlist sync runner - minimal output for production.
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

# Set up quieter logging - only important messages
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and errors
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mixsync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to be less verbose
logging.getLogger('app.downloader').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Global variable for graceful shutdown
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.warning(f"Received signal {signum}, shutting down...")
    shutdown_event.set()

async def run_quiet_sync():
    """Run the Spotify sync quietly - only show important events."""
    print("🎵 Audio Fetcher started - monitoring playlist...")
    
    # Validate configuration
    if not config.validate():
        print("❌ Configuration invalid - check your .env file")
        return False
    
    # Initialize Spotify watcher
    watcher = SpotifyWatcher()
    
    if not watcher.spotify_client:
        print("❌ Failed to connect to Spotify - check your credentials")
        return False
    
    # Get playlist info quietly
    playlist_info = watcher.get_playlist_info()
    if playlist_info:
        print(f"📋 Monitoring: {playlist_info['name']} ({playlist_info['tracks_total']} tracks)")
        print(f"⏱️  Check interval: {config.POLL_INTERVAL_MINUTES} minutes")
        print(f"📁 Download path: {config.DOWNLOAD_PATH}")
    else:
        print("❌ Could not access playlist")
        return False
    
    print("✅ Started - Press Ctrl+C to stop\n")
    
    try:
        # Run initial sync
        stats = watcher.sync_playlist()
        if stats['new_tracks'] > 0:
            print(f"🎶 Initial sync: {stats['downloaded']} downloaded, {stats['failed']} failed")
        
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
                stats = watcher.sync_playlist()
                
                if stats['new_tracks'] > 0:
                    print(f"🎶 {stats['downloaded']} downloaded, {stats['failed']} failed")
                # Don't print anything if no new tracks
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n👋 Audio Fetcher stopped")
    return True

def main():
    """Main function."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = asyncio.run(run_quiet_sync())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
