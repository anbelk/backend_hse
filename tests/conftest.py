import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.dependencies import get_model_manager

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
def app_with_dependency_overrides(mock_model_manager):
    original_overrides = app.dependency_overrides.copy()
    
    app.dependency_overrides[get_model_manager] = lambda: mock_model_manager
    
    yield app
    
    app.dependency_overrides = original_overrides

@pytest.fixture
def client_with_model(app_with_dependency_overrides):
    return TestClient(app_with_dependency_overrides)

@pytest.fixture
def app_with_unavailable_model():
    def mock_unavailable_model():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Model service is not available")
    
    original_overrides = app.dependency_overrides.copy()
    
    app.dependency_overrides[get_model_manager] = mock_unavailable_model
    
    yield app
    
    app.dependency_overrides = original_overrides

@pytest.fixture
def client_with_unavailable_model(app_with_unavailable_model):
    return TestClient(app_with_unavailable_model)
