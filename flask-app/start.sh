#!/bin/bash

cd "$(dirname "$0")"
source .venv/bin/activate

echo "🎙️  Transcriber - Starting..."
echo "================================"
echo ""

# Check if port is in use
if lsof -i :5000 > /dev/null 2>&1; then
    echo "⚠️  Port 5000 is already in use!"
    echo ""
    echo "Running processes:"
    lsof -i :5000
    echo ""
    read -p "Kill existing process and restart? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing process..."
        kill -9 $(lsof -t -i :5000) 2>/dev/null
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Start the app
echo "🚀 Starting Transcriber..."
echo "📍 URL: http://localhost:5000"
echo "🌐 Also accessible at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py
