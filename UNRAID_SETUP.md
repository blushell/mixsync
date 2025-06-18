# MixSync Unraid Setup Guide

This guide will help you install and configure MixSync on your Unraid server using Docker.

## 🎯 Prerequisites

- Unraid 6.8+ with Docker support enabled
- Spotify Developer Account (free)
- Internet connection for downloading audio

## 🚀 Quick Setup Methods

### Method 1: Community Applications (Easiest)

1. **Install Community Applications** (if not already installed)

   - Go to **Apps** tab in Unraid
   - Install Community Applications plugin

2. **Search and Install MixSync**
   - Search for "MixSync" in Community Applications
   - Click Install and configure (see configuration section below)

### Method 2: Docker Compose (Recommended for Advanced Users)

1. **Prepare directories:**

   ```bash
   # SSH into your Unraid server
   mkdir -p /mnt/user/appdata/mixsync/{downloads,config}
   ```

2. **Setup environment file:**

   ```bash
   # Copy and configure environment
   cp env_unraid_example.txt /mnt/user/appdata/mixsync/.env
   # Edit with your Spotify credentials (see configuration below)
   ```

3. **Deploy with docker-compose:**
   ```bash
   # In your MixSync directory
   docker-compose -f docker-compose.unraid.yml up -d
   ```

### Method 3: Manual Docker Container

1. **Go to Docker tab in Unraid**
2. **Click "Add Container"**
3. **Fill in the template values** (see configuration section)

## 🔧 Configuration

### 1. Spotify API Setup

1. **Create Spotify App:**

   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Click "Create App"
   - Name: "MixSync" (or any name)
   - Description: "Audio downloader for personal use"
   - Website: `http://localhost` (not important)
   - **Redirect URI**: `http://YOUR_UNRAID_IP:8888/callback`
     - Replace `YOUR_UNRAID_IP` with your actual Unraid server IP
     - Example: `http://192.168.1.100:8888/callback`

2. **Get Credentials:**
   - Copy your **Client ID** and **Client Secret**
   - You'll need these for the Docker configuration

### 2. Get Playlist ID

1. **Open Spotify** → Go to your playlist
2. **Click Share** → **Copy Spotify URI**
3. **Use the full URI**: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`

### 3. Docker Container Configuration

#### Container Settings:

```
Name: mixsync
Repository: yourusername/mixsync
Network Type: Bridge
Console shell command: Bash
```

#### Port Mappings:

```
Container Port: 8000 → Host Port: 8000
Connection Type: TCP
```

#### Volume Mappings:

```
Host Path: /mnt/user/appdata/mixsync/downloads → Container Path: /app/downloads
Host Path: /mnt/user/appdata/mixsync/config → Container Path: /app/config
Host Path: /mnt/user/appdata/mixsync/.spotify_cache → Container Path: /app/.spotify_cache
Host Path: /mnt/user/appdata/mixsync/.env → Container Path: /app/.env
```

#### Environment Variables:

```
PUID = 99
PGID = 100
SPOTIPY_CLIENT_ID = your_spotify_client_id
SPOTIPY_CLIENT_SECRET = your_spotify_client_secret
SPOTIFY_REDIRECT_URI = http://YOUR_UNRAID_IP:8888/callback
SPOTIFY_PLAYLIST_ID = spotify:playlist:your_playlist_id
POLL_INTERVAL_MINUTES = 10
```

## 📁 Directory Structure

After setup, your Unraid appdata will look like:

```
/mnt/user/appdata/mixsync/
├── downloads/          # Downloaded audio files
├── config/            # Application logs and config
├── .env              # Environment configuration
└── .spotify_cache    # Spotify authentication (auto-created)
```

## 🎵 First Run & Authentication

1. **Start the container** and wait for it to be healthy
2. **Visit the web UI**: `http://YOUR_UNRAID_IP:8000`
3. **Initial Spotify auth** will redirect you to authorize the app
4. **Complete authentication** and you'll be redirected back
5. **Verify setup** by checking the container logs

## 💻 Usage

### Web UI Access

- **Main Interface**: `http://YOUR_UNRAID_IP:8000`
- **API Documentation**: `http://YOUR_UNRAID_IP:8000/docs`
- **Health Check**: `http://YOUR_UNRAID_IP:8000/health`

### Automated Sync

1. Add tracks to your configured Spotify playlist
2. MixSync automatically detects and downloads them every 10 minutes
3. Downloaded tracks are removed from the playlist

### Manual Downloads

1. Open the web UI
2. Paste any YouTube/SoundCloud URL
3. Optional: Set custom filename
4. Click download and watch progress

## 🔧 Unraid-Specific Features

### Proper Permissions

- Uses PUID=99 and PGID=100 (standard Unraid nobody user)
- All files are owned by the correct user for Unraid access

### Integration

- **WebUI link** in Unraid Docker tab
- **Health monitoring** shows container status
- **Auto-restart** if container fails
- **Logs** accessible through Unraid Docker interface

### File Management

- Downloads appear in `/mnt/user/appdata/mixsync/downloads`
- Accessible via Unraid shares
- Compatible with Unraid file permissions

## 🔍 Troubleshooting

### Container Won't Start

- Check Docker logs in Unraid interface
- Verify all required environment variables are set
- Ensure directories exist: `/mnt/user/appdata/mixsync/`

### Spotify Authentication Issues

- Verify redirect URI matches exactly: `http://YOUR_UNRAID_IP:8888/callback`
- Check Client ID and Secret are correct
- Delete `.spotify_cache` file and restart container

### Permission Issues

- Ensure PUID=99 and PGID=100 are set
- Check that appdata directory is accessible
- Restart container if permission errors occur

### Download Issues

- Check internet connectivity from container
- Verify YouTube is accessible
- Some tracks may not be available on YouTube

### Can't Access Web UI

- Verify port 8000 is not blocked by firewall
- Check container is running and healthy
- Try accessing from different device on network

## 📊 Monitoring

### Container Health

- Unraid shows health status in Docker tab
- Health check runs every 30 seconds
- Green = healthy, Red = unhealthy

### Logs

- View logs through Unraid Docker interface
- Or use: `docker logs mixsync`
- Logs show sync activity and any errors

### File Activity

- Downloads appear in real-time in downloads directory
- Check file timestamps to verify recent activity
- Web UI shows download progress

## 🔄 Updates

### Updating the Container

1. **Stop** the container in Unraid
2. **Update** the repository (if using external image)
3. **Start** the container again
4. **Verify** functionality after update

### Backup Important Data

- **Environment file**: `/mnt/user/appdata/mixsync/.env`
- **Spotify cache**: `/mnt/user/appdata/mixsync/.spotify_cache`
- **Downloaded files**: `/mnt/user/appdata/mixsync/downloads`

## 🎯 Performance Tips

- **Set appropriate poll interval** (10-30 minutes recommended)
- **Monitor disk space** in downloads directory
- **Use SSD** for appdata if possible for better performance
- **Check network bandwidth** if downloading many files

---

## 🆘 Support

If you encounter issues:

1. **Check the logs** first (Docker tab → MixSync → Logs)
2. **Verify configuration** matches this guide
3. **Test Spotify connection** using the health endpoint
4. **Create GitHub issue** with logs and configuration details

**Happy music downloading! 🎵**
