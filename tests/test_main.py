import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_predict_positive():
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": True,
            "item_id": 1,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": 2
        }
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] == True


def test_predict_negative():
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": False,
            "item_id": 1,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": 0
        }
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] == False


def test_predict_validation_wrong_type():
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": "not_a_bool",
            "item_id": 1,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": 0
        }
    )
    assert response.status_code == 422
    assert "boolean" in response.json()["detail"][0]["msg"].lower()


def test_predict_validation_missing_required():
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "item_id": 1,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": 0
        }
    )
    assert response.status_code == 422
    assert "is_verified_seller" in str(response.json()["detail"][0]["loc"])


@pytest.mark.parametrize("is_verified,images_qty,expected", [
    (True, 0, True),
    (False, 0, False),
    (False, 5, True),
    (True, 10, True),
])
def test_predict_business_logic(is_verified, images_qty, expected):
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": is_verified,
            "item_id": 1,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": images_qty
        }
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] == expected