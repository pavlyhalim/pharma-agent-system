#!/bin/bash

# Startup script for Pharma Agent System

echo "=========================================="
echo "Pharma Agent System - Startup"
echo "=========================================="

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  Warning: backend/.env not found!"
    echo "Copying .env.example to .env..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env and add your ANTHROPIC_API_KEY"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check for Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# echo "Installing backend dependencies..."
# pip install --upgrade pip
# pip install -r requirements.txt

echo "✅ Backend ready"
echo ""

# Frontend setup
echo "🔧 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "✅ Frontend ready"
echo ""

# Start services
echo "=========================================="
echo "🚀 Starting services..."
echo "=========================================="

# Start backend in background
cd ../backend
source venv/bin/activate
echo "Starting backend on http://localhost:8000"
python -m api.main &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

# Start frontend
cd ../frontend
echo "Starting frontend on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "✅ Services started!"
echo "=========================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Trap Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for processes
wait
