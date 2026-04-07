"""
agents/dummy_weather.py – Dummy LangGraph agent with a fake get_weather tool.

Purpose: Prove that LangGraph v2 astream_events can be translated to OpenAI SSE.
This agent is intentionally simple: it always calls get_weather, then summarizes.
"""
import json
import random
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# ─── Fake Tool ────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city. This is a fake tool for demo purposes."""
    conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "windy"]
    temp = random.randint(-5, 35)
    condition = random.choice(conditions)
    return json.dumps({
        "city": city,
        "temperature_celsius": temp,
        "condition": condition,
        "humidity_percent": random.randint(30, 90),
    })


TOOLS = [get_weather]
TOOL_MAP = {t.name: t for t in TOOLS}


# ─── Graph State ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ─── Graph Nodes ──────────────────────────────────────────────────────────────

def agent_node(state: AgentState) -> AgentState:
    """Simulates an LLM deciding to call get_weather or respond directly."""
    last = state["messages"][-1]

    # If the last message is a ToolMessage, generate a summary response
    if isinstance(last, ToolMessage):
        try:
            data = json.loads(last.content)
            city = data.get("city", "unknown")
            temp = data.get("temperature_celsius", "?")
            cond = data.get("condition", "unknown")
            humidity = data.get("humidity_percent", "?")
        except (json.JSONDecodeError, AttributeError):
            city, temp, cond, humidity = "unknown", "?", "unknown", "?"
        summary = (
            f"The weather in {city} is currently {cond} "
            f"with a temperature of {temp}°C and {humidity}% humidity."
        )
        return {"messages": [AIMessage(content=summary)]}

    # Otherwise, extract a city and call get_weather
    user_text = last.content if isinstance(last, HumanMessage) else str(last.content)
    city = "Berlin"  # Default
    lower = user_text.lower()
    for word in user_text.split():
        cleaned = word.strip("?,!.")
        if cleaned and cleaned[0].isupper() and cleaned.lower() not in (
            "what", "how", "the", "is", "weather", "in", "whats", "what's",
            "tell", "me", "about", "get", "show", "please", "can", "you",
        ):
            city = cleaned
            break

    tool_call_id = f"call_{random.randint(100000, 999999)}"
    ai_msg = AIMessage(
        content="",
        tool_calls=[{
            "id": tool_call_id,
            "name": "get_weather",
            "args": {"city": city},
        }],
    )
    return {"messages": [ai_msg]}


def tool_node(state: AgentState) -> AgentState:
    """Execute the tool calls from the last AI message."""
    last = state["messages"][-1]
    results: list[ToolMessage] = []
    if isinstance(last, AIMessage) and last.tool_calls:
        for tc in last.tool_calls:
            fn = TOOL_MAP.get(tc["name"])
            if fn:
                result = fn.invoke(tc["args"])
                results.append(ToolMessage(content=result, tool_call_id=tc["id"]))
            else:
                results.append(ToolMessage(
                    content=f"Error: Unknown tool '{tc['name']}'",
                    tool_call_id=tc["id"],
                ))
    return {"messages": results}


def _should_call_tool(state: AgentState) -> str:
    """Route: if the agent produced tool_calls, go to tool_node; else END."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tool_node"
    return END


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_dummy_graph():
    """Build and compile the dummy weather agent graph."""
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tool_node", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_call_tool)
    graph.add_edge("tool_node", "agent")
    return graph.compile()
