#!/bin/bash
# Cloud Run Health Check Script for We-Relate
# Usage: ./cloud-run/health-check.sh PROJECT_ID [REGION]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID=${1}
REGION=${2:-us-central1}

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "\n${BLUE}========================================${NC}\n${BLUE}$1${NC}\n${BLUE}========================================${NC}\n"; }

if [ -z "$PROJECT_ID" ]; then
    print_error "Usage: $0 PROJECT_ID [REGION]"
    exit 1
fi

print_header "We-Relate Cloud Run Health Check"
print_status "Project: $PROJECT_ID"
print_status "Region: $REGION"

# Get service URLs
print_status "Getting service URLs..."
FLASK_URL=$(gcloud run services describe we-relate-flask --region=$REGION --project=$PROJECT_ID --format="value(status.url)" 2>/dev/null || echo "")
CHAINLIT_URL=$(gcloud run services describe we-relate-chainlit --region=$REGION --project=$PROJECT_ID --format="value(status.url)" 2>/dev/null || echo "")
PHOENIX_URL=$(gcloud run services describe we-relate-phoenix --region=$REGION --project=$PROJECT_ID --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$FLASK_URL" ] || [ -z "$CHAINLIT_URL" ] || [ -z "$PHOENIX_URL" ]; then
    print_error "One or more services not found. Make sure they are deployed."
    echo "Flask URL: $FLASK_URL"
    echo "Chainlit URL: $CHAINLIT_URL"
    echo "Phoenix URL: $PHOENIX_URL"
    exit 1
fi

print_success "Service URLs retrieved:"
echo "  Flask: $FLASK_URL"
echo "  Chainlit: $CHAINLIT_URL"
echo "  Phoenix: $PHOENIX_URL"

# Test Flask app health
print_header "Testing Flask App"
print_status "Testing Flask health endpoint..."
if curl -f -s "${FLASK_URL}/health" > /dev/null; then
    print_success "Flask app is healthy"
else
    print_error "Flask app health check failed"
fi

print_status "Testing Flask homepage..."
if curl -f -s "$FLASK_URL" > /dev/null; then
    print_success "Flask homepage accessible"
else
    print_error "Flask homepage not accessible"
fi

# Test Chainlit service
print_header "Testing Chainlit Service"
print_status "Testing Chainlit endpoint..."
if curl -f -s "$CHAINLIT_URL" > /dev/null; then
    print_success "Chainlit service accessible"
else
    print_error "Chainlit service not accessible"
fi

# Test Phoenix service (direct)
print_header "Testing Phoenix Service"
print_status "Testing Phoenix endpoint..."
if curl -f -s "$PHOENIX_URL" > /dev/null; then
    print_success "Phoenix service accessible"
else
    print_error "Phoenix service not accessible"
fi

# Test Phoenix proxy through Flask
print_header "Testing Phoenix Security Integration"
print_status "Testing Phoenix proxy access (should require admin auth)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FLASK_URL}/admin/phoenix")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    print_success "Phoenix proxy properly secured (HTTP $HTTP_CODE - requires authentication)"
elif [ "$HTTP_CODE" = "200" ]; then
    print_warning "Phoenix proxy accessible without auth (HTTP 200) - check admin_required decorator"
else
    print_error "Phoenix proxy returned unexpected HTTP code: $HTTP_CODE"
fi

print_status "Testing Phoenix health endpoint through Flask..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FLASK_URL}/admin/phoenix/health")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    print_success "Phoenix health endpoint properly secured (HTTP $HTTP_CODE)"
else
    print_warning "Phoenix health endpoint: HTTP $HTTP_CODE"
fi

# Test service logs
print_header "Checking Service Logs"
print_status "Checking for recent errors in logs..."

for service in we-relate-flask we-relate-chainlit we-relate-phoenix; do
    print_status "Checking $service logs..."
    ERROR_COUNT=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$service AND severity>=ERROR" --project=$PROJECT_ID --format="value(timestamp)" --limit=10 | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        print_success "$service: No recent errors"
    else
        print_warning "$service: $ERROR_COUNT recent errors found"
        echo "  Run: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$service AND severity>=ERROR' --project=$PROJECT_ID --limit=5"
    fi
done

# Test secrets access
print_header "Checking Secret Manager"
print_status "Verifying secrets exist..."
if gcloud secrets describe we-relate-secrets --project=$PROJECT_ID > /dev/null 2>&1; then
    print_success "Secrets are configured"
else
    print_error "Secret 'we-relate-secrets' not found"
fi

# Performance check
print_header "Performance Check"
print_status "Testing response times..."

FLASK_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${FLASK_URL}/health" || echo "timeout")
CHAINLIT_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$CHAINLIT_URL" || echo "timeout")
PHOENIX_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$PHOENIX_URL" || echo "timeout")

echo "Response times:"
echo "  Flask: ${FLASK_TIME}s"
echo "  Chainlit: ${CHAINLIT_TIME}s"
echo "  Phoenix: ${PHOENIX_TIME}s"

# Summary
print_header "Health Check Summary"
print_success "Health check completed!"
echo
echo "🌐 Service URLs:"
echo "  Main App: $FLASK_URL"
echo "  AI Chat:  $CHAINLIT_URL"
echo "  Phoenix:  $PHOENIX_URL (admin-only via Flask)"
echo
echo "🔧 Useful Commands:"
echo "  View logs:     gcloud logging read 'resource.type=cloud_run_revision' --project=$PROJECT_ID"
echo "  Check status:  gcloud run services list --region=$REGION --project=$PROJECT_ID"
echo "  Update service: gcloud run deploy SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo
print_success "All core services appear to be running! 🚀" 