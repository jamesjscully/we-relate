# We-Relate: De-escalation Coach Platform

**Practice intentional dialogue for peace, function, and closeness in relationships**

We-Relate is an AI-powered de-escalation coach that helps people practice difficult conversations in a safe environment. Using a sophisticated 3-agent system, users can practice with realistic personas while receiving expert coaching feedback.

## 🎯 How It Works

1. **Setup Phase**: Tell us about your relationship situation and conflict scenario
2. **Practice Phase**: Have a realistic conversation with an AI persona representing the person you're in conflict with
3. **Coaching Phase**: Receive real-time expert feedback on your de-escalation techniques

## 🏗️ Architecture

### Simple Two-Agent System
- **Teacher Agent**: Asks educational questions and provides feedback
- **Student Agent**: Answers questions and engages in learning dialogue
- **User**: Can observe the conversation or interact with either agent

### Technology Stack
- **Frontend**: Flask web application with modern UI
- **Chat Interface**: Chainlit 2.5.5 for conversational AI
- **Backend**: Python with Poetry dependency management
- **AI**: OpenAI GPT-3.5-turbo for natural language processing
- **Deployment**: Docker-ready with multi-service architecture

## 🚀 Quick Start

### Prerequisites
- Python 3.12.8 (managed via pyenv)
- Poetry for dependency management
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd we-relate
```

2. **Set up Python 3.12.8 with pyenv**
```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Install Python 3.12.8
pyenv install 3.12.8
pyenv local 3.12.8
```

3. **Install dependencies with Poetry**
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

4. **Configure environment variables**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

5. **Run the application**
```bash
# Start Flask app (port 5000)
cd flask-app
poetry run python app.py

# Start Chainlit service (port 8000) - in another terminal
cd chainlit-service
poetry run chainlit run app.py --port 8000
```

6. **Access the application**
- Main app: http://localhost:5000
- Direct chat: http://localhost:8000

## 🎭 Features

### For Users
- **Realistic Practice**: AI personas that respond authentically to your communication style
- **Expert Coaching**: Real-time feedback on de-escalation techniques
- **Safe Environment**: Practice difficult conversations without real-world consequences
- **Progress Tracking**: Monitor your communication effectiveness over time

### For Developers
- **Modern Architecture**: Clean separation between web app and chat interface
- **Poetry Management**: Reliable dependency management and virtual environments
- **Extensible Design**: Easy to add new agents or modify existing behavior
- **Docker Ready**: Containerized deployment for production environments

## 🔧 Development

### Project Structure
```
we-relate/
├── flask-app/              # Main web application
│   ├── templates/          # HTML templates
│   ├── static/            # CSS, JS, images
│   └── app.py             # Flask application
├── chainlit-service/       # Chat interface service
│   ├── agents/            # AI agent implementations
│   │   ├── setup_agent.py    # Scenario setup
│   │   ├── persona_agent.py  # Roleplay persona
│   │   └── coach_agent.py    # Coaching feedback
│   ├── config.py          # Configuration management
│   └── app.py             # Chainlit application
├── pyproject.toml         # Poetry configuration
└── README.md              # This file
```

### Adding New Features

#### Adding New Agent Types
To add new agent types for different scenarios:

1. **Create agent classes** in `chainlit-service/app.py`
```python
class CustomAgent(Agent):
    def __init__(self, name: str, specialty: str):
        system_message = f"You are a {specialty} specialist..."
        super().__init__(name, system_message)
```

2. **Implement conversation flows**
```python
class MultiAgentChat:
    def __init__(self, agent_types: List[str]):
        self.agents = [self.create_agent(t) for t in agent_types]
```

#### Customizing Personas
Modify `chainlit-service/agents/persona_agent.py` to:
- Add new personality types
- Implement different conflict scenarios
- Adjust emotional response patterns

#### Enhancing Coaching
Update `chainlit-service/agents/coach_agent.py` to:
- Add new de-escalation techniques
- Implement scoring algorithms
- Create personalized learning paths

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
# Format code
poetry run black .

# Lint code  
poetry run flake8

# Type checking
poetry run mypy .
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Main app: http://localhost:5000
# Chat service: http://localhost:8000
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `DATABASE_URL` | Database connection string | No |
| `DEBUG` | Enable debug mode | No |

## 📊 Subscription Tiers

### Free Tier
- 10 practice sessions per month
- Basic coaching feedback
- Standard personas

### Pro Tier ($9.99/month)
- Unlimited practice sessions
- Advanced coaching analytics
- Custom persona creation
- Progress tracking

### Enterprise Tier (Custom)
- Team management
- Custom integrations
- Advanced analytics
- Priority support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.we-relate.com](https://docs.we-relate.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/we-relate/issues)
- **Email**: support@we-relate.com
- **Discord**: [Join our community](https://discord.gg/we-relate)

## 🙏 Acknowledgments

- OpenAI for GPT-4 language model
- Chainlit for conversational AI framework
- Poetry for dependency management
- The open-source community for inspiration and tools

---

**Built with ❤️ for better relationships and peaceful communication**