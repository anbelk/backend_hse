import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from fastapi.testclient import TestClient

from src.main import app
from src.dependencies import (
    get_ad_repository,
    get_kafka_producer,
    get_model_manager,
    get_moderation_repository,
)

@pytest.fixture(autouse=True)
def mock_db_pool(monkeypatch):
    async def fake_create_pool(*args, **kwargs):
        pool = MagicMock()
        pool.close = AsyncMock()
        return pool
    monkeypatch.setattr("asyncpg.create_pool", fake_create_pool)


@pytest.fixture(autouse=True)
def mock_kafka_producer(monkeypatch):
    mock_producer = MagicMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.send_moderation_request = AsyncMock()
    mock_producer.send_to_dlq = AsyncMock()

    def fake_create_producer(*args, **kwargs):
        return mock_producer
    monkeypatch.setattr("src.main.create_kafka_producer", fake_create_producer)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_ad_payload():
    return {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 1,
        "name": "Item",
        "description": "Description text",
        "category": 1,
        "images_qty": 2
    }

@pytest.fixture
def mock_model_manager():
    mock_manager = Mock()
    mock_manager.model = Mock()
    mock_manager.predict = AsyncMock()
    
    mock_manager.predict.return_value = {
        "is_violation": True,
        "probability": 0.75
    }
    
    return mock_manager

@pytest.fixture
def mock_ad_repository():
    mock = Mock()
    mock.get_with_user_by_id = AsyncMock()
    return mock


@pytest.fixture
def mock_moderation_repository():
    mock = Mock()
    mock.create_pending = AsyncMock(return_value=42)
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_oldest_pending_by_item_id = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_kafka_producer_dep():
    mock = MagicMock()
    mock.send_moderation_request = AsyncMock()
    return mock


@pytest.fixture
def app_with_dependency_overrides(
    mock_model_manager,
    mock_ad_repository,
    mock_moderation_repository,
    mock_kafka_producer_dep,
):
    original_overrides = app.dependency_overrides.copy()

    async def get_mock_ad_repo():
        return mock_ad_repository

    async def get_mock_moderation_repo():
        return mock_moderation_repository

    async def get_mock_kafka():
        return mock_kafka_producer_dep

    async def get_mock_model():
        return mock_model_manager
    app.dependency_overrides[get_model_manager] = get_mock_model
    app.dependency_overrides[get_ad_repository] = get_mock_ad_repo
    app.dependency_overrides[get_moderation_repository] = get_mock_moderation_repo
    app.dependency_overrides[get_kafka_producer] = get_mock_kafka

    yield app

    app.dependency_overrides = original_overrides

@pytest.fixture
def client_with_model(app_with_dependency_overrides):
    return TestClient(app_with_dependency_overrides)

@pytest.fixture
def app_with_unavailable_model():
    async def mock_unavailable_model():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Model service is not available")
    
    original_overrides = app.dependency_overrides.copy()
    
    app.dependency_overrides[get_model_manager] = mock_unavailable_model
    
    yield app
    
    app.dependency_overrides = original_overrides

@pytest.fixture
def client_with_unavailable_model(app_with_unavailable_model):
    return TestClient(app_with_unavailable_model)
