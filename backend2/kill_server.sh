#!/bin/bash

echo "Looking for file organizer server processes..."

# Find and kill python server processes
PIDS=$(pgrep -f "python.*server.py" || true)

if [ -z "$PIDS" ]; then
    echo "No server processes found."
else
    echo "Found server processes: $PIDS"
    echo "Killing processes..."
    pkill -f "python.*server.py"
    sleep 2
    
    # Check if still running and force kill
    REMAINING=$(pgrep -f "python.*server.py" || true)
    if [ ! -z "$REMAINING" ]; then
        echo "Force killing remaining processes: $REMAINING"
        pkill -9 -f "python.*server.py"
    fi
    
    echo "Server processes terminated."
fi

# Also kill any hanging curl processes
CURL_PIDS=$(pgrep -f "curl.*localhost:8080" || true)
if [ ! -z "$CURL_PIDS" ]; then
    echo "Killing hanging curl processes: $CURL_PIDS"
    pkill -f "curl.*localhost:8080"
fi

echo "Cleanup complete."
