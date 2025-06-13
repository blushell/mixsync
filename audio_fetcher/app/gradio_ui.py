"""
Gradio web interface for the Audio Fetcher application.
Provides a user-friendly web UI for manual downloads and system monitoring.
"""

import logging
import asyncio
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import gradio as gr

from .downloader import AudioDownloader
from .spotify_watcher import SpotifyWatcher
from .utils import validate_media_url
from .config import config


class GradioUI:
    """Gradio web interface manager."""
    
    def __init__(self, spotify_watcher: SpotifyWatcher):
        self.logger = logging.getLogger(__name__)
        self.downloader = AudioDownloader()
        self.spotify_watcher = spotify_watcher
        self.download_history: list = []
        
    def create_interface(self) -> gr.Blocks:
        """
        Create and configure the Gradio interface.
        
        Returns:
            Configured Gradio Blocks interface
        """
        with gr.Blocks(
            title="Audio Fetcher",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as interface:
            
            # Header
            gr.Markdown("# 🎵 Audio Fetcher")
            gr.Markdown("Download audio from YouTube, SoundCloud, and other platforms")
            
            with gr.Tabs():
                # Manual Download Tab
                with gr.Tab("Manual Download"):
                    self._create_download_tab()
                
                # Spotify Status Tab
                with gr.Tab("Spotify Monitor"):
                    self._create_spotify_tab()
                
                # Download History Tab
                with gr.Tab("Download History"):
                    self._create_history_tab()
                
                # System Status Tab
                with gr.Tab("System Status"):
                    self._create_status_tab()
        
        return interface
    
    def _create_download_tab(self) -> None:
        """Create the manual download tab interface."""
        gr.Markdown("## Manual Audio Download")
        gr.Markdown("Enter a URL from YouTube, SoundCloud, or provide a direct MP3 link")
        
        with gr.Row():
            with gr.Column(scale=3):
                url_input = gr.Textbox(
                    label="Media URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    lines=1
                )
                filename_input = gr.Textbox(
                    label="Custom Filename (optional)",
                    placeholder="Leave empty to use original title",
                    lines=1
                )
                
                with gr.Row():
                    download_btn = gr.Button("Download Audio", variant="primary")
                    preview_btn = gr.Button("Preview Info", variant="secondary")
            
            with gr.Column(scale=2):
                status_output = gr.Textbox(
                    label="Status",
                    lines=3,
                    interactive=False
                )
        
        # Preview info display
        with gr.Row():
            preview_info = gr.JSON(
                label="Media Information",
                visible=False
            )
        
        # Download result display
        download_result = gr.File(
            label="Downloaded File",
            visible=False
        )
        
        # Event handlers
        download_btn.click(
            fn=self._handle_download,
            inputs=[url_input, filename_input],
            outputs=[status_output, download_result]
        )
        
        preview_btn.click(
            fn=self._handle_preview,
            inputs=[url_input],
            outputs=[preview_info, status_output]
        )
    
    def _create_spotify_tab(self) -> None:
        """Create the Spotify monitoring tab interface."""
        gr.Markdown("## Spotify Playlist Monitor")
        gr.Markdown("Monitor and manage automatic playlist downloads")
        
        with gr.Row():
            with gr.Column():
                spotify_status = gr.JSON(
                    label="Spotify Status",
                    value={}
                )
                
                with gr.Row():
                    refresh_status_btn = gr.Button("Refresh Status")
                    manual_sync_btn = gr.Button("Manual Sync", variant="primary")
                    retry_failed_btn = gr.Button("Retry Failed")
            
            with gr.Column():
                sync_result = gr.Textbox(
                    label="Sync Result",
                    lines=5,
                    interactive=False
                )
        
        # Playlist configuration display
        gr.Markdown("### Configuration")
        with gr.Row():
            gr.Textbox(
                label="Playlist ID",
                value=config.SPOTIFY_PLAYLIST_ID,
                interactive=False
            )
            gr.Number(
                label="Poll Interval (minutes)",
                value=config.POLL_INTERVAL_MINUTES,
                interactive=False
            )
        
        # Event handlers
        refresh_status_btn.click(
            fn=self._get_spotify_status,
            outputs=[spotify_status]
        )
        
        manual_sync_btn.click(
            fn=self._handle_manual_sync,
            outputs=[sync_result, spotify_status]
        )
        
        retry_failed_btn.click(
            fn=self._handle_retry_failed,
            outputs=[sync_result, spotify_status]
        )
    
    def _create_history_tab(self) -> None:
        """Create the download history tab interface."""
        gr.Markdown("## Download History")
        
        with gr.Row():
            refresh_history_btn = gr.Button("Refresh History")
            clear_history_btn = gr.Button("Clear History", variant="secondary")
        
        history_display = gr.Dataframe(
            headers=["Timestamp", "Source", "Title", "Status", "File Size"],
            datatype=["str", "str", "str", "str", "str"],
            label="Recent Downloads"
        )
        
        # Event handlers
        refresh_history_btn.click(
            fn=self._get_download_history,
            outputs=[history_display]
        )
        
        clear_history_btn.click(
            fn=self._clear_history,
            outputs=[history_display]
        )
    
    def _create_status_tab(self) -> None:
        """Create the system status tab interface."""
        gr.Markdown("## System Status")
        
        with gr.Row():
            with gr.Column():
                system_info = gr.JSON(
                    label="System Information",
                    value={}
                )
                
            with gr.Column():
                download_stats = gr.JSON(
                    label="Download Statistics",
                    value={}
                )
        
        with gr.Row():
            refresh_system_btn = gr.Button("Refresh System Info")
            cleanup_btn = gr.Button("Cleanup Old Files", variant="secondary")
        
        cleanup_result = gr.Textbox(
            label="Cleanup Result",
            lines=3,
            interactive=False
        )
        
        # Event handlers
        refresh_system_btn.click(
            fn=self._get_system_status,
            outputs=[system_info, download_stats]
        )
        
        cleanup_btn.click(
            fn=self._handle_cleanup,
            outputs=[cleanup_result, download_stats]
        )
    
    def _handle_download(self, url: str, custom_filename: str) -> Tuple[str, Optional[str]]:
        """
        Handle manual download request.
        
        Args:
            url: Media URL to download
            custom_filename: Optional custom filename
            
        Returns:
            Tuple of (status_message, file_path)
        """
        try:
            if not url.strip():
                return "Please enter a URL", None
            
            if not validate_media_url(url):
                return "Invalid or unsupported URL", None
            
            # Run async download in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                filename = custom_filename.strip() if custom_filename else None
                result = loop.run_until_complete(
                    self.downloader.download_from_url(url, filename)
                )
                
                if result:
                    # Add to history
                    self.download_history.append({
                        'timestamp': str(asyncio.get_event_loop().time()),
                        'source': 'manual',
                        'url': url,
                        'filename': result.name,
                        'status': 'success'
                    })
                    
                    return f"✅ Successfully downloaded: {result.name}", str(result)
                else:
                    return "❌ Download failed. Check logs for details.", None
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Download error in UI: {e}")
            return f"❌ Error: {str(e)}", None
    
    def _handle_preview(self, url: str) -> Tuple[Dict[str, Any], str]:
        """
        Handle media preview request.
        
        Args:
            url: Media URL to preview
            
        Returns:
            Tuple of (media_info, status_message)
        """
        try:
            if not url.strip():
                return {}, "Please enter a URL"
            
            if not validate_media_url(url):
                return {}, "Invalid or unsupported URL"
            
            # Run async preview in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                info = loop.run_until_complete(
                    self.downloader.get_media_info(url)
                )
                
                if info:
                    return info, "✅ Media information retrieved"
                else:
                    return {}, "❌ Could not retrieve media information"
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Preview error in UI: {e}")
            return {}, f"❌ Error: {str(e)}"
    
    def _get_spotify_status(self) -> Dict[str, Any]:
        """Get current Spotify watcher status."""
        try:
            return self.spotify_watcher.get_status()
        except Exception as e:
            self.logger.error(f"Error getting Spotify status: {e}")
            return {'error': str(e)}
    
    def _handle_manual_sync(self) -> Tuple[str, Dict[str, Any]]:
        """
        Handle manual Spotify sync request.
        
        Returns:
            Tuple of (sync_result, updated_status)
        """
        try:
            # Run async sync in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.spotify_watcher.manual_sync()
                )
                
                if result['success']:
                    message = f"✅ Sync completed in {result['sync_time']:.1f} seconds"
                else:
                    message = f"❌ Sync failed: {result['error']}"
                
                status = self.spotify_watcher.get_status()
                return message, status
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Manual sync error in UI: {e}")
            return f"❌ Error: {str(e)}", {}
    
    def _handle_retry_failed(self) -> Tuple[str, Dict[str, Any]]:
        """
        Handle retry failed tracks request.
        
        Returns:
            Tuple of (result_message, updated_status)
        """
        try:
            # Run async retry in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    self.spotify_watcher.retry_failed_tracks()
                )
                
                status = self.spotify_watcher.get_status()
                return "✅ Retry completed", status
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Retry failed error in UI: {e}")
            return f"❌ Error: {str(e)}", {}
    
    def _get_download_history(self) -> list:
        """Get download history for display."""
        try:
            return [[
                item.get('timestamp', ''),
                item.get('source', ''),
                item.get('filename', ''),
                item.get('status', ''),
                ''  # File size placeholder
            ] for item in self.download_history[-50:]]  # Last 50 items
        except Exception as e:
            self.logger.error(f"Error getting download history: {e}")
            return []
    
    def _clear_history(self) -> list:
        """Clear download history."""
        self.download_history.clear()
        return []
    
    def _get_system_status(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get system status and download statistics."""
        try:
            system_info = {
                'download_path': str(config.get_download_path()),
                'ytdlp_format': config.YTDLP_FORMAT,
                'audio_format': config.YTDLP_AUDIO_FORMAT,
                'audio_quality': config.YTDLP_AUDIO_QUALITY
            }
            
            download_stats = self.downloader.get_download_stats()
            
            return system_info, download_stats
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}, {}
    
    def _handle_cleanup(self) -> Tuple[str, Dict[str, Any]]:
        """Handle cleanup old files request."""
        try:
            self.downloader.cleanup_old_files()
            stats = self.downloader.get_download_stats()
            return "✅ Cleanup completed", stats
        except Exception as e:
            self.logger.error(f"Cleanup error in UI: {e}")
            return f"❌ Cleanup error: {str(e)}", {}
    
    def _get_custom_css(self) -> str:
        """Get custom CSS for the interface."""
        return """
        .gradio-container {
            max-width: 1200px !important;
        }
        
        .tab-nav {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .download-section {
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
        }
        
        .status-success {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        
        .status-error {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        """ 
