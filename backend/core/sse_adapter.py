"""
core/sse_adapter.py – Translates LangGraph v2 astream_events into OpenAI SSE chunks.

Event mapping:
  - on_chat_model_stream  → delta.content chunks (text streaming)
  - on_tool_start         → delta.tool_calls chunks (tool invocation)
  - on_tool_end           → delta.tool_calls with result (function response)

Each yielded string is a complete SSE line: "data: {json}\\n\\n"
The stream ends with "data: [DONE]\\n\\n".
"""
import json
import time
import uuid
from typing import AsyncIterator

from langchain_core.messages import AIMessageChunk


def _make_chunk_json(
    chat_id: str,
    created: int,
    model: str,
    delta: dict,
    finish_reason: str | None = None,
) -> str:
    """Build a single OpenAI-compatible SSE chunk payload."""
    return json.dumps({
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish_reason,
        }],
    })


async def langgraph_to_openai_sse(
    graph,
    input_messages: list,
    model_name: str = "maxclaw-agent",
) -> AsyncIterator[str]:
    """
    Run a compiled LangGraph and yield OpenAI-compatible SSE chunks.

    Translates the following LangGraph v2 astream_events:
      - on_chat_model_stream: streamed text content → delta.content
      - on_tool_start: tool invocation begins → delta.tool_calls
      - on_tool_end: tool execution result → separate chunk with tool output

    Args:
        graph: A compiled LangGraph StateGraph.
        input_messages: List of LangChain BaseMessage objects for the input.
        model_name: The model name to include in SSE chunks.

    Yields:
        SSE-formatted strings ("data: {...}\\n\\n").
    """
    chat_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    # Send the initial role chunk
    yield f"data: {_make_chunk_json(chat_id, created, model_name, {'role': 'assistant'})}\n\n"

    # Track tool call indices for proper OpenAI formatting
    tool_call_index = 0

    async for event in graph.astream_events(
        {"messages": input_messages},
        version="v2",
    ):
        kind = event.get("event", "")

        # ── on_chat_model_stream: streamed text tokens ──
        if kind == "on_chat_model_stream":
            data = event.get("data", {})
            chunk = data.get("chunk")
            if isinstance(chunk, AIMessageChunk):
                # Stream tool_calls from the model
                if chunk.tool_call_chunks:
                    for tc_chunk in chunk.tool_call_chunks:
                        tc_delta: dict = {}
                        if tc_chunk.get("name"):
                            tc_delta = {
                                "index": tool_call_index,
                                "id": tc_chunk.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                                "type": "function",
                                "function": {
                                    "name": tc_chunk["name"],
                                    "arguments": tc_chunk.get("args", ""),
                                },
                            }
                        elif tc_chunk.get("args"):
                            tc_delta = {
                                "index": tool_call_index,
                                "function": {
                                    "arguments": tc_chunk["args"],
                                },
                            }
                        if tc_delta:
                            yield f"data: {_make_chunk_json(chat_id, created, model_name, {'tool_calls': [tc_delta]})}\n\n"
                # Stream text content
                elif chunk.content:
                    yield f"data: {_make_chunk_json(chat_id, created, model_name, {'content': chunk.content})}\n\n"

        # ── on_tool_start: tool invocation ──
        elif kind == "on_tool_start":
            data = event.get("data", {})
            tool_input = data.get("input", {})
            tool_name = event.get("name", "unknown_tool")

            tc_obj = {
                "index": tool_call_index,
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input),
                },
            }
            yield f"data: {_make_chunk_json(chat_id, created, model_name, {'tool_calls': [tc_obj]})}\n\n"
            tool_call_index += 1

        # ── on_tool_end: tool execution result ──
        elif kind == "on_tool_end":
            data = event.get("data", {})
            output = data.get("output", "")
            tool_name = event.get("name", "unknown_tool")
            # Emit tool result as a content delta so the UI can display it
            result_text = str(output.content) if hasattr(output, "content") else str(output)
            yield f"data: {_make_chunk_json(chat_id, created, model_name, {'content': f'[Tool: {tool_name}] {result_text}'})}\n\n"

    # Final chunk with finish_reason and DONE sentinel
    yield f"data: {_make_chunk_json(chat_id, created, model_name, {}, finish_reason='stop')}\n\n"
    yield "data: [DONE]\n\n"
