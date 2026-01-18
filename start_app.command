#!/bin/bash
# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================="
echo "   Starting Resume AI Tailor..."
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    read -n 1 -s -r -p "Press any key to exit..."
    exit 1
fi

# Build and start services
echo "Spinning up containers..."
/usr/local/bin/docker compose up -d

echo "Waiting for services to initialize..."
sleep 5

# Open browser
echo "Opening application..."
open http://localhost:5173

echo "=========================================="
echo "   App is running at http://localhost:5173"
echo "=========================================="
