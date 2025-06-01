#!/bin/bash
# Interactive secrets setup for We-Relate Cloud Run deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID=${1}

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

if [ -z "$PROJECT_ID" ]; then
    print_error "Usage: $0 PROJECT_ID"
    exit 1
fi

print_header "We-Relate Secrets Setup"
print_status "Project ID: $PROJECT_ID"

# Generate a random Flask secret key
generate_flask_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Generate a random Chainlit auth secret
generate_chainlit_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

print_header "Gathering Secrets"

# Flask secret key
print_status "Generating Flask secret key..."
FLASK_SECRET=$(generate_flask_secret)
print_success "Flask secret key generated"

# OpenAI API key
print_warning "OpenAI API Key required"
echo "Please enter your OpenAI API key (starts with sk-):"
read -r OPENAI_API_KEY

if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OpenAI API key is required"
    exit 1
fi

if [[ ! "$OPENAI_API_KEY" =~ ^sk- ]]; then
    print_warning "OpenAI API key should start with 'sk-'"
    echo "Are you sure this is correct? (y/N)"
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        print_error "Aborted"
        exit 1
    fi
fi

# Chainlit auth secret
print_status "Generating Chainlit auth secret..."
CHAINLIT_SECRET=$(generate_chainlit_secret)
print_success "Chainlit auth secret generated"

# Create the secrets JSON
print_header "Creating Secrets"
print_status "Preparing secrets JSON..."

SECRETS_JSON=$(cat <<EOF
{
  "flask-secret-key": "$FLASK_SECRET",
  "openai-api-key": "$OPENAI_API_KEY",
  "chainlit-auth-secret": "$CHAINLIT_SECRET"
}
EOF
)

# Enable Secret Manager API
print_status "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Create the secret
print_status "Creating secret in Google Secret Manager..."
echo "$SECRETS_JSON" | gcloud secrets create we-relate-secrets \
    --project=$PROJECT_ID \
    --data-file=-

print_success "Secrets created successfully!"

# Display summary
print_header "Secrets Summary"
echo "✅ Flask secret key: Generated (32 bytes)"
echo "✅ OpenAI API key: Set (${OPENAI_API_KEY:0:7}...)"
echo "✅ Chainlit auth secret: Generated (32 bytes)"
echo ""
print_status "Secret name: we-relate-secrets"
print_status "Project: $PROJECT_ID"
echo ""
print_success "You can now proceed with the deployment!"
echo ""
print_warning "Security notes:"
echo "- Keep your OpenAI API key secure and monitor usage"
echo "- Rotate secrets regularly in production"
echo "- Consider using IAM conditions for additional security" 