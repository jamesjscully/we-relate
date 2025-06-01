# speakers/partner.py - Roleplay partner AI
from __future__ import annotations
import os
import openai
import logging
from typing import Dict, List, Protocol, Optional

# Import shared dependencies
logger = logging.getLogger(__name__)
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Partner:
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
        # Import here to avoid circular imports
        from conversation import AIServiceError
        
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
        except Exception as e:
            # This is a critical failure - profile setting must work
            AIServiceError.log_and_raise_user_error("Partner.set_profile_from_user_perspective", e)
        
        return user_profile  # Return the original user perspective

    async def set_scenario_from_user_perspective(self, user_scenario: str) -> str:
        """
        Convert user's perspective of the scenario to partner's perspective.
        Returns the user's perspective for use by other components (like coach).
        """
        # Import here to avoid circular imports
        from conversation import AIServiceError
        
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
        except Exception as e:
            # This is a critical failure - scenario setting must work
            AIServiceError.log_and_raise_user_error("Partner.set_scenario_from_user_perspective", e)
        
        return user_scenario  # Return the original user perspective

    async def react(self, history) -> str:
        """Generate an emotional reaction to the latest user message and update emotional state"""
        # Import here to avoid circular imports
        from conversation import AIServiceError
        
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
            # This is a critical failure - emotional reaction must work
            AIServiceError.log_and_raise_user_error("Partner.react", e)

    async def respond(self, history) -> str:
        # Import here to avoid circular imports
        from conversation import AIServiceError
        
        msg = [{"role": "system", "content": self.system_prompt}] + history.partner_view()
        
        try:
            response = await client.chat.completions.create(model=self.MODEL, messages=msg)
            response_content = response.choices[0].message.content
            return response_content
        except Exception as e:
            # This is a critical failure - partner must be able to respond
            AIServiceError.log_and_raise_user_error("Partner.respond", e) 