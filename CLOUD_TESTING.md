# Cloud Deployment Testing

## Overview

The `test_cloud_deployment.py` script simulates your cloud deployment environment locally using Docker containers. This helps catch deployment issues early during development.

## Purpose

- **Early Detection**: Catch cloud compatibility issues before actual deployment
- **Environment Simulation**: Test in production-like containerized environment
- **Automated Testing**: Comprehensive test suite for all application components
- **Development Confidence**: Ensure your changes won't break cloud deployment

## What It Tests

### 🏗️ Build Process
- Docker image builds for both Flask app and Chainlit service
- Poetry dependency installation in containers
- Proper container configuration

### 🚀 Deployment Simulation
- Container networking (services communicating with each other)
- Environment variable configuration
- Port mapping and service discovery
- Production-like startup sequence

### 🧪 Functionality Tests
- Health check endpoints
- Landing page rendering
- Authentication pages
- User registration flow
- Service-to-service communication

### 📊 Monitoring
- Container log analysis for errors
- Service startup verification
- Response time and reliability checks

## Usage

### Quick Test
```bash
python test_cloud_deployment.py
```

### With Virtual Environment
```bash
# If you need requests library
pip install requests
python test_cloud_deployment.py
```

## What to Expect

### Successful Run Output
```
============================================================
🚀 We-Relate Cloud Deployment Test
============================================================

[INFO] Checking prerequisites...
[SUCCESS] Docker is available
[INFO] Cleaning up existing containers...
[SUCCESS] Cleanup completed
[INFO] Building Docker images...
[INFO] Building Flask app image...
[INFO] Building Chainlit service image...
[SUCCESS] All images built successfully
[INFO] Creating test network...
[SUCCESS] Test network created
[INFO] Starting containers...
[INFO] Starting Chainlit service...
[INFO] Starting Flask app...
[SUCCESS] All containers started
[INFO] Waiting for services to be ready...
[INFO] Waiting for Flask app...
[SUCCESS] Flask app is ready!
[INFO] Waiting for Chainlit service...
[SUCCESS] Chainlit service is ready!
[INFO] Testing application endpoints...
[SUCCESS] Flask Health Check: ✓
[SUCCESS] Flask Landing Page: ✓
[SUCCESS] Flask Login Page: ✓
[SUCCESS] Chainlit Service: ✓
[INFO] Testing user registration flow...
[SUCCESS] Registration flow: ✓
[INFO] Checking container logs for errors...
[INFO] Checking logs for we-relate-flask-test...
[SUCCESS] No critical errors found in we-relate-flask-test
[INFO] Checking logs for we-relate-chainlit-test...
[SUCCESS] No critical errors found in we-relate-chainlit-test

============================================================
📋 Test Summary
============================================================

[SUCCESS] 🎉 All tests passed! Your application is ready for cloud deployment.
[INFO] ✓ Docker images build successfully
[INFO] ✓ Containers start and run properly
[INFO] ✓ All endpoints respond correctly
[INFO] ✓ Registration flow works
[INFO] Cleaning up test containers...
[SUCCESS] Cleanup completed
```

## When to Run

### During Development
- After making changes to Dockerfiles
- Before committing major features
- When modifying environment variables
- After updating dependencies in `pyproject.toml`

### Before Deployment
- Always run before pushing to production
- After merging feature branches
- When preparing release candidates

## Troubleshooting

### Common Issues

#### Docker Permission Errors
```bash
# If you get permission errors, the script uses sudo automatically
# Make sure your user can run sudo docker commands
```

#### Port Already in Use
```bash
# The script automatically cleans up, but if ports are still busy:
sudo docker stop $(sudo docker ps -q)
sudo docker system prune -f
```

#### Build Failures
- Check that `pyproject.toml` and `poetry.lock` are up to date
- Ensure Dockerfiles are properly configured for Poetry
- Verify all required files are present in the correct directories

#### Service Startup Issues
- Check container logs: `sudo docker logs we-relate-flask-test`
- Verify environment variables are correctly set
- Ensure services can communicate over the Docker network

## Integration with CI/CD

You can integrate this script into your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Test Cloud Deployment
  run: python test_cloud_deployment.py
```

## Files Used

The test script uses these Docker configurations:
- `flask-app/Dockerfile` - Flask application container
- `chainlit-service/Dockerfile` - Chainlit service container
- `pyproject.toml` & `poetry.lock` - Python dependencies

## Cleanup

The script automatically cleans up after itself, but if you need manual cleanup:

```bash
# Stop test containers
sudo docker stop we-relate-flask-test we-relate-chainlit-test

# Remove test containers
sudo docker rm we-relate-flask-test we-relate-chainlit-test

# Remove test network
sudo docker network rm we-relate-test-network

# Remove test images (optional)
sudo docker rmi we-relate-flask-test we-relate-chainlit-test
``` 