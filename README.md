# MixSync - Automated Audio Download Solution

A complete audio fetcher application with **automated Spotify playlist sync** and **manual web downloads**.

## 🌟 Features

### 🎵 Automated Playlist Sync

- Watches Spotify playlists for new tracks
- Automatically downloads audio using yt-dlp (YouTube search)
- Removes tracks from playlist after successful download
- Configurable polling interval
- Clean, consistent filenames from Spotify metadata

### 🌐 Web UI for Manual Downloads

- Beautiful, modern web interface
- Download from YouTube, SoundCloud, and other platforms
- Custom filename support
- Real-time download progress
- Mobile-responsive design

### 🚀 API & Monitoring

- FastAPI backend with REST endpoints
- Health checks and status monitoring
- Interactive API documentation at `/docs`

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd MixSync

# 2. Configure environment
cp env_example.txt .env
# Edit .env with your Spotify credentials

# 3. Run with Docker
docker-compose up -d

# 4. Access web UI
# http://localhost:8000
```

### Option 2: Unraid Docker Setup

See the [Unraid Setup Guide](#unraid-setup) below for complete instructions.

### Option 3: Python Direct

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env_example.txt .env
# Edit .env with your credentials

# Run the application
python -m app.main
```

## 🔧 Configuration

### 1. Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your `Client ID` and `Client Secret`
4. Add `http://localhost:8888/callback` to redirect URIs

### 2. Environment Variables

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
POLL_INTERVAL_MINUTES=10
DOWNLOAD_PATH=./downloads
```

### 3. Get Your Playlist ID

1. Open Spotify → Your playlist
2. Click "Share" → "Copy Spotify URI"
3. Use the full URI: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`

## 🐳 Unraid Setup

### Method 1: Using Docker Compose

1. **Prepare directories:**

   ```bash
   mkdir -p /mnt/user/appdata/mixsync/{downloads,config}
   ```

2. **Create environment file:**

   ```bash
   # Copy your configured .env to:
   /mnt/user/appdata/mixsync/.env
   ```

3. **Use the Unraid docker-compose:**
   ```bash
   docker-compose -f docker-compose.unraid.yml up -d
   ```

### Method 2: Unraid Docker UI

**Container Settings:**

- **Name**: `mixsync`
- **Repository**: `your-dockerhub/mixsync` or build locally
- **Network**: `Bridge`
- **WebUI**: `http://[IP]:[PORT:8000]`

**Port Mappings:**

- Container: `8000` → Host: `8000`

**Volume Mappings:**

```
/mnt/user/appdata/mixsync/downloads → /app/downloads
/mnt/user/appdata/mixsync/config → /app/config
/mnt/user/appdata/mixsync/.spotify_cache → /app/.spotify_cache
/mnt/user/appdata/mixsync/.env → /app/.env
```

**Environment Variables:**

```
PUID=99
PGID=100
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://YOUR_UNRAID_IP:8888/callback
SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
POLL_INTERVAL_MINUTES=10
```

### Method 3: Community Applications Template

Install the MixSync template from Unraid's Community Applications for the easiest setup.

## 📱 Usage

### Automated Sync

1. Add tracks to your configured Spotify playlist
2. MixSync automatically detects and downloads them
3. Tracks are removed from playlist after successful download

### Manual Downloads

1. Visit `http://localhost:8000` (or your Unraid IP)
2. Paste any media URL (YouTube, SoundCloud, etc.)
3. Optional: Set custom filename
4. Click download and watch progress

### API Access

- **Web UI**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## 🎵 Audio Quality & Formats

- **Default**: Downloads best available audio format
- **With FFmpeg**: Converts to MP3 (192kbps)
- **Filenames**: Clean format using Spotify metadata
  - Example: `Artist - Track Name.mp3`

## 🔧 API Endpoints

| Endpoint           | Method | Description            |
| ------------------ | ------ | ---------------------- |
| `/`                | GET    | Web UI                 |
| `/health`          | GET    | Health check           |
| `/docs`            | GET    | API documentation      |
| `/playlist/info`   | GET    | Playlist information   |
| `/playlist/tracks` | GET    | All tracks in playlist |
| `/playlist/new`    | GET    | New tracks to download |
| `/sync`            | POST   | Manual sync trigger    |
| `/status`          | GET    | Application status     |
| `/download`        | POST   | Manual download        |

## 🏃‍♂️ Running Options

### Docker (Production)

```bash
docker-compose up -d
```

**Benefits:** Complete setup, auto-restart, health checks

### Python Scripts

```bash
# Full web application
python -m app.main

# Continuous sync only (no web UI)
python run_continuous.py

# Quiet mode
python run_quiet.py

# One-time test
python test_sync.py
```

## 🔍 Troubleshooting

### Spotify Authentication

- Ensure redirect URI is exactly: `http://localhost:8888/callback`
- For Unraid, use your server IP: `http://YOUR_UNRAID_IP:8888/callback`
- Delete `.spotify_cache` and re-authenticate if needed

### Download Issues

- Check internet connection and YouTube availability
- Ensure download directory has write permissions
- Some tracks may not be found on YouTube

### Unraid Specific

- Use PUID=99 and PGID=100 for proper permissions
- Ensure appdata directory exists and is accessible
- Check Docker logs in Unraid UI for errors

## 📁 File Structure

```
MixSync/
├── app/
│   ├── main.py              # FastAPI app & startup
│   ├── web_ui.py           # Gradio web interface
│   ├── spotify_watcher.py   # Playlist monitoring
│   ├── downloader.py        # yt-dlp download logic
│   ├── utils.py             # Helper functions
│   └── config.py            # Configuration management
├── docker-compose.yml       # Standard Docker setup
├── docker-compose.unraid.yml # Unraid-optimized setup
├── Dockerfile              # Container definition
├── Dockerfile.unraid       # Unraid-optimized container
├── requirements.txt        # Python dependencies
├── run_continuous.py       # Continuous sync script
├── run_quiet.py           # Quiet mode script
└── test_sync.py           # Test/validation script
```

## 🎯 What's New

- **🌐 Modern Web UI**: Beautiful interface for manual downloads
- **📱 Mobile Responsive**: Works on all devices
- **🐳 Unraid Ready**: Optimized for Unraid Docker
- **⚡ Real-time Progress**: Live download feedback
- **🔄 Auto-restart**: Resilient container management
- **🎨 Clean Filenames**: Consistent, readable file naming

## 📦 Dependencies

- **FastAPI** - Modern web framework
- **Gradio** - Web UI components
- **spotipy** - Spotify API client
- **yt-dlp** - Universal media downloader
- **uvicorn** - ASGI server
- **python-dotenv** - Environment management

---

**🎵 Perfect for music lovers who want automated playlist management with a beautiful web interface! 🎵**
