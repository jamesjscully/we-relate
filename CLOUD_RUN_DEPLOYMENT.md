# We-Relate Cloud Run Deployment Guide

This guide walks you through deploying the We-Relate application to Google Cloud Run for production use.

## Overview

The We-Relate application consists of three services:
- **Phoenix Service**: AI observability and tracing (port 8080)
- **Chainlit Service**: AI conversation interface (port 8080) 
- **Flask App**: Main web application with admin features (port 8080)

## Prerequisites

1. **Google Cloud Project**: Create or select a GCP project
2. **gcloud CLI**: Install and authenticate with Google Cloud
3. **Docker**: For building container images
4. **OpenAI API Key**: Required for AI functionality

### Install Prerequisites

```bash
# Install gcloud CLI (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login to Google Cloud
gcloud auth login

# Install Docker (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

## Quick Deployment

### 1. Set Up Secrets (Interactive)

```bash
# Make scripts executable
chmod +x cloud-run/setup-secrets.sh
chmod +x cloud-run/deploy.sh

# Set up secrets interactively
./cloud-run/setup-secrets.sh YOUR_PROJECT_ID
```

This will prompt you for your OpenAI API key and automatically generate secure secrets for Flask and Chainlit.

### 2. Deploy All Services

```bash
# Deploy everything at once
./cloud-run/deploy.sh YOUR_PROJECT_ID us-central1
```

Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

## Manual Deployment Steps

If you prefer to deploy step-by-step or customize the deployment:

### 1. Enable Required APIs

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Create Secrets

```bash
# Create a JSON file with your secrets
cat > secrets.json << EOF
{
  "flask-secret-key": "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')",
  "openai-api-key": "YOUR_OPENAI_API_KEY",
  "chainlit-auth-secret": "$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
}
EOF

# Create the secret in Google Secret Manager
gcloud secrets create we-relate-secrets --data-file=secrets.json

# Clean up the local file
rm secrets.json
```

### 3. Build and Push Images

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push Phoenix service
docker build -f phoenix-service/Dockerfile -t gcr.io/YOUR_PROJECT_ID/we-relate-phoenix:latest .
docker push gcr.io/YOUR_PROJECT_ID/we-relate-phoenix:latest

# Build and push Flask app
docker build -f flask-app/Dockerfile -t gcr.io/YOUR_PROJECT_ID/we-relate-flask:latest .
docker push gcr.io/YOUR_PROJECT_ID/we-relate-flask:latest

# Build and push Chainlit service
docker build -f chainlit-service/Dockerfile -t gcr.io/YOUR_PROJECT_ID/we-relate-chainlit:latest .
docker push gcr.io/YOUR_PROJECT_ID/we-relate-chainlit:latest
```

### 4. Deploy Services (in order)

Deploy Phoenix first since other services depend on it:

```bash
# Update deployment files with your project ID
sed "s/PROJECT_ID/YOUR_PROJECT_ID/g" cloud-run/deploy-phoenix.yaml > deploy-phoenix.yaml
gcloud run services replace deploy-phoenix.yaml --region=us-central1

# Get Phoenix URL
PHOENIX_URL=$(gcloud run services describe we-relate-phoenix --region=us-central1 --format="value(status.url)")
echo "Phoenix URL: $PHOENIX_URL"
```

Deploy Chainlit service:

```bash
# Update deployment file with project ID and Phoenix URL
sed -e "s/PROJECT_ID/YOUR_PROJECT_ID/g" \
    -e "s|https://we-relate-phoenix-HASH-uc.a.run.app|$PHOENIX_URL|g" \
    cloud-run/deploy-chainlit.yaml > deploy-chainlit.yaml
gcloud run services replace deploy-chainlit.yaml --region=us-central1

# Get Chainlit URL
CHAINLIT_URL=$(gcloud run services describe we-relate-chainlit --region=us-central1 --format="value(status.url)")
echo "Chainlit URL: $CHAINLIT_URL"
```

Deploy Flask app:

```bash
# Update deployment file with all URLs
sed -e "s/PROJECT_ID/YOUR_PROJECT_ID/g" \
    -e "s|https://we-relate-phoenix-HASH-uc.a.run.app|$PHOENIX_URL|g" \
    -e "s|https://we-relate-chainlit-HASH-uc.a.run.app|$CHAINLIT_URL|g" \
    cloud-run/deploy-flask.yaml > deploy-flask.yaml
gcloud run services replace deploy-flask.yaml --region=us-central1

# Get Flask URL
FLASK_URL=$(gcloud run services describe we-relate-flask --region=us-central1 --format="value(status.url)")
echo "Flask URL: $FLASK_URL"
```

### 5. Configure Service-to-Service Authentication

```bash
# Allow Flask to call Chainlit
gcloud run services add-iam-policy-binding we-relate-chainlit \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# Allow Flask to call Phoenix  
gcloud run services add-iam-policy-binding we-relate-phoenix \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# Allow Chainlit to call Phoenix
gcloud run services add-iam-policy-binding we-relate-phoenix \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"
```

## Access Your Application

After deployment, you'll have three service URLs:

- **Main Application**: `https://we-relate-flask-HASH-uc.a.run.app`
- **AI Chat Interface**: `https://we-relate-chainlit-HASH-uc.a.run.app`
- **Phoenix Observability**: Only accessible via Flask admin at `/admin/phoenix`

### Security Model

- **Phoenix Service**: Only accessible through Flask admin proxy
- **Flask App**: Public access, with admin features protected by authentication
- **Chainlit Service**: Public access for AI conversations

## Post-Deployment Setup

1. **Register Admin Account**: Visit your Flask URL and register the first admin account
2. **Test Phoenix Access**: Login as admin and visit `/admin/phoenix`
3. **Configure Domain** (optional): Set up custom domain with Cloud DNS
4. **Monitor Usage**: Use Google Cloud Console to monitor service metrics

## Environment Variables

The following environment variables are automatically configured:

### Flask App
- `PORT=8080`
- `FLASK_ENV=production`
- `SECRET_KEY` (from Secret Manager)
- `OPENAI_API_KEY` (from Secret Manager)
- `PHOENIX_SERVICE_URL` (auto-configured to Phoenix service)
- `CHAINLIT_SERVICE_URL` (auto-configured to Chainlit service)
- `PHOENIX_TRACING_ENABLED=true`

### Chainlit Service
- `PORT=8080`
- `OPENAI_API_KEY` (from Secret Manager)
- `PHOENIX_SERVICE_URL` (auto-configured to Phoenix service)
- `PHOENIX_TRACING_ENABLED=true`
- `CHAINLIT_AUTH_SECRET` (from Secret Manager)

### Phoenix Service
- `PORT=8080`
- `PHOENIX_HOST=0.0.0.0`
- `PHOENIX_WORKING_DIR=/app/data`

## Monitoring and Logs

### View Logs
```bash
# View all service logs
gcloud logging read 'resource.type=cloud_run_revision' --project=YOUR_PROJECT_ID

# View specific service logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=we-relate-flask' --project=YOUR_PROJECT_ID
```

### Monitor Performance
Visit the [Cloud Run console](https://console.cloud.google.com/run) to monitor:
- Request volume and latency
- Error rates
- Memory and CPU usage
- Cold start metrics

## Troubleshooting

### Common Issues

1. **Service Not Responding**: Check health check endpoints and startup time
2. **Authentication Errors**: Verify Secret Manager permissions and secret values
3. **Service-to-Service Communication**: Check IAM policies and URL configuration
4. **Phoenix Not Loading**: Verify admin authentication and proxy configuration

### Debug Commands

```bash
# Check service status
gcloud run services describe SERVICE_NAME --region=us-central1

# View recent logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME' --limit=50

# Test service health
curl -f "https://YOUR_SERVICE_URL/health"
```

## Scaling and Performance

### Automatic Scaling
Cloud Run automatically scales based on request volume:
- **Min instances**: 1 (always warm)
- **Max instances**: 3-10 depending on service
- **Concurrency**: 80 requests per instance

### Performance Optimization
- Services use gen2 execution environment for better performance
- CPU is not throttled to maintain responsiveness
- Memory limits set appropriately for each service type

## Security Considerations

1. **Secret Management**: All sensitive data stored in Google Secret Manager
2. **Phoenix Security**: No direct external access - only through authenticated Flask proxy
3. **HTTPS Only**: All services automatically use HTTPS
4. **IAM Controls**: Fine-grained access control for service-to-service communication

## Cost Optimization

- Services scale to zero when not in use
- Pay only for actual usage (CPU-seconds and memory)
- Use Cloud Run's free tier for development/testing
- Monitor usage through Cloud Console billing

## Updates and Maintenance

### Deploy Updates
```bash
# Rebuild and redeploy a single service
docker build -f flask-app/Dockerfile -t gcr.io/YOUR_PROJECT_ID/we-relate-flask:latest .
docker push gcr.io/YOUR_PROJECT_ID/we-relate-flask:latest
gcloud run deploy we-relate-flask --image gcr.io/YOUR_PROJECT_ID/we-relate-flask:latest --region=us-central1
```

### Rollback
```bash
# List revisions
gcloud run revisions list --service=we-relate-flask --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic we-relate-flask --to-revisions=REVISION_NAME=100 --region=us-central1
```

## Support

For issues specific to the We-Relate application, please check:
1. Application logs in Cloud Console
2. Phoenix observability dashboard (via Flask admin)
3. GitHub repository for known issues and updates 