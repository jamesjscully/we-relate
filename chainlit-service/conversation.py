# conversation.py - Core conversation logic for We-Relate
from __future__ import annotations
import os
import openai
import logging
from typing import Dict, List, Protocol, Optional
from enum import Enum, auto

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI async client
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ────────────── error handling ─────────────────────────────────────── #
class AIServiceError:
    """Handles AI service errors and user notifications"""
    
    @staticmethod
    def log_and_raise_user_error(operation: str, error: Exception) -> None:
        """Log error and raise user-friendly exception"""
        logger.error(f"Critical AI service error in {operation}: {type(error).__name__}: {str(error)}")
        raise RuntimeError(f"We're experiencing technical difficulties with our AI service. Please try again in a moment. If the problem persists, contact support.")

# ────────────── low-level chat data ─────────────────────────────────────── #
class ChatChannel(Enum):
    COACH = auto()
    PARTNER = auto()


class ChatMessage:
    def __init__(self, role: str, content: str, channel: ChatChannel = ChatChannel.PARTNER):
        self.role = role
        self.content = content
        self.channel = channel


class ChatHistory:
    def __init__(self):
        self._log: List[ChatMessage] = []

    def add(self, role: str, content: str,
            channel: ChatChannel = ChatChannel.PARTNER) -> None:
        self._log.append(ChatMessage(role, content, channel))

    def full(self) -> List[Dict]:
        return [{"role": m.role, "content": m.content} for m in self._log]

    def partner_view(self) -> List[Dict]:
        return [{"role": m.role, "content": m.content}
                for m in self._log
                if m.channel == ChatChannel.PARTNER]


# ────────────── speakers ────────────────────────────────────── #
class Speaker(Protocol):
    async def respond(self, history: ChatHistory) -> str: ...


# Import speaker classes from separate modules
from speakers.coach import Coach
from speakers.partner import Partner


class Router:
    """Deterministic router - checks for @coach prefix to route to coach, otherwise routes to partner"""
    def route(self, user_message: str) -> ChatChannel:
        """Route based on @coach prefix - deterministic, no AI needed"""
        if user_message.strip().lower().startswith("@coach"):
            return ChatChannel.COACH
        return ChatChannel.PARTNER


# ────────────── conversation orchestrator ───────────────────────────────── #
class Conversation:
    def __init__(self) -> None:
        self.history = ChatHistory()
        self.router = Router()
        self.partner = Partner()
        self.coach = Coach()
        self.speakers: Dict[ChatChannel, Speaker] = {
            ChatChannel.COACH: self.coach,
            ChatChannel.PARTNER: self.partner,
        }
        # Store context from user's perspective (for coach)
        self.user_profile: str | None = None
        self.user_scenario: str | None = None
        # Store context from partner's perspective (for partner roleplay)
        self.partner_profile: str | None = None
        self.partner_scenario: str | None = None

    async def set_profile(self, user_profile: str) -> None:
        """Set profile by delegating to partner and updating coach"""
        # Let partner handle the conversion and set its own profile
        self.user_profile = await self.partner.set_profile_from_user_perspective(user_profile)
        
        # Store the partner's converted profile for reference
        self.partner_profile = self.partner.profile
        
        # Update coach with the user's perspective
        self.coach.partner_profile = self.user_profile

    async def set_scenario(self, user_scenario: str) -> None:
        """Set scenario by delegating to partner and updating coach"""
        # Let partner handle the conversion and set its own scenario
        self.user_scenario = await self.partner.set_scenario_from_user_perspective(user_scenario)
        
        # Store the partner's converted scenario for reference
        self.partner_scenario = self.partner.scenario
        
        # Update coach with the user's perspective
        self.coach.partner_scenario = self.user_scenario

    async def process_user_message(self, user_text: str) -> tuple[str, ChatChannel]:
        """Process user message and generate response (pure business logic)"""
        # Determine who the user is talking to
        who = self.router.route(user_text)
        
        # Clean the message if it starts with @coach
        clean_text = user_text
        if user_text.strip().lower().startswith("@coach"):
            clean_text = user_text.strip()[6:].strip()  # Remove "@coach" prefix
            
        # Add user message to appropriate channel
        self.history.add("user", clean_text, who)
        
        # If responding as Partner, update emotional state first
        if who == ChatChannel.PARTNER:
            await self.partner.react(self.history)
        
        # Generate and add response
        reply = await self.speakers[who].respond(self.history)
        self.history.add("assistant", reply, who)
        
        return reply, who

    async def generate_partner_opening(self) -> str:
        """Generate the partner's opening message based on the scenario"""
        return await self.partner.respond(self.history) 