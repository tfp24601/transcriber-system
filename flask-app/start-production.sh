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

# Set cuDNN library path for GPU acceleration
CUDNN_DIR="$PWD/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib"

# Start with gunicorn
echo "🚀 Starting Transcriber with Gunicorn..."
nohup env \
    LD_LIBRARY_PATH="$CUDNN_DIR:${LD_LIBRARY_PATH:-}" \
    gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 600 \
    --graceful-timeout 60 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 100 \
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
