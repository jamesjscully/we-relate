# core.py - Main integration point for We-Relate Chainlit app
import chainlit as cl
from ui_controller import ChainlitUIController

# Create global UI controller instance
ui_controller = ChainlitUIController()


@cl.on_chat_start
async def on_chat_start():
    """Initialize new chat session"""
    await ui_controller.initialize_session()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages"""
    await ui_controller.handle_user_message(message) 