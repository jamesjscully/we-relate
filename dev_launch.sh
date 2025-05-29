#!/bin/bash

# We-Relate Development Launch Script
# Starts both Flask app and Chainlit service using Poetry

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing existing processes on port $port"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to cleanup on exit
cleanup() {
    print_warning "Shutting down services..."
    kill_port 5000
    kill_port 8000
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "🚀 Starting We-Relate Development Environment"
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory (where pyproject.toml is located)"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Check Poetry environment
print_status "Checking Poetry environment..."
poetry env info --path > /dev/null 2>&1 || {
    print_error "Poetry environment not found. Please run 'poetry install' first."
    exit 1
}

# Kill any existing processes on our ports
kill_port 5000
kill_port 8000

print_status "Starting Flask app on port 5000..."
cd flask-app
poetry run python app.py &
FLASK_PID=$!
cd ..

# Wait a moment for Flask to start
sleep 3

# Check if Flask started successfully
if check_port 5000; then
    print_success "Flask app started successfully on http://localhost:5000"
else
    print_error "Failed to start Flask app"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

print_status "Starting Chainlit service on port 8000..."
cd chainlit-service
poetry run chainlit run app.py --host 0.0.0.0 --port 8000 -h > /tmp/chainlit.log 2>&1 &
CHAINLIT_PID=$!
cd ..

# Wait for Chainlit to start (it takes longer to initialize)
print_status "Waiting for Chainlit to initialize..."
sleep 3

# Check if Chainlit started successfully with retries
CHAINLIT_READY=false
for i in {1..10}; do
    if check_port 8000; then
        CHAINLIT_READY=true
        break
    fi
    print_status "Waiting for Chainlit... (attempt $i/10)"
    sleep 2
done

if [ "$CHAINLIT_READY" = true ]; then
    print_success "Chainlit service started successfully on http://localhost:8000"
else
    print_error "Failed to start Chainlit service after 20 seconds"
    print_error "Chainlit logs:"
    tail -20 /tmp/chainlit.log 2>/dev/null || echo "No logs available"
    kill $FLASK_PID 2>/dev/null || true
    kill $CHAINLIT_PID 2>/dev/null || true
    exit 1
fi

echo
print_success "🎉 Both services are running!"
echo
echo "📱 Services:"
echo "   • Flask App:       http://localhost:5000"
echo "   • Chainlit Service: http://localhost:8000"
echo
echo "🔧 Development Info:"
echo "   • Flask PID:       $FLASK_PID"
echo "   • Chainlit PID:    $CHAINLIT_PID"
echo "   • Python Version:  $(poetry run python --version)"
echo

# Open Flask app in default browser
print_status "Opening Flask app in browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000 > /dev/null 2>&1 &
elif command -v open > /dev/null; then
    open http://localhost:5000 > /dev/null 2>&1 &
else
    print_warning "Could not detect browser command. Please open http://localhost:5000 manually."
fi

print_warning "Press Ctrl+C to stop both services"

# Wait for both processes
wait $FLASK_PID $CHAINLIT_PID 