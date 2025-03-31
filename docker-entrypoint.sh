#!/bin/bash
set -e

export VIRTUAL_ENV=/opt/venv

alembic upgrade head

# Start the application
echo "Starting web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
