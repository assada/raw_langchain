import json
import tracemalloc
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from langfuse import Langfuse
from langgraph.graph.state import CompiledStateGraph

from app.agent.services.agent_service import AgentService
from app.agent.services.events.base_event import BaseEvent
from app.models import Thread, User
from app.models.thread import ThreadStatus

tracemalloc.start()

@pytest.fixture
def mock_langfuse():
    lf = Mock(spec=Langfuse)
    span = Mock(trace_id="test_trace_id")
    span.__enter__ = Mock(return_value=span)
    span.__exit__ = Mock(return_value=None)
    lf.start_as_current_span.return_value = span
    lf.create_score = Mock()
    return lf


@pytest.fixture
def mock_graph():
    g = Mock(spec=CompiledStateGraph)
    g.name = "test_graph"
    g.astream = AsyncMock()
    g.aget_state = AsyncMock()
    return g


@pytest.fixture
def agent_service(mock_graph, mock_langfuse):
    return AgentService(mock_graph, mock_langfuse)


@pytest.fixture
def mock_thread():
    return Thread(
        id="test_thread_id",
        metadata={"key": "value"},
        status=ThreadStatus.idle,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_user():
    return User(id="test_user_id", email="test@example.com")


class TestAgentService:
    @pytest.mark.asyncio
    @patch("app.agent.services.agent_service.uuid4")
    async def test_stream_response_success(self, mock_uuid4, agent_service, mock_thread, mock_user):
        mock_uuid4.return_value = uuid4()
        mock_event = Mock()
        mock_event.model_dump.return_value = {"event": "test", "data": "test_data"}

        async def stream():
            yield ("updates", {"t": "d"})

        agent_service.graph.astream.return_value = stream()

        with patch.object(agent_service.stream_processor, "process_stream") as mproc:
            async def proc(*_):
                yield mock_event

            mproc.return_value = proc()

            out = [r async for r in agent_service.stream_response("msg", mock_thread, mock_user)]

            assert out == [{"event": "test", "data": "test_data"}]
            assert mock_thread.status == ThreadStatus.idle

            cfg = agent_service.graph.astream.call_args.kwargs["config"]
            assert cfg["configurable"]["thread_id"] == mock_thread.id
            assert cfg["configurable"]["user_id"] == mock_user.id
            assert cfg["run_id"] is not None

    @pytest.mark.asyncio
    async def test_stream_response_thread_status_updates(self, agent_service, mock_thread, mock_user):
        ts0 = mock_thread.updated_at

        async def stream():
            yield ("updates", {"t": "d"})

        agent_service.graph.astream.return_value = stream()
        ev = Mock()
        ev.model_dump.return_value = {"e": "d"}

        with patch.object(agent_service.stream_processor, "process_stream") as mproc:
            async def proc(*_):
                yield ev

            mproc.return_value = proc()
            async for _ in agent_service.stream_response("m", mock_thread, mock_user):
                pass

        assert mock_thread.status == ThreadStatus.idle
        assert mock_thread.updated_at > ts0

    @pytest.mark.asyncio
    @patch("app.agent.services.agent_service.to_chat_message")
    async def test_load_history_with_messages(self, m_to, agent_service, mock_thread, mock_user):
        chat = Mock()
        chat.type = "ai_message"
        chat.model_dump.return_value = {"c": "t"}
        m_to.return_value = chat

        msg = Mock(id="m1")
        st = Mock(values={"messages": [msg], "message_trace_map": [{"id": "m1", "trace_id": "tr"}]})
        agent_service.graph.aget_state.return_value = st

        with patch.object(BaseEvent, "from_payload") as fp:
            ev = Mock()
            ev.model_dump.return_value = {"e": "ai"}
            fp.return_value = ev

            res = [r async for r in agent_service.load_history(mock_thread, mock_user)]

        assert res[0] == {"e": "ai"}
        assert json.loads(res[1]["data"])["status"] == "completed"
        m_to.assert_called_once_with(msg, trace_id="tr")

    @pytest.mark.asyncio
    async def test_load_history_no_messages(self, agent_service, mock_thread, mock_user):
        st = Mock(values={"messages": []})
        agent_service.graph.aget_state.return_value = st
        res = [r async for r in agent_service.load_history(mock_thread, mock_user)]
        assert json.loads(res[0]["data"])["status"] == "completed"

    @pytest.mark.asyncio
    async def test_add_feedback_success(self, agent_service, mock_thread, mock_user):
        t0 = mock_thread.updated_at
        r = await agent_service.add_feedback("tr", 1.0, mock_thread, mock_user)
        assert r["status"] == "success"
        assert mock_thread.updated_at > t0
        agent_service.langfuse.create_score.assert_called_once()

