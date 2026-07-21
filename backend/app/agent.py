"""
Part 3 — The brain: a LangChain (LangGraph ReAct) agent that uses the
MCP Playwright server to browse real event sites and answer the user.

Public API (used by Part 4 / main.py):
    await run_agent(user_text: str) -> AgentResult

How it works:
  1. Connect to the Playwright MCP server (mcp_config.playwright_mcp_server()).
  2. Load its browser tools into LangChain via langchain-mcp-adapters.
  3. Build a ReAct agent (create_react_agent) over ChatOpenAI + those tools.
  4. Give it a system prompt that lists the TARGET_SITES and tells it to go
     surf the right one for the user's request, read the page, and summarize.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .mcp_config import SETTINGS, TARGET_SITES, playwright_mcp_server
from .schemas import AgentResult, Event


def _system_prompt() -> str:
    sites = "\n".join(
        f"  - {s['name']} — {s['url']} (good for: {s['good_for']})" for s in TARGET_SITES
    )
    return f"""You are a voice assistant that helps people plan their leisure time
in Almaty (concerts, standup, movies, exhibitions, events).

You have BROWSER tools (via Playwright MCP): you can navigate to a URL, read the
page content, and click. Use them to find CURRENT, REAL events — never invent them.

Known event sites:
{sites}

Workflow for a request:
  1. Decide which site fits (movies -> kino.kz; concerts/standup/city events ->
     sxodim.com; ticketed shows -> ticketon.kz). You may visit more than one.
  2. Navigate there, read the page, and extract a few concrete options that match
     the user's ask (day/time, genre, city).
  3. Reply in the SAME language the user used, warm and concise — like you're
     talking out loud, because your answer will be read aloud by TTS.

At the very end of your final message, append a machine-readable block on its own
lines, exactly:

<EVENTS>
{{"events": [{{"title": "...", "when": "...", "venue": "...", "url": "..."}}], "sources": ["https://..."]}}
</EVENTS>

Put your spoken answer BEFORE that block. Keep the spoken part free of URLs and JSON.
If you found nothing, still include an empty events list and say so politely."""


def _split_answer_and_data(text: str) -> tuple[str, list[Event], list[str]]:
    marker = "<EVENTS>"
    if marker not in text:
        return text.strip(), [], []
    spoken, _, rest = text.partition(marker)
    raw = rest.replace("</EVENTS>", "").strip()
    try:
        data = json.loads(raw)
        events = [Event(**e) for e in data.get("events", [])]
        sources = list(data.get("sources", []))
    except (json.JSONDecodeError, TypeError, ValueError):
        events, sources = [], []
    return spoken.strip(), events, sources


async def run_agent(user_text: str) -> AgentResult:
    """Run one turn of the agent over the user's transcribed request."""
    # MultiServerMCPClient is an async context manager: entering it connects to
    # every configured server (spawns/talks to the Playwright MCP process) and
    # populates its tool list; get_tools() itself is synchronous.
    async with MultiServerMCPClient(playwright_mcp_server()) as client:
        tools = client.get_tools()

        llm = ChatOpenAI(model=SETTINGS.llm_model, temperature=0.2)
        agent = create_react_agent(llm, tools)

        result = await agent.ainvoke(
            {
                "messages": [
                    SystemMessage(content=_system_prompt()),
                    HumanMessage(content=user_text),
                ]
            },
            # allow enough steps to navigate + read a couple of pages
            config={"recursion_limit": 40},
        )

    final = result["messages"][-1].content
    if isinstance(final, list):  # some providers return content blocks
        final = "".join(part.get("text", "") for part in final if isinstance(part, dict))

    answer, events, sources = _split_answer_and_data(final)
    return AgentResult(answer=answer, events=events, sources=sources)
