# conversation.py - Core conversation logic for We-Relate
from __future__ import annotations
import os
import openai
from typing import Dict, List, Protocol
from enum import Enum, auto

# Initialize OpenAI async client
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


class Coach(Speaker):
    MODEL = "gpt-4o"
    
    def __init__(self):
        self.partner_profile: str | None = None
        self.partner_scenario: str | None = None
    
    @property
    def system_prompt(self) -> str:
        return (
            f"""You are a communication coach. You are coaching the user on how to use intentional dialogue techniques to identify and validate the emotional concerns of the user's conversation partner. The partner is currently feeling very emotional, and is not able to engage in productive dialogue. Our goal is to understand and mirror their emotional experience without judgement. As the Partner calms down, you should guide the user towards a more productive dialogue.

            These are the principles of intentional dialogue:
            Presence: Participants commit to being fully attentive—mentally and emotionally—throughout the exchange.
            Safety and Respect: A shared commitment to nonjudgmental listening, avoiding blame or interruption, and honoring each person's experience.
            Speaking from the "I": Communicating personal experience rather than generalizations or accusations (e.g., "I felt..." rather than "You always...").
            Active Listening: Responding with reflection, validation, and empathy to demonstrate accurate understanding before offering one's own view.
            Curiosity over Judgment: Prioritizing exploration of the other's perspective over defending one's own.
            Intentional Turn-Taking: Structured exchanges where speakers and listeners alternate roles, often with guided prompts, to prevent domination or escalation.
            
            The conversation partner cannot read what you have to say. Only the user can see your messages. 
            Do not praise the user or tell them they did a good job."""
        )

    async def respond(self, history: ChatHistory) -> str:
        sys_prompt = self.system_prompt
        msg = [{"role": "system", "content": sys_prompt}] + history.full()
        
        response = await client.chat.completions.create(model=self.MODEL, messages=msg)
        response_content = response.choices[0].message.content
        
        return response_content


class Partner(Speaker):
    MODEL = "gpt-4o"
    
    def __init__(self) -> None:
        self.profile: str | None = None
        self.scenario: str | None = None
        self.emotional_state: str | None = None

    @property
    def system_prompt(self) -> str:
        return (
            f""""You are roleplaying in a scenario with the user. Your job is react to the user's messages in a psychologically realistic way.
            You are the following person:
            Your relationship/profile: {self.profile or 'unspecified'}.
            Current scenario: {self.scenario or 'unspecified'}. 
            Current emotional state: {self.emotional_state}
            Stay in character and respond.
            """
        )

    async def set_profile_from_user_perspective(self, user_profile: str) -> str:
        """
        Convert user's perspective of the relationship to partner's perspective.
        Returns the partner's perspective for use by other components (like coach).
        """
        user_profile = user_profile.strip()
        
        # Generate partner's perspective
        prompt = [
            {"role": "system", "content": (
                "Convert this relationship description from the user's perspective to the partner's perspective. "
                "Change 'my wife/husband/partner' to 'you are' and make it first-person for the partner. "
                "Keep all other details intact.\n\n"
                f"User's perspective: '{user_profile}'\n\n"
                "Respond with ONLY the converted text."
            )},
            {"role": "user", "content": user_profile}
        ]
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=prompt,
                temperature=0.3,
                max_tokens=100
            )
            self.profile = response.choices[0].message.content.strip()
        except Exception:
            # Fallback to simple conversion
            self.profile = user_profile.replace("my ", "you are ").replace("My ", "You are ")
        
        return user_profile  # Return the original user perspective

    async def set_scenario_from_user_perspective(self, user_scenario: str) -> str:
        """
        Convert user's perspective of the scenario to partner's perspective.
        Returns the user's perspective for use by other components (like coach).
        """
        user_scenario = user_scenario.strip()
        
        # Generate partner's perspective
        prompt = [
            {"role": "system", "content": (
                "Convert this scenario description from the user's perspective to the partner's perspective. "
                "Change 'I' to 'your partner' and make it describe what's happening to/around the partner. "
                "Keep the emotional context intact.\n\n"
                f"User's perspective: '{user_scenario}'\n\n"
                "Respond with ONLY the converted text."
            )},
            {"role": "user", "content": user_scenario}
        ]
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=prompt,
                temperature=0.3,
                max_tokens=100
            )
            self.scenario = response.choices[0].message.content.strip()
        except Exception:
            # Fallback to simple conversion
            self.scenario = user_scenario.replace("I ", "your partner ").replace(" me ", " them ")
        
        return user_scenario  # Return the original user perspective

    async def react(self, history: ChatHistory) -> str:
        """Generate an emotional reaction to the latest user message and update emotional state"""
        # Get the latest user message from partner view
        partner_messages = history.partner_view()
        if not partner_messages:
            # Initialize emotional state if not set
            if self.emotional_state is None:
                self.emotional_state = "neutral, but ready to react emotionally to the situation"
            return self.emotional_state
            
        latest_user_message = partner_messages[-1]['content'] if partner_messages else ""
        
        # Initialize current emotional state if None
        current_state = self.emotional_state or "neutral, but ready to react emotionally to the situation"
        
        # Generate emotional reaction
        reaction_prompt = [
            {"role": "system", "content": (
                f"You are analyzing the emotional impact of a message in this context:\n"
                f"Relationship: {self.profile or 'unspecified'}\n"
                f"Scenario: {self.scenario or 'unspecified'}\n"
                f"Current emotional state: {current_state}\n\n"
                f"Latest message: '{latest_user_message}'\n\n"
                f"Respond with ONLY a brief emotional state description (e.g., 'frustrated and defensive', 'hurt but trying to stay calm', 'angry and feeling unheard'). "
                f"Consider how this message would affect someone in this situation emotionally."
            )},
            {"role": "user", "content": latest_user_message}
        ]
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=reaction_prompt,
                temperature=0.7,
                max_tokens=50
            )
            new_emotional_state = response.choices[0].message.content.strip()
            
            self.emotional_state = new_emotional_state
            return new_emotional_state
        except Exception as e:
            # Fallback if API call fails
            if self.emotional_state is None:
                self.emotional_state = "neutral, but ready to react emotionally to the situation"
            return self.emotional_state

    async def respond(self, history: ChatHistory) -> str:
        msg = [{"role": "system", "content": self.system_prompt}] + history.partner_view()
        
        response = await client.chat.completions.create(model=self.MODEL, messages=msg)
        response_content = response.choices[0].message.content
        
        return response_content


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