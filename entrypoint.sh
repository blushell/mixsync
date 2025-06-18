#!/bin/bash

# Unraid entrypoint script for proper user permissions

# Set user and group IDs from environment (Unraid defaults)
PUID=${PUID:-99}
PGID=${PGID:-100}

echo "Setting up user permissions..."
echo "PUID: $PUID"
echo "PGID: $PGID"

# Create group if it doesn't exist
if ! getent group $PGID > /dev/null 2>&1; then
    groupadd -g $PGID mixsync
fi

# Create user if it doesn't exist
if ! getent passwd $PUID > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -d /app -s /bin/bash mixsync
fi

# Ensure proper ownership of directories
echo "Setting up directory permissions..."
chown -R $PUID:$PGID /app/downloads 2>/dev/null || true
chown -R $PUID:$PGID /app/config 2>/dev/null || true
chown -R $PUID:$PGID /app/.spotify_cache 2>/dev/null || true
chmod -R 755 /app/downloads 2>/dev/null || true
chmod -R 755 /app/config 2>/dev/null || true

echo "Starting MixSync as user ID $PUID..."

# Execute the main command as the correct user
exec gosu $PUID:$PGID "$@" 
