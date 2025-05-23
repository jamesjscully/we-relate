# We Relate

A ChatGPT-style web application for improving de-escalation communication skills in all human relationships. Practice healthy communication with AI-powered coaching tailored to the important people in your life.

![We Relate Screenshot](https://via.placeholder.com/800x400/10b981/ffffff?text=We+Relate+Chat+Interface)

## ✨ Features

- **🎯 ChatGPT-style Interface**: Modern sidebar with recent chats and navigation
- **👥 People Profiles**: Store detailed information about important people in your life
- **🤖 AI Coaching**: Get personalized advice from Claude Sonnet 4
- **💬 Real-time Chat**: Interactive conversation practice with HTMX
- **📱 Mobile Responsive**: Works seamlessly on all devices
- **🔒 Privacy First**: All data stored locally, mock authentication for demos

## 🚀 Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone git@github.com:jamesjscully/we-relate.git
   cd we-relate
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Anthropic API key
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the app**
   Open http://localhost:5000 in your browser

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Anthropic API key from [console.anthropic.com](https://console.anthropic.com/)

### Local Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment setup**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   SECRET_KEY=your-random-secret-key
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

### Docker Development

1. **Build the image**
   ```bash
   docker build -t we-relate .
   ```

2. **Run the container**
   ```bash
   docker run -p 5000:5000 --env-file .env we-relate
   ```

## 📖 Usage Guide

1. **Login**: Enter any username (demo authentication)
2. **Add People**: Click "Add Person" to create profiles for people in your life
3. **Start Conversations**: Use "New Chat" to begin coaching sessions
4. **Get Coaching**: Receive personalized communication advice based on your situation

## 🏗️ Architecture

### Backend
- **Flask 3.0.3**: Web framework
- **SQLAlchemy**: Database ORM with SQLite
- **Anthropic Claude**: AI coaching responses
- **Python-dotenv**: Environment management

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **HTMX**: Dynamic interactions without JavaScript frameworks
- **Custom CSS**: ChatGPT-inspired design

### Infrastructure
- **Docker**: Containerized deployment
- **SQLite**: Local database storage
- **Git**: Version control

## 🗃️ Database Schema

```sql
-- Users table
User: id, username, email, created_at

-- People profiles
Person: id, user_id, name, description, diagnoses, communication_style, triggers, created_at

-- Chat sessions
Conversation: id, user_id, person_id, title, scenario, created_at

-- Individual messages
Message: id, conversation_id, role, content, created_at
```

## 🔒 Privacy & Security

- **Local Storage**: All data stored in local SQLite database
- **No External Sharing**: Person information only used for coaching
- **Mock Authentication**: Demo-friendly, not production-ready
- **API Security**: Anthropic API key stored in environment variables

## 🚢 Deployment

### Docker Production

1. **Set production environment**
   ```bash
   export FLASK_ENV=production
   ```

2. **Use docker-compose**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

### Manual Deployment

1. **Set up production database**
2. **Configure reverse proxy** (nginx recommended)
3. **Set environment variables**
4. **Run with WSGI server** (gunicorn recommended)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude AI capabilities
- **OpenAI** for ChatGPT UI inspiration
- **Bootstrap** for responsive design
- **HTMX** for seamless interactions