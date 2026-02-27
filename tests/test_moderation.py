"""Tests for async moderation endpoints."""


class TestAsyncPredict:
    def test_async_predict_creates_task_and_returns_task_id(
        self,
        client_with_model,
        mock_ad_repository,
        mock_moderation_repository,
        mock_kafka_producer_dep,
    ):
        mock_ad_repository.get_with_user_by_id.return_value = {
            "is_verified": True,
            "images_qty": 2,
            "description": "Text",
            "category": 1,
        }
        mock_moderation_repository.create_pending.return_value = 123

        response = client_with_model.post("/async_predict", json={"item_id": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 123
        assert data["status"] == "pending"
        assert "accepted" in data["message"].lower()
        mock_moderation_repository.create_pending.assert_called_once_with(item_id=1)
        mock_kafka_producer_dep.send_moderation_request.assert_called_once_with(1)

    def test_async_predict_ad_not_found(
        self, client_with_model, mock_ad_repository
    ):
        mock_ad_repository.get_with_user_by_id.return_value = None

        response = client_with_model.post("/async_predict", json={"item_id": 999})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_async_predict_validation_negative_item_id(
        self, client_with_model
    ):
        response = client_with_model.post("/async_predict", json={"item_id": -1})

        assert response.status_code == 422


class TestModerationResult:
    def test_moderation_result_pending(
        self, client_with_model, mock_moderation_repository
    ):
        mock_moderation_repository.get_by_id.return_value = {
            "id": 42,
            "status": "pending",
            "is_violation": None,
            "probability": None,
            "error_message": None,
        }

        response = client_with_model.get("/moderation_result/42")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 42
        assert data["status"] == "pending"
        assert data["is_violation"] is None
        assert data["probability"] is None

    def test_moderation_result_completed(
        self, client_with_model, mock_moderation_repository
    ):
        mock_moderation_repository.get_by_id.return_value = {
            "id": 42,
            "status": "completed",
            "is_violation": True,
            "probability": 0.87,
            "error_message": None,
        }

        response = client_with_model.get("/moderation_result/42")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 42
        assert data["status"] == "completed"
        assert data["is_violation"] is True
        assert data["probability"] == 0.87

    def test_moderation_result_failed(
        self, client_with_model, mock_moderation_repository
    ):
        mock_moderation_repository.get_by_id.return_value = {
            "id": 42,
            "status": "failed",
            "is_violation": None,
            "probability": None,
            "error_message": "Ad not found",
        }

        response = client_with_model.get("/moderation_result/42")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Ad not found"

    def test_moderation_result_not_found(
        self, client_with_model, mock_moderation_repository
    ):
        mock_moderation_repository.get_by_id.return_value = None

        response = client_with_model.get("/moderation_result/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
