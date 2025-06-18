#!/bin/bash

# Default values
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting MixSync with UID: $PUID and GID: $PGID"

# Create group if it doesn't exist
if ! getent group $PGID > /dev/null 2>&1; then
    groupadd -g $PGID appuser
fi

# Create user if it doesn't exist
if ! getent passwd $PUID > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -d /app -s /bin/bash appuser
fi

# Ensure directories exist and have correct permissions
mkdir -p /app/downloads /app/config /app/.spotify_cache
chown -R $PUID:$PGID /app/downloads /app/config /app/.spotify_cache

# If .env file doesn't exist, create from environment variables
if [ ! -f /app/.env ] && [ -n "$SPOTIPY_CLIENT_ID" ]; then
    echo "Creating .env file from environment variables..."
    cat > /app/.env << EOF
SPOTIPY_CLIENT_ID=${SPOTIPY_CLIENT_ID}
SPOTIPY_CLIENT_SECRET=${SPOTIPY_CLIENT_SECRET}
SPOTIPY_REDIRECT_URI=${SPOTIPY_REDIRECT_URI:-http://localhost:8888/callback}
SPOTIFY_PLAYLIST_ID=${SPOTIFY_PLAYLIST_ID}
POLL_INTERVAL_MINUTES=${POLL_INTERVAL_MINUTES:-10}
DOWNLOAD_PATH=${DOWNLOAD_PATH:-./downloads}
EOF
    chown $PUID:$PGID /app/.env
fi

# Execute the command as the specified user
exec gosu $PUID:$PGID "$@" 
