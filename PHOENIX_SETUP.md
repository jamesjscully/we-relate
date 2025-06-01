# Phoenix Tracing Setup for We-Relate

This document explains how to use Phoenix tracing with the We-Relate application for observability and debugging.

## 🏃 Quick Start

### 1. Start Phoenix Server

Phoenix is already configured in `docker-compose.yml`. Start it with:

```bash
docker-compose up phoenix -d
```

### 2. Verify Phoenix is Running

- Check the container: `docker ps | grep phoenix`
- Access Phoenix UI: http://localhost:6006
- Test API: `curl http://localhost:6006/v1/projects`

### 3. Test Tracing

Run our test scripts to verify everything works:

```bash
# Basic tracing test
poetry run python test_phoenix_tracing.py

# Advanced tracing patterns
poetry run python test_phoenix_advanced.py

# Configuration module test
poetry run python test_phoenix_config.py
```

## 📋 Environment Variables

Set these in your `.env` file:

```bash
# Enable/disable tracing (default: true)
PHOENIX_TRACING_ENABLED=true

# Phoenix endpoint (default: self-hosted)
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# For Phoenix Cloud (alternative to self-hosted):
# PHOENIX_CLIENT_HEADERS=api_key=your_phoenix_api_key_here
# PHOENIX_ENDPOINT=https://app.phoenix.arize.com/v1/traces
```

## 🛠 Integration with We-Relate

### Using the Configuration Module

```python
from phoenix_config import setup_phoenix_tracing, trace_coach_response, trace_partner_response

# Setup tracing at app startup
setup_phoenix_tracing()

# Use decorators for automatic tracing
@trace_coach_response
def coach_respond(self, history):
    # Your coach logic here
    return response

@trace_partner_response  
def partner_respond(self, history):
    # Your partner logic here
    return response
```

### Manual Span Creation

```python
from phoenix_config import get_tracer, add_span_attributes

tracer = get_tracer()
if tracer:
    with tracer.start_as_current_span("custom_operation") as span:
        add_span_attributes(
            user_id="123",
            conversation_type="de_escalation"
        )
        # Your logic here
```

## 📊 What Gets Traced

### Automatic Instrumentation
- All OpenAI API calls (tokens, timing, responses)
- HTTP requests and responses
- Database queries (if configured)

### Custom Tracing
- Coach response generation
- Partner response generation  
- Conversation flows
- Error handling
- Custom business logic

### Trace Attributes

Phoenix captures:
- Function execution time
- Input/output data
- Error details and stack traces
- Custom attributes (user_id, conversation_id, etc.)
- Token usage and costs

## 🎯 Use Cases

### 1. Performance Monitoring
- Track response generation times
- Monitor OpenAI API latency
- Identify slow operations

### 2. Debugging
- See exact conversation flows
- Track error propagation
- Analyze user interaction patterns

### 3. Cost Analysis
- Monitor OpenAI token usage
- Track API costs per conversation
- Optimize prompt efficiency

### 4. User Experience
- Analyze conversation quality
- Track coaching effectiveness
- Monitor emotional state transitions

## 🔧 Troubleshooting

### Phoenix Not Starting
```bash
# Check logs
docker-compose logs phoenix

# Restart Phoenix
docker-compose restart phoenix
```

### No Traces Appearing
1. Verify `PHOENIX_TRACING_ENABLED=true`
2. Check Phoenix endpoint is correct
3. Ensure OpenAI API key is set
4. Run test scripts to verify setup

### Performance Issues
The current setup uses `SimpleSpanProcessor` which is fine for development but not optimal for production. For production:

1. Consider using `BatchSpanProcessor`
2. Adjust trace sampling rates
3. Use Phoenix Cloud for better performance

## 📚 Next Steps

Once Phoenix is working with our test scripts:

1. Integrate tracing into `chainlit-service/core.py`
2. Add tracing to Flask app routes
3. Set up custom dashboards in Phoenix
4. Configure alerts for errors/performance issues

## 🔗 Useful Links

- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [Phoenix Tracing Guide](https://docs.arize.com/phoenix/tracing/llm-traces-1/quickstart-tracing-python)
- [Phoenix UI](http://localhost:6006) (when running)

## 📁 Files in This Setup

- `test_phoenix_tracing.py` - Basic tracing test
- `test_phoenix_advanced.py` - Advanced patterns and error handling
- `test_phoenix_config.py` - Configuration module test
- `phoenix_config.py` - Centralized configuration and utilities
- `docker-compose.yml` - Phoenix server configuration 