import os
import asyncio
import json
import requests
from typing import Dict, Any, Optional
import chainlit as cl
from chainlit.config import config as cl_config
import openai
from agents.teacher import TeacherAgent
from agents.student import StudentAgent
from config import config

# Configure Chainlit
cl_config.project.enable_telemetry = False

# Validate configuration
try:
    config.validate()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    exit(1)

# Initialize OpenAI
openai.api_key = config.OPENAI_API_KEY

# Global variables for agents
teacher_agent = None
student_agent = None

class UserContext:
    """Manages user context and session data"""
    def __init__(self):
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.tier: Optional[str] = None
        self.credits: Optional[int] = None
        self.current_agent: Optional[str] = None
        
    def update_from_dict(self, data: Dict[str, Any]):
        """Update context from dictionary"""
        self.user_id = data.get('user_id')
        self.username = data.get('username')
        self.tier = data.get('tier')
        self.credits = data.get('credits')

@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    global teacher_agent, student_agent
    
    # Initialize agents
    teacher_agent = TeacherAgent()
    student_agent = StudentAgent()
    
    # Initialize user context
    user_context = UserContext()
    cl.user_session.set("user_context", user_context)
    cl.user_session.set("conversation_history", [])
    
    # Send welcome message
    await cl.Message(
        content="🤖 **Welcome to AI Chat Platform!**\n\nI'm here to help you with various tasks. You can:\n\n"
                "• Ask questions and get intelligent responses\n"
                "• Switch between different AI agents\n"
                "• Have natural conversations\n\n"
                "**Available Agents:**\n"
                "- 👨‍🏫 **Teacher**: Educational support and explanations\n"
                "- 👨‍🎓 **Student**: Learning companion and study help\n\n"
                "Type your message to get started, or use `/agent <name>` to switch agents!",
        author="System"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    user_context = cl.user_session.get("user_context")
    conversation_history = cl.user_session.get("conversation_history", [])
    
    # Check for agent switching commands
    if message.content.startswith("/agent"):
        await handle_agent_switch(message.content)
        return
    
    # Check for other commands
    if message.content.startswith("/"):
        await handle_command(message.content)
        return
    
    # Check user credits (if context is available)
    if user_context and user_context.credits is not None and user_context.credits <= 0:
        await cl.Message(
            content="❌ **Insufficient Credits**\n\nYou've run out of credits. Please upgrade your plan to continue chatting.",
            author="System"
        ).send()
        return
    
    # Process the message with current agent
    current_agent = cl.user_session.get("current_agent", "general")
    
    try:
        # Show typing indicator
        async with cl.Step(name="thinking", type="tool") as step:
            step.output = "Processing your message..."
            
            # Get response from appropriate agent
            if current_agent == "teacher":
                response = await teacher_agent.process_message(
                    message.content, 
                    conversation_history,
                    user_context
                )
            elif current_agent == "student":
                response = await student_agent.process_message(
                    message.content, 
                    conversation_history,
                    user_context
                )
            else:
                response = await process_general_message(
                    message.content, 
                    conversation_history,
                    user_context
                )
        
        # Send response
        await cl.Message(
            content=response,
            author=get_agent_display_name(current_agent)
        ).send()
        
        # Update conversation history
        from datetime import datetime
        conversation_history.append({
            "user": message.content,
            "assistant": response,
            "agent": current_agent,
            "timestamp": datetime.now().isoformat()
        })
        cl.user_session.set("conversation_history", conversation_history)
        
        # Deduct credits if user context is available
        if user_context and user_context.credits is not None:
            await deduct_credits(user_context)
            
    except Exception as e:
        await cl.Message(
            content=f"❌ **Error**: {str(e)}\n\nPlease try again or contact support if the issue persists.",
            author="System"
        ).send()

async def handle_agent_switch(command: str):
    """Handle agent switching commands"""
    parts = command.split()
    if len(parts) < 2:
        await cl.Message(
            content="**Available Agents:**\n\n"
                    "• `/agent teacher` - Educational support\n"
                    "• `/agent student` - Learning companion\n"
                    "• `/agent general` - General assistant\n\n"
                    "Example: `/agent teacher`",
            author="System"
        ).send()
        return
    
    agent_name = parts[1].lower()
    valid_agents = ["teacher", "student", "general"]
    
    if agent_name not in valid_agents:
        await cl.Message(
            content=f"❌ Unknown agent: `{agent_name}`\n\nValid agents: {', '.join(valid_agents)}",
            author="System"
        ).send()
        return
    
    cl.user_session.set("current_agent", agent_name)
    
    agent_messages = {
        "teacher": "👨‍🏫 **Teacher Agent Activated**\n\nI'm here to help you learn! I can explain concepts, provide educational content, and guide you through learning materials.",
        "student": "👨‍🎓 **Student Agent Activated**\n\nI'm your learning companion! I can help you study, practice problems, and understand difficult concepts from a student's perspective.",
        "general": "🤖 **General Assistant Activated**\n\nI'm ready to help with a wide variety of tasks and questions!"
    }
    
    await cl.Message(
        content=agent_messages[agent_name],
        author="System"
    ).send()

async def handle_command(command: str):
    """Handle various commands"""
    if command == "/help":
        await cl.Message(
            content="**Available Commands:**\n\n"
                    "• `/agent <name>` - Switch AI agent\n"
                    "• `/history` - View conversation history\n"
                    "• `/clear` - Clear conversation history\n"
                    "• `/credits` - Check remaining credits\n"
                    "• `/help` - Show this help message",
            author="System"
        ).send()
    elif command == "/history":
        await show_conversation_history()
    elif command == "/clear":
        cl.user_session.set("conversation_history", [])
        await cl.Message(
            content="✅ Conversation history cleared!",
            author="System"
        ).send()
    elif command == "/credits":
        await show_credits_info()
    else:
        await cl.Message(
            content=f"❌ Unknown command: `{command}`\n\nType `/help` for available commands.",
            author="System"
        ).send()

async def show_conversation_history():
    """Display conversation history"""
    history = cl.user_session.get("conversation_history", [])
    
    if not history:
        await cl.Message(
            content="📝 No conversation history yet. Start chatting to build your history!",
            author="System"
        ).send()
        return
    
    history_text = "📝 **Conversation History:**\n\n"
    for i, entry in enumerate(history[-5:], 1):  # Show last 5 conversations
        agent_name = get_agent_display_name(entry.get("agent", "general"))
        history_text += f"**{i}.** *You:* {entry['user'][:100]}{'...' if len(entry['user']) > 100 else ''}\n"
        history_text += f"*{agent_name}:* {entry['assistant'][:100]}{'...' if len(entry['assistant']) > 100 else ''}\n\n"
    
    await cl.Message(content=history_text, author="System").send()

async def show_credits_info():
    """Display credits information"""
    user_context = cl.user_session.get("user_context")
    
    if not user_context or user_context.credits is None:
        await cl.Message(
            content="💰 **Credits Information**\n\nCredits info not available. Please refresh the page or contact support.",
            author="System"
        ).send()
        return
    
    credits_text = f"💰 **Credits Information**\n\n"
    credits_text += f"**Remaining Credits:** {user_context.credits}\n"
    credits_text += f"**Account Tier:** {user_context.tier.title() if user_context.tier else 'Unknown'}\n\n"
    
    if user_context.credits < 10:
        credits_text += "⚠️ **Low Credits Warning**\nConsider upgrading your plan to continue chatting."
    
    await cl.Message(content=credits_text, author="System").send()

async def process_general_message(message: str, history: list, user_context: UserContext) -> str:
    """Process message with general AI assistant"""
    # Check if demo mode is enabled
    if config.DEMO_MODE:
        return get_demo_response(message)
    
    try:
        # Prepare conversation context
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise, and helpful responses."}
        ]
        
        # Add recent history for context
        for entry in history[-3:]:  # Last 3 conversations for context
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get response from OpenAI
        client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except openai.RateLimitError:
        return "🚫 **API Rate Limit Exceeded**\n\nThe OpenAI API is currently rate-limited. Please try again in a few moments."
    except openai.AuthenticationError:
        return "🔑 **API Authentication Error**\n\nThere's an issue with the OpenAI API key. Please contact support."
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "insufficient_quota" in error_msg:
            return "💳 **API Quota Exceeded**\n\nThe OpenAI API quota has been exceeded. Please contact support to resolve this issue."
        elif "429" in error_msg:
            return "⏳ **Too Many Requests**\n\nThe API is receiving too many requests. Please wait a moment and try again."
        else:
            return f"❌ **Error**: I encountered an issue processing your request. Please try again or contact support if the issue persists.\n\nError details: {str(e)}"

def get_demo_response(message: str) -> str:
    """Generate demo responses when OpenAI API is not available"""
    message_lower = message.lower()
    
    # Simple keyword-based responses for demo
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "🤖 **Demo Mode**: Hello! I'm running in demo mode since the OpenAI API is not available. I can still help you explore the platform features!"
    
    elif any(word in message_lower for word in ['help', 'what can you do', 'features']):
        return """🤖 **Demo Mode Features**:

• **Agent Switching**: Try `/agent teacher` or `/agent student`
• **Commands**: Use `/help` to see all available commands
• **Chat History**: Use `/history` to view conversation history
• **Credits**: Use `/credits` to check your account status

This is a demonstration of the chat interface. In production mode with a valid OpenAI API key, I would provide intelligent AI responses!"""
    
    elif any(word in message_lower for word in ['python', 'programming', 'code']):
        return """🤖 **Demo Response - Programming**:

I'd love to help you with programming! In full mode, I can:
- Explain programming concepts
- Help debug code
- Suggest best practices
- Provide code examples

*Note: This is a demo response. With OpenAI API access, I'd provide detailed, contextual programming assistance.*"""
    
    elif any(word in message_lower for word in ['math', 'mathematics', 'calculate']):
        return """🤖 **Demo Response - Mathematics**:

I can help with various math topics! In full mode, I would:
- Solve equations step by step
- Explain mathematical concepts
- Help with homework problems
- Provide practice exercises

*Note: This is a demo response. With OpenAI API access, I'd provide detailed mathematical assistance.*"""
    
    else:
        return f"""🤖 **Demo Response**:

You asked: "{message}"

In full mode with OpenAI API access, I would provide a thoughtful, contextual response to your question. Currently running in demo mode to showcase the platform's interface and features.

Try these commands:
- `/agent teacher` - Switch to educational assistant
- `/agent student` - Switch to study companion  
- `/help` - See all available commands"""

async def deduct_credits(user_context: UserContext):
    """Deduct credits from user account via Flask API"""
    if not user_context or not user_context.user_id:
        return
    
    try:
        # Call Flask API to deduct credits
        response = requests.post(
            f"{config.FLASK_SERVICE_URL}/api/user/update-credits",
            json={"credits_used": config.CREDIT_COST_PER_MESSAGE},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                user_context.credits = data.get('credits', 0)
                print(f"✅ Credits updated: {user_context.credits} remaining")
            else:
                print(f"❌ Failed to deduct credits: {data.get('error')}")
        else:
            print(f"❌ Credit deduction failed with status {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Error calling Flask API: {e}")
        # Fallback: just decrement locally
        if user_context.credits is not None and user_context.credits > 0:
            user_context.credits -= config.CREDIT_COST_PER_MESSAGE

def get_agent_display_name(agent: str) -> str:
    """Get display name for agent"""
    agent_names = {
        "teacher": "👨‍🏫 Teacher",
        "student": "👨‍🎓 Student",
        "general": "🤖 Assistant"
    }
    return agent_names.get(agent, "🤖 Assistant")

@cl.on_stop
async def on_stop():
    """Handle session stop"""
    print("Chat session ended")

# Handle messages from parent window (Flask app)
@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates from parent window"""
    user_context = cl.user_session.get("user_context")
    if user_context and "user_context" in settings:
        user_context.update_from_dict(settings["user_context"])
        cl.user_session.set("user_context", user_context)

if __name__ == "__main__":
    cl.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 