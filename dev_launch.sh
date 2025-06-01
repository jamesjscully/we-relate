#!/bin/bash

# We-Relate Development Launch Script
# Starts Flask app and Chainlit service using Poetry

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_phoenix() {
    echo -e "${PURPLE}[PHOENIX]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    # Use netstat or nc to check if port is listening
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    elif command -v nc >/dev/null 2>&1; then
        # Fallback to nc (netcat) if available
        if nc -z localhost $port 2>/dev/null; then
            return 0  # Port is in use
        fi
    fi
    return 1  # Port is free
}

# Function to check Phoenix health
check_phoenix_health() {
    # Check if port is open
    if ! check_port 6006; then
        return 1
    fi
    
    # Check if Phoenix API responds
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:6006/ 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ]; then
        return 0  # Phoenix is healthy
    else
        return 1  # Phoenix is not responding properly
    fi
}

# Function to get Phoenix project info
get_phoenix_info() {
    local projects
    projects=$(curl -s http://localhost:6006/v1/projects 2>/dev/null || echo "")
    
    if [ ! -z "$projects" ]; then
        local project_count
        project_count=$(echo "$projects" | grep -o '"name":' | wc -l)
        echo "Projects: $project_count"
    else
        echo "No project data available"
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    # Use netstat to find processes on the port, then extract PIDs and kill them
    local pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$' 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing existing processes on port $port"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to start Phoenix if not running
start_phoenix() {
    print_phoenix "Checking Phoenix status..."
    
    if check_phoenix_health; then
        print_success "Phoenix is already running and healthy"
        local info=$(get_phoenix_info)
        print_phoenix "Phoenix info: $info"
        return 0
    fi
    
    # Check if Phoenix container exists
    if docker ps -a --format "{{.Names}}" | grep -q "phoenix"; then
        print_phoenix "Phoenix container exists, checking status..."
        
        # Check if container is running
        if docker ps --format "{{.Names}}" | grep -q "phoenix"; then
            print_phoenix "Phoenix container is running but not responding, restarting..."
            docker restart we-relate-phoenix-1 > /dev/null 2>&1 || docker restart phoenix > /dev/null 2>&1 || true
        else
            print_phoenix "Phoenix container is stopped, starting..."
            docker start we-relate-phoenix-1 > /dev/null 2>&1 || docker start phoenix > /dev/null 2>&1 || true
        fi
    else
        print_phoenix "Phoenix container not found, starting with docker-compose..."
        docker-compose up phoenix -d > /dev/null 2>&1 || true
    fi
    
    # Wait for Phoenix to start and check health
    print_phoenix "Waiting for Phoenix to initialize..."
    for i in {1..15}; do
        if check_phoenix_health; then
            print_success "Phoenix started successfully!"
            local info=$(get_phoenix_info)
            print_phoenix "Phoenix info: $info"
            return 0
        fi
        sleep 2
    done
    
    print_warning "Phoenix did not start properly, but continuing..."
    return 1
}

# Function to kill Phoenix processes specifically
kill_phoenix() {
    print_warning "Stopping Phoenix processes..."
    # Kill Phoenix processes by name
    pkill -f "phoenix" 2>/dev/null || true
    # Kill processes on Phoenix ports
    kill_port 6006    # Phoenix web UI
    kill_port 4317    # Phoenix gRPC port
    kill_port 4318    # Phoenix HTTP OTLP port
    sleep 2
}

# Function to cleanup on exit
cleanup() {
    print_warning "Shutting down services..."
    kill_port 5000
    kill_port 8000
    kill_phoenix
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

# Start Phoenix first
start_phoenix

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

print_status "Starting Chainlit service (with Phoenix) on port 8000..."
cd chainlit-service
poetry run chainlit run app.py --host 0.0.0.0 --port 8000 -h > /tmp/chainlit.log 2>&1 &
CHAINLIT_PID=$!
cd ..

# Wait for Chainlit to start (it takes longer to initialize)
print_status "Waiting for Chainlit and Phoenix to initialize..."
sleep 5

# Check if Chainlit started successfully with retries
CHAINLIT_READY=false
for i in {1..15}; do
    if check_port 8000; then
        CHAINLIT_READY=true
        break
    fi
    print_status "Waiting for Chainlit... (attempt $i/15)"
    sleep 2
done

if [ "$CHAINLIT_READY" = true ]; then
    print_success "Chainlit service started successfully on http://localhost:8000"
else
    print_error "Failed to start Chainlit service after 30 seconds"
    print_error "Chainlit logs:"
    tail -20 /tmp/chainlit.log 2>/dev/null || echo "No logs available"
    kill $FLASK_PID 2>/dev/null || true
    kill $CHAINLIT_PID 2>/dev/null || true
    exit 1
fi

echo
print_success "🎉 All services are running!"
echo

# Final Phoenix status check
echo "📊 Service Status:"
echo "   • Flask App:                ✅ http://localhost:5000"
echo "   • Chainlit Service:         ✅ http://localhost:8000"

# Enhanced Phoenix status reporting
if check_phoenix_health; then
    echo "   • Phoenix Observability:    ✅ Running (Secured)"
    phoenix_info=$(get_phoenix_info)
    echo "     └─ Status: $phoenix_info"
    echo "     └─ Security: Admin-only access via Flask proxy"
    echo "     └─ Admin Interface: http://localhost:5000/admin/phoenix"
    echo "     └─ Health Check: http://localhost:5000/admin/phoenix/health"
    echo "     └─ Internal Network: phoenix:8080 (Docker)"
else
    echo "   • Phoenix Observability:    ❌ Not responding"
    echo "     └─ Container may be starting or misconfigured"
    echo "     └─ Try: docker-compose up phoenix -d"
    echo "     └─ Logs: docker logs phoenix-secure"
    echo "     └─ Note: No external port for security"
fi

echo
echo "🔧 Development Info:"
echo "   • Flask PID:              $FLASK_PID"
echo "   • Chainlit PID:           $CHAINLIT_PID"
echo "   • Python Version:         $(poetry run python --version)"
echo "   • Docker Status:          $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(phoenix|we-relate)' | wc -l) containers running"
echo
echo "👨‍💼 Admin Access:"
echo "   • Admin Login:            http://localhost:5000/auth/admin/login"
echo "   • Admin Dashboard:        http://localhost:5000/admin"
echo "   • Phoenix Observability:  http://localhost:5000/admin/phoenix (Admin Only)"
echo "   • Default Admin:          admin@we-relate.com / admin123"
echo
echo "🔍 Observability & Debugging:"
if check_phoenix_health; then
    echo "   • Phoenix Admin Access:   http://localhost:5000/admin/phoenix"
    echo "   • Phoenix Health Check:   http://localhost:5000/admin/phoenix/health"
    echo "   • Test Phoenix Setup:     poetry run python test_phoenix_tracing.py"
else
    echo "   • Phoenix Setup:          docker-compose up phoenix -d"
    echo "   • Phoenix Logs:           docker logs phoenix"
    echo "   • Test Phoenix:           poetry run python test_phoenix_tracing.py"
fi

# Open Flask app in default browser
print_status "Opening Flask app in browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000 > /dev/null 2>&1 &
elif command -v open > /dev/null; then
    open http://localhost:5000 > /dev/null 2>&1 &
fi

print_status "Press Ctrl+C to stop all services"
echo
echo "📊 Real-time Logs:"
echo "   • Chainlit:           tail -f /tmp/chainlit.log"
if check_phoenix_health; then
    echo "   • Phoenix:            docker logs -f phoenix"
fi

# Wait for interrupt signal
wait 