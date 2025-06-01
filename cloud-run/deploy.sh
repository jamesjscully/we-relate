#!/bin/bash
# We-Relate Cloud Run Deployment Script
# 
# Usage: ./cloud-run/deploy.sh [PROJECT_ID] [REGION]
# Example: ./cloud-run/deploy.sh my-gcp-project us-central1

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_REGION="us-central1"
PROJECT_ID=${1}
REGION=${2:-$DEFAULT_REGION}

# Print functions
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

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Validation
if [ -z "$PROJECT_ID" ]; then
    print_error "Usage: $0 PROJECT_ID [REGION]"
    print_error "Example: $0 my-gcp-project us-central1"
    exit 1
fi

print_header "We-Relate Cloud Run Deployment"
print_status "Project ID: $PROJECT_ID"
print_status "Region: $REGION"

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

# Set gcloud project
print_status "Setting gcloud project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
print_header "Enabling Required APIs"
print_status "Enabling Cloud Run API..."
gcloud services enable run.googleapis.com

print_status "Enabling Container Registry API..."
gcloud services enable containerregistry.googleapis.com

print_status "Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Configure Docker for GCR
print_status "Configuring Docker for Google Container Registry..."
gcloud auth configure-docker

# Build and push images
print_header "Building and Pushing Images"

# Phoenix Service
print_status "Building Phoenix service..."
docker build -f phoenix-service/Dockerfile -t gcr.io/$PROJECT_ID/we-relate-phoenix:latest .
print_status "Pushing Phoenix service..."
docker push gcr.io/$PROJECT_ID/we-relate-phoenix:latest

# Flask App
print_status "Building Flask app..."
docker build -f flask-app/Dockerfile -t gcr.io/$PROJECT_ID/we-relate-flask:latest .
print_status "Pushing Flask app..."
docker push gcr.io/$PROJECT_ID/we-relate-flask:latest

# Chainlit Service
print_status "Building Chainlit service..."
docker build -f chainlit-service/Dockerfile -t gcr.io/$PROJECT_ID/we-relate-chainlit:latest .
print_status "Pushing Chainlit service..."
docker push gcr.io/$PROJECT_ID/we-relate-chainlit:latest

# Create secrets
print_header "Creating Secrets"
print_warning "Please set the following secrets manually:"
echo "gcloud secrets create we-relate-secrets --data-file=-"
echo "Then create a JSON file with:"
echo '{'
echo '  "flask-secret-key": "your-secure-random-key-here",'
echo '  "openai-api-key": "your-openai-api-key",'
echo '  "chainlit-auth-secret": "your-chainlit-auth-secret"'
echo '}'
echo ""
print_warning "Or run the interactive secret setup:"
echo "./cloud-run/setup-secrets.sh $PROJECT_ID"
echo ""
read -p "Press Enter after setting up secrets..."

# Deploy Phoenix service first (other services depend on it)
print_header "Deploying Phoenix Service"
# Update the deployment file with the actual project ID
sed "s/PROJECT_ID/$PROJECT_ID/g" cloud-run/deploy-phoenix.yaml > /tmp/deploy-phoenix.yaml
gcloud run services replace /tmp/deploy-phoenix.yaml --region=$REGION

# Get Phoenix service URL
PHOENIX_URL=$(gcloud run services describe we-relate-phoenix --region=$REGION --format="value(status.url)")
print_status "Phoenix service URL: $PHOENIX_URL"

# Deploy Chainlit service
print_header "Deploying Chainlit Service"
# Update the deployment file with the actual project ID and Phoenix URL
sed -e "s/PROJECT_ID/$PROJECT_ID/g" -e "s|https://we-relate-phoenix-HASH-uc.a.run.app|$PHOENIX_URL|g" cloud-run/deploy-chainlit.yaml > /tmp/deploy-chainlit.yaml
gcloud run services replace /tmp/deploy-chainlit.yaml --region=$REGION

# Get Chainlit service URL
CHAINLIT_URL=$(gcloud run services describe we-relate-chainlit --region=$REGION --format="value(status.url)")
print_status "Chainlit service URL: $CHAINLIT_URL"

# Deploy Flask app
print_header "Deploying Flask App"
# Update the deployment file with the actual project ID and service URLs
sed -e "s/PROJECT_ID/$PROJECT_ID/g" \
    -e "s|https://we-relate-phoenix-HASH-uc.a.run.app|$PHOENIX_URL|g" \
    -e "s|https://we-relate-chainlit-HASH-uc.a.run.app|$CHAINLIT_URL|g" \
    cloud-run/deploy-flask.yaml > /tmp/deploy-flask.yaml
gcloud run services replace /tmp/deploy-flask.yaml --region=$REGION

# Get Flask service URL
FLASK_URL=$(gcloud run services describe we-relate-flask --region=$REGION --format="value(status.url)")

# Configure IAM permissions for service-to-service communication
print_header "Configuring IAM Permissions"
print_status "Setting up service-to-service authentication..."

# Allow Flask app to invoke Chainlit service
gcloud run services add-iam-policy-binding we-relate-chainlit \
    --region=$REGION \
    --member="serviceAccount:$(gcloud run services describe we-relate-flask --region=$REGION --format='value(spec.template.spec.serviceAccountName)')" \
    --role="roles/run.invoker" || true

# Allow Flask app to invoke Phoenix service  
gcloud run services add-iam-policy-binding we-relate-phoenix \
    --region=$REGION \
    --member="serviceAccount:$(gcloud run services describe we-relate-flask --region=$REGION --format='value(spec.template.spec.serviceAccountName)')" \
    --role="roles/run.invoker" || true

# Allow Chainlit to invoke Phoenix service
gcloud run services add-iam-policy-binding we-relate-phoenix \
    --region=$REGION \
    --member="serviceAccount:$(gcloud run services describe we-relate-chainlit --region=$REGION --format='value(spec.template.spec.serviceAccountName)')" \
    --role="roles/run.invoker" || true

# Deployment complete
print_header "Deployment Complete!"
print_success "All services deployed successfully!"
echo ""
print_status "Service URLs:"
echo "📱 Flask App (Main):    $FLASK_URL"
echo "💬 Chainlit Service:    $CHAINLIT_URL"  
echo "🔍 Phoenix Observability: $PHOENIX_URL (Admin only via Flask app)"
echo ""
print_status "Next steps:"
echo "1. Visit $FLASK_URL to access the application"
echo "2. Register an admin account or log in"
echo "3. Access Phoenix observability at $FLASK_URL/admin/phoenix"
echo "4. Monitor logs: gcloud logging read 'resource.type=cloud_run_revision' --project=$PROJECT_ID"
echo ""
print_success "Deployment completed successfully! 🚀" 