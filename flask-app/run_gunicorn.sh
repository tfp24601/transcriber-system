#!/usr/bin/env bash
set -euo pipefail
exec /path/to/transcriber/flask-app/.venv/bin/gunicorn \
    --bind "${FLASK_HOST:-0.0.0.0}:${FLASK_PORT:-5000}" \
    --timeout 300 \
    --graceful-timeout 30 \
    --workers 2 \
    app:app
