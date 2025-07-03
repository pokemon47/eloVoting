import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from app.crud import create_poll, get_poll_by_id, upsert_global_score
from app.schemas import PollCreate
from app.models import Poll, GlobalScore
import uuid

@pytest.mark.asyncio
async def test_create_poll_success():
    session = AsyncMock()
    session.add = Mock()
    poll_data = PollCreate(title="Unit Poll", creator_email="unit@example.com")
    poll = await create_poll(poll=poll_data, session=session)
    session.add.assert_called_once()
    session.commit.assert_awaited()
    session.refresh.assert_awaited()
    assert poll.title == "Unit Poll"

@pytest.mark.asyncio
async def test_get_poll_by_id_found():
    session = AsyncMock()
    fake_poll = Poll(id=uuid.uuid4(), title="Test", creator_email="a@b.com")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = Mock(return_value=fake_poll)
    session.execute = AsyncMock(return_value=mock_result)
    result = await get_poll_by_id(poll_id=fake_poll.id, session=session)
    assert result == fake_poll

@pytest.mark.asyncio
async def test_get_poll_by_id_not_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    session.execute = AsyncMock(return_value=mock_result)
    result = await get_poll_by_id(poll_id=uuid.uuid4(), session=session)
    assert result is None

@pytest.mark.asyncio
async def test_upsert_global_score_new():
    session = AsyncMock()
    mock_result = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    poll_id = uuid.uuid4()
    option_id = uuid.uuid4()
    await upsert_global_score(poll_id=poll_id, option_id=option_id, total_score=5.0, session=session)
    session.execute.assert_awaited()
    session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_upsert_global_score_update():
    session = AsyncMock()
    poll_id = uuid.uuid4()
    option_id = uuid.uuid4()
    session.execute = AsyncMock()
    await upsert_global_score(poll_id=poll_id, option_id=option_id, total_score=3.0, session=session)
    session.execute.assert_awaited()
    session.commit.assert_awaited() 