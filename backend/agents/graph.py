"""
agents/graph.py – LangGraph supervisor agent for the MaxClaw system.

Architecture:
  - A single supervisor node powered by ChatOpenAI (configured for Requesty / MiniMax).
  - Tool nodes for web_search, read/write workspace files, and core memory updates.
  - Core memory is injected into the system prompt before every LLM call.
"""
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from agents.tools import AGENT_TOOLS
from config import AGENT_MODEL_NAME, REQUESTY_API_KEY, REQUESTY_BASE_URL

logger = logging.getLogger("ai_workhorse.graph")

TOOL_MAP = {t.name: t for t in AGENT_TOOLS}


# ─── Graph State ──────────────────────────────────────────────────────────────

class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    core_memory: str


# ─── LLM ──────────────────────────────────────────────────────────────────────

def _build_llm():
    """Build the ChatOpenAI instance targeting Requesty (or any OpenAI-compatible provider)."""
    return ChatOpenAI(
        model=AGENT_MODEL_NAME,
        openai_api_key=REQUESTY_API_KEY or "sk-placeholder",
        openai_api_base=REQUESTY_BASE_URL,
        temperature=0.3,
        streaming=True,
    )


# ─── System Prompt with Core Memory Injection ────────────────────────────────

_BASE_SYSTEM_PROMPT = """\
Du bist "MaxClaw", der intelligente KI-Agent von AI-Workhorse.
Du hilfst dem Nutzer mit Recherchen, Dateimanagement und Wissensaufbau.

Verfügbare Tools:
- web_search: Durchsuche das Internet nach Informationen.
- visit_webpage: Besuche eine beliebige URL (auch lokale Ports wie http://localhost:3000)
  und lese den Seiteninhalt als Text. Ideal zum Prüfen von laufenden Web-Apps und Integrationen.
- http_request: Sende HTTP-Anfragen (GET, POST, PUT, DELETE, …) an beliebige URLs.
  Unterstützt lokale Dienste (z. B. http://localhost:8000/health) und öffentliche APIs.
  Gibt Statuscode, Header und Body zurück – perfekt für Integrationstests.
- read_workspace_file: Lies eine Datei aus dem Workspace des Nutzers.
- write_workspace_file: Schreibe eine Datei in den Workspace des Nutzers.
- update_core_memory: Aktualisiere dein dauerhaftes Gedächtnis über den Nutzer.

WICHTIG: Bei read_workspace_file, write_workspace_file und update_core_memory
musst du immer den 'user_id' Parameter mitgeben. Dieser wird dir im State
bereitgestellt.

Antworte immer auf Deutsch, es sei denn, der Nutzer schreibt auf Englisch.
Sei präzise, hilfsbereit und proaktiv."""


def _build_system_message(core_memory: str) -> SystemMessage:
    """Build the system prompt, injecting the user's core memory."""
    prompt = _BASE_SYSTEM_PROMPT
    if core_memory and core_memory.strip():
        prompt += f"\n\n== DEIN DAUERHAFTES GEDÄCHTNIS ÜBER DEN NUTZER ==\n{core_memory}\n== ENDE GEDÄCHTNIS =="
    return SystemMessage(content=prompt)


# ─── Nodes ────────────────────────────────────────────────────────────────────

def supervisor_node(state: SupervisorState) -> dict:
    """The supervisor calls the LLM with the current messages and core memory."""
    llm = _build_llm()
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    system_msg = _build_system_message(state.get("core_memory", ""))
    messages = [system_msg] + list(state["messages"])

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: SupervisorState) -> dict:
    """Execute tool calls from the last AI message."""
    last = state["messages"][-1]
    results: list[ToolMessage] = []
    if isinstance(last, AIMessage) and last.tool_calls:
        for tc in last.tool_calls:
            fn = TOOL_MAP.get(tc["name"])
            if fn:
                result = fn.invoke(tc["args"])
                results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            else:
                results.append(ToolMessage(
                    content=f"Error: Unknown tool '{tc['name']}'",
                    tool_call_id=tc["id"],
                ))
    return {"messages": results}


def _should_use_tools(state: SupervisorState) -> str:
    """Route: if the LLM produced tool_calls, go to tools; else END."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_supervisor_graph():
    """Build and compile the MaxClaw supervisor graph."""
    graph = StateGraph(SupervisorState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", _should_use_tools)
    graph.add_edge("tools", "supervisor")

    return graph.compile()
