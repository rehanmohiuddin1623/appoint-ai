#!/bin/bash

# Docker build script for med-assist-agent
# This script ensures clean builds and handles common issues

echo "🐳 Building Medical Assist Agent Docker Image..."

# Clean any existing containers and images
echo "🧹 Cleaning up existing containers and images..."
docker-compose down --remove-orphans 2>/dev/null || true
docker rmi med-assist-agent-app 2>/dev/null || true

# Build with no cache to ensure fresh installation
echo "🔨 Building Docker image with no cache..."
docker-compose build --no-cache app

# Verify the build
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "🚀 Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    # Check service status
    echo "📊 Service status:"
    docker-compose ps
    
    # Show logs if there are issues
    if ! docker-compose ps | grep -q "Up"; then
        echo "❌ Some services failed to start. Showing logs:"
        docker-compose logs app
    else
        echo "✅ All services are running!"
        echo "🌐 Application should be available at: http://localhost:8000"
        echo "📚 API Documentation: http://localhost:8000/docs"
    fi
else
    echo "❌ Docker build failed!"
    exit 1
fi