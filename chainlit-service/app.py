# app.py  ── regular chainlit app, run with:  chainlit run app.py
import chainlit as cl
import asyncio
from core import WeRelateApp

# Create the app instance
app = WeRelateApp()

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    await app.start()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    await app.handle_message(message.content)