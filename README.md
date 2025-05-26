# Flask + Chainlit/Langroid AI Chat Platform

A modern, scalable AI chat platform built with Flask and Chainlit, featuring user authentication, billing, and multiple AI agents.

## 🏗️ Architecture Overview

This application uses a microservices architecture with two main components:

### 1. **Flask App** (Port 5000)
- **Purpose**: User management, authentication, billing, and web interface
- **Features**:
  - User registration and login
  - Session management with Redis support
  - Credit-based billing system
  - Subscription management
  - Modern responsive UI
  - API endpoints for Chainlit integration

### 2. **Chainlit Service** (Port 8000)
- **Purpose**: AI chat interface and agent management
- **Features**:
  - Multiple AI agents (Teacher, Student, General)
  - Real-time chat interface
  - OpenAI integration
  - Credit tracking and deduction
  - Conversation history
  - Command system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis (optional, for session sharing)
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd we-relate
python setup.py
```

### 2. Configure Environment Variables
Update the generated `.env` files:

**flask-app/.env:**
```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
CHAINLIT_SERVICE_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
```

**chainlit-service/.env:**
```env
OPENAI_API_KEY=your-openai-api-key-here
FLASK_SERVICE_URL=http://localhost:5000
REDIS_URL=redis://localhost:6379
```

### 3. Start the Services

**Option 1: Docker Compose (Recommended)**
```bash
docker-compose up --build
```

**Option 2: Manual Start**
```bash
# Terminal 1 - Flask App
cd flask-app
python app.py

# Terminal 2 - Chainlit Service
cd chainlit-service
chainlit run app.py --host 0.0.0.0 --port 8000
```

### 4. Access the Application
- **Web Interface**: http://localhost:5000
- **Demo User**: username=`demo`, password=`demo123`

## 📁 Project Structure

```
we-relate/
├── flask-app/                 # Flask web application
│   ├── auth/                  # Authentication module
│   │   ├── __init__.py
│   │   ├── auth.py           # Auth routes
│   │   ├── models.py         # User models
│   │   └── decorators.py     # Auth decorators
│   ├── billing/              # Billing module
│   │   ├── __init__.py
│   │   ├── billing.py        # Billing routes
│   │   ├── models.py         # Subscription models
│   │   └── stripe_integration.py
│   ├── static/               # Static assets
│   │   └── css/style.css
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── chat.html
│   │   ├── billing.html
│   │   └── settings.html
│   ├── app.py               # Main Flask application
│   ├── config.py            # Configuration
│   └── requirements.txt
├── chainlit-service/         # Chainlit AI service
│   ├── agents/              # AI agent implementations
│   │   ├── __init__.py
│   │   ├── teacher.py       # Teacher agent
│   │   └── student.py       # Student agent
│   ├── app.py              # Main Chainlit application
│   ├── config.py           # Configuration
│   └── requirements.txt
├── docker-compose.yml       # Docker orchestration
├── deploy.sh               # Deployment script
├── setup.py               # Setup script
└── README.md
```

## 🎯 Features

### User Management
- **Registration/Login**: Secure user authentication
- **Session Management**: Redis-backed sessions for scalability
- **User Tiers**: Free, Premium, Admin tiers with different privileges
- **Credit System**: Pay-per-use credit system

### AI Chat Interface
- **Multiple Agents**: Switch between Teacher, Student, and General agents
- **Real-time Chat**: Powered by Chainlit for smooth UX
- **Conversation History**: Persistent chat history
- **Commands**: Built-in commands for agent switching and utilities

### Billing & Subscriptions
- **Credit Tracking**: Real-time credit deduction
- **Subscription Management**: Upgrade/downgrade plans
- **Payment Integration**: Stripe-ready (placeholder implementation)

### Technical Features
- **Microservices**: Loosely coupled services
- **API Integration**: RESTful APIs between services
- **Responsive Design**: Modern, mobile-friendly UI
- **Docker Support**: Easy deployment with Docker
- **Configuration Management**: Environment-based config

## 🔧 Configuration

### Flask App Configuration
```python
# config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    CHAINLIT_SERVICE_URL = os.environ.get('CHAINLIT_SERVICE_URL')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
```

### Chainlit Service Configuration
```python
# config.py
class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    FLASK_SERVICE_URL = os.environ.get('FLASK_SERVICE_URL')
    MAX_CONVERSATION_HISTORY = 50
```

## 🤖 AI Agents

### Teacher Agent
- Educational support and explanations
- Structured learning guidance
- Concept clarification

### Student Agent
- Learning companion
- Study assistance
- Problem-solving help

### General Agent
- General-purpose AI assistant
- Wide variety of tasks
- Conversational AI

## 💳 Billing System

### Credit System
- **Free Tier**: 100 credits
- **Premium Tier**: 500 credits
- **Credit Cost**: 1 credit per message

### Subscription Tiers
- **Free**: Limited credits, basic features
- **Premium**: More credits, advanced features
- **Admin**: Unlimited access, admin features

## 🔌 API Endpoints

### Flask App APIs
```
GET  /                          # Main chat interface
POST /auth/login               # User login
POST /auth/register            # User registration
GET  /auth/logout              # User logout
GET  /billing                  # Billing dashboard
POST /billing/upgrade          # Upgrade subscription
GET  /api/user/credits         # Get user credits
POST /api/user/update-credits  # Update credits
```

### Chainlit Service
```
WebSocket /                    # Chat interface
GET  /health                   # Health check
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and start all services
docker-compose up --build

# Scale services
docker-compose up --scale chainlit-service=2

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Deploy to production
./deploy.sh production

# Deploy to staging
./deploy.sh staging
```

## 🔒 Security Features

- **Password Hashing**: Werkzeug security
- **Session Security**: Secure cookies, CSRF protection
- **API Authentication**: Session-based auth
- **Environment Variables**: Sensitive data protection
- **CORS Configuration**: Controlled cross-origin requests

## 🧪 Testing

```bash
# Run Flask app tests
cd flask-app
python -m pytest tests/

# Run Chainlit service tests
cd chainlit-service
python -m pytest tests/
```

## 📊 Monitoring

### Health Checks
- Flask: `GET /health`
- Chainlit: WebSocket connection status
- Redis: Connection monitoring

### Logging
- Application logs
- Error tracking
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and code comments
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions

## 🔮 Roadmap

- [ ] Stripe payment integration
- [ ] Advanced AI agent capabilities
- [ ] Real-time collaboration
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Multi-language support

---

**Built with ❤️ using Flask, Chainlit, and OpenAI**