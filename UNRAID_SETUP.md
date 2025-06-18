# MixSync Unraid Setup Guide

This guide will help you set up MixSync on your Unraid server using Docker.

## Prerequisites

1. Unraid 6.8+ with Docker enabled
2. Spotify Developer Account and API credentials
3. A Spotify playlist you want to sync

## Setup Methods

### Method 1: Docker Compose (Recommended)

1. **Create the appdata directory:**

   ```bash
   mkdir -p /mnt/user/appdata/mixsync/{downloads,config}
   ```

2. **Create environment file:**

   ```bash
   nano /mnt/user/appdata/mixsync/.env
   ```

   Add your configuration:

   ```env
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://YOUR_UNRAID_IP:8888/callback
   SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
   POLL_INTERVAL_MINUTES=10
   DOWNLOAD_PATH=/app/downloads
   PUID=99
   PGID=100
   ```

3. **Deploy using Docker Compose:**
   ```bash
   cd /mnt/user/appdata/mixsync
   wget https://raw.githubusercontent.com/blushell/mixsync/main/docker-compose.unraid.yml
   docker-compose -f docker-compose.unraid.yml up -d
   ```

### Method 2: Unraid Docker UI

1. **Create directories:**

   ```bash
   mkdir -p /mnt/user/appdata/mixsync/{downloads,config,.spotify_cache}
   ```

2. **Add Container in Unraid UI:**

   - Go to Docker tab in Unraid UI
   - Click "Add Container"
   - Use template URL: `https://raw.githubusercontent.com/blushell/mixsync/main/mixsync-unraid-template.xml`

3. **Configure Container Settings:**

   **Basic Settings:**

   - **Name**: `mixsync`
   - **Repository**: `ghcr.io/blushell/mixsync:latest`
   - **Network**: `Bridge`
   - **WebUI**: `http://[IP]:[PORT:8000]`

   **Port Mappings:**

   ```
   Container Port: 8000 → Host Port: 8000
   ```

   **Volume Mappings:**

   ```
   Host Path: /mnt/user/appdata/mixsync/downloads → Container Path: /app/downloads
   Host Path: /mnt/user/appdata/mixsync/config → Container Path: /app/config
   Host Path: /mnt/user/appdata/mixsync/.spotify_cache → Container Path: /app/.spotify_cache
   ```

   **Environment Variables:**

   ```
   PUID=99
   PGID=100
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://YOUR_UNRAID_IP:8888/callback
   SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
   POLL_INTERVAL_MINUTES=10
   DOWNLOAD_PATH=/app/downloads
   ```

### Method 3: Build from Source

1. **Clone the repository:**

   ```bash
   cd /mnt/user/appdata
   git clone https://github.com/blushell/mixsync.git
   cd mixsync
   ```

2. **Build and run:**
   ```bash
   docker build -f Dockerfile.unraid -t mixsync:local .
   docker-compose -f docker-compose.unraid.yml up -d
   ```

## Configuration

### Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your `Client ID` and `Client Secret`
4. In app settings, add redirect URI: `http://YOUR_UNRAID_IP:8888/callback`
   - Replace `YOUR_UNRAID_IP` with your actual Unraid server IP

### Get Playlist ID

1. Open Spotify and navigate to your playlist
2. Click the three dots (⋯) menu
3. Select "Share" → "Copy Spotify URI"
4. Use the full URI: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`

## Directory Structure

After setup, your appdata directory should look like:

```
/mnt/user/appdata/mixsync/
├── downloads/          # Downloaded audio files
├── config/            # Application config files
├── .spotify_cache/    # Spotify authentication cache
└── .env              # Environment variables (optional)
```

## Usage

1. **Access Web UI**: Navigate to `http://YOUR_UNRAID_IP:8000`

2. **First Run Authentication**:

   - The app will prompt for Spotify authentication on first run
   - Follow the OAuth flow to authorize the application

3. **Automatic Sync**:

   - Add tracks to your configured Spotify playlist
   - MixSync will automatically detect and download them
   - Successfully downloaded tracks are removed from the playlist

4. **Manual Downloads**:
   - Use the web UI to download from YouTube, SoundCloud, etc.
   - Paste any media URL and optionally set a custom filename

## Monitoring

- **Web UI**: `http://YOUR_UNRAID_IP:8000`
- **API Documentation**: `http://YOUR_UNRAID_IP:8000/docs`
- **Health Check**: `http://YOUR_UNRAID_IP:8000/health`
- **Container Logs**: Check Docker logs in Unraid UI

## Troubleshooting

### Common Issues

1. **Permission Errors**:

   - Ensure PUID=99 and PGID=100 (nobody/users)
   - Check directory permissions: `chown -R 99:100 /mnt/user/appdata/mixsync`

2. **Spotify Authentication Fails**:

   - Verify redirect URI matches exactly: `http://YOUR_UNRAID_IP:8888/callback`
   - Check Client ID and Secret are correct
   - Delete `.spotify_cache` directory and retry

3. **Downloads Not Working**:

   - Check internet connectivity from container
   - Verify YouTube/source availability
   - Check container logs for yt-dlp errors

4. **Container Won't Start**:
   - Check environment variables are set correctly
   - Verify all required directories exist
   - Review Docker logs for specific error messages

### Log Locations

- **Container Logs**: Unraid Docker UI → Container → Logs
- **Application Logs**: Available via API at `/logs` endpoint
- **Download Logs**: Check downloads directory for error files

## Updates

To update MixSync:

1. **Pull latest image**:

   ```bash
   docker pull ghcr.io/blushell/mixsync:latest
   ```

2. **Recreate container**:
   ```bash
   docker-compose -f docker-compose.unraid.yml down
   docker-compose -f docker-compose.unraid.yml up -d
   ```

Or use Unraid's built-in update functionality in the Docker UI.

## Support

- **GitHub Issues**: [https://github.com/blushell/mixsync/issues](https://github.com/blushell/mixsync/issues)
- **Documentation**: [https://github.com/blushell/mixsync](https://github.com/blushell/mixsync)

## Advanced Configuration

### Custom Download Formats

You can customize download formats by mounting a custom yt-dlp config:

```
Host Path: /mnt/user/appdata/mixsync/yt-dlp.conf → Container Path: /app/yt-dlp.conf
```

### Network Configuration

For advanced networking (VPN, custom networks), modify the docker-compose file or use Unraid's network settings.

### Backup Configuration

Regularly backup your configuration:

```bash
tar -czf mixsync-backup.tar.gz /mnt/user/appdata/mixsync/
```
