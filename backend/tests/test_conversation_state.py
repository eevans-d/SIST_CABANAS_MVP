"""Tests for conversation_state service."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.services.conversation_state import (
    CONTEXT_TTL_SECONDS,
    delete_user_context,
    get_ttl_remaining,
    get_user_context,
    set_user_context,
    update_user_context,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.ttl = AsyncMock(return_value=-2)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.aclose = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_redis_pool(mock_redis):
    """Mock Redis connection pool."""
    with patch("app.services.conversation_state.get_redis_pool") as mock_pool:
        with patch("app.services.conversation_state.redis.Redis") as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            yield mock_pool


@pytest.mark.asyncio
async def test_set_user_context_success(mock_redis_pool, mock_redis):
    """Test successful context storage."""
    user_id = "+5491112345678"
    context = {
        "current_step": "selecting_accommodation",
        "selected_dates": {"check_in": "2025-10-20", "check_out": "2025-10-22"},
        "guests_count": 2,
    }

    result = await set_user_context(user_id, context)

    assert result is True
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == f"user_context:{user_id}"
    assert call_args[1]["ex"] == CONTEXT_TTL_SECONDS

    # Verify JSON contains context data
    stored_json = call_args[0][1]
    stored_data = json.loads(stored_json)
    assert stored_data["current_step"] == "selecting_accommodation"
    assert "_updated_at" in stored_data


@pytest.mark.asyncio
async def test_set_user_context_custom_ttl(mock_redis_pool, mock_redis):
    """Test context storage with custom TTL."""
    user_id = "+5491112345678"
    context = {"test": "data"}
    custom_ttl = 600

    result = await set_user_context(user_id, context, ttl_seconds=custom_ttl)

    assert result is True
    call_args = mock_redis.set.call_args
    assert call_args[1]["ex"] == custom_ttl


@pytest.mark.asyncio
async def test_set_user_context_redis_error(mock_redis_pool, mock_redis):
    """Test handling of Redis errors during set."""
    mock_redis.set.side_effect = Exception("Redis connection error")

    user_id = "+5491112345678"
    context = {"test": "data"}

    result = await set_user_context(user_id, context)

    assert result is False


@pytest.mark.asyncio
async def test_get_user_context_found(mock_redis_pool, mock_redis):
    """Test retrieving existing context."""
    user_id = "+5491112345678"
    stored_context = {
        "current_step": "confirming",
        "accommodation_id": 5,
        "_updated_at": "2025-10-13T12:00:00",
    }

    mock_redis.get.return_value = json.dumps(stored_context)
    mock_redis.ttl.return_value = 1200

    result = await get_user_context(user_id)

    assert result is not None
    assert result["current_step"] == "confirming"
    assert result["accommodation_id"] == 5
    mock_redis.get.assert_called_once_with(f"user_context:{user_id}")
    mock_redis.ttl.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_context_not_found(mock_redis_pool, mock_redis):
    """Test retrieving non-existent context."""
    user_id = "+5491112345678"
    mock_redis.get.return_value = None

    result = await get_user_context(user_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_user_context_invalid_json(mock_redis_pool, mock_redis):
    """Test handling of corrupted JSON data."""
    user_id = "+5491112345678"
    mock_redis.get.return_value = "invalid json {{"

    result = await get_user_context(user_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_user_context_redis_error(mock_redis_pool, mock_redis):
    """Test handling of Redis errors during get."""
    mock_redis.get.side_effect = Exception("Redis timeout")

    user_id = "+5491112345678"

    result = await get_user_context(user_id)

    assert result is None


@pytest.mark.asyncio
async def test_update_user_context_new_context(mock_redis_pool, mock_redis):
    """Test updating when no previous context exists."""
    user_id = "+5491112345678"
    updates = {"accommodation_id": 3, "current_step": "payment_pending"}

    # First call to get_user_context returns None (no existing context)
    mock_redis.get.return_value = None
    # Second call from set_user_context
    mock_redis.set.return_value = True

    result = await update_user_context(user_id, updates)

    assert result is True
    # Verify set was called with merged data
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_context_merge_existing(mock_redis_pool, mock_redis):
    """Test updating existing context (merge)."""
    user_id = "+5491112345678"
    existing_context = {
        "current_step": "selecting_accommodation",
        "selected_dates": {"check_in": "2025-10-20", "check_out": "2025-10-22"},
        "guests_count": 2,
    }
    updates = {"accommodation_id": 5, "current_step": "confirming"}

    mock_redis.get.return_value = json.dumps(existing_context)
    mock_redis.set.return_value = True

    result = await update_user_context(user_id, updates)

    assert result is True

    # Verify merged context was saved
    call_args = mock_redis.set.call_args
    stored_json = call_args[0][1]
    stored_data = json.loads(stored_json)

    assert stored_data["accommodation_id"] == 5
    assert stored_data["current_step"] == "confirming"
    assert stored_data["selected_dates"] == existing_context["selected_dates"]
    assert stored_data["guests_count"] == 2


@pytest.mark.asyncio
async def test_update_user_context_no_reset_ttl(mock_redis_pool, mock_redis):
    """Test updating without resetting TTL."""
    user_id = "+5491112345678"
    existing_context = {"current_step": "selecting"}
    updates = {"accommodation_id": 5}

    mock_redis.get.return_value = json.dumps(existing_context)
    mock_redis.ttl.return_value = 600  # 10 minutes remaining
    mock_redis.set.return_value = True

    result = await update_user_context(user_id, updates, reset_ttl=False)

    assert result is True

    # Verify TTL was preserved (not reset to 1800)
    call_args = mock_redis.set.call_args
    assert call_args[1]["ex"] == 600


@pytest.mark.asyncio
async def test_delete_user_context_success(mock_redis_pool, mock_redis):
    """Test deleting context."""
    user_id = "+5491112345678"
    mock_redis.delete.return_value = 1  # Key existed

    result = await delete_user_context(user_id)

    assert result is True
    mock_redis.delete.assert_called_once_with(f"user_context:{user_id}")


@pytest.mark.asyncio
async def test_delete_user_context_not_exists(mock_redis_pool, mock_redis):
    """Test deleting non-existent context."""
    user_id = "+5491112345678"
    mock_redis.delete.return_value = 0  # Key didn't exist

    result = await delete_user_context(user_id)

    assert result is True  # Still successful (idempotent)


@pytest.mark.asyncio
async def test_delete_user_context_redis_error(mock_redis_pool, mock_redis):
    """Test handling of Redis errors during delete."""
    mock_redis.delete.side_effect = Exception("Redis error")

    user_id = "+5491112345678"

    result = await delete_user_context(user_id)

    assert result is False


@pytest.mark.asyncio
async def test_get_ttl_remaining_success(mock_redis_pool, mock_redis):
    """Test getting TTL remaining."""
    user_id = "+5491112345678"
    mock_redis.ttl.return_value = 1200

    ttl = await get_ttl_remaining(user_id)

    assert ttl == 1200
    mock_redis.ttl.assert_called_once_with(f"user_context:{user_id}")


@pytest.mark.asyncio
async def test_get_ttl_remaining_not_exists(mock_redis_pool, mock_redis):
    """Test getting TTL for non-existent key."""
    user_id = "+5491112345678"
    mock_redis.ttl.return_value = -2  # Key doesn't exist

    ttl = await get_ttl_remaining(user_id)

    assert ttl == -2


@pytest.mark.asyncio
async def test_get_ttl_remaining_redis_error(mock_redis_pool, mock_redis):
    """Test handling of Redis errors during TTL check."""
    mock_redis.ttl.side_effect = Exception("Redis error")

    user_id = "+5491112345678"

    ttl = await get_ttl_remaining(user_id)

    assert ttl == -2


@pytest.mark.asyncio
async def test_conversation_flow_integration(mock_redis_pool, mock_redis):
    """Test complete conversation flow: set → get → update → delete."""
    user_id = "+5491112345678"

    # Step 1: Initial context
    initial_context = {"current_step": "awaiting_dates"}
    mock_redis.set.return_value = True
    result = await set_user_context(user_id, initial_context)
    assert result is True

    # Step 2: Get context
    mock_redis.get.return_value = json.dumps(initial_context)
    mock_redis.ttl.return_value = 1800
    context = await get_user_context(user_id)
    assert context["current_step"] == "awaiting_dates"

    # Step 3: Update context
    updates = {"selected_dates": {"check_in": "2025-10-20", "check_out": "2025-10-22"}}
    mock_redis.get.return_value = json.dumps({**initial_context, **updates})
    result = await update_user_context(user_id, updates)
    assert result is True

    # Step 4: Delete context (reset conversation)
    mock_redis.delete.return_value = 1
    result = await delete_user_context(user_id)
    assert result is True
