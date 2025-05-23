# We Relate

A web application for improving de-escalation communication skills in all human relationships. Practice healthy communication with AI-powered coaching tailored to the important people in your life.

## Features

- **People Profiles**: Store information about important people in your life including personality, diagnoses, communication style, and triggers
- **AI Coaching**: Get personalized advice from Claude Sonnet 4 based on your specific situation
- **Conversation Practice**: Interactive chat interface for practicing communication scenarios
- **Mock Authentication**: Simple username-based authentication for demo purposes
- **Responsive Design**: Bootstrap-powered UI that works on all devices

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
   
   Required variables:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access
   - `SECRET_KEY`: A secret key for Flask sessions

3. **Run the Application**
   ```bash
   python run.py
   ```
   
   The app will be available at `http://localhost:5000`

## Usage

1. **Login**: Enter any username (demo authentication)
2. **Add People**: Create profiles with information about people in your life
3. **Start Chat**: Begin a coaching conversation with optional scenario description
4. **Get Advice**: Receive personalized de-escalation and communication guidance

## Technology Stack

- **Backend**: Flask with SQLAlchemy (SQLite database)
- **Frontend**: Bootstrap 5 + HTMX for dynamic interactions
- **AI**: Anthropic Claude Sonnet 4 for coaching responses
- **Authentication**: Mock service (username-only for demo)

## Database Schema

- **Users**: Basic user information
- **People**: People profiles with communication details
- **Conversations**: Chat sessions with scenarios
- **Messages**: Individual messages in conversations

## Privacy

All data is stored locally in SQLite. People information is used only to provide better coaching advice and can be edited or deleted at any time.