#!/usr/bin/env python3
"""
Advanced Phoenix tracing test demonstrating various patterns.
This helps us understand how to properly integrate tracing into the We-Relate app.
"""

import os
import asyncio
from phoenix.otel import register
import openai
from opentelemetry import trace

# Set up Phoenix endpoint
PHOENIX_ENDPOINT = "http://localhost:6006/v1/traces"

# Configure Phoenix tracer
print("Setting up Phoenix tracer...")
tracer_provider = register(
    project_name="we-relate-advanced-test",
    auto_instrument=True,
    endpoint=PHOENIX_ENDPOINT,
)
tracer = tracer_provider.get_tracer(__name__)

# Manual trace creation (alternative to decorators)
def get_current_tracer():
    """Get the current tracer for manual span creation"""
    return trace.get_tracer(__name__)

@tracer.chain
def simulate_coach_response(user_input: str) -> str:
    """Simulate coach response generation with tracing"""
    # Add custom attributes to the span
    current_span = trace.get_current_span()
    current_span.set_attribute("user_input_length", len(user_input))
    current_span.set_attribute("component", "coach")
    
    # Simulate processing
    if "angry" in user_input.lower():
        response = "I understand you're feeling upset. Let's practice some de-escalation techniques."
    elif "help" in user_input.lower():
        response = "I'm here to guide you through intentional dialogue. What's the situation?"
    else:
        response = "Tell me more about what's happening in your relationship."
    
    current_span.set_attribute("response_type", "coaching_advice")
    current_span.set_attribute("response_length", len(response))
    
    return response

@tracer.chain
def simulate_partner_response(user_input: str, emotional_state: str) -> str:
    """Simulate partner response with emotional state tracking"""
    current_span = trace.get_current_span()
    current_span.set_attribute("emotional_state", emotional_state)
    current_span.set_attribute("user_input", user_input)
    current_span.set_attribute("component", "partner")
    
    # Simulate emotional response based on state
    if emotional_state == "angry":
        response = "You never listen to me! This is exactly what I'm talking about!"
    elif emotional_state == "hurt":
        response = "I just feel like you don't care about my feelings..."
    else:
        response = "I'm trying to understand, but it's difficult."
    
    current_span.set_attribute("response_emotion", emotional_state)
    return response

@tracer.chain
def simulate_error_scenario() -> str:
    """Test error handling in traces"""
    current_span = trace.get_current_span()
    current_span.set_attribute("test_type", "error_handling")
    
    try:
        # Simulate an error
        raise ValueError("Simulated error for testing Phoenix error tracking")
    except ValueError as e:
        # Record the error in the span
        current_span.record_exception(e)
        current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        return f"Error handled: {str(e)}"

async def test_async_openai_call():
    """Test async OpenAI calls with automatic instrumentation"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found, skipping async OpenAI test")
        return None
    
    # Manual span creation for async context
    tracer = get_current_tracer()
    with tracer.start_as_current_span("async_openai_test") as span:
        span.set_attribute("test_type", "async_openai")
        span.set_attribute("model", "gpt-4o-mini")
        
        client = openai.AsyncOpenAI()
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a relationship coach."},
                    {"role": "user", "content": "My partner is upset, what should I do?"}
                ],
                max_tokens=100
            )
            result = response.choices[0].message.content
            span.set_attribute("response_length", len(result))
            span.set_attribute("completion_tokens", response.usage.completion_tokens if response.usage else 0)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            return None

def test_nested_function_tracing():
    """Test nested function calls with tracing"""
    tracer = get_current_tracer()
    
    with tracer.start_as_current_span("conversation_flow") as conversation_span:
        conversation_span.set_attribute("conversation_type", "de_escalation")
        
        # Simulate a conversation flow
        user_input = "My partner is really angry at me"
        conversation_span.set_attribute("initial_user_input", user_input)
        
        # Coach responds
        coach_advice = simulate_coach_response(user_input)
        conversation_span.set_attribute("coach_response", coach_advice)
        
        # User tries the advice with partner
        partner_response = simulate_partner_response("I understand you're upset", "angry")
        conversation_span.set_attribute("partner_response", partner_response)
        
        # Test error handling
        error_result = simulate_error_scenario()
        conversation_span.set_attribute("error_test_result", error_result)
        
        return {
            "coach_advice": coach_advice,
            "partner_response": partner_response,
            "error_result": error_result
        }

async def main():
    """Run comprehensive Phoenix tracing tests"""
    print("=== Advanced Phoenix Tracing Test ===")
    print(f"Phoenix endpoint: {PHOENIX_ENDPOINT}")
    print(f"Project name: we-relate-advanced-test")
    print()
    
    # Test 1: Basic function tracing
    print("1. Testing basic coach simulation...")
    coach_result = simulate_coach_response("I need help with my angry partner")
    print(f"Coach advice: {coach_result}")
    print()
    
    # Test 2: Partner simulation with emotional state
    print("2. Testing partner simulation...")
    partner_result = simulate_partner_response("I'm sorry, let's talk", "hurt")
    print(f"Partner response: {partner_result}")
    print()
    
    # Test 3: Error handling
    print("3. Testing error handling...")
    error_result = simulate_error_scenario()
    print(f"Error test: {error_result}")
    print()
    
    # Test 4: Nested function tracing
    print("4. Testing nested conversation flow...")
    conversation_result = test_nested_function_tracing()
    print(f"Conversation flow completed: {len(conversation_result)} steps traced")
    print()
    
    # Test 5: Async OpenAI call
    print("5. Testing async OpenAI call...")
    async_result = await test_async_openai_call()
    if async_result:
        print(f"Async OpenAI response: {async_result[:100]}...")
    print()
    
    print("=== Advanced Test Complete ===")
    print("Check Phoenix UI at http://localhost:6006 to see:")
    print("- Function-level traces with custom attributes")
    print("- Error traces with exception details")
    print("- Nested span relationships")
    print("- OpenAI API call traces")
    print("- Performance metrics and timing")

if __name__ == "__main__":
    asyncio.run(main()) 