#!/bin/bash

# Simple frontend starter script

cd "$(dirname "$0")/frontend"

echo "=========================================="
echo "Starting Pharma Agent Frontend"
echo "=========================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found!"
    echo "Run: npm install"
    exit 1
fi

echo "🚀 Starting frontend on http://localhost:3000"
echo ""
echo "Make sure backend is running first!"
echo "Backend: http://localhost:8000"
echo ""
echo "Press CTRL+C to stop"
echo "=========================================="
echo ""

# Start frontend
npm run dev
