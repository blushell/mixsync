"""
Audio downloader module using yt-dlp.
Handles downloading audio from various platforms including YouTube and SoundCloud.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

from .config import config
from .utils import get_safe_filename, validate_media_url


class AudioDownloader:
    """Audio downloader class using yt-dlp."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.download_path = config.get_download_path()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def get_ytdlp_options(self, output_template: Optional[str] = None) -> Dict[str, Any]:
        """
        Get yt-dlp options configuration.
        
        Args:
            output_template: Optional custom output template
            
        Returns:
            Dictionary of yt-dlp options
        """
        if not output_template:
            output_template = str(self.download_path / "%(title)s.%(ext)s")
            
        return {
            'format': config.YTDLP_FORMAT,
            'outtmpl': output_template,
            'extractaudio': True,
            'audioformat': config.YTDLP_AUDIO_FORMAT,
            'audioquality': config.YTDLP_AUDIO_QUALITY,
            'embed_info_json': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writeautomaticsub': False,
            'writesubtitles': False,
            'ignoreerrors': True,
            'no_warnings': False,
            'extractflat': False,
            'youtube_include_dash_manifest': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': config.YTDLP_AUDIO_FORMAT,
                'preferredquality': config.YTDLP_AUDIO_QUALITY,
            }]
        }
    
    async def search_and_download(self, search_query: str, max_results: int = 1) -> Optional[Path]:
        """
        Search for audio on YouTube and download the first result.
        
        Args:
            search_query: Search query string
            max_results: Maximum number of results to consider
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            self.logger.info(f"Searching for: {search_query}")
            
            # Use executor to run blocking yt-dlp operations
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._search_and_download_sync, 
                search_query, 
                max_results
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in search_and_download: {e}")
            return None
    
    def _search_and_download_sync(self, search_query: str, max_results: int) -> Optional[Path]:
        """
        Synchronous version of search and download for use with executor.
        
        Args:
            search_query: Search query string
            max_results: Maximum number of results to consider
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            # Search YouTube for the query
            search_url = f"ytsearch{max_results}:{search_query}"
            
            # Custom output filename
            safe_filename = get_safe_filename(search_query)
            output_template = str(self.download_path / f"{safe_filename}.%(ext)s")
            
            ydl_opts = self.get_ytdlp_options(output_template)
            
            downloaded_files = []
            
            def hook(d):
                if d['status'] == 'finished':
                    downloaded_files.append(Path(d['filename']))
                    self.logger.info(f"Downloaded: {d['filename']}")
            
            ydl_opts['progress_hooks'] = [hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check if results exist
                info = ydl.extract_info(search_url, download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    self.logger.warning(f"No results found for: {search_query}")
                    return None
                
                # Download the first entry
                first_entry = info['entries'][0]
                if first_entry:
                    self.logger.info(f"Found: {first_entry.get('title', 'Unknown')} by {first_entry.get('uploader', 'Unknown')}")
                    ydl.download([first_entry['webpage_url']])
                    
                    if downloaded_files:
                        return downloaded_files[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in sync download: {e}")
            return None
    
    async def download_from_url(self, url: str, custom_filename: Optional[str] = None) -> Optional[Path]:
        """
        Download audio from a direct URL.
        
        Args:
            url: Media URL to download
            custom_filename: Optional custom filename
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            if not validate_media_url(url):
                self.logger.error(f"Invalid or unsupported URL: {url}")
                return None
            
            self.logger.info(f"Downloading from URL: {url}")
            
            # Use executor to run blocking yt-dlp operations
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._download_from_url_sync, 
                url, 
                custom_filename
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error downloading from URL: {e}")
            return None
    
    def _download_from_url_sync(self, url: str, custom_filename: Optional[str]) -> Optional[Path]:
        """
        Synchronous version of URL download for use with executor.
        
        Args:
            url: Media URL to download
            custom_filename: Optional custom filename
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            # Determine output filename
            if custom_filename:
                safe_filename = get_safe_filename(custom_filename)
                output_template = str(self.download_path / f"{safe_filename}.%(ext)s")
            else:
                output_template = str(self.download_path / "%(title)s.%(ext)s")
            
            ydl_opts = self.get_ytdlp_options(output_template)
            
            downloaded_files = []
            
            def hook(d):
                if d['status'] == 'finished':
                    downloaded_files.append(Path(d['filename']))
                    self.logger.info(f"Downloaded: {d['filename']}")
            
            ydl_opts['progress_hooks'] = [hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
                if downloaded_files:
                    return downloaded_files[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in sync URL download: {e}")
            return None
    
    async def get_media_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract media information without downloading.
        
        Args:
            url: Media URL to analyze
            
        Returns:
            Dictionary with media information or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._get_media_info_sync, 
                url
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting media info: {e}")
            return None
    
    def _get_media_info_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous version of media info extraction.
        
        Args:
            url: Media URL to analyze
            
        Returns:
            Dictionary with media information or None if failed
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    return {
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'description': info.get('description', ''),
                        'thumbnail': info.get('thumbnail', ''),
                        'webpage_url': info.get('webpage_url', url)
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in sync media info extraction: {e}")
            return None
    
    def cleanup_old_files(self, max_files: int = 100) -> None:
        """
        Clean up old downloaded files to manage storage.
        
        Args:
            max_files: Maximum number of files to keep
        """
        try:
            # Get all audio files in download directory
            audio_files = []
            for pattern in ['*.mp3', '*.m4a', '*.wav', '*.flac']:
                audio_files.extend(self.download_path.glob(pattern))
            
            # Sort by modification time (newest first)
            audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess files
            if len(audio_files) > max_files:
                files_to_remove = audio_files[max_files:]
                for file_path in files_to_remove:
                    try:
                        file_path.unlink()
                        self.logger.info(f"Removed old file: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Error removing file {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_download_stats(self) -> Dict[str, int]:
        """
        Get statistics about downloaded files.
        
        Returns:
            Dictionary with download statistics
        """
        try:
            audio_files = []
            for pattern in ['*.mp3', '*.m4a', '*.wav', '*.flac']:
                audio_files.extend(self.download_path.glob(pattern))
            
            total_size = sum(f.stat().st_size for f in audio_files)
            
            return {
                'total_files': len(audio_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_bytes': total_size
            }
            
        except Exception as e:
            self.logger.error(f"Error getting download stats: {e}")
            return {'total_files': 0, 'total_size_mb': 0, 'total_size_bytes': 0} 
