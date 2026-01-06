#!/bin/bash

# Complete Deployment Script
# This script builds and deploys the entire application

set -e  # Exit on error

echo "🚀 Smart Algo Trade - Production Deployment"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi
print_success "Node.js found"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 found"

# Check for .env files
echo ""
echo "🔐 Checking environment configuration..."

if [ ! -f ".env" ]; then
    print_warning "Frontend .env not found, copying from .env.example"
    cp .env.example .env
fi
print_success "Frontend .env exists"

if [ ! -f "backend/.env" ]; then
    print_warning "Backend .env not found, copying from .env.example"
    cp backend/.env.example backend/.env
    print_warning "Please configure backend/.env with your Kite API credentials"
fi
print_success "Backend .env exists"

# Build frontend
echo ""
echo "🏗️  Building frontend..."
npm install
npm run build
print_success "Frontend built successfully"

# Setup backend
echo ""
echo "🐍 Setting up backend..."

if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found, creating..."
    python3 -m venv venv
fi

source venv/bin/activate

cd backend
pip install -q -r requirements.txt
print_success "Backend dependencies installed"

echo ""
echo "=============================================="
print_success "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "  1. Configure your API credentials in backend/.env"
echo "  2. Start backend: cd backend && ./start_prod.sh"
echo "  3. Serve frontend: npm run preview (or use nginx)"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"
echo "=============================================="
