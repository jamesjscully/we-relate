# Demo Mode Guide

## Issues Fixed

### 1. WebsocketSession Attribute Error
**Problem**: `'WebsocketSession' object has no attribute 'created_at'`
**Solution**: Replaced `cl.context.session.created_at.isoformat()` with `datetime.now().isoformat()`

### 2. OpenAI API Quota Exceeded
**Problem**: 429 errors due to insufficient OpenAI API quota
**Solution**: Added comprehensive error handling and demo mode functionality

## Demo Mode Features

When `DEMO_MODE=true` is set in the environment, the application provides:

### 🤖 General Assistant Demo Responses
- Keyword-based responses for common queries
- Programming help demonstrations
- Mathematics assistance examples
- Feature explanations

### 👨‍🏫 Teacher Agent Demo
- Educational explanations and study guidance
- Learning tips and resource suggestions
- Structured teaching approach demonstrations

### 👨‍🎓 Student Agent Demo
- Peer learning support examples
- Study strategies and motivation
- Stress management and study tips

## How to Enable Demo Mode

1. **Environment Variable**: Add `DEMO_MODE=true` to your `.env` file
2. **No OpenAI API Key Required**: The app will work without a valid OpenAI API key
3. **Full Interface**: All chat features, commands, and agent switching work normally

## Available Commands in Demo Mode

- `/agent teacher` - Switch to educational assistant
- `/agent student` - Switch to study companion
- `/agent general` - Switch to general assistant
- `/help` - Show all available commands
- `/history` - View conversation history
- `/clear` - Clear conversation history
- `/credits` - Check account status

## Error Handling Improvements

### OpenAI API Errors
- **Rate Limit (429)**: Friendly message asking to wait
- **Authentication**: Clear message about API key issues
- **Quota Exceeded**: Specific message about quota limits
- **General Errors**: Detailed error information for debugging

### Agent-Specific Error Messages
- **Teacher Agent**: Educational context in error messages
- **Student Agent**: Peer-friendly error explanations
- **General Agent**: Standard helpful error responses

## Running the Services

### Flask Service
```bash
cd flask-app
python app.py
```
Access at: http://localhost:5000

### Chainlit Service (Demo Mode)
```bash
cd chainlit-service
chainlit run app.py --host 0.0.0.0 --port 8000
```
Access at: http://localhost:8000

## Production Mode

To switch back to production mode with OpenAI API:

1. Set `DEMO_MODE=false` in `.env`
2. Add valid `OPENAI_API_KEY` to `.env`
3. Restart the Chainlit service

## Benefits of Demo Mode

- **No API Costs**: Demonstrate functionality without API usage
- **Instant Responses**: No waiting for API calls
- **Feature Showcase**: All interface features work normally
- **Error-Free**: No API-related errors during demonstrations
- **Educational**: Shows different agent personalities and approaches

## User Experience

Users can:
- Experience the full chat interface
- Test all commands and features
- Switch between different AI agents
- See conversation history
- Understand the platform's capabilities

The demo responses are designed to be informative and showcase what the full AI-powered version would provide. 