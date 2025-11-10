#!/bin/bash

# ==============================================================================
# CRYPTOGRAPHIC PERFORMANCE SIMULATOR - ONE-COMMAND SETUP
# ==============================================================================
# This script sets up and runs the dashboard with a single command.
# Works on ANY system with Docker installed!
# ==============================================================================

set -e  # Exit on any error

echo ""
echo "======================================================================"
echo "🔐 Cryptographic Performance Simulator"
echo "======================================================================"
echo ""
echo "🚀 Starting setup..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo ""
    echo "Please install Docker first:"
    echo "  - Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  - Linux: https://docs.docker.com/engine/install/"
    echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
    echo ""
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo ""
    echo "Please install Docker Compose:"
    echo "  https://docs.docker.com/compose/install/"
    echo ""
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Stop any existing containers
echo "🧹 Cleaning up old containers..."
docker-compose down 2>/dev/null || true
echo ""

# Build the Docker image
echo "🔨 Building Docker image (this may take 2-3 minutes)..."
echo ""
docker-compose build
echo ""
echo "✅ Docker image built successfully!"
echo ""

# Start the container
echo "🚀 Starting web dashboard..."
echo ""
docker-compose up -d
echo ""

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "======================================================================"
    echo "✅ SUCCESS! Dashboard is running!"
    echo "======================================================================"
    echo ""
    echo "📊 Open your web browser and go to:"
    echo ""
    echo "    http://localhost:8080"
    echo ""
    echo "💡 Then click 'Run Performance Benchmark' to see the comparison!"
    echo ""
    echo "======================================================================"
    echo ""
    echo "Commands:"
    echo "  • View logs:     docker-compose logs -f"
    echo "  • Stop server:   docker-compose down"
    echo "  • Restart:       docker-compose restart"
    echo ""
    echo "======================================================================"
    echo ""
else
    echo ""
    echo "❌ Something went wrong! Check the logs:"
    echo ""
    echo "    docker-compose logs"
    echo ""
    exit 1
fi
