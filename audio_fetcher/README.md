# 🎵 Audio Fetcher

A Dockerized Python application that automatically monitors Spotify playlists and downloads newly added songs using yt-dlp, with a beautiful web interface for manual downloads.

## ✨ Features

- **🎧 Automated Spotify Monitoring**: Watches your playlist and downloads new tracks automatically
- **🌐 Web Interface**: Beautiful Gradio-based UI for manual downloads and system monitoring
- **📱 Multi-Platform Support**: Download from YouTube, SoundCloud, and other platforms
- **🐳 Fully Dockerized**: Easy deployment with Docker and Docker Compose
- **🔄 Smart Playlist Management**: Automatically removes downloaded tracks from playlist
- **📊 Download Statistics**: Track your downloads and system status
- **🛡️ Error Handling**: Robust error handling with retry mechanisms
- **📋 Download History**: Keep track of all your downloads

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Spotify Developer Account
- Spotify Playlist to monitor

### 1. Setup Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Create a new application
3. Note your `Client ID` and `Client Secret`
4. Add `http://localhost:8888/callback` to your Redirect URIs

### 2. Get Your Playlist ID

1. Open your Spotify playlist in the web browser
2. Copy the playlist ID from the URL: `https://open.spotify.com/playlist/PLAYLIST_ID`
3. Format as: `spotify:playlist:PLAYLIST_ID`

### 3. Configure Environment

```bash
# Copy environment template
cp env_example.txt .env

# Edit .env with your values
nano .env
```

Required environment variables:

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
```

### 4. Run with Docker Compose

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### 5. Access the Web Interface

Open your browser and navigate to: `http://localhost:7860`

## 📖 Usage Guide

### Web Interface Tabs

#### 🎵 Manual Download

- Enter any supported media URL (YouTube, SoundCloud, etc.)
- Optionally provide a custom filename
- Preview media information before downloading
- Download files directly to your system

#### 📊 Spotify Monitor

- View connection status and monitoring statistics
- Trigger manual playlist synchronization
- Retry failed downloads
- Monitor automatic download progress

#### 📚 Download History

- View recent download history
- Track successful and failed downloads
- Clear download history

#### ⚙️ System Status

- Monitor system health and statistics
- View download directory information
- Cleanup old files
- Check application configuration

### API Endpoints

The application also provides REST API endpoints:

- `GET /health` - Health check endpoint
- `GET /status` - Detailed system status
- `POST /api/sync` - Trigger manual sync
- `POST /api/retry-failed` - Retry failed downloads
- `POST /api/cleanup` - Cleanup old files

## 🔧 Configuration

### Environment Variables

| Variable                | Description               | Default    |
| ----------------------- | ------------------------- | ---------- |
| `SPOTIPY_CLIENT_ID`     | Spotify API Client ID     | Required   |
| `SPOTIPY_CLIENT_SECRET` | Spotify API Client Secret | Required   |
| `SPOTIFY_PLAYLIST_ID`   | Playlist to monitor       | Required   |
| `POLL_INTERVAL_MINUTES` | Check interval in minutes | 10         |
| `DOWNLOAD_PATH`         | Download directory path   | /downloads |
| `YTDLP_AUDIO_FORMAT`    | Output audio format       | mp3        |
| `YTDLP_AUDIO_QUALITY`   | Audio quality/bitrate     | 192        |
| `HOST`                  | Server host               | 0.0.0.0    |
| `PORT`                  | Server port               | 7860       |
| `LOG_LEVEL`             | Logging level             | INFO       |

### Audio Quality Settings

For MP3 format, supported quality values:

- `128` - Standard quality (smaller files)
- `192` - High quality (recommended)
- `256` - Very high quality
- `320` - Maximum quality (larger files)

## 🏗️ Architecture

```
audio_fetcher/
├── app/
│   ├── main.py              # FastAPI app & startup logic
│   ├── gradio_ui.py         # Gradio web interface
│   ├── spotify_watcher.py   # Spotify polling & management
│   ├── downloader.py        # yt-dlp download functionality
│   ├── utils.py             # Helper functions
│   └── config.py            # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

### Component Overview

- **FastAPI**: Web framework and API server
- **Gradio**: Modern web interface
- **Spotipy**: Spotify API client
- **yt-dlp**: Universal media downloader
- **Docker**: Containerization and deployment

## 🔒 Security

- Runs as non-root user in container
- Environment variable based configuration
- Input validation for all user inputs
- Secure file handling and downloads

## 🚨 Troubleshooting

### Common Issues

#### Spotify Authentication Errors

```bash
# Check your credentials
docker-compose logs | grep -i spotify

# Ensure redirect URI is correctly set in Spotify app settings
```

#### Download Failures

```bash
# Check yt-dlp compatibility
docker-compose exec audio_fetcher yt-dlp --version

# Verify network connectivity
docker-compose exec audio_fetcher ping youtube.com
```

#### Permission Issues

```bash
# Check download directory permissions
ls -la downloads/

# Fix permissions if needed
sudo chown -R $USER:$USER downloads/
```

### Debug Mode

Enable debug mode for detailed error information:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd audio_fetcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python -m app.main
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for personal use only. Please respect copyright laws and terms of service of the platforms you download from. Only download content you have the right to download.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the logs: `docker-compose logs`
3. Check existing issues on GitHub
4. Create a new issue with detailed information

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Universal media downloader
- [Spotipy](https://github.com/spotipy-dev/spotipy) - Spotify API client
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Gradio](https://gradio.app/) - Beautiful web interfaces
