"""Spotify playlist watcher and sync module."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .config import config
from .downloader import AudioDownloader
from .utils import format_search_query, log_track_info, get_track_id_from_uri

logger = logging.getLogger(__name__)

class SpotifyWatcher:
    """Handles Spotify playlist monitoring and syncing."""
    
    def __init__(self):
        """Initialize the Spotify watcher with API credentials."""
        self.downloader = AudioDownloader()
        self.spotify_client = None
        self.processed_tracks: Set[str] = set()  # Track IDs that have been processed
        self._initialize_spotify_client()
    
    def _initialize_spotify_client(self) -> None:
        """Initialize the Spotify API client with OAuth."""
        try:
            # Set up OAuth with required scopes
            scope = "playlist-read-private playlist-modify-private playlist-modify-public"
            
            auth_manager = SpotifyOAuth(
                client_id=config.SPOTIPY_CLIENT_ID,
                client_secret=config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=config.SPOTIPY_REDIRECT_URI,
                scope=scope,
                cache_path=".spotify_cache"
            )
            
            self.spotify_client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection
            user = self.spotify_client.current_user()
            logger.info(f"Successfully connected to Spotify as: {user.get('display_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            self.spotify_client = None
    
    def get_playlist_tracks(self) -> List[Dict[str, Any]]:
        """
        Get all tracks from the configured playlist.
        
        Returns:
            List of track information dictionaries
        """
        if not self.spotify_client:
            logger.error("Spotify client not initialized")
            return []
        
        try:
            logger.info(f"Fetching tracks from playlist: {config.SPOTIFY_PLAYLIST_ID}")
            
            tracks = []
            results = self.spotify_client.playlist_tracks(config.SPOTIFY_PLAYLIST_ID)
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['id']:
                        tracks.append({
                            'track_info': item['track'],
                            'added_at': item['added_at'],
                            'playlist_position': len(tracks)
                        })
                
                # Get next page if available
                if results['next']:
                    results = self.spotify_client.next(results)
                else:
                    break
            
            logger.info(f"Found {len(tracks)} tracks in playlist")
            return tracks
            
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {e}")
            return []
    
    def get_new_tracks(self) -> List[Dict[str, Any]]:
        """
        Get tracks that haven't been processed yet.
        
        Returns:
            List of new track information dictionaries
        """
        all_tracks = self.get_playlist_tracks()
        new_tracks = []
        
        for track_data in all_tracks:
            track_id = track_data['track_info']['id']
            if track_id not in self.processed_tracks:
                new_tracks.append(track_data)
        
        logger.info(f"Found {len(new_tracks)} new tracks to process")
        return new_tracks
    
    def remove_track_from_playlist(self, track_id: str) -> bool:
        """
        Remove a track from the playlist.
        
        Args:
            track_id: Spotify track ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.spotify_client:
            logger.error("Spotify client not initialized")
            return False
        
        try:
            track_uri = f"spotify:track:{track_id}"
            
            self.spotify_client.playlist_remove_all_occurrences_of_items(
                config.SPOTIFY_PLAYLIST_ID,
                [track_uri]
            )
            
            logger.info(f"Successfully removed track {track_id} from playlist")
            return True
            
        except Exception as e:
            logger.error(f"Error removing track {track_id} from playlist: {e}")
            return False
    
    def process_track(self, track_data: Dict[str, Any]) -> bool:
        """
        Process a single track: download and remove from playlist if successful.
        
        Args:
            track_data: Track information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        track_info = track_data['track_info']
        track_id = track_info['id']
        
        try:
            log_track_info(track_info, "Processing")
            
            # Format search query
            search_query = format_search_query(track_info)
            
            # Create preferred filename from Spotify track info
            artists = ", ".join([artist['name'] for artist in track_info['artists']])
            title = track_info['name']
            spotify_filename = f"{artists} - {title}"
            
            # Attempt to download using Spotify info for filename
            logger.info(f"Will save as: {spotify_filename}")
            downloaded_file = self.downloader.search_and_download(search_query, spotify_filename)
            
            if downloaded_file:
                log_track_info(track_info, "Successfully downloaded")
                
                # Remove from playlist after successful download
                if self.remove_track_from_playlist(track_id):
                    log_track_info(track_info, "Removed from playlist")
                    self.processed_tracks.add(track_id)
                    return True
                else:
                    logger.error(f"Failed to remove track {track_id} from playlist")
                    return False
            else:
                logger.error(f"Failed to download track: {search_query}")
                # Mark as processed to avoid repeated attempts
                self.processed_tracks.add(track_id)
                return False
                
        except Exception as e:
            logger.error(f"Error processing track {track_id}: {e}")
            return False
    
    def sync_playlist(self) -> Dict[str, int]:
        """
        Sync the playlist by processing all new tracks.
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting playlist sync...")
        
        stats = {
            'new_tracks': 0,
            'downloaded': 0,
            'failed': 0
        }
        
        if not self.spotify_client:
            logger.error("Cannot sync: Spotify client not initialized")
            return stats
        
        new_tracks = self.get_new_tracks()
        stats['new_tracks'] = len(new_tracks)
        
        if not new_tracks:
            logger.info("No new tracks to process")
            return stats
        
        for track_data in new_tracks:
            track_info = track_data['track_info']
            
            if self.process_track(track_data):
                stats['downloaded'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"Sync completed: {stats['downloaded']} downloaded, {stats['failed']} failed")
        return stats
    
    async def start_monitoring(self) -> None:
        """Start the periodic playlist monitoring."""
        logger.info(f"Starting playlist monitoring (interval: {config.POLL_INTERVAL_MINUTES} minutes)")
        
        # Initial sync
        self.sync_playlist()
        
        # Periodic sync
        while True:
            try:
                await asyncio.sleep(config.POLL_INTERVAL_MINUTES * 60)
                logger.info("Running scheduled playlist sync...")
                self.sync_playlist()
                
            except asyncio.CancelledError:
                logger.info("Monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def get_playlist_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured playlist.
        
        Returns:
            Playlist information dictionary or None if error
        """
        if not self.spotify_client:
            return None
        
        try:
            playlist = self.spotify_client.playlist(config.SPOTIFY_PLAYLIST_ID)
            return {
                'name': playlist.get('name', 'Unknown'),
                'description': playlist.get('description', ''),
                'owner': playlist.get('owner', {}).get('display_name', 'Unknown'),
                'tracks_total': playlist.get('tracks', {}).get('total', 0),
                'public': playlist.get('public', False),
                'url': playlist.get('external_urls', {}).get('spotify', '')
            }
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None 
