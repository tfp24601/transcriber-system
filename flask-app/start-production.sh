#!/bin/bash

cd "$(dirname "$0")"
source .venv/bin/activate

echo "🎙️  Transcriber - Production Mode"
echo "================================"
echo ""

# Check if port is in use
if lsof -i :5000 > /dev/null 2>&1; then
    echo "⚠️  Port 5000 is already in use!"
    echo ""
    read -p "Kill existing process and restart? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "gunicorn.*app:app"
        sleep 2
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Start with gunicorn
echo "🚀 Starting Transcriber with Gunicorn..."
nohup gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 300 \
    --graceful-timeout 30 \
    app:app \
    > /tmp/transcriber-gunicorn.log 2>&1 &

sleep 2

if lsof -i :5000 > /dev/null 2>&1; then
    PID=$(lsof -t -i :5000 | head -1)
    echo "✅ Transcriber started successfully!"
    echo "   PID: $PID"
    echo "   URL: http://localhost:5000"
    echo "   Logs: tail -f /tmp/transcriber-gunicorn.log"
    echo ""
    echo "To stop: ./stop.sh or kill $PID"
else
    echo "❌ Failed to start!"
    echo "Check logs: tail -30 /tmp/transcriber-gunicorn.log"
fi
