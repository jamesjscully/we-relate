#!/usr/bin/env python3
"""
Demonstration script showing the enhanced error handling system in action.
This simulates various error conditions to demonstrate logging and explicit failure behavior.
"""

import asyncio
import os
import logging
from unittest.mock import patch

# Configure logging to see our error handling in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from conversation import Conversation, Partner, Coach, ChatHistory, ChatChannel

async def demo_profile_explicit_failure():
    """Demonstrate profile setting with API failure - now raises explicit error"""
    print("\n🔧 Demonstrating Profile Setting with API Failure (Explicit Error)")
    print("=" * 60)
    
    partner = Partner()
    
    # Simulate API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("OpenAI API rate limit exceeded")):
        print("Setting profile: 'my supportive wife Maria who is a teacher'")
        print("💥 Simulating OpenAI API failure...")
        
        try:
            result = await partner.set_profile_from_user_perspective("my supportive wife Maria who is a teacher")
            print("❌ ERROR: Should have raised RuntimeError!")
        except RuntimeError as e:
            print(f"✅ Explicit failure with user message: '{e}'")
            print("📝 Check the logs above - you should see error logging!")

async def demo_scenario_explicit_failure():
    """Demonstrate scenario setting with API failure - now raises explicit error"""
    print("\n🔧 Demonstrating Scenario Setting with API Failure (Explicit Error)")
    print("=" * 60)
    
    partner = Partner()
    
    # Simulate API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("Network timeout")):
        print("Setting scenario: 'I forgot to pick up the kids from school'")
        print("💥 Simulating network timeout...")
        
        try:
            result = await partner.set_scenario_from_user_perspective("I forgot to pick up the kids from school")
            print("❌ ERROR: Should have raised RuntimeError!")
        except RuntimeError as e:
            print(f"✅ Explicit failure with user message: '{e}'")
            print("📝 Check the logs above - you should see error logging!")

async def demo_emotional_state_explicit_failure():
    """Demonstrate emotional state with API failure - now raises explicit error"""
    print("\n🔧 Demonstrating Emotional State with API Failure (Explicit Error)")
    print("=" * 60)
    
    partner = Partner()
    partner.profile = "you are my frustrated husband"
    partner.scenario = "your partner came home late again"
    
    history = ChatHistory()
    history.add("user", "I'm sorry I'm late, traffic was terrible", ChatChannel.PARTNER)
    
    # Simulate API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("Service unavailable")):
        print("Partner reacting to: 'I'm sorry I'm late, traffic was terrible'")
        print("💥 Simulating service unavailable...")
        
        try:
            result = await partner.react(history)
            print("❌ ERROR: Should have raised RuntimeError!")
        except RuntimeError as e:
            print(f"✅ Explicit failure with user message: '{e}'")
            print("📝 Check the logs above - you should see error logging!")

async def demo_critical_failure():
    """Demonstrate critical failure (Partner.respond) - same behavior as before"""
    print("\n🔧 Demonstrating Critical Failure - Partner.respond")
    print("=" * 60)
    
    partner = Partner()
    partner.profile = "you are my upset partner"
    partner.scenario = "you are feeling ignored lately"
    
    history = ChatHistory()
    history.add("user", "Hi honey, how was your day?", ChatChannel.PARTNER)
    
    # Simulate API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("API key invalid")):
        print("Partner responding to: 'Hi honey, how was your day?'")
        print("💥 Simulating API key invalid...")
        
        try:
            result = await partner.respond(history)
            print("❌ ERROR: Should have raised RuntimeError!")
        except RuntimeError as e:
            print(f"✅ Critical failure with user message: '{e}'")
            print("📝 This is expected - critical functions must notify users!")

async def demo_complete_conversation_flow():
    """Demonstrate complete conversation flow with errors"""
    print("\n🔧 Demonstrating Complete Conversation Flow with Errors")
    print("=" * 60)
    
    conv = Conversation()
    
    # Try to set up conversation with API failures
    print("1. Setting up profile and scenario...")
    
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("Service outage")):
        try:
            await conv.set_profile("my caring wife who is a doctor")
            print("❌ Profile setting should have failed!")
        except RuntimeError as e:
            print(f"✅ Profile setup failed with: '{e}'")
        
        try:
            await conv.set_scenario("I lost my job today")
            print("❌ Scenario setting should have failed!")
        except RuntimeError as e:
            print(f"✅ Scenario setup failed with: '{e}'")
        
        try:
            reply, channel = await conv.process_user_message("I have something to tell you...")
            print("❌ Message processing should have failed!")
        except RuntimeError as e:
            print(f"✅ Message processing failed with: '{e}'")

async def main():
    """Run all demonstrations"""
    print("🚀 Enhanced Error Handling System - Live Demonstration (No Graceful Fallbacks)")
    print("=" * 80)
    print("This demo simulates various API failures to show our explicit error handling.")
    print("Watch the logs to see server-side error reporting!")
    print("=" * 80)
    
    await demo_profile_explicit_failure()
    await demo_scenario_explicit_failure()
    await demo_emotional_state_explicit_failure()
    await demo_critical_failure()
    await demo_complete_conversation_flow()
    
    print("\n" + "=" * 80)
    print("🎉 Demonstration Complete!")
    print("\n✨ What You Just Saw:")
    print("  • ALL LLM completion failures now raise explicit RuntimeError")
    print("  • Users are always informed when AI services fail") 
    print("  • All failures are logged to server for debugging")
    print("  • No silent degradation or fallback behavior")
    print("  • Clear, consistent error messages for all AI failures")
    print("\n📊 Production Benefits:")
    print("  • Developers can debug issues using detailed server logs")
    print("  • Users always know when AI services are unavailable")
    print("  • No hidden degradation that could mask critical issues")
    print("  • Explicit error handling ensures reliable system behavior")

if __name__ == "__main__":
    # Set required environment variable for testing
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-key-for-error-testing"
    
    asyncio.run(main()) 