# chat_app.py  ── run with:  chainlit run chat_app.py
from __future__ import annotations
import os
import openai
import chainlit as cl
from abc import ABC, abstractmethod
from enum import Enum, auto

from typing import Dict, List

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ────────────── low-level chat data ─────────────────────────────────────── #
class ChatChannel(Enum):
    BOTH = auto()
    COACH = auto()
    PARTNER = auto()


class ChatMessage:
    def __init__(self, role: str, content: str, channel: ChatChannel = ChatChannel.BOTH):
        self.role = role
        self.content = content
        self.channel = channel


class ChatHistory:
    def __init__(self):
        self._log: List[ChatMessage] = []

    def add(self, role: str, content: str,
            channel: ChatChannel = ChatChannel.BOTH) -> None:
        self._log.append(ChatMessage(role, content, channel))

    def full(self) -> List[Dict]:
        return [{"role": m.role, "content": m.content} for m in self._log]

    def partner_view(self) -> List[Dict]:
        return [{"role": m.role, "content": m.content}
                for m in self._log
                if m.channel in (ChatChannel.PARTNER, ChatChannel.BOTH)]


# ────────────── speakers (unchanged) ────────────────────────────────────── #
class Speaker(ABC):
    @abstractmethod
    def respond(self, history: ChatHistory) -> str: ...


class Coach(Speaker):
    MODEL = "gpt-4o-mini"
    SYS = "You are a supportive communication coach. You see the entire chat."

    def respond(self, history: ChatHistory) -> str:
        msg = [{"role": "system", "content": self.SYS}] + history.full()
        return client.chat.completions.create(model=self.MODEL,
                                            messages=msg).choices[0].message.content


class Partner(Speaker):
    MODEL = "gpt-3.5-turbo-0125"

    def __init__(self) -> None:
        self.profile: str | None = None
        self.scenario: str | None = None

    @property
    def sys(self) -> str:
        return (
            f"You are the user's conversation partner.\n"
            f"Profile (relationship + diagnosis): {self.profile or 'unspecified'}.\n"
            f"Scenario: {self.scenario or 'unspecified'}.\n"
            "You see only messages labelled BOTH or PARTNER."
        )

    def respond(self, history: ChatHistory) -> str:
        msg = [{"role": "system", "content": self.sys}] + history.partner_view()
        return client.chat.completions.create(model=self.MODEL,
                                            messages=msg).choices[0].message.content


class Router:
    MODEL = "gpt-3.5-turbo-0125"
    SYS = ("You are a router. Examine the latest user message and reply with "
           "COACH or PARTNER (one word).")

    def route(self, history: ChatHistory) -> ChatChannel:
        msg = [{"role": "system", "content": self.SYS}] + history.full()
        dec = client.chat.completions.create(model=self.MODEL,
                                           messages=msg,
                                           temperature=0).choices[0].message.content.lower()
        return ChatChannel.COACH if "coach" in dec else ChatChannel.PARTNER


# ────────────── stage machine (Strategy) ────────────────────────────────── #
class Stage(Enum):
    PROFILE = auto()
    SCENARIO = auto()
    CHAT = auto()


class StageHandler(ABC):
    @abstractmethod
    async def prompt(self) -> None: ...
    @abstractmethod
    async def handle(self, text: str, conv: "Conversation") -> Stage: ...


class ProfileStage(StageHandler):
    async def prompt(self) -> None:
        await cl.Message(
            "Describe **relationship** to the person *and* any diagnosed mental "
            "condition they have (one sentence).").send()

    async def handle(self, text: str, conv: "Conversation") -> Stage:
        conv.partner.profile = text.strip()
        return Stage.SCENARIO


class ScenarioStage(StageHandler):
    async def prompt(self) -> None:
        await cl.Message(
            "Briefly set the **triggering scenario** (e.g., *I came home late "
            "and she is yelling at me.*)").send()

    async def handle(self, text: str, conv: "Conversation") -> Stage:
        conv.partner.scenario = text.strip()
        await cl.Message(
            "Great—start talking as you would in the real situation. The coach "
            "and partner will reply.").send()
        return Stage.CHAT


class ChatStage(StageHandler):
    async def prompt(self) -> None:  # never called; entry is via router
        ...

    async def handle(self, text: str, conv: "Conversation") -> Stage:
        reply, who = conv.dialogue(text)
        label = "Coach" if who is ChatChannel.COACH else "Partner"
        await cl.Message(f"**{label}:** {reply}").send()
        return Stage.CHAT  # remain here


STAGE_STRATEGY: Dict[Stage, StageHandler] = {
    Stage.PROFILE: ProfileStage(),
    Stage.SCENARIO: ScenarioStage(),
    Stage.CHAT: ChatStage(),
}


# ────────────── conversation orchestrator ───────────────────────────────── #
class Conversation:
    def __init__(self) -> None:
        self.history = ChatHistory()
        self.router = Router()
        self.partner = Partner()
        self.speakers: Dict[ChatChannel, Speaker] = {
            ChatChannel.COACH: Coach(),
            ChatChannel.PARTNER: self.partner,
        }

    def dialogue(self, user_text: str) -> tuple[str, ChatChannel]:
        self.history.add("user", user_text, ChatChannel.BOTH)
        who = self.router.route(self.history)
        reply = self.speakers[who].respond(self.history)
        self.history.add("assistant", reply, who)
        return reply, who


# ────────────── Chainlit integration ────────────────────────────────────── #
@cl.on_chat_start
async def start() -> None:
    conv = Conversation()
    cl.user_session.set("conv", conv)
    cl.user_session.set("stage", Stage.PROFILE)
    await STAGE_STRATEGY[Stage.PROFILE].prompt()


@cl.on_message
async def on_message(msg: cl.Message) -> None:
    conv: Conversation = cl.user_session.get("conv")  # type: ignore
    stage: Stage = cl.user_session.get("stage")       # type: ignore

    next_stage = await STAGE_STRATEGY[stage].handle(msg.content, conv)
    if next_stage != stage and next_stage != Stage.CHAT:
        await STAGE_STRATEGY[next_stage].prompt()

    cl.user_session.set("stage", next_stage)