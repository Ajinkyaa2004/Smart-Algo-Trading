#!/bin/bash

# Production Startup Script for Backend
# This script starts the FastAPI backend in production mode

echo "🚀 Starting Smart Algo Trade Backend (Production Mode)"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source ../venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Start the server
echo "✅ Starting server on http://0.0.0.0:8000"
echo "=================================================="
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info
