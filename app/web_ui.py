"""Web UI module for manual audio downloads."""

import logging
from typing import Optional
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .downloader import AudioDownloader
from .utils import sanitize_filename

logger = logging.getLogger(__name__)

# HTML template for the web UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Fetcher - Manual Download</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .title {
            color: #333;
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1rem;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 1.1rem;
        }
        
        .form-input {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #fafbfc;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.1);
        }
        
        .form-input::placeholder {
            color: #999;
        }
        
        .download-btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .download-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.3);
        }
        
        .download-btn:active {
            transform: translateY(-1px);
        }
        
        .download-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .supported-sites {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        
        .supported-sites h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .sites-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        
        .site-tag {
            background: white;
            padding: 8px 12px;
            border-radius: 8px;
            text-align: center;
            color: #666;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .status-message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-weight: 500;
            display: none;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status-loading {
            background: #cce7f0;
            color: #004085;
            border: 1px solid #b6d4ea;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .api-info {
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
        
        .api-info a {
            color: #667eea;
            text-decoration: none;
        }
        
        .api-info a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🎵 Audio Fetcher</h1>
            <p class="subtitle">Download audio from any supported platform</p>
        </div>
        
        <form id="downloadForm" onsubmit="downloadAudio(event)">
            <div class="form-group">
                <label for="url" class="form-label">Media URL</label>
                <input 
                    type="url" 
                    id="url" 
                    name="url" 
                    class="form-input"
                    placeholder="https://www.youtube.com/watch?v=..."
                    required
                >
            </div>
            
            <div class="form-group">
                <label for="filename" class="form-label">Custom Filename (Optional)</label>
                <input 
                    type="text" 
                    id="filename" 
                    name="filename" 
                    class="form-input"
                    placeholder="Artist - Song Name"
                >
            </div>
            
            <button type="submit" class="download-btn" id="downloadBtn">
                Download Audio
            </button>
        </form>
        
        <div id="statusMessage" class="status-message"></div>
        
        <div class="supported-sites">
            <h3>Supported Platforms</h3>
            <div class="sites-list">
                <div class="site-tag">YouTube</div>
                <div class="site-tag">SoundCloud</div>
                <div class="site-tag">Bandcamp</div>
                <div class="site-tag">Vimeo</div>
                <div class="site-tag">Direct MP3</div>
                <div class="site-tag">Many More</div>
            </div>
        </div>
        
        <div class="api-info">
            <p>Powered by <a href="https://github.com/yt-dlp/yt-dlp" target="_blank">yt-dlp</a></p>
            <p>API available at <a href="/docs" target="_blank">/docs</a></p>
        </div>
    </div>

    <script>
        async function downloadAudio(event) {
            event.preventDefault();
            
            const form = event.target;
            const url = form.url.value.trim();
            const filename = form.filename.value.trim();
            const statusMessage = document.getElementById('statusMessage');
            const downloadBtn = document.getElementById('downloadBtn');
            
            // Reset status
            statusMessage.style.display = 'none';
            
            // Validate URL
            if (!url) {
                showStatus('Please enter a valid URL', 'error');
                return;
            }
            
            // Show loading state
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<span class="loading-spinner"></span>Downloading...';
            showStatus('Starting download...', 'loading');
            
            try {
                const formData = new FormData();
                formData.append('url', url);
                if (filename) {
                    formData.append('filename', filename);
                }
                
                const response = await fetch('/download', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showStatus(`✅ Successfully downloaded: ${result.filename}`, 'success');
                    form.reset();
                } else {
                    showStatus(`❌ Download failed: ${result.detail || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Network error: ${error.message}`, 'error');
            } finally {
                // Reset button state
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = 'Download Audio';
            }
        }
        
        function showStatus(message, type) {
            const statusMessage = document.getElementById('statusMessage');
            statusMessage.textContent = message;
            statusMessage.className = `status-message status-${type}`;
            statusMessage.style.display = 'block';
            
            // Auto-hide success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    statusMessage.style.display = 'none';
                }, 5000);
            }
        }
        
        // Auto-focus the URL input
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('url').focus();
        });
    </script>
</body>
</html>
'''

class WebUI:
    """Web UI handler for manual downloads."""
    
    def __init__(self):
        """Initialize the web UI with downloader instance."""
        self.downloader = AudioDownloader()
    
    def get_main_page(self, request: Request) -> HTMLResponse:
        """
        Serve the main web UI page.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response with the web UI
        """
        return HTMLResponse(content=HTML_TEMPLATE)
    
    async def download_from_form(
        self, 
        url: str = Form(...), 
        filename: Optional[str] = Form(None)
    ) -> JSONResponse:
        """
        Handle download request from the web form.
        
        Args:
            url: Media URL to download from
            filename: Optional custom filename
            
        Returns:
            JSON response with download result
        """
        try:
            logger.info(f"Web UI download request: {url}")
            
            # Validate URL
            if not url or not url.strip():
                raise HTTPException(status_code=400, detail="URL is required")
            
            url = url.strip()
            
            # Basic URL validation
            if not (url.startswith('http://') or url.startswith('https://')):
                raise HTTPException(status_code=400, detail="Invalid URL format")
            
            # Prepare filename
            preferred_filename = None
            if filename and filename.strip():
                preferred_filename = sanitize_filename(filename.strip())
                logger.info(f"Using custom filename: {preferred_filename}")
            
            # Download the audio
            if preferred_filename:
                # For custom filename, we need to modify the downloader behavior
                downloaded_file = self.downloader.download_from_url_with_filename(url, preferred_filename)
            else:
                downloaded_file = self.downloader.download_from_url(url)
            
            if downloaded_file:
                logger.info(f"Web UI download successful: {downloaded_file}")
                return JSONResponse(content={
                    "success": True,
                    "message": "Download completed successfully",
                    "filename": downloaded_file
                })
            else:
                logger.error(f"Web UI download failed: {url}")
                raise HTTPException(status_code=500, detail="Download failed")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Web UI download error: {e}")
            raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")
    
    async def get_download_info(self, url: str) -> JSONResponse:
        """
        Get information about a URL without downloading.
        
        Args:
            url: Media URL to get info for
            
        Returns:
            JSON response with media information
        """
        try:
            info = self.downloader.get_download_info(url)
            
            if info:
                return JSONResponse(content={
                    "success": True,
                    "info": info
                })
            else:
                raise HTTPException(status_code=404, detail="Could not get media information")
                
        except Exception as e:
            logger.error(f"Error getting download info: {e}")
            raise HTTPException(status_code=500, detail=f"Info error: {str(e)}")

# Global web UI instance
web_ui = WebUI() 
