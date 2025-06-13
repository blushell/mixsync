🎯 Project Goal

A Dockerized Python app that:

    Watches a specific Spotify playlist on startup and at regular intervals.

    Downloads newly added songs by searching YouTube via yt-dlp.

    Removes the song from the playlist after successful download.

    Provides a simple web UI where users can input a media URL (YouTube, SoundCloud, MP3) to download the audio manually.

🧱 Stack Overview Component Tool / Library Language Python Backend Framework FastAPI Web UI Gradio Spotify API Client spotipy Downloader yt-dlp Scheduler / Timer Async loop or APScheduler Containerization Docker 📁 Project Structure

```
audio_fetcher/
├── app/
│   ├── main.py              # FastAPI app & startup logic
│   ├── gradio_ui.py         # Gradio web interface
│   ├── spotify_watcher.py   # Spotify polling + download/removal logic
│   ├── downloader.py        # yt-dlp logic
│   ├── utils.py             # Helpers (e.g., formatting search strings)
│   └── config.py            # Settings, tokens, env config
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

🔁 Core Workflow A. Spotify Monitoring

    Runs at startup and every X minutes.

    Pulls tracks from a configured playlist.

    For each:

        Builds a search query (e.g., "artist - title").

        Uses yt-dlp to search & download audio.

        If successful, removes the track from the playlist.

B. Gradio Web UI

    Text input for a media URL.

    On submit:

        Validates URL (YouTube, SoundCloud, or direct MP3).

        Uses yt-dlp to download the audio.

C. FastAPI App

    Hosts the Gradio interface (inline).

    Starts Spotify watcher on launch.

    Optional: Add /health or /status endpoints if you need them later.

🐳 Dockerization

    Mounts /downloads folder to persist files.

    Exposes port (e.g., 7860 for Gradio UI).

    Injects env vars (Spotify credentials) via .env.

🧪 Example .env File

```
SPOTIPY_CLIENT_ID=your_id
SPOTIPY_CLIENT_SECRET=your_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
POLL_INTERVAL_MINUTES=10
```
