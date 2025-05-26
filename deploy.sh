#!/bin/bash

# Flask + Chainlit Deployment Script for Google Cloud Run
# Usage: ./deploy.sh [environment]
# Environment: dev, staging, prod (default: dev)

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}

echo "🚀 Deploying Flask + Chainlit Architecture to Google Cloud Run"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set project
print_status "Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Deploy Chainlit Service first (Flask depends on it)
print_status "Deploying Chainlit Service..."
cd chainlit-service

# Set environment-specific variables for Chainlit
if [ "$ENVIRONMENT" = "prod" ]; then
    SERVICE_NAME="chainlit-service"
    MEMORY="2Gi"
    CPU="2"
    MAX_INSTANCES="10"
else
    SERVICE_NAME="chainlit-service-$ENVIRONMENT"
    MEMORY="1Gi"
    CPU="1"
    MAX_INSTANCES="3"
fi

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --max-instances $MAX_INSTANCES \
    --set-env-vars "ENVIRONMENT=$ENVIRONMENT" \
    --timeout 300

# Get Chainlit service URL
CHAINLIT_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
print_status "Chainlit service deployed at: $CHAINLIT_URL"

cd ..

# Deploy Flask App
print_status "Deploying Flask Application..."
cd flask-app

# Set environment-specific variables for Flask
if [ "$ENVIRONMENT" = "prod" ]; then
    FLASK_SERVICE_NAME="flask-app"
    MEMORY="1Gi"
    CPU="1"
    MAX_INSTANCES="10"
else
    FLASK_SERVICE_NAME="flask-app-$ENVIRONMENT"
    MEMORY="512Mi"
    CPU="1"
    MAX_INSTANCES="3"
fi

gcloud run deploy $FLASK_SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --max-instances $MAX_INSTANCES \
    --set-env-vars "ENVIRONMENT=$ENVIRONMENT,CHAINLIT_SERVICE_URL=$CHAINLIT_URL" \
    --timeout 300

# Get Flask service URL
FLASK_URL=$(gcloud run services describe $FLASK_SERVICE_NAME --region $REGION --format="value(status.url)")
print_status "Flask application deployed at: $FLASK_URL"

cd ..

# Summary
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Flask App: $FLASK_URL"
echo "  Chainlit Service: $CHAINLIT_URL"
echo ""
echo "🔧 Next Steps:"
echo "  1. Set up your OpenAI API key in the Chainlit service environment"
echo "  2. Configure any custom domain names"
echo "  3. Set up monitoring and logging"
echo "  4. Test the application end-to-end"
echo ""
echo "💡 Useful Commands:"
echo "  View logs: gcloud run services logs tail $FLASK_SERVICE_NAME --region $REGION"
echo "  Update env vars: gcloud run services update $FLASK_SERVICE_NAME --set-env-vars KEY=VALUE --region $REGION"
echo "  Scale service: gcloud run services update $FLASK_SERVICE_NAME --max-instances 20 --region $REGION" 