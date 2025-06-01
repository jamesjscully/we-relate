# speakers/coach.py - Communication coach AI
from __future__ import annotations
import os
import openai
import logging
from typing import Dict, List, Protocol, Optional

# Import shared dependencies
logger = logging.getLogger(__name__)
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# We'll need to import these from conversation after we refactor
# For now, we'll define the minimal needed types here and import from conversation later


class Coach:
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

    async def respond(self, history) -> str:
        # Import here to avoid circular imports
        from conversation import AIServiceError
        
        sys_prompt = self.system_prompt
        msg = [{"role": "system", "content": sys_prompt}] + history.full()
        
        try:
            response = await client.chat.completions.create(model=self.MODEL, messages=msg)
            response_content = response.choices[0].message.content
            return response_content
        except Exception as e:
            # This is a critical failure - coach must be able to respond
            AIServiceError.log_and_raise_user_error("Coach.respond", e) 