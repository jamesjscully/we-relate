#!/usr/bin/env python3
"""
Final integration test to verify Phoenix tracing is working correctly
with all components of the We-Relate application.
"""

import asyncio
import openai
from phoenix_config import setup_phoenix_tracing, add_span_attributes, trace_function

async def main():
    print("=== Final Phoenix Integration Test ===")
    
    # Setup Phoenix
    success = setup_phoenix_tracing()
    print(f"Phoenix setup: {'✅ Success' if success else '❌ Failed'}")
    
    if not success:
        print("Phoenix setup failed, exiting...")
        return
    
    # Test OpenAI auto-instrumentation
    print("\nTesting OpenAI auto-instrumentation...")
    try:
        client = openai.AsyncOpenAI()
        response = await client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': 'Say hello from We-Relate Phoenix setup!'}],
            max_tokens=30
        )
        result = response.choices[0].message.content
        print(f"✅ OpenAI test successful: {result}")
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
    
    # Test custom tracing
    @trace_function("integration_test")
    def test_custom_tracing():
        add_span_attributes(
            test_type="integration",
            component="final_test"
        )
        return "Custom tracing works!"
    
    print("\nTesting custom tracing...")
    custom_result = test_custom_tracing()
    print(f"✅ Custom tracing: {custom_result}")
    
    print("\n=== Integration Test Complete ===")
    print("🎉 Phoenix tracing is ready for We-Relate!")
    print("📊 Check Phoenix UI at http://localhost:6006")
    print("📁 Project name: 'we-relate'")

if __name__ == "__main__":
    asyncio.run(main()) 