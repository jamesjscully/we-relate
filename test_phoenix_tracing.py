#!/usr/bin/env python3
"""
Simple Phoenix tracing test script following the official documentation.
This tests Phoenix tracing functionality before integrating into the main app.
"""

import os
from phoenix.otel import register
import openai

# Set up Phoenix endpoint for self-hosted (we'll run Phoenix in Docker)
PHOENIX_ENDPOINT = "http://localhost:6006/v1/traces"

# Configure Phoenix tracer following the documentation
print("Setting up Phoenix tracer...")
tracer_provider = register(
    project_name="we-relate-test",  # Test project name
    auto_instrument=True,  # Enable automatic instrumentation
    endpoint=PHOENIX_ENDPOINT,
)
tracer = tracer_provider.get_tracer(__name__)

# Test function with Phoenix decorator
@tracer.chain
def test_simple_function(input_text: str = "hello world") -> str:
    """Test function that will be traced by Phoenix"""
    print(f"Processing: {input_text}")
    processed = f"Processed: {input_text.upper()}"
    return processed

# Test OpenAI integration (if API key is available)
def test_openai_tracing():
    """Test OpenAI auto-instrumentation"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found, skipping OpenAI test")
        return
    
    print("Testing OpenAI auto-instrumentation...")
    client = openai.OpenAI()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for testing
            messages=[{"role": "user", "content": "Say hello from Phoenix tracing test!"}],
            max_tokens=50
        )
        result = response.choices[0].message.content
        print(f"OpenAI response: {result}")
        return result
    except Exception as e:
        print(f"OpenAI test failed: {e}")
        return None

def main():
    """Run Phoenix tracing tests"""
    print("=== Phoenix Tracing Test ===")
    print(f"Phoenix endpoint: {PHOENIX_ENDPOINT}")
    print(f"Project name: we-relate-test")
    print()
    
    # Test simple function tracing
    print("1. Testing simple function tracing...")
    result1 = test_simple_function("hello world")
    print(f"Result: {result1}")
    print()
    
    # Test OpenAI auto-instrumentation
    print("2. Testing OpenAI auto-instrumentation...")
    result2 = test_openai_tracing()
    print()
    
    print("=== Test Complete ===")
    print("Check Phoenix UI at http://localhost:6006 to see traces")
    print("If traces appear, Phoenix is working correctly!")

if __name__ == "__main__":
    main() 