# ui_controller.py - UI presentation layer for Chainlit
from __future__ import annotations
import chainlit as cl
import logging
from typing import Optional, Any

from conversation import Conversation, ChatChannel
from stages import Stage, StageManager, StageResult

logger = logging.getLogger(__name__)


class ChainlitUIController:
    """Handles all UI interactions and coordinates with business logic"""
    
    def __init__(self):
        self.stage_manager = StageManager()
    
    async def send_message(self, content: str, author: str = "System") -> None:
        """Send a message to the user via Chainlit"""
        await cl.Message(content=content, author=author).send()
    
    async def send_error_message(self, error_message: str) -> None:
        """Send an error message with specific styling"""
        await cl.Message(
            content=f"⚠️ **Error**: {error_message}",
            author="⚠️ System Error"
        ).send()
    
    async def send_conversation_info(self, conversation: Conversation) -> None:
        """Send conversation context information"""
        info_parts = []
        
        if conversation.user_profile:
            info_parts.append(f"**Relationship**: {conversation.user_profile}")
        
        if conversation.user_scenario:
            info_parts.append(f"**Scenario**: {conversation.user_scenario}")
        
        if conversation.partner.emotional_state:
            info_parts.append(f"**{conversation.user_profile or 'Partner'}'s emotional state**: {conversation.partner.emotional_state}")
        
        info_parts.append("You can:\n- Reply normally to talk to your partner\n- Type `@coach <message>` to get coaching advice")
        
        if info_parts:
            await self.send_message("\n\n".join(info_parts))
    
    async def handle_stage_result(self, result: StageResult, conversation: Conversation) -> Stage:
        """Handle the result of stage processing and send appropriate messages"""
        # Handle errors
        if result.error:
            await self.send_error_message(result.error)
            return cl.user_session.get("current_stage", Stage.WELCOME)
        
        # Send prompt message if provided
        if result.prompt_message:
            await self.send_message(result.prompt_message)
        
        # Send response message if provided
        if result.response_message:
            # Determine author based on current stage
            author = "Partner" if cl.user_session.get("current_stage") in [Stage.SCENARIO, Stage.CONVERSATION] else "System"
            await self.send_message(result.response_message, author)
        
        # Show conversation info if requested
        if result.show_conversation_info:
            await self.send_conversation_info(conversation)
        
        # Update and return the new stage
        if result.next_stage:
            cl.user_session.set("current_stage", result.next_stage)
            return result.next_stage
        
        return cl.user_session.get("current_stage", Stage.WELCOME)
    
    async def initialize_session(self) -> None:
        """Initialize a new user session"""
        try:
            # Create conversation instance
            conversation = Conversation()
            cl.user_session.set("conversation", conversation)
            
            # Set initial stage
            initial_stage = self.stage_manager.get_initial_stage()
            cl.user_session.set("current_stage", initial_stage)
            
            # Send welcome message
            handler = self.stage_manager.get_handler(initial_stage)
            welcome_result = await handler.handle("", conversation)
            await self.handle_stage_result(welcome_result, conversation)
        except Exception as e:
            logger.error(f"Error initializing session: {type(e).__name__}: {str(e)}")
            await self.send_error_message("Failed to initialize the application. Please refresh the page and try again.")
    
    async def handle_user_message(self, message: cl.Message) -> None:
        """Handle incoming user message"""
        try:
            # Get session data
            conversation: Conversation = cl.user_session.get("conversation")
            current_stage: Stage = cl.user_session.get("current_stage", Stage.WELCOME)
            
            if not conversation:
                await self.send_error_message("Session not initialized properly. Please refresh the page.")
                return
            
            # Get appropriate handler and process message
            handler = self.stage_manager.get_handler(current_stage)
            result = await handler.handle(message.content, conversation)
            
            # Handle the result and update UI
            new_stage = await self.handle_stage_result(result, conversation)
            
            # Update session with new stage
            cl.user_session.set("current_stage", new_stage)
            
        except RuntimeError as e:
            # These are user-facing errors from AI service failures
            logger.info(f"User-facing error: {str(e)}")
            await self.send_error_message(str(e))
            
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error handling user message: {type(e).__name__}: {str(e)}")
            await self.send_error_message(
                "Something unexpected happened. Please try your message again. "
                "If the problem continues, please refresh the page or contact support."
            ) 