#!/usr/bin/env python3
"""
Setup script for Flask + Chainlit/Langroid Architecture
This script helps initialize the application with proper configuration.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_env_file(service_dir, env_content):
    """Create .env file from template"""
    env_path = os.path.join(service_dir, '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_path}")
    else:
        print(f"⚠️  {env_path} already exists, skipping...")

def install_dependencies(service_dir):
    """Install Python dependencies for a service"""
    requirements_path = os.path.join(service_dir, 'requirements.txt')
    if os.path.exists(requirements_path):
        print(f"📦 Installing dependencies for {service_dir}...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', requirements_path
            ], check=True, cwd=service_dir)
            print(f"✅ Dependencies installed for {service_dir}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies for {service_dir}: {e}")
    else:
        print(f"⚠️  No requirements.txt found in {service_dir}")

def main():
    """Main setup function"""
    print("🚀 Setting up Flask + Chainlit/Langroid Architecture")
    print("=" * 50)
    
    # Flask app environment
    flask_env = """# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
PORT=5000

# Service URLs
CHAINLIT_SERVICE_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite:///app.db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Stripe (for billing - optional)
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
"""
    
    # Chainlit service environment
    chainlit_env = """# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Service Configuration
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000

# Flask Service Integration
FLASK_SERVICE_URL=http://localhost:5000

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Agent Configuration
MAX_CONVERSATION_HISTORY=50
DEFAULT_AGENT=general

# Rate Limiting
RATE_LIMIT_FREE=10
RATE_LIMIT_PREMIUM=100
CREDIT_COST_PER_MESSAGE=1
"""
    
    # Create environment files
    print("📝 Creating environment files...")
    create_env_file('flask-app', flask_env)
    create_env_file('chainlit-service', chainlit_env)
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    install_dependencies('flask-app')
    install_dependencies('chainlit-service')
    
    # Initialize database
    print("\n🗄️  Initializing database...")
    try:
        os.chdir('flask-app')
        subprocess.run([sys.executable, '-c', 
                       'from app import init_db; init_db()'], check=True)
        print("✅ Database initialized")
        os.chdir('..')
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        os.chdir('..')
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Update the .env files with your actual API keys")
    print("2. For OpenAI: Add your OPENAI_API_KEY to chainlit-service/.env")
    print("3. For Stripe (optional): Add your Stripe keys to flask-app/.env")
    print("4. Start the services:")
    print("   - Option 1: docker-compose up --build")
    print("   - Option 2: Run manually:")
    print("     • Flask: cd flask-app && python app.py")
    print("     • Chainlit: cd chainlit-service && chainlit run app.py --host 0.0.0.0 --port 8000")
    print("\n🌐 Access the app at http://localhost:5000")
    print("👤 Demo user: username=demo, password=demo123")

if __name__ == '__main__':
    main() 