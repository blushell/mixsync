"""
Spotify playlist watcher module.
Monitors a Spotify playlist for new tracks and manages downloads and removals.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .config import config
from .downloader import AudioDownloader
from .utils import format_search_query, extract_track_info


class SpotifyWatcher:
    """Spotify playlist watcher and manager."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.spotify_client: Optional[spotipy.Spotify] = None
        self.downloader = AudioDownloader()
        self.last_check: Optional[datetime] = None
        self.processed_tracks: Set[str] = set()  # Track IDs that have been processed
        self.failed_tracks: Set[str] = set()     # Track IDs that failed to download
        
    async def initialize(self) -> bool:
        """
        Initialize Spotify client with authentication.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not config.validate_spotify_config():
                self.logger.error("Spotify configuration is incomplete")
                return False
            
            # Set up Spotify OAuth
            auth_manager = SpotifyOAuth(
                client_id=config.SPOTIPY_CLIENT_ID,
                client_secret=config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=config.SPOTIPY_REDIRECT_URI,
                scope="playlist-read-private playlist-modify-private playlist-modify-public",
                cache_path=".spotify_cache"
            )
            
            self.spotify_client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection
            user_info = self.spotify_client.current_user()
            self.logger.info(f"Connected to Spotify as: {user_info['display_name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Spotify client: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start the playlist monitoring loop."""
        if not self.spotify_client:
            if not await self.initialize():
                self.logger.error("Cannot start monitoring without Spotify client")
                return
        
        self.logger.info("Starting Spotify playlist monitoring")
        
        while True:
            try:
                await self.check_playlist_for_new_tracks()
                
                # Wait for the configured interval
                await asyncio.sleep(config.POLL_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def check_playlist_for_new_tracks(self) -> None:
        """Check the configured playlist for new tracks."""
        try:
            if not self.spotify_client:
                self.logger.error("Spotify client not initialized")
                return
            
            self.logger.info("Checking playlist for new tracks")
            
            # Get playlist tracks
            tracks = await self.get_playlist_tracks()
            
            if not tracks:
                self.logger.info("No tracks found in playlist")
                return
            
            # Filter out already processed tracks
            new_tracks = [
                track for track in tracks 
                if track['id'] not in self.processed_tracks 
                and track['id'] not in self.failed_tracks
            ]
            
            if not new_tracks:
                self.logger.info("No new tracks to process")
                return
            
            self.logger.info(f"Found {len(new_tracks)} new tracks to process")
            
            # Process each new track
            for track in new_tracks:
                await self.process_track(track)
                
                # Small delay between downloads to be respectful
                await asyncio.sleep(2)
            
            self.last_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error checking playlist: {e}")
    
    async def get_playlist_tracks(self) -> List[Dict[str, Any]]:
        """
        Get all tracks from the configured playlist.
        
        Returns:
            List of track information dictionaries
        """
        try:
            tracks = []
            offset = 0
            limit = 100
            
            while True:
                # Get playlist tracks with pagination
                results = self.spotify_client.playlist_tracks(
                    config.SPOTIFY_PLAYLIST_ID,
                    offset=offset,
                    limit=limit,
                    fields="items(track(id,name,artists,album,duration_ms,uri)),next"
                )
                
                if not results or not results['items']:
                    break
                
                # Extract track information
                for item in results['items']:
                    if item['track'] and item['track']['id']:
                        track_info = extract_track_info(item)
                        tracks.append(track_info)
                
                # Check if there are more pages
                if not results['next']:
                    break
                    
                offset += limit
            
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error getting playlist tracks: {e}")
            return []
    
    async def process_track(self, track: Dict[str, str]) -> bool:
        """
        Process a single track: download and remove from playlist if successful.
        
        Args:
            track: Track information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            track_id = track['id']
            self.logger.info(f"Processing track: {track['artist']} - {track['title']}")
            
            # Create search query
            search_query = format_search_query(
                track['artist'], 
                track['title'], 
                track.get('album')
            )
            
            # Attempt to download
            download_result = await self.downloader.search_and_download(search_query)
            
            if download_result:
                self.logger.info(f"Successfully downloaded: {track['artist']} - {track['title']}")
                
                # Remove from playlist if download was successful
                if await self.remove_track_from_playlist(track['uri']):
                    self.processed_tracks.add(track_id)
                    return True
                else:
                    self.logger.warning(f"Downloaded but failed to remove from playlist: {track_id}")
                    self.processed_tracks.add(track_id)  # Still mark as processed
                    return True
            else:
                self.logger.warning(f"Failed to download: {track['artist']} - {track['title']}")
                self.failed_tracks.add(track_id)
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing track {track.get('id', 'unknown')}: {e}")
            if track.get('id'):
                self.failed_tracks.add(track['id'])
            return False
    
    async def remove_track_from_playlist(self, track_uri: str) -> bool:
        """
        Remove a track from the configured playlist.
        
        Args:
            track_uri: Spotify track URI
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.spotify_client:
                self.logger.error("Spotify client not initialized")
                return False
            
            # Remove track from playlist
            self.spotify_client.playlist_remove_all_occurrences_of_items(
                config.SPOTIFY_PLAYLIST_ID,
                [track_uri]
            )
            
            self.logger.info(f"Removed track from playlist: {track_uri}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing track from playlist: {e}")
            return False
    
    async def retry_failed_tracks(self) -> None:
        """Retry downloading tracks that previously failed."""
        if not self.failed_tracks:
            self.logger.info("No failed tracks to retry")
            return
        
        self.logger.info(f"Retrying {len(self.failed_tracks)} failed tracks")
        
        # Get current playlist tracks
        current_tracks = await self.get_playlist_tracks()
        current_track_ids = {track['id'] for track in current_tracks}
        
        # Find failed tracks that are still in the playlist
        failed_tracks_to_retry = [
            track for track in current_tracks
            if track['id'] in self.failed_tracks and track['id'] in current_track_ids
        ]
        
        if not failed_tracks_to_retry:
            self.logger.info("No failed tracks found in current playlist")
            return
        
        # Clear the failed tracks set for tracks we're retrying
        for track in failed_tracks_to_retry:
            self.failed_tracks.discard(track['id'])
        
        # Process the tracks again
        for track in failed_tracks_to_retry:
            await self.process_track(track)
            await asyncio.sleep(2)  # Delay between retries
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the Spotify watcher.
        
        Returns:
            Dictionary with status information
        """
        return {
            'connected': self.spotify_client is not None,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'processed_tracks_count': len(self.processed_tracks),
            'failed_tracks_count': len(self.failed_tracks),
            'poll_interval_minutes': config.POLL_INTERVAL_MINUTES,
            'playlist_id': config.SPOTIFY_PLAYLIST_ID
        }
    
    async def manual_sync(self) -> Dict[str, Any]:
        """
        Manually trigger a playlist sync.
        
        Returns:
            Dictionary with sync results
        """
        try:
            self.logger.info("Manual sync triggered")
            
            start_time = datetime.now()
            await self.check_playlist_for_new_tracks()
            end_time = datetime.now()
            
            return {
                'success': True,
                'sync_time': (end_time - start_time).total_seconds(),
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error during manual sync: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup_processed_tracks(self, days_old: int = 7) -> None:
        """
        Clean up tracking of old processed tracks.
        
        Args:
            days_old: Remove tracking for tracks processed more than this many days ago
        """
        try:
            # For simplicity, just clear the sets periodically
            # In a production app, you might want to persist this data with timestamps
            if len(self.processed_tracks) > 1000:
                self.logger.info("Clearing old processed tracks cache")
                self.processed_tracks.clear()
            
            if len(self.failed_tracks) > 100:
                self.logger.info("Clearing old failed tracks cache")
                self.failed_tracks.clear()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}") 
