#!/usr/bin/env python3
"""
Cloud Deployment Test Script for We-Relate
==========================================

This script tests the application in a cloud-like environment using Docker containers
to catch deployment issues early during development.

Usage: python test_cloud_deployment.py
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {cmd}")
        return False, "", "Timeout"
    except Exception as e:
        print_error(f"Command failed: {cmd} - {e}")
        return False, "", str(e)

def check_prerequisites():
    """Check if Docker is available"""
    print_status("Checking prerequisites...")
    
    success, _, _ = run_command("docker --version")
    if not success:
        print_error("Docker is not installed or not accessible")
        print_error("Please install Docker or run with sudo if needed")
        return False
    
    print_success("Docker is available")
    return True

def cleanup_containers():
    """Clean up any existing containers"""
    print_status("Cleaning up existing containers...")
    
    # Stop and remove containers
    containers = ["we-relate-flask-test", "we-relate-chainlit-test"]
    for container in containers:
        run_command(f"sudo docker stop {container}", capture_output=True)
        run_command(f"sudo docker rm {container}", capture_output=True)
    
    # Remove test network if it exists
    run_command("sudo docker network rm we-relate-test-network", capture_output=True)
    
    print_success("Cleanup completed")

def build_images():
    """Build Docker images for both services"""
    print_status("Building Docker images...")
    
    # Build Flask app image
    print_status("Building Flask app image...")
    success, stdout, stderr = run_command(
        "sudo docker build -f flask-app/Dockerfile -t we-relate-flask-test ."
    )
    if not success:
        print_error("Failed to build Flask app image")
        print_error(f"Error: {stderr}")
        return False
    
    # Build Chainlit service image
    print_status("Building Chainlit service image...")
    success, stdout, stderr = run_command(
        "sudo docker build -f chainlit-service/Dockerfile -t we-relate-chainlit-test ."
    )
    if not success:
        print_error("Failed to build Chainlit service image")
        print_error(f"Error: {stderr}")
        return False
    
    print_success("All images built successfully")
    return True

def create_test_network():
    """Create a test network for containers"""
    print_status("Creating test network...")
    success, _, _ = run_command("sudo docker network create we-relate-test-network")
    if success:
        print_success("Test network created")
    return True

def start_containers():
    """Start containers in cloud-like configuration"""
    print_status("Starting containers...")
    
    # Start Chainlit service first
    print_status("Starting Chainlit service...")
    chainlit_cmd = """
    sudo docker run -d \
        --name we-relate-chainlit-test \
        --network we-relate-test-network \
        -p 8000:8080 \
        -e PORT=8080 \
        -e OPENAI_API_KEY=${OPENAI_API_KEY:-invalid-key-for-testing} \
        we-relate-chainlit-test
    """
    success, _, stderr = run_command(chainlit_cmd)
    if not success:
        print_error(f"Failed to start Chainlit service: {stderr}")
        return False
    
    # Wait a moment for Chainlit to initialize
    time.sleep(3)
    
    # Start Flask app
    print_status("Starting Flask app...")
    flask_cmd = """
    sudo docker run -d \
        --name we-relate-flask-test \
        --network we-relate-test-network \
        -p 5000:8080 \
        -e PORT=8080 \
        -e SECRET_KEY=test-secret-key \
        -e CHAINLIT_SERVICE_URL=http://we-relate-chainlit-test:8080 \
        -e DATABASE_PATH=/app/data/app.db \
        -e FLASK_ENV=production \
        we-relate-flask-test
    """
    success, _, stderr = run_command(flask_cmd)
    if not success:
        print_error(f"Failed to start Flask app: {stderr}")
        return False
    
    print_success("All containers started")
    return True

def wait_for_services():
    """Wait for services to be ready"""
    print_status("Waiting for services to be ready...")
    
    services = [
        ("Flask app", "http://localhost:5000/health"),
        ("Chainlit service", "http://localhost:8000")
    ]
    
    for service_name, url in services:
        print_status(f"Waiting for {service_name}...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    print_success(f"{service_name} is ready!")
                    break
            except requests.exceptions.RequestException:
                pass
            
            if attempt == max_attempts - 1:
                print_error(f"{service_name} failed to start within {max_attempts * 2} seconds")
                return False
            
            time.sleep(2)
            print(".", end="", flush=True)
        print()  # New line after dots
    
    return True

def test_endpoints():
    """Test various endpoints to ensure functionality"""
    print_status("Testing application endpoints...")
    
    tests = [
        {
            "name": "Flask Health Check",
            "url": "http://localhost:5000/health",
            "expected_status": 200,
            "check_json": True
        },
        {
            "name": "Flask Landing Page",
            "url": "http://localhost:5000/",
            "expected_status": 200,
            "check_content": "We-Relate"
        },
        {
            "name": "Flask Login Page",
            "url": "http://localhost:5000/auth/login",
            "expected_status": 200,
            "check_content": "Login"
        },
        {
            "name": "Chainlit Service",
            "url": "http://localhost:8000/",
            "expected_status": 200
        }
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            response = requests.get(test["url"], timeout=10)
            
            # Check status code
            if response.status_code != test["expected_status"]:
                print_error(f"{test['name']}: Expected {test['expected_status']}, got {response.status_code}")
                all_passed = False
                continue
            
            # Check JSON response if required
            if test.get("check_json"):
                try:
                    data = response.json()
                    if "status" not in data:
                        print_error(f"{test['name']}: Invalid JSON response")
                        all_passed = False
                        continue
                except json.JSONDecodeError:
                    print_error(f"{test['name']}: Response is not valid JSON")
                    all_passed = False
                    continue
            
            # Check content if required
            if test.get("check_content"):
                if test["check_content"] not in response.text:
                    print_error(f"{test['name']}: Expected content '{test['check_content']}' not found")
                    all_passed = False
                    continue
            
            print_success(f"{test['name']}: ✓")
            
        except requests.exceptions.RequestException as e:
            print_error(f"{test['name']}: Connection failed - {e}")
            all_passed = False
    
    return all_passed

def test_registration_flow():
    """Test user registration functionality"""
    print_status("Testing user registration flow...")
    
    try:
        # Test registration
        registration_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123"
        }
        
        response = requests.post(
            "http://localhost:5000/",
            data=registration_data,
            timeout=10,
            allow_redirects=False
        )
        
        # Should redirect on successful registration
        if response.status_code in [302, 200]:
            print_success("Registration flow: ✓")
            return True
        else:
            print_error(f"Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Registration test failed: {e}")
        return False

def check_container_logs():
    """Check container logs for errors"""
    print_status("Checking container logs for errors...")
    
    containers = ["we-relate-flask-test", "we-relate-chainlit-test"]
    
    for container in containers:
        print_status(f"Checking logs for {container}...")
        success, logs, _ = run_command(f"sudo docker logs {container}")
        
        if success and logs:
            # Look for common error patterns
            error_patterns = ["ERROR", "CRITICAL", "Exception", "Traceback", "Failed"]
            errors_found = []
            
            for line in logs.split('\n'):
                for pattern in error_patterns:
                    if pattern in line and "404" not in line:  # Ignore 404s
                        errors_found.append(line.strip())
            
            if errors_found:
                print_warning(f"Potential issues found in {container}:")
                for error in errors_found[-5:]:  # Show last 5 errors
                    print(f"  {error}")
            else:
                print_success(f"No critical errors found in {container}")

def main():
    """Main test function"""
    print_header("🚀 We-Relate Cloud Deployment Test")
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    try:
        # Prerequisites
        if not check_prerequisites():
            return False
        
        # Cleanup
        cleanup_containers()
        
        # Build images
        if not build_images():
            return False
        
        # Create network
        create_test_network()
        
        # Start containers
        if not start_containers():
            return False
        
        # Wait for services
        if not wait_for_services():
            return False
        
        # Test endpoints
        endpoints_passed = test_endpoints()
        
        # Test registration
        registration_passed = test_registration_flow()
        
        # Check logs
        check_container_logs()
        
        # Summary
        print_header("📋 Test Summary")
        
        if endpoints_passed and registration_passed:
            print_success("🎉 All tests passed! Your application is ready for cloud deployment.")
            print_status("✓ Docker images build successfully")
            print_status("✓ Containers start and run properly")
            print_status("✓ All endpoints respond correctly")
            print_status("✓ Registration flow works")
            return True
        else:
            print_error("❌ Some tests failed. Please check the issues above.")
            return False
    
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        return False
    
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False
    
    finally:
        # Always cleanup
        print_status("Cleaning up test containers...")
        cleanup_containers()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 