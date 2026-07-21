from pydantic import BaseModel, Field


class Event(BaseModel):
    title: str
    when: str | None = Field(default=None, description="Date/time as found on the site")
    venue: str | None = None
    url: str | None = None


class AgentResult(BaseModel):
    """What the LangChain agent (Part 3) returns to the orchestrator."""

    answer: str = Field(description="Natural-language reply to read back to the user")
    events: list[Event] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list, description="URLs the agent visited")


class ChatResponse(BaseModel):
    """Full response of the /api/chat pipeline (Part 4)."""

    transcript: str = Field(description="What ASR heard from the user")
    answer: str
    events: list[Event] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    audio_base64: str | None = Field(
        default=None, description="TTS audio (mp3) as base64; null if TTS not wired yet"
    )
