import pytest
from unittest.mock import Mock

from src.main import app
from src.dependencies import get_model_manager

class TestInputValidation:
    def test_predict_validation_wrong_type(self, client_with_model, valid_ad_payload):
        payload = valid_ad_payload.copy()
        payload["is_verified_seller"] = "not_a_bool"
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 422
        assert "boolean" in response.json()["detail"][0]["msg"].lower()

    def test_predict_validation_missing_required(self, client_with_model, valid_ad_payload):
        payload = valid_ad_payload.copy()
        del payload["is_verified_seller"]
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 422
        assert "is_verified_seller" in str(response.json()["detail"][0]["loc"])

    def test_predict_validation_negative_seller_id(self, client_with_model, valid_ad_payload):
        payload = valid_ad_payload.copy()
        payload["seller_id"] = -1
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 422
        assert "seller_id" in str(response.json()["detail"][0]["loc"])

    def test_predict_validation_negative_item_id(self, client_with_model, valid_ad_payload):
        payload = valid_ad_payload.copy()
        payload["item_id"] = -1
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 422
        assert "item_id" in str(response.json()["detail"][0]["loc"])

    def test_predict_validation_negative_images_qty(self, client_with_model, valid_ad_payload):
        payload = valid_ad_payload.copy()
        payload["images_qty"] = -1
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 422
        assert "images_qty" in str(response.json()["detail"][0]["loc"])

class TestModelPrediction:
    def test_predict_ml_model_success(self, client_with_model, valid_ad_payload, mock_model_manager):
        mock_model_manager.predict.return_value = {
            "is_violation": True,
            "probability": 0.75
        }
        
        payload = valid_ad_payload.copy()
        payload["description"] = "A very suspicious item description"
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "is_violation" in result
        assert "probability" in result
        assert result["is_violation"] is True
        assert result["probability"] == 0.75

    def test_predict_ml_model_false_prediction(self, client_with_model, valid_ad_payload, mock_model_manager):
        mock_model_manager.predict.return_value = {
            "is_violation": False,
            "probability": 0.25
        }
        
        payload = valid_ad_payload.copy()
        payload["description"] = "A normal item description"
        
        response = client_with_model.post("/predict", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_violation"] is False
        assert result["probability"] == 0.25

    def test_predict_ml_model_unavailable(self, client_with_unavailable_model, valid_ad_payload):
        response = client_with_unavailable_model.post("/predict", json=valid_ad_payload)
        
        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_predict_ml_model_prediction_error(self, client_with_model, valid_ad_payload, mock_model_manager):
        mock_model_manager.predict.side_effect = ValueError("Model prediction error")

        response = client_with_model.post("/predict", json=valid_ad_payload)

        assert response.status_code == 400
        assert "Model prediction error" in response.json()["detail"]


class TestSimplePredict:
    def test_simple_predict_positive_result(
        self, client_with_model, mock_ad_repository, mock_model_manager
    ):
        mock_ad_repository.get_with_user_by_id.return_value = {
            "is_verified": True,
            "images_qty": 2,
            "description": "Short text",
            "category": 1,
        }
        mock_model_manager.predict.return_value = {
            "is_violation": True,
            "probability": 0.8,
        }

        response = client_with_model.post("/simple_predict", json={"item_id": 1})

        assert response.status_code == 200
        result = response.json()
        assert result["is_violation"] is True
        assert result["probability"] == 0.8

    def test_simple_predict_negative_result(
        self, client_with_model, mock_ad_repository, mock_model_manager
    ):
        mock_ad_repository.get_with_user_by_id.return_value = {
            "is_verified": True,
            "images_qty": 5,
            "description": "Normal description",
            "category": 2,
        }
        mock_model_manager.predict.return_value = {
            "is_violation": False,
            "probability": 0.2,
        }

        response = client_with_model.post("/simple_predict", json={"item_id": 42})

        assert response.status_code == 200
        result = response.json()
        assert result["is_violation"] is False
        assert result["probability"] == 0.2

    def test_simple_predict_ad_not_found(self, client_with_model, mock_ad_repository):
        mock_ad_repository.get_with_user_by_id.return_value = None

        response = client_with_model.post("/simple_predict", json={"item_id": 999})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_simple_predict_validation_negative_item_id(
        self, client_with_model, mock_ad_repository
    ):
        response = client_with_model.post("/simple_predict", json={"item_id": -1})

        assert response.status_code == 422
        assert "item_id" in str(response.json()["detail"][0]["loc"])
