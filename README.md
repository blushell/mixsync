# MixSync - Complete Audio Download Solution

A complete audio fetcher application with both **automated playlist sync** and **manual web downloads**.

## Features

### 🎵 Playlist Sync (Automated)

- Watches a Spotify playlist for new tracks
- Automatically downloads audio using yt-dlp (YouTube search)
- Removes tracks from playlist after successful download
- Configurable polling interval
- Uses clean Spotify track names for files

### 🌐 Web UI (Manual Downloads)

- Beautiful, modern web interface at `http://localhost:8000`
- Download audio from any supported platform (YouTube, SoundCloud, etc.)
- Custom filename support
- Real-time download progress
- Mobile-responsive design

### 🚀 API & Monitoring

- FastAPI backend with REST endpoints
- Comprehensive monitoring and status endpoints
- Interactive API documentation at `/docs`

## Setup

### 1. Install Dependencies

```bash
cd audio_fetcher
pip install --upgrade pip
pip install -r requirements.txt
```

**Optional: Use a virtual environment (recommended for isolation)**

```bash
# Create a virtual environment
python -m venv audio_fetcher_env
source audio_fetcher_env/bin/activate  # On Windows: audio_fetcher_env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your `Client ID` and `Client Secret`
4. Add `http://localhost:8888/callback` to your app's redirect URIs

### 3. Environment Configuration

1. Copy the example environment file:

   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` with your credentials:
   ```
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
   SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
   POLL_INTERVAL_MINUTES=10
   DOWNLOAD_PATH=./downloads
   ```

### 4. Get Your Playlist ID

1. Open Spotify and go to your playlist
2. Click "Share" → "Copy Spotify URI"
3. The URI looks like: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`
4. Use the full URI in your `.env` file

## Running the Application

### Option 1: Docker (Recommended for Production)

The easiest way to run the complete application is with Docker, which includes FFmpeg automatically:

```bash
# 1. Set up your .env file first
cp env_example.txt .env
# Edit .env with your Spotify credentials

# 2. Run with Docker Compose
docker-compose up -d

# 3. Access the application
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs

# 4. Check logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

**Docker Benefits:**

- ✅ **Complete application**: Auto-sync + Web UI + API in one container
- ✅ **FFmpeg included**: No additional setup needed
- ✅ **Persistent data**: Downloads and auth cache preserved
- ✅ **Auto-restart**: Restarts automatically if container crashes
- ✅ **Health monitoring**: Built-in health checks
- ✅ **Easy management**: Simple start/stop/update

#### Alternative Docker Commands

```bash
# Build and run manually
docker build -t audio-fetcher .
docker run -d --name audio-fetcher \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/.spotify_cache:/app/.spotify_cache \
  audio-fetcher

# View logs
docker logs -f audio-fetcher

# Access web UI: http://localhost:8000

# Stop
docker stop audio-fetcher
```

### Option 2: Continuous Running (Python Direct)

#### Quiet Mode (Recommended)

```bash
cd audio_fetcher
python run_quiet.py
```

#### Verbose Mode (for debugging)

```bash
cd audio_fetcher
python run_continuous.py
```

Both will:

- Run continuously in the background
- Automatically download new tracks
- Log all activity to `mixsync.log` and console
- No user prompts - fully automated

**Quiet mode** shows only important events, **verbose mode** shows all download details.

### Option 2: Simple Test Script

Run the test script to verify everything is working:

```bash
cd audio_fetcher
python test_sync.py
```

This script will:

- Validate your configuration
- Connect to Spotify
- Show playlist information
- List tracks to be downloaded
- Ask if you want to proceed with sync (interactive)

### Option 3: Full Web Application (Recommended)

Start the complete application with both playlist sync AND web UI:

```bash
cd audio_fetcher
python -m app.main
```

Or with uvicorn for development:

```bash
cd audio_fetcher
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then visit:

- **`http://localhost:8000/`** - 🌐 **Web UI for manual downloads**
- `http://localhost:8000/docs` - 📚 Interactive API documentation
- `http://localhost:8000/api` - 📊 API info and status

### Available API Endpoints

- `http://localhost:8000/health` - Health check
- `http://localhost:8000/playlist/info` - Playlist information
- `http://localhost:8000/playlist/tracks` - All tracks
- `http://localhost:8000/playlist/new` - New tracks to download
- `http://localhost:8000/sync` - Manual sync trigger (POST)
- `http://localhost:8000/status` - Application status
- `http://localhost:8000/download` - Manual download (POST)
- `http://localhost:8000/download/info` - Get media info (GET)

## How It Works

### 🔄 Automated Playlist Sync

1. **Startup**: App connects to Spotify and starts monitoring
2. **Monitoring**: Every `POLL_INTERVAL_MINUTES`, checks for new tracks
3. **Download**: For each new track:
   - Formats search query: "Artist - Track Name"
   - Searches YouTube using yt-dlp
   - Downloads the first result and saves with clean Spotify filename
4. **Cleanup**: Removes successfully downloaded tracks from playlist
5. **Repeat**: Continues monitoring for new tracks

### 🌐 Manual Web Downloads

1. **Access**: Visit `http://localhost:8000` in your browser
2. **Input**: Paste any supported media URL (YouTube, SoundCloud, etc.)
3. **Customize**: Optionally set a custom filename
4. **Download**: Click download and watch real-time progress
5. **Complete**: Files saved to your configured download directory

## Downloads

- Files are saved to the `DOWNLOAD_PATH` directory (default: `./downloads`)
- **Without FFmpeg**: Downloads in original format (usually .m4a, .webm, or .opus)
- **With FFmpeg**: Converts to MP3, 192K bitrate
- **Filename**: Uses clean Spotify track information for consistent, readable filenames

### Filename Sources

**Primary (Spotify-based)**: For playlist sync, files are named using the original Spotify track information:

- Format: `Artist - Track Name`
- Examples:
  - `Jessica Audiffred - Don't Speak (feat. GG Magree)`
  - `ATLiens - BLACK SHEEP (feat. GG MAGREE)`
  - `Post Malone - Congratulations ft. Quavo`

**Fallback (YouTube title cleaning)**: For manual downloads or when Spotify info isn't available:

- Automatically removes YouTube video metadata like "[Official Music Video]", "(Official Audio)", etc.
- Examples:
  - `ATLiens - BLACK SHEEP (feat. GG MAGREE) [Official Music Video]` → `ATLiens - BLACK SHEEP (feat. GG MAGREE)`
  - `Post Malone - Congratulations ft. Quavo (Official Video)` → `Post Malone - Congratulations ft. Quavo`

### Installing FFmpeg (Optional)

FFmpeg is **optional** but recommended for consistent MP3 output:

- **Windows**: Download from [FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

The app works fine without FFmpeg - you'll just get audio in whatever format YouTube provides.

## Authentication

On first run, you'll be redirected to Spotify for authorization. This creates a `.spotify_cache` file to store your token.

## Logging

The application logs all activities including:

- Spotify connections
- Track discoveries
- Download attempts
- Successes and failures

## API Endpoints

### GET `/`

Basic application information

### GET `/health`

Health check - returns 200 if Spotify is connected

### GET `/playlist/info`

Information about your configured playlist

### GET `/playlist/tracks`

All tracks currently in the playlist

### GET `/playlist/new`

Tracks that haven't been processed yet

### POST `/sync`

Manually trigger a sync operation

### GET `/status`

Application status and statistics

### GET `/config`

Current configuration (sensitive data excluded)

## Troubleshooting

### Spotify Authentication Issues

- Make sure your redirect URI is exactly: `http://localhost:8888/callback`
- Check that your Client ID and Secret are correct
- Delete `.spotify_cache` file and re-authenticate

### Download Issues

- Ensure you have FFmpeg installed for audio conversion
- Check that the download directory exists and is writable
- Some tracks might not be found on YouTube

### Permission Issues

- Make sure your Spotify app has the correct scopes
- You need to be able to modify the playlist (owner or collaborative)

## ✨ What's New in V2

- **🌐 Beautiful Web UI**: Modern, responsive interface for manual downloads
- **📱 Mobile Support**: Works perfectly on phones and tablets
- **🎨 Custom Filenames**: Set your own filenames for downloads
- **⚡ Real-time Progress**: Live download status and feedback
- **🔗 Universal Support**: Download from any yt-dlp supported platform
- **🚀 Zero Setup**: Just start the app and visit localhost:8000
- **🐳 Docker Ready**: Complete application runs perfectly in Docker

The complete application now includes both automated playlist monitoring AND a beautiful web interface for manual downloads!

## 🚀 Deployment Options

| Option | Use Case | Features | Resource Usage |
| --- | --- | --- | --- |
| **Docker** | Production, easy deployment | Auto-sync + Web UI + API | Medium |
| **FastAPI App** | Development, home server | Auto-sync + Web UI + API | Medium |
| **Lightweight Scripts** | Headless servers, VPS | Auto-sync only | Minimal |
| **Test Script** | One-time testing | Interactive sync | Minimal |

## Dependencies

- `fastapi` - Web framework
- `spotipy` - Spotify API client
- `yt-dlp` - YouTube downloader
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variable management
- `APScheduler` - Task scheduling
