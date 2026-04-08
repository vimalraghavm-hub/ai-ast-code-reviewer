#!/bin/bash
# Robust prestart script for Reflex on Hugging Face Spaces
# This script handles frontend export, database init, and app launch.

LOGFILE="/home/user/app/startup.log"
echo "$(date): Starting prestart sequence..." > "$LOGFILE"

# Ensure we're in the right directory
cd /home/user/app || cd .
echo "$(date): Working directory: $(pwd)" >> "$LOGFILE"

# Build the frontend (moved from Dockerfile to here so Docker builds are fast).
# This only takes ~60-90s on first run; subsequent container restarts can skip
# this if the .web/dist directory already exists.
if [ ! -d ".web/dist" ]; then
    echo "$(date): Building frontend with reflex export..." >> "$LOGFILE"
    reflex export --frontend-only --no-zip >> "$LOGFILE" 2>&1
    echo "$(date): Frontend export complete." >> "$LOGFILE"
else
    echo "$(date): Frontend already built, skipping export." >> "$LOGFILE"
fi

# Force database initialization
echo "$(date): Attempting database initialization..." >> "$LOGFILE"
reflex db init >> "$LOGFILE" 2>&1

# Apply migrations
echo "$(date): Applying database migrations..." >> "$LOGFILE"
reflex db migrate >> "$LOGFILE" 2>&1

# Double check if the database file exists
if [ -f "reflex.db" ]; then
    echo "$(date): Database file (reflex.db) verified." >> "$LOGFILE"
else
    echo "$(date): WARNING: reflex.db not found after initialization!" >> "$LOGFILE"
fi

# Launch the application in production mode using Reflex's native single-port support
echo "$(date): Launching Neural Compile in Single-Port mode on ${PORT:-7860}..." >> "$LOGFILE"
exec reflex run --env prod --backend-port "${PORT:-7860}" --single-port
