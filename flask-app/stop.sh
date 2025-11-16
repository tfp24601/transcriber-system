#!/bin/bash

echo "🛑 Stopping Transcriber..."

# Kill gunicorn
pkill -f "gunicorn.*app:app" 2>/dev/null

# Kill flask dev server
pkill -f "flask-app.*python.*app.py" 2>/dev/null

# Force kill anything on port 5000
if lsof -i :5000 > /dev/null 2>&1; then
    kill -9 $(lsof -t -i :5000) 2>/dev/null
fi

sleep 1

if lsof -i :5000 > /dev/null 2>&1; then
    echo "⚠️  Something is still running on port 5000"
    lsof -i :5000
else
    echo "✅ Transcriber stopped"
fi
