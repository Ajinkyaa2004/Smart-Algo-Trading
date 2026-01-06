#!/bin/bash

# Development Startup Script for Backend
# This script starts the FastAPI backend in development mode with hot reload

echo "🛠️  Starting Smart Algo Trade Backend (Development Mode)"
echo "=================================================="

# Activate virtual environment
source ../venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please configure .env with your API credentials"
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Start the server with hot reload
echo "✅ Starting server on http://localhost:8000 (Hot Reload Enabled)"
echo "=================================================="
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
