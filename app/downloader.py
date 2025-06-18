"""Audio downloader module using yt-dlp."""

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp

from .config import config
from .utils import sanitize_filename, clean_track_title

logger = logging.getLogger(__name__)

class AudioDownloader:
    """Handles audio downloading using yt-dlp."""
    
    def __init__(self):
        """Initialize the downloader with default options."""
        self.download_path = Path(config.DOWNLOAD_PATH)
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Check for FFmpeg
        self._check_ffmpeg()
        
        # yt-dlp options for audio download with YouTube anti-bot measures
        base_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'quiet': True,  # Reduce output noise
            'no_warnings': True,  # Hide warnings about missing tokens
            'extract_flat': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            # Anti-bot measures - use more compatible settings
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_creator', 'android', 'web'],
                    'player_skip': ['webpage'],
                    'formats': 'missing_pot',  # Allow formats even without PO tokens
                }
            },
            # Headers to appear more like a browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            },
            # Retry settings
            'retries': 3,
            'fragment_retries': 3,
        }
        
        if shutil.which('ffmpeg'):
            logger.info("FFmpeg found - using high-quality conversion to MP3")
            self.ydl_opts = {
                **base_opts,
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'prefer_ffmpeg': True,
            }
        else:
            logger.info("No FFmpeg found - downloading best available audio format")
            self.ydl_opts = base_opts
    
    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is available for audio conversion."""
        try:
            if shutil.which('ffmpeg') is None:
                logger.info("FFmpeg not found - will download audio in original format")
                logger.info("To get MP3 files, install FFmpeg:")
                logger.info("  Windows: Download from https://www.gyan.dev/ffmpeg/builds/")
                logger.info("  macOS: brew install ffmpeg")
                logger.info("  Ubuntu/Debian: sudo apt install ffmpeg")
            else:
                logger.info("FFmpeg found - will convert to MP3")
        except Exception as e:
            logger.info(f"Could not check for FFmpeg: {e}")
    
    def search_and_download(self, search_query: str, preferred_filename: Optional[str] = None) -> Optional[str]:
        """
        Search YouTube for a track and download the first result.
        
        Args:
            search_query: Search string for YouTube
            preferred_filename: Optional preferred filename (from Spotify info)
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            logger.info(f"Searching and downloading: {search_query}")
            
            # Try multiple search strategies
            search_variations = [
                f"ytsearch1:{search_query}",
                f"ytsearch1:{search_query} audio",
                f"ytsearch1:{search_query} official",
                f"ytsearch1:{search_query} music",
            ]
            
            for i, search_url in enumerate(search_variations):
                try:
                    logger.info(f"Attempt {i+1}: {search_url}")
                    
                    with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                        # Extract info to get the video details
                        info = ydl.extract_info(search_url, download=False)
                        
                        if not info or 'entries' not in info or not info['entries']:
                            logger.warning(f"No results found for: {search_url}")
                            continue
                        
                        entry = info['entries'][0]
                        video_title = entry.get('title', 'Unknown')
                        video_url = entry.get('webpage_url', '')
                        
                        # Check if this video actually has audio formats
                        formats = entry.get('formats', [])
                        audio_formats = [f for f in formats if f.get('acodec') != 'none']
                        
                        if not audio_formats:
                            logger.warning(f"No audio formats found for: {video_title}")
                            continue
                        
                        logger.info(f"Found video with audio: {video_title}")
                        logger.info(f"Video URL: {video_url}")
                        logger.info(f"Available audio formats: {len(audio_formats)}")
                        
                        # Use preferred filename from Spotify, fallback to cleaned YouTube title
                        if preferred_filename:
                            final_filename = sanitize_filename(preferred_filename)
                            logger.info(f"Using Spotify filename: {final_filename}")
                        else:
                            clean_title = clean_track_title(video_title)
                            final_filename = sanitize_filename(clean_title)
                            logger.info(f"Using cleaned YouTube title: {final_filename}")
                        
                        # Create a custom ydl instance with the final filename
                        custom_opts = self.ydl_opts.copy()
                        custom_opts['outtmpl'] = str(self.download_path / f'{final_filename}.%(ext)s')
                        
                        # Download the audio with custom filename
                        with yt_dlp.YoutubeDL(custom_opts) as custom_ydl:
                            custom_ydl.download([video_url])
                        
                        # Wait a moment for file system to sync
                        time.sleep(2)
                        
                        # Find the downloaded file using the final filename
                        downloaded_file = self._find_downloaded_file(final_filename)
                        
                        if downloaded_file:
                            logger.info(f"Successfully downloaded: {downloaded_file}")
                            return str(downloaded_file)
                        else:
                            logger.warning(f"Downloaded file not found for: {video_title}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Attempt {i+1} failed: {e}")
                    continue
            
            logger.error(f"All download attempts failed for: {search_query}")
            return None
                    
        except Exception as e:
            logger.error(f"Error downloading {search_query}: {e}")
            return None
    
    def download_from_url(self, url: str) -> Optional[str]:
        """
        Download audio from a specific URL.
        
        Args:
            url: Direct URL to download from
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        return self.download_from_url_with_filename(url, None)
    
    def download_from_url_with_filename(self, url: str, preferred_filename: Optional[str] = None) -> Optional[str]:
        """
        Download audio from a specific URL with optional custom filename.
        
        Args:
            url: Direct URL to download from
            preferred_filename: Optional custom filename
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            logger.info(f"Downloading from URL: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    logger.warning(f"Could not extract info from URL: {url}")
                    return None
                
                video_title = info.get('title', 'Unknown')
                logger.info(f"Video title: {video_title}")
                
                # Use preferred filename or fall back to cleaned title
                if preferred_filename:
                    final_filename = sanitize_filename(preferred_filename)
                    logger.info(f"Using custom filename: {final_filename}")
                else:
                    clean_title = clean_track_title(video_title)
                    final_filename = sanitize_filename(clean_title)
                    logger.info(f"Using cleaned title: {final_filename}")
                
                # Create custom options with final filename
                custom_opts = self.ydl_opts.copy()
                custom_opts['outtmpl'] = str(self.download_path / f'{final_filename}.%(ext)s')
                
                # Download the audio with custom filename
                with yt_dlp.YoutubeDL(custom_opts) as custom_ydl:
                    custom_ydl.download([url])
                
                # Wait a moment for file system to sync
                time.sleep(2)
                
                # Find the downloaded file using final filename
                downloaded_file = self._find_downloaded_file(final_filename)
                
                if downloaded_file:
                    logger.info(f"Successfully downloaded: {downloaded_file}")
                    return str(downloaded_file)
                else:
                    logger.error(f"Downloaded file not found for URL: {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading from URL {url}: {e}")
            return None
    
    def _find_downloaded_file(self, video_title: str) -> Optional[Path]:
        """
        Find the downloaded file based on video title.
        
        Args:
            video_title: Title of the video that was downloaded
            
        Returns:
            Path to the downloaded file or None if not found
        """
        try:
            logger.info(f"Looking for downloaded file for: {video_title}")
            
            # List all files in download directory for debugging
            all_files = list(self.download_path.iterdir())
            logger.info(f"Files in download directory: {[f.name for f in all_files if f.is_file()]}")
            
            # Filter out .mhtml files and other non-audio formats
            audio_extensions = ['.mp3', '.m4a', '.wav', '.flac', '.ogg', '.webm', '.opus', '.aac']
            web_formats = ['.mhtml', '.html', '.htm', '.part', '.tmp', '.ytdl']
            
            audio_files = []
            
            for file_path in self.download_path.iterdir():
                if file_path.is_file():
                    # Skip web formats and temporary files
                    if file_path.suffix.lower() in web_formats:
                        logger.warning(f"Skipping web/temp file: {file_path.name}")
                        continue
                    
                    # Include audio files
                    if file_path.suffix.lower() in audio_extensions:
                        audio_files.append(file_path)
                        logger.info(f"Found audio file: {file_path.name}")
            
            if audio_files:
                # Return the most recently modified audio file
                latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"Selected latest audio file: {latest_file.name}")
                return latest_file
            
            # If no audio files found, try broader search
            logger.warning("No audio files found, checking all recent files...")
            recent_files = [f for f in all_files if f.is_file() and 
                          f.suffix.lower() not in web_formats and
                          f.stat().st_mtime > (time.time() - 60)]  # Files from last minute
            
            if recent_files:
                latest_file = max(recent_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"Found recent file: {latest_file.name}")
                return latest_file
            
            logger.error("No suitable download file found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding downloaded file: {e}")
            return None
    
    def get_download_info(self, search_query: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video without downloading it.
        
        Args:
            search_query: Search string for YouTube
            
        Returns:
            Dictionary with video information or None if not found
        """
        try:
            search_url = f"ytsearch1:{search_query}"
            
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(search_url, download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    return None
                
                entry = info['entries'][0]
                return {
                    'title': entry.get('title', 'Unknown'),
                    'duration': entry.get('duration', 0),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'url': entry.get('webpage_url', ''),
                    'thumbnail': entry.get('thumbnail', ''),
                }
                
        except Exception as e:
            logger.error(f"Error getting download info for {search_query}: {e}")
            return None 
