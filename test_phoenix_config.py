#!/usr/bin/env python3
"""
Test script for the Phoenix configuration module.
This verifies that our configuration approach works correctly.
"""

import os
from phoenix_config import (
    setup_phoenix_tracing, 
    trace_function, 
    trace_coach_response, 
    trace_partner_response,
    add_span_attributes
)

# Test the configuration setup
print("Testing Phoenix configuration module...")

# Setup tracing
success = setup_phoenix_tracing()
print(f"Phoenix tracing setup: {'Success' if success else 'Failed'}")

# Test basic function tracing
@trace_function("test_basic_function")
def basic_function(message: str) -> str:
    add_span_attributes(message_length=len(message), message_type="test")
    return f"Processed: {message}"

# Test coach-specific tracing
@trace_coach_response
def mock_coach_respond(user_input: str) -> str:
    add_span_attributes(
        user_input_length=len(user_input),
        advice_type="de_escalation"
    )
    return "I understand you're feeling frustrated. Let's take a step back and practice some breathing exercises."

# Test partner-specific tracing
@trace_partner_response
def mock_partner_respond(user_input: str, emotional_state: str) -> str:
    add_span_attributes(
        emotional_state=emotional_state,
        input_type="response_attempt"
    )
    
    if emotional_state == "angry":
        return "I'm still upset! You're not really listening to me!"
    else:
        return "I appreciate you trying to understand. It's just hard."

def main():
    print("=== Phoenix Configuration Test ===")
    
    # Test 1: Basic function
    print("\n1. Testing basic function tracing...")
    result1 = basic_function("Hello Phoenix!")
    print(f"Result: {result1}")
    
    # Test 2: Coach function
    print("\n2. Testing coach response tracing...")
    result2 = mock_coach_respond("My partner is really angry at me")
    print(f"Coach advice: {result2}")
    
    # Test 3: Partner function
    print("\n3. Testing partner response tracing...")
    result3 = mock_partner_respond("I'm trying to understand", "angry")
    print(f"Partner response: {result3}")
    
    # Test 4: Different emotional state
    print("\n4. Testing partner response with different emotion...")
    result4 = mock_partner_respond("I hear you", "hurt")
    print(f"Partner response: {result4}")
    
    print("\n=== Configuration Test Complete ===")
    print("If Phoenix is running, check http://localhost:6006 for traces in the 'we-relate' project")

if __name__ == "__main__":
    main() 