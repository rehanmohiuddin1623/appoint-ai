#!/bin/bash

# Med Assist Agent - Docker Management Script
# This script provides convenient commands for managing the Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE} Med Assist Agent - Docker Manager${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        if [ -f .env.docker ]; then
            print_warning ".env file not found. Copying from .env.docker template..."
            cp .env.docker .env
            print_warning "Please edit .env file with your actual API keys before starting the application."
        else
            print_error ".env file not found. Please create one with your API keys."
            exit 1
        fi
    fi
}

# Build the application
build() {
    print_status "Building Med Assist Agent Docker image..."
    docker-compose build
    print_status "Build completed successfully!"
}

# Start the application
start() {
    check_docker
    check_env
    print_status "Starting Med Assist Agent services..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    print_status "Services started! Checking health..."
    docker-compose ps
    
    print_status "Application is running at:"
    echo "  🌐 API Documentation: http://localhost:8000/docs"
    echo "  🏥 Health Check: http://localhost:8000/health"
    echo "  📊 Database: localhost:5432 (user: medassist, db: medassist)"
    echo "  🔴 Redis: localhost:6379"
}

# Stop the application
stop() {
    print_status "Stopping Med Assist Agent services..."
    docker-compose down
    print_status "Services stopped successfully!"
}

# Restart the application
restart() {
    stop
    start
}

# Show logs
logs() {
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# Show status
status() {
    print_header
    print_status "Service Status:"
    docker-compose ps
    
    print_status "Container Health:"
    docker-compose exec app curl -f http://localhost:8000/health || print_error "App health check failed"
}

# Clean up (remove containers and volumes)
cleanup() {
    print_warning "This will remove all containers and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up containers and volumes..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_status "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Database operations
db_migrate() {
    print_status "Running database migrations..."
    docker-compose exec app python migrate.py create
    print_status "Database migration completed!"
}

db_reset() {
    print_warning "This will reset the database and delete all data. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Resetting database..."
        docker-compose exec app python migrate.py reset
        print_status "Database reset completed!"
    else
        print_status "Database reset cancelled."
    fi
}

db_shell() {
    print_status "Connecting to database shell..."
    docker-compose exec postgres psql -U medassist -d medassist
}

# Application shell
shell() {
    print_status "Opening application shell..."
    docker-compose exec app /bin/bash
}

# Production start with nginx
start_prod() {
    check_docker
    check_env
    print_status "Starting Med Assist Agent in production mode..."
    docker-compose --profile production up -d
    
    print_status "Production services started!"
    print_status "Application is running at:"
    echo "  🌐 HTTP: http://localhost"
    echo "  🔒 HTTPS: https://localhost (if SSL configured)"
    echo "  📊 API Documentation: http://localhost/docs"
}

# Show help
help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build         Build the Docker image"
    echo "  start         Start all services"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  status        Show service status"
    echo "  logs [service] Show logs (optionally for specific service)"
    echo "  cleanup       Remove containers and volumes"
    echo "  shell         Open application shell"
    echo ""
    echo "Database commands:"
    echo "  db:migrate    Run database migrations"
    echo "  db:reset      Reset database (WARNING: deletes all data)"
    echo "  db:shell      Open database shell"
    echo ""
    echo "Production commands:"
    echo "  start:prod    Start with nginx reverse proxy"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start the application"
    echo "  $0 logs app           # Show application logs"
    echo "  $0 db:migrate         # Run database migrations"
    echo "  $0 start:prod         # Start in production mode"
}

# Main command handling
case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    cleanup)
        cleanup
        ;;
    shell)
        shell
        ;;
    db:migrate)
        db_migrate
        ;;
    db:reset)
        db_reset
        ;;
    db:shell)
        db_shell
        ;;
    start:prod)
        start_prod
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac