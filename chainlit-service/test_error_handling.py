#!/usr/bin/env python3
"""
Test script for enhanced error handling in the AI service calls.
Tests that errors are properly logged and users get appropriate notifications when LLM calls fail.
"""

import asyncio
import os
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock chainlit before importing our modules
sys.modules['chainlit'] = MagicMock()

from conversation import Conversation, AIServiceError
from speakers.partner import Partner
from speakers.coach import Coach
from ui_controller import ChainlitUIController


async def test_ai_service_error_logging():
    """Test that AIServiceError properly logs errors"""
    print("🧪 Testing AIServiceError logging...")
    
    # Capture log output
    import io
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger('conversation')
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    
    # Test log_and_raise_user_error
    test_error = Exception("Test API error")
    try:
        AIServiceError.log_and_raise_user_error("test_critical", test_error)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "technical difficulties" in str(e)
        log_output = log_capture.getvalue()
        assert "Critical AI service error in test_critical" in log_output
    print("✅ AIServiceError.log_and_raise_user_error works correctly")
    
    logger.removeHandler(handler)
    print("✅ AIServiceError logging tests passed!\n")


async def test_partner_error_handling():
    """Test Partner class error handling with mocked failures - all should now raise RuntimeError"""
    print("🧪 Testing Partner error handling...")
    
    partner = Partner()
    
    # Test set_profile_from_user_perspective with API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("API down")):
        try:
            await partner.set_profile_from_user_perspective("my wife Sarah")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Partner.set_profile_from_user_perspective raises error on failure")
    
    # Test set_scenario_from_user_perspective with API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("API down")):
        try:
            await partner.set_scenario_from_user_perspective("I came home late")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Partner.set_scenario_from_user_perspective raises error on failure")
    
    # Test react with API failure
    from conversation import ChatHistory, ChatChannel
    history = ChatHistory()
    history.add("user", "Hello", ChatChannel.PARTNER)
    
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("API down")):
        try:
            await partner.react(history)
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Partner.react raises error on failure")
    
    print("✅ Partner error handling tests passed!\n")


async def test_critical_failures():
    """Test that critical failures (Coach.respond, Partner.respond) raise RuntimeError"""
    print("🧪 Testing critical AI failures...")
    
    # Test Coach.respond failure
    coach = Coach()
    from conversation import ChatHistory
    history = ChatHistory()
    
    with patch('speakers.coach.client.chat.completions.create', side_effect=Exception("API down")):
        try:
            await coach.respond(history)
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Coach.respond raises user-friendly error on failure")
    
    # Test Partner.respond failure
    partner = Partner()
    
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("API down")):
        try:
            await partner.respond(history)
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Partner.respond raises user-friendly error on failure")
    
    print("✅ Critical failure tests passed!\n")


async def test_ui_controller_error_handling():
    """Test that UI controller handles RuntimeError properly"""
    print("🧪 Testing UI Controller error handling...")
    
    # Mock chainlit
    import chainlit as cl
    cl.Message = AsyncMock()
    cl.user_session = MagicMock()
    cl.user_session.get.return_value = MagicMock()
    
    ui_controller = ChainlitUIController()
    ui_controller.send_error_message = AsyncMock()
    
    # Create a mock message that will cause a RuntimeError
    mock_message = MagicMock()
    mock_message.content = "test message"
    
    # Mock conversation to raise RuntimeError
    mock_conversation = MagicMock()
    mock_conversation.process_user_message = AsyncMock(side_effect=RuntimeError("AI service down"))
    cl.user_session.get.side_effect = lambda key, default=None: {
        "conversation": mock_conversation,
        "current_stage": MagicMock()
    }.get(key, default)
    
    # This should catch the RuntimeError and send error message
    with patch.object(ui_controller.stage_manager, 'get_handler') as mock_handler:
        mock_handler.return_value.handle = AsyncMock(side_effect=RuntimeError("AI service down"))
        
        await ui_controller.handle_user_message(mock_message)
        
        # Should have called send_error_message with the RuntimeError message
        ui_controller.send_error_message.assert_called_once()
        call_args = ui_controller.send_error_message.call_args[0][0]
        assert "AI service down" in call_args
        print("✅ UI Controller handles RuntimeError correctly")
    
    print("✅ UI Controller error handling tests passed!\n")


async def test_complete_error_flow():
    """Test complete error flow from API failure to user notification"""
    print("🧪 Testing complete error flow...")
    
    conv = Conversation()
    
    # Test that profile setting fails with API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("Rate limited")):
        try:
            await conv.set_profile("my husband John")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Complete profile flow with error raises RuntimeError")
    
    # Test that scenario setting fails with API failure
    with patch('speakers.partner.client.chat.completions.create', side_effect=Exception("Rate limited")):
        try:
            await conv.set_scenario("I forgot our anniversary")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "technical difficulties" in str(e)
            print("✅ Complete scenario flow with error raises RuntimeError")
    
    print("✅ Complete error flow tests passed!\n")


async def main():
    """Run all error handling tests"""
    print("🚀 Testing Enhanced Error Handling System (No Graceful Fallbacks)\n")
    print("=" * 60)
    
    try:
        await test_ai_service_error_logging()
        await test_partner_error_handling()
        await test_critical_failures()
        await test_ui_controller_error_handling()
        await test_complete_error_flow()
        
        print("=" * 60)
        print("🎉 ALL ERROR HANDLING TESTS PASSED!")
        print("\n✨ Error Handling Features:")
        print("  • Server-side error logging for debugging")
        print("  • User-friendly error messages")
        print("  • Explicit failures for ALL LLM completions")
        print("  • Clear notifications for all AI service failures")
        print("  • Proper error propagation through UI layer")
        print("  • No silent degradation or hidden fallbacks")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set required environment variable for testing
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-key-for-error-testing"
    
    asyncio.run(main()) 