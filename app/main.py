"""Main FastAPI application for audio fetcher."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse

from .config import config
from .spotify_watcher import SpotifyWatcher
from .web_ui import web_ui

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to hold the Spotify watcher
spotify_watcher = None
monitoring_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global spotify_watcher, monitoring_task
    
    # Startup
    logger.info("Starting Audio Fetcher application...")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        raise RuntimeError("Invalid configuration")
    
    # Initialize Spotify watcher
    spotify_watcher = SpotifyWatcher()
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(spotify_watcher.start_monitoring())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Application shutdown complete")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Audio Fetcher",
    description="Spotify playlist sync and audio downloader",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Serve the main web UI page."""
    return web_ui.get_main_page(request)

@app.get("/api")
async def api_root():
    """API root endpoint with basic app info."""
    return {
        "name": "Audio Fetcher",
        "version": "1.0.0",
        "description": "Spotify playlist sync and audio downloader",
        "status": "running",
        "web_ui": "Available at /",
        "api_docs": "Available at /docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global spotify_watcher
    
    if not spotify_watcher or not spotify_watcher.spotify_client:
        raise HTTPException(status_code=503, detail="Spotify client not initialized")
    
    return {"status": "healthy", "spotify_connected": True}

@app.get("/playlist/info")
async def get_playlist_info():
    """Get information about the configured playlist."""
    global spotify_watcher
    
    if not spotify_watcher:
        raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
    
    playlist_info = spotify_watcher.get_playlist_info()
    
    if not playlist_info:
        raise HTTPException(status_code=404, detail="Could not fetch playlist information")
    
    return playlist_info

@app.get("/playlist/tracks")
async def get_playlist_tracks():
    """Get all tracks from the configured playlist."""
    global spotify_watcher
    
    if not spotify_watcher:
        raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
    
    tracks = spotify_watcher.get_playlist_tracks()
    
    return {
        "total_tracks": len(tracks),
        "tracks": [
            {
                "id": track["track_info"]["id"],
                "name": track["track_info"]["name"],
                "artists": [artist["name"] for artist in track["track_info"]["artists"]],
                "added_at": track["added_at"],
                "duration_ms": track["track_info"]["duration_ms"],
                "external_urls": track["track_info"]["external_urls"]
            }
            for track in tracks
        ]
    }

@app.get("/playlist/new")
async def get_new_tracks():
    """Get tracks that haven't been processed yet."""
    global spotify_watcher
    
    if not spotify_watcher:
        raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
    
    new_tracks = spotify_watcher.get_new_tracks()
    
    return {
        "new_tracks_count": len(new_tracks),
        "tracks": [
            {
                "id": track["track_info"]["id"],
                "name": track["track_info"]["name"],
                "artists": [artist["name"] for artist in track["track_info"]["artists"]],
                "added_at": track["added_at"]
            }
            for track in new_tracks
        ]
    }

@app.post("/sync")
async def manual_sync():
    """Manually trigger a playlist sync."""
    global spotify_watcher
    
    if not spotify_watcher:
        raise HTTPException(status_code=503, detail="Spotify watcher not initialized")
    
    try:
        stats = spotify_watcher.sync_playlist()
        return {
            "message": "Sync completed",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.get("/config")
async def get_config():
    """Get current configuration (excluding sensitive data)."""
    return {
        "playlist_id": config.SPOTIFY_PLAYLIST_ID,
        "poll_interval_minutes": config.POLL_INTERVAL_MINUTES,
        "download_path": config.DOWNLOAD_PATH,
        "redirect_uri": config.SPOTIPY_REDIRECT_URI
    }

@app.get("/status")
async def get_status():
    """Get application status and statistics."""
    global spotify_watcher, monitoring_task
    
    status = {
        "spotify_watcher_initialized": spotify_watcher is not None,
        "spotify_client_connected": False,
        "monitoring_active": False,
        "processed_tracks_count": 0
    }
    
    if spotify_watcher:
        status["spotify_client_connected"] = spotify_watcher.spotify_client is not None
        status["processed_tracks_count"] = len(spotify_watcher.processed_tracks)
    
    if monitoring_task:
        status["monitoring_active"] = not monitoring_task.done()
    
    return status

# Web UI endpoints
@app.post("/download")
async def web_download(url: str = Form(...), filename: str = Form(None)):
    """Handle download request from web UI."""
    return await web_ui.download_from_form(url, filename)

@app.get("/download/info")
async def get_media_info(url: str):
    """Get information about a media URL."""
    return await web_ui.get_download_info(url)

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Audio Fetcher application...")
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=False,
        log_level="info"
    ) 
