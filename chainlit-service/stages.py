# stages.py - Business logic for stage transitions and validation
from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Protocol
from dataclasses import dataclass

from conversation import Conversation


class Stage(Enum):
    WELCOME = auto()
    PROFILE = auto()
    SCENARIO = auto()
    CONVERSATION = auto()


@dataclass
class StageResult:
    """Result of processing a stage action"""
    next_stage: Optional[Stage] = None
    prompt_message: Optional[str] = None
    response_message: Optional[str] = None
    show_conversation_info: bool = False
    error: Optional[str] = None


class StageHandler(Protocol):
    """Protocol for stage handlers"""
    def get_prompt(self) -> str:
        """Get the prompt message for this stage"""
        ...
    
    async def handle(self, user_input: str, conversation: Conversation) -> StageResult:
        """Handle user input and return stage result"""
        ...


class WelcomeStage(StageHandler):
    def get_prompt(self) -> str:
        return "Welcome to We-Relate. This is an app that lets you roleplay conversations with AI to practice intentional dialogue."

    async def handle(self, user_input: str, conversation: Conversation) -> StageResult:
        # Welcome stage immediately transitions to profile
        return StageResult(
            next_stage=Stage.PROFILE,
            prompt_message="Describe the **relationship** to the person you want to practice with (e.g., 'my spouse Sarah', 'my teenage daughter Alex', 'my co-worker Jim'):"
        )


class ProfileStage(StageHandler):
    def get_prompt(self) -> str:
        return "Describe the **relationship** to the person you want to practice with (e.g., 'my spouse Sarah', 'my teenage daughter Alex', 'my co-worker Jim'):"

    async def handle(self, user_input: str, conversation: Conversation) -> StageResult:
        if not user_input.strip():
            return StageResult(error="Please describe your relationship.")
        
        # Set the profile in the conversation
        await conversation.set_profile(user_input.strip())
        
        return StageResult(
            next_stage=Stage.SCENARIO,
            prompt_message="Describe the **scenario** or situation you want to practice (e.g., 'I forgot to pick up groceries and she's frustrated'):"
        )


class ScenarioStage(StageHandler):
    def get_prompt(self) -> str:
        return "Describe the **scenario** or situation you want to practice (e.g., 'I forgot to pick up groceries and she's frustrated'):"

    async def handle(self, user_input: str, conversation: Conversation) -> StageResult:
        if not user_input.strip():
            return StageResult(error="Please describe the scenario.")
        
        # Set the scenario in the conversation
        await conversation.set_scenario(user_input.strip())
        
        # Generate partner's opening message
        partner_opening = await conversation.generate_partner_opening()
        
        return StageResult(
            next_stage=Stage.CONVERSATION,
            response_message=partner_opening,
            show_conversation_info=True
        )


class ConversationStage(StageHandler):
    def get_prompt(self) -> str:
        # No prompt for conversation stage - user can message freely
        return ""

    async def handle(self, user_input: str, conversation: Conversation) -> StageResult:
        if not user_input.strip():
            return StageResult(error="Please enter a message.")
        
        # Process the message through the conversation system
        response, channel = await conversation.process_user_message(user_input.strip())
        
        # Stay in conversation stage
        return StageResult(
            next_stage=Stage.CONVERSATION,
            response_message=response
        )


class StageManager:
    """Manages stage transitions and handlers"""
    
    def __init__(self):
        self._handlers = {
            Stage.WELCOME: WelcomeStage(),
            Stage.PROFILE: ProfileStage(),
            Stage.SCENARIO: ScenarioStage(),
            Stage.CONVERSATION: ConversationStage(),
        }
    
    def get_handler(self, stage: Stage) -> StageHandler:
        """Get the handler for a given stage"""
        return self._handlers[stage]
    
    def get_initial_stage(self) -> Stage:
        """Get the initial stage for new sessions"""
        return Stage.WELCOME 