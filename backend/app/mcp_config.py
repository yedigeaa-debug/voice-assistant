"""
Part 3 — MCP Playwright configuration + target sites.

Central place for: which sites the agent is allowed to surf, and how to
launch the Playwright MCP server (a Node process spoken to over stdio).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


# The Афиша (event listing) sites the agent knows about. The agent picks which
# one(s) to visit based on the user's request. Add/adjust freely.
TARGET_SITES: list[dict[str, str]] = [
    {
        "name": "sxodim.com (Almaty)",
        "url": "https://sxodim.com/almaty",
        "good_for": "concerts, standup, parties, exhibitions, city events in Almaty",
    },
    {
        "name": "ticketon.kz",
        "url": "https://ticketon.kz/almaty",
        "good_for": "concerts, theatre, shows with ticket sales",
    },
    {
        "name": "kino.kz",
        "url": "https://kino.kz",
        "good_for": "movies and cinema schedules",
    },
]


@dataclass
class Settings:
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    mcp_cmd: str = field(default_factory=lambda: os.getenv("MCP_PLAYWRIGHT_CMD", "npx"))
    mcp_args: list[str] = field(
        default_factory=lambda: os.getenv(
            "MCP_PLAYWRIGHT_ARGS", "-y,@playwright/mcp@latest,--headless"
        ).split(",")
    )


SETTINGS = Settings()


def playwright_mcp_server() -> dict:
    """
    Server spec consumed by langchain_mcp_adapters.MultiServerMCPClient.

    Launches `npx -y @playwright/mcp@latest --headless`, which exposes browser
    tools (navigate, click, snapshot/read page, ...) to the agent over stdio.
    """
    return {
        "playwright": {
            "command": SETTINGS.mcp_cmd,
            "args": SETTINGS.mcp_args,
            "transport": "stdio",
        }
    }
