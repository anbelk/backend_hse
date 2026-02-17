import pytest
from unittest.mock import AsyncMock, MagicMock

from src.repositories import UserRepository, AdRepository


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    conn = MagicMock()
    conn.fetchval = AsyncMock(return_value=1)
    conn.fetchrow = AsyncMock(return_value=None)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=None)
    pool.acquire.return_value = cm

    return pool


@pytest.mark.asyncio
async def test_user_repository_create(mock_pool):
    mock_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 42

    repo = UserRepository(mock_pool)
    user_id = await repo.create(is_verified=True)

    assert user_id == 42


@pytest.mark.asyncio
async def test_user_repository_get_by_id(mock_pool):
    record = {"id": 1, "is_verified": True}
    mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = record

    repo = UserRepository(mock_pool)
    result = await repo.get_by_id(1)

    assert result == record
    assert result["is_verified"] is True


@pytest.mark.asyncio
async def test_ad_repository_create(mock_pool):
    mock_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 100

    repo = AdRepository(mock_pool)
    ad_id = await repo.create(
        user_id=1,
        name="Test",
        description="Desc",
        category=5,
        images_qty=3,
    )

    assert ad_id == 100


@pytest.mark.asyncio
async def test_ad_repository_get_with_user_by_id(mock_pool):
    record = {
        "id": 10,
        "images_qty": 2,
        "description": "Ad description",
        "category": 3,
        "is_verified": False,
    }
    mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = record

    repo = AdRepository(mock_pool)
    result = await repo.get_with_user_by_id(10)

    assert result == record
    assert result["category"] == 3
    assert result["is_verified"] is False


@pytest.mark.asyncio
async def test_ad_repository_get_with_user_not_found(mock_pool):
    mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = None

    repo = AdRepository(mock_pool)
    result = await repo.get_with_user_by_id(999)

    assert result is None
