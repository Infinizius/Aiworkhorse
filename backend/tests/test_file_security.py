from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import _get_rag_context, app


pytestmark = pytest.mark.anyio


def _headers(user_id: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer workhorse-test",
        "X-User-Email": user_id,
    }


class _Result:
    def __init__(self, *, scalar=None, scalars_all=None, rows=None):
        self._scalar = scalar
        self._scalars_all = scalars_all or []
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars_all)

    def all(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class _SessionFactory:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        session = self._session

        class _Context:
            async def __aenter__(self_inner):
                return session

            async def __aexit__(self_inner, exc_type, exc, tb):
                return None

        return _Context()


async def test_list_files_only_returns_current_user_files(client):
    user_file = SimpleNamespace(
        id="owned-file",
        filename="owned.pdf",
        extracted_text="secret",
        page_count=2,
        uploaded_at=datetime.now(timezone.utc),
    )

    async def execute_side_effect(query):
        sql = str(query)
        if "count(file_embeddings.id)" in sql:
            return _Result(rows=[SimpleNamespace(file_id="owned-file", cnt=3)])
        assert "uploaded_files.user_id" in sql
        return _Result(scalars_all=[user_file])

    session = MagicMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)
    original_factory = app.state.db_session_factory
    app.state.db_session_factory = _SessionFactory(session)

    try:
        response = await client.get("/v1/files", headers=_headers("alice@example.com"))
    finally:
        app.state.db_session_factory = original_factory

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["files"][0]["file_id"] == "owned-file"
    assert body["files"][0]["chunks_embedded"] == 3


async def test_get_file_returns_404_for_unowned_file(client):
    session = MagicMock()
    session.execute = AsyncMock(return_value=_Result(scalar=None))
    original_factory = app.state.db_session_factory
    app.state.db_session_factory = _SessionFactory(session)

    try:
        response = await client.get("/v1/files/foreign-file", headers=_headers("alice@example.com"))
    finally:
        app.state.db_session_factory = original_factory

    assert response.status_code == 404
    query = session.execute.await_args.args[0]
    assert "uploaded_files.user_id" in str(query)


async def test_delete_file_returns_404_for_unowned_file(client):
    session = MagicMock()
    session.execute = AsyncMock(return_value=_Result(scalar=None))
    session.commit = AsyncMock()
    original_factory = app.state.db_session_factory
    app.state.db_session_factory = _SessionFactory(session)

    try:
        response = await client.delete("/v1/files/foreign-file", headers=_headers("alice@example.com"))
    finally:
        app.state.db_session_factory = original_factory

    assert response.status_code == 404
    session.commit.assert_not_awaited()
    query = session.execute.await_args.args[0]
    assert "uploaded_files.user_id" in str(query)


async def test_download_file_returns_404_for_unowned_file(client):
    session = MagicMock()
    session.execute = AsyncMock(return_value=_Result(scalar=None))
    original_factory = app.state.db_session_factory
    app.state.db_session_factory = _SessionFactory(session)

    try:
        response = await client.get("/v1/files/foreign-file/download", headers=_headers("alice@example.com"))
    finally:
        app.state.db_session_factory = original_factory

    assert response.status_code == 404
    query = session.execute.await_args.args[0]
    assert "uploaded_files.user_id" in str(query)


async def test_rag_context_ignores_unowned_file_ids():
    owned_chunk = SimpleNamespace(file_id="owned-file", chunk_text="owned content")

    async def execute_side_effect(query):
        sql = str(query)
        if "uploaded_files.id" in sql:
            assert "uploaded_files.user_id" in sql
            return _Result(scalars_all=["owned-file"])
        assert "file_embeddings.file_id" in sql
        return _Result(scalars_all=[owned_chunk])

    session = MagicMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)
    original_factory = app.state.db_session_factory
    app.state.db_session_factory = _SessionFactory(session)

    try:
        with patch("main.asyncio.to_thread", new=AsyncMock(return_value=SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1, 0.2])]))):
            rag_context = await _get_rag_context(
                ["owned-file", "foreign-file"],
                "Summarize",
                app,
                "alice@example.com",
            )
    finally:
        app.state.db_session_factory = original_factory

    assert "owned-file" in rag_context
    assert "foreign-file" not in rag_context
