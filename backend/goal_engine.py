import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import httpx
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import API_KEY, DATABASE_URL, GOAL_MAX_ITERATIONS
from models import GoalTask

logger = logging.getLogger("ai_workhorse.goal_engine")
logging.basicConfig(level=logging.INFO)

GOAL_ENGINE_API_URL = os.getenv("GOAL_ENGINE_API_URL", "http://api:8000")
GOAL_ENGINE_POLL_SECONDS = int(os.getenv("GOAL_ENGINE_POLL_SECONDS", "30"))


class GoalState(TypedDict):
    goal_id: str
    user_id: str
    goal: str
    model: str
    search_query: str
    tool_result: str
    summary: str


def _checkpoint_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _prepare_goal(state: GoalState) -> GoalState:
    return {
        **state,
        "search_query": state["goal"].strip(),
    }


async def _execute_web_search(state: GoalState) -> GoalState:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-Source": "goal-engine",
    }
    payload = {
        "tool_name": "web_search",
        "arguments": {"query": state["search_query"]},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{GOAL_ENGINE_API_URL}/internal/tools/execute",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()
    return {
        **state,
        "tool_result": body.get("result", ""),
    }


async def _summarize_goal(state: GoalState) -> GoalState:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-Source": "goal-engine",
        "X-User-Email": state["user_id"],
    }
    payload = {
        "model": state["model"],
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Fasse die Recherche kurz auf Deutsch zusammen und leite konkrete nächste "
                    "Schritte für das Ziel ab.\n\n"
                    f"Ziel:\n{state['goal']}\n\n"
                    f"Recherche:\n{state['tool_result']}"
                ),
            }
        ],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{GOAL_ENGINE_API_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()
    summary = body["choices"][0]["message"]["content"]
    return {
        **state,
        "summary": summary,
    }


def _build_graph(checkpointer: AsyncPostgresSaver):
    graph = StateGraph(GoalState)
    graph.add_node("prepare_goal", _prepare_goal)
    graph.add_node("execute_web_search", _execute_web_search)
    graph.add_node("summarize_goal", _summarize_goal)
    graph.add_edge(START, "prepare_goal")
    graph.add_edge("prepare_goal", "execute_web_search")
    graph.add_edge("execute_web_search", "summarize_goal")
    graph.add_edge("summarize_goal", END)
    return graph.compile(checkpointer=checkpointer)


async def _claim_due_goals(session: AsyncSession) -> list[GoalTask]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(GoalTask)
        .where(
            GoalTask.status.in_(("pending", "failed")),
            GoalTask.next_run_at.is_not(None),
            GoalTask.next_run_at <= now,
        )
        .order_by(GoalTask.next_run_at.asc())
        .with_for_update(skip_locked=True)
    )
    goals = result.scalars().all()
    for goal in goals:
        goal.status = "running"
        goal.last_error = None
        goal.updated_at = now
    if goals:
        await session.commit()
    return goals


async def _mark_goal_success(session_factory, goal_id: str, summary: str) -> None:
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        goal = await session.get(GoalTask, goal_id)
        if not goal:
            return
        goal.last_result = summary
        goal.last_error = None
        goal.last_run_at = now
        goal.run_count = (goal.run_count or 0) + 1
        goal.updated_at = now
        if goal.schedule_minutes:
            goal.status = "pending"
            goal.next_run_at = now + timedelta(minutes=goal.schedule_minutes)
        else:
            goal.status = "completed"
            goal.next_run_at = None
        await session.commit()


async def _mark_goal_failure(session_factory, goal_id: str, error_message: str) -> None:
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        goal = await session.get(GoalTask, goal_id)
        if not goal:
            return
        goal.last_error = error_message[:4000]
        goal.updated_at = now
        if goal.schedule_minutes:
            goal.status = "pending"
            goal.next_run_at = now + timedelta(minutes=goal.schedule_minutes)
        else:
            goal.status = "failed"
            goal.next_run_at = None
        await session.commit()


async def run() -> None:
    if not API_KEY:
        raise RuntimeError("API_KEY is required for the goal engine")

    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncPostgresSaver.from_conn_string(_checkpoint_dsn(DATABASE_URL)) as checkpointer:
        await checkpointer.setup()
        graph = _build_graph(checkpointer)
        try:
            while True:
                async with session_factory() as session:
                    goals = await _claim_due_goals(session)
                for goal in goals:
                    try:
                        result = await graph.ainvoke(
                            {
                                "goal_id": goal.id,
                                "user_id": goal.user_id,
                                "goal": goal.goal,
                                "model": goal.model,
                                "search_query": "",
                                "tool_result": "",
                                "summary": "",
                            },
                            config={
                                "configurable": {"thread_id": goal.id},
                                "recursion_limit": GOAL_MAX_ITERATIONS,
                            },
                        )
                        await _mark_goal_success(session_factory, goal.id, result.get("summary", ""))
                        logger.info("Goal executed", extra={"goal_id": goal.id, "status": "completed"})
                    except Exception as exc:
                        logger.exception("Goal execution failed")
                        await _mark_goal_failure(session_factory, goal.id, str(exc))
                await asyncio.sleep(GOAL_ENGINE_POLL_SECONDS)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
