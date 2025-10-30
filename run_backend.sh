#!/bin/bash

# Simple backend starter script

cd "$(dirname "$0")/backend"

echo "=========================================="
echo "Starting Pharma Agent Backend"
echo "=========================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Copy .env.example to .env and add your API keys"
    exit 1
fi

# Check for ANTHROPIC_API_KEY
if grep -q "sk-ant-api03-placeholder" .env; then
    echo "⚠️  WARNING: You need to add your ANTHROPIC_API_KEY to backend/.env"
    echo "Get your key from: https://console.anthropic.com/"
    echo ""
    echo "Backend will start but you'll need a valid key to run analyses."
    echo ""
fi

echo "🚀 Starting backend on http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo "=========================================="
echo ""

# Start backend
venv/bin/python -m api.main
