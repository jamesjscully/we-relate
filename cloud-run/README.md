# We-Relate Cloud Run Deployment

This directory contains the Cloud Run deployment configuration and scripts for the We-Relate application.

## Files Overview

- **`deploy.sh`** - Main deployment script that handles the complete deployment process
- **`setup-secrets.sh`** - Interactive script to set up Google Secret Manager secrets
- **`health-check.sh`** - Post-deployment health check and validation script
- **`deploy-*.yaml`** - Knative service definitions for each component

## Quick Start

### 1. Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated
- Docker installed
- OpenAI API key
- Google Cloud project with billing enabled

### 2. Deploy
```bash
# Set up secrets (interactive)
./cloud-run/setup-secrets.sh YOUR_PROJECT_ID

# Deploy all services
./cloud-run/deploy.sh YOUR_PROJECT_ID us-central1
```

### 3. Validate
```bash
# Check deployment health
./cloud-run/health-check.sh YOUR_PROJECT_ID us-central1
```

## Service Architecture

### Phoenix Service (`deploy-phoenix.yaml`)
- **Purpose**: AI observability and tracing
- **Port**: 8080
- **Access**: Internal only (no public ingress for security)
- **Resources**: 1 CPU, 2GB RAM
- **Scaling**: 1-3 instances

### Chainlit Service (`deploy-chainlit.yaml`)
- **Purpose**: AI conversation interface
- **Port**: 8080
- **Access**: Public
- **Resources**: 1 CPU, 1GB RAM
- **Scaling**: 1-5 instances
- **Timeout**: 900s (for AI processing)

### Flask App (`deploy-flask.yaml`)
- **Purpose**: Main web application with admin features
- **Port**: 8080
- **Access**: Public (admin features protected by auth)
- **Resources**: 1 CPU, 1GB RAM
- **Scaling**: 1-10 instances

## Security Model

### Phoenix Access Control
- Phoenix service has no public ingress
- Access only through Flask admin proxy at `/admin/phoenix`
- Admin authentication required via `@admin_required` decorator
- Internal service-to-service communication only

### Secret Management
All sensitive data stored in Google Secret Manager:
- `flask-secret-key` - Flask session encryption
- `openai-api-key` - OpenAI API access
- `chainlit-auth-secret` - Chainlit authentication

### Service-to-Service Communication
- Flask can invoke Chainlit and Phoenix services
- Chainlit can invoke Phoenix service
- All communication over HTTPS
- IAM policies control access

## Environment Variables

### Automatic Configuration
The deployment script automatically configures:
- Service URLs based on actual Cloud Run endpoints
- Secret references for sensitive data
- Phoenix tracing endpoints
- Production environment settings

### Manual Override
You can manually edit the YAML files to customize:
- Resource limits
- Scaling parameters
- Environment variables
- Security settings

## Monitoring

### Health Checks
Each service includes:
- Startup probes for initialization
- Liveness probes for ongoing health
- HTTP health endpoints

### Logging
All logs automatically sent to Google Cloud Logging:
```bash
# View all service logs
gcloud logging read 'resource.type=cloud_run_revision' --project=PROJECT_ID

# View specific service
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=we-relate-flask' --project=PROJECT_ID
```

### Metrics
Monitor in Google Cloud Console:
- Request volume and latency
- Error rates
- Resource utilization
- Cold start frequency

## Scaling Configuration

### Automatic Scaling
- **Phoenix**: 1-3 instances (lower scale for observability workload)
- **Chainlit**: 1-5 instances (AI processing demands)
- **Flask**: 1-10 instances (web traffic handling)

### Concurrency
- All services: 80 concurrent requests per instance
- CPU throttling disabled for responsiveness
- gen2 execution environment for performance

## Cost Optimization

### Scaling to Zero
- Services automatically scale to zero during low usage
- Minimum 1 instance to avoid cold starts in production
- Pay only for actual usage (CPU-seconds and memory)

### Resource Allocation
- Phoenix: Higher memory for data processing
- Chainlit: Balanced for AI model interactions
- Flask: Optimized for web request handling

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check project ID and region
   - Verify API enablement
   - Check Docker registry permissions

2. **Service Not Responding**
   - Review startup probe settings
   - Check health endpoint implementations
   - Verify environment variables

3. **Authentication Errors**
   - Verify secrets in Secret Manager
   - Check IAM permissions
   - Validate secret key format

4. **Phoenix Not Accessible**
   - Confirm admin authentication
   - Check Flask proxy configuration
   - Verify internal service URLs

### Debug Commands

```bash
# Check service status
gcloud run services list --region=us-central1

# View service details
gcloud run services describe SERVICE_NAME --region=us-central1

# Check recent logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME' --limit=20

# Test health endpoint
curl -f "https://SERVICE_URL/health"
```

## Updates and Maintenance

### Deploy Updates
```bash
# Rebuild specific service
docker build -f SERVICE_DIR/Dockerfile -t gcr.io/PROJECT_ID/SERVICE_NAME:latest .
docker push gcr.io/PROJECT_ID/SERVICE_NAME:latest

# Deploy update
gcloud run deploy SERVICE_NAME --image gcr.io/PROJECT_ID/SERVICE_NAME:latest --region=us-central1
```

### Rollback
```bash
# List revisions
gcloud run revisions list --service=SERVICE_NAME --region=us-central1

# Rollback to previous
gcloud run services update-traffic SERVICE_NAME --to-revisions=REVISION_NAME=100 --region=us-central1
```

### Update Secrets
```bash
# Update secret value
echo "NEW_SECRET_VALUE" | gcloud secrets versions add we-relate-secrets --data-file=-

# Deploy services to pick up new secret
./cloud-run/deploy.sh PROJECT_ID us-central1
```

## Development vs Production

### Development (Docker Compose)
- Services communicate via internal Docker network
- Phoenix accessible at localhost:6006 (with external port)
- Local file system for data persistence

### Production (Cloud Run)
- Services communicate via HTTPS URLs
- Phoenix only accessible through Flask admin proxy
- Cloud storage for data persistence
- Auto-scaling and load balancing

## Support

For deployment issues:
1. Check the health check script output
2. Review Cloud Run service logs
3. Verify Secret Manager configuration
4. Check IAM permissions and service URLs

For application issues:
1. Use Phoenix observability dashboard
2. Check application-specific logs
3. Monitor OpenAI API usage and quotas 