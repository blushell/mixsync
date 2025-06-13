"""
Main FastAPI application for Audio Fetcher.
Integrates Spotify monitoring, download functionality, and Gradio web interface.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from .config import config
from .utils import setup_logging
from .spotify_watcher import SpotifyWatcher
from .gradio_ui import GradioUI
from .downloader import AudioDownloader


# Global instances
spotify_watcher: SpotifyWatcher = None
gradio_ui: GradioUI = None
monitoring_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global spotify_watcher, gradio_ui, monitoring_task
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Audio Fetcher application")
    
    try:
        # Initialize components
        spotify_watcher = SpotifyWatcher()
        gradio_ui = GradioUI(spotify_watcher)
        
        # Initialize Spotify connection
        if config.validate_spotify_config():
            logger.info("Initializing Spotify connection...")
            if await spotify_watcher.initialize():
                logger.info("Spotify connection established")
                
                # Start monitoring task in background
                monitoring_task = asyncio.create_task(
                    spotify_watcher.start_monitoring()
                )
                logger.info("Spotify monitoring started")
            else:
                logger.warning("Failed to initialize Spotify connection")
        else:
            logger.warning("Spotify configuration incomplete - monitoring disabled")
        
        # Create and mount Gradio interface
        gradio_interface = gradio_ui.create_interface()
        
        # Mount Gradio app to FastAPI
        app.mount("/", gradio_interface, name="gradio")
        
        logger.info(f"Application started successfully on {config.HOST}:{config.PORT}")
        
        yield
        
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Audio Fetcher application")
        
        if monitoring_task and not monitoring_task.done():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                logger.info("Monitoring task cancelled")
        
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Audio Fetcher",
    description="Automated audio downloading from Spotify playlists with manual download capability",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to Gradio interface."""
    return RedirectResponse(url="/gradio", status_code=302)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with health status information
    """
    try:
        # Check download directory
        download_path = config.get_download_path()
        download_path_accessible = download_path.exists() and download_path.is_dir()
        
        # Check Spotify connection
        spotify_connected = (
            spotify_watcher is not None and 
            spotify_watcher.spotify_client is not None
        )
        
        # Get basic stats
        downloader = AudioDownloader()
        download_stats = downloader.get_download_stats()
        
        return {
            "status": "healthy",
            "components": {
                "download_path": download_path_accessible,
                "spotify_connected": spotify_connected,
                "monitoring_active": monitoring_task is not None and not monitoring_task.done()
            },
            "download_stats": download_stats,
            "config": {
                "poll_interval_minutes": config.POLL_INTERVAL_MINUTES,
                "audio_format": config.YTDLP_AUDIO_FORMAT,
                "audio_quality": config.YTDLP_AUDIO_QUALITY
            }
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get detailed application status.
    
    Returns:
        Dictionary with detailed status information
    """
    try:
        status = {
            "application": "Audio Fetcher",
            "version": "1.0.0",
            "spotify": {
                "configured": config.validate_spotify_config(),
                "connected": False,
                "status": {}
            },
            "monitoring": {
                "active": False,
                "task_status": "not_started"
            },
            "downloads": {
                "path": str(config.get_download_path()),
                "stats": {}
            }
        }
        
        # Get Spotify status
        if spotify_watcher:
            status["spotify"]["connected"] = spotify_watcher.spotify_client is not None
            status["spotify"]["status"] = spotify_watcher.get_status()
        
        # Get monitoring status
        if monitoring_task:
            status["monitoring"]["active"] = not monitoring_task.done()
            if monitoring_task.done():
                status["monitoring"]["task_status"] = "completed"
            elif monitoring_task.cancelled():
                status["monitoring"]["task_status"] = "cancelled"
            else:
                status["monitoring"]["task_status"] = "running"
        
        # Get download stats
        downloader = AudioDownloader()
        status["downloads"]["stats"] = downloader.get_download_stats()
        
        return status
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync")
async def manual_sync() -> Dict[str, Any]:
    """
    Trigger manual Spotify playlist sync.
    
    Returns:
        Dictionary with sync results
    """
    try:
        if not spotify_watcher:
            raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
        
        if not spotify_watcher.spotify_client:
            raise HTTPException(status_code=503, detail="Spotify not connected")
        
        result = await spotify_watcher.manual_sync()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retry-failed")
async def retry_failed_tracks() -> Dict[str, Any]:
    """
    Retry downloading failed tracks.
    
    Returns:
        Dictionary with retry results
    """
    try:
        if not spotify_watcher:
            raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
        
        await spotify_watcher.retry_failed_tracks()
        
        return {
            "success": True,
            "message": "Retry completed",
            "status": spotify_watcher.get_status()
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Retry failed tracks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cleanup")
async def cleanup_downloads() -> Dict[str, Any]:
    """
    Clean up old downloaded files.
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        downloader = AudioDownloader()
        
        # Get stats before cleanup
        stats_before = downloader.get_download_stats()
        
        # Perform cleanup
        downloader.cleanup_old_files()
        
        # Get stats after cleanup
        stats_after = downloader.get_download_stats()
        
        return {
            "success": True,
            "message": "Cleanup completed",
            "stats_before": stats_before,
            "stats_after": stats_after,
            "files_removed": stats_before["total_files"] - stats_after["total_files"]
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return {
        "error": "Internal server error",
        "detail": str(exc) if config.DEBUG else "An unexpected error occurred"
    }


def run_app():
    """Run the FastAPI application with uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    run_app() 
