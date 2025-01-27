#!/bin/bash

# Paths (Update these according to your system!)
PROJECT_DIR="/c/Users/User/Desktop/parking_backend"
VENV_ACTIVATE="$PROJECT_DIR/env/Scripts/activate"
MANAGE_PY="$PROJECT_DIR/parking_project/manage.py"
NGROK_CONFIG="$PROJECT_DIR/ngrok_backend.yml"  # Path to ngrok config file

# Start Django Backend on port 8000
echo "Starting Django Server..."
cd "$PROJECT_DIR"
source "$VENV_ACTIVATE"
python "$MANAGE_PY" runserver 0.0.0.0:8000 &

# Wait 5 seconds for Django to initialize
echo "Waiting for Django to start..."
sleep 5

# Start ngrok tunnel to port 8000
echo "Starting ngrok..."
ngrok start --config="$NGROK_CONFIG" --all &

# Keep the script running
wait