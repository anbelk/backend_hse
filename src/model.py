import pickle
import os
import logging
import asyncio
from typing import Dict, Any

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = "models/model.pkl"


class ModelManager:
    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, threshold: float = 0.5):
        self.model = None
        self.model_path = model_path
        self.threshold = threshold

    def load(self, path: str | None = None) -> None:
        path = path or self.model_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}. Run scripts/train_model.py first.")
        with open(path, "rb") as f:
            self.model = pickle.load(f)
        logger.info("Model loaded from %s", path)

    @staticmethod
    def prepare_features(
        is_verified_seller: bool,
        images_qty: int,
        description_length: int,
        category: int,
    ) -> np.ndarray:
        is_verified = float(is_verified_seller)
        images = min(images_qty, 10) / 10.0
        desc_len = min(description_length, 1000) / 1000.0
        cat = min(category, 100) / 100.0
        return np.array([[is_verified, images, desc_len, cat]])

    async def predict(
        self,
        is_verified_seller: bool,
        images_qty: int,
        description_length: int,
        category: int,
    ) -> Dict[str, Any]:
        if self.model is None:
            raise ValueError("Model is not loaded")

        features = self.prepare_features(
            is_verified_seller, images_qty, description_length, category
        )
        loop = asyncio.get_running_loop()
        violation_proba = await loop.run_in_executor(
            None,
            lambda: self.model.predict_proba(features)[0, 1],
        )
        is_violation = violation_proba > self.threshold
        return {
            "is_violation": is_violation,
            "probability": float(violation_proba),
        }

    async def initialize(self) -> None:
        try:
            self.load()
            logger.info("Model initialized")
        except Exception as e:
            logger.critical("Model init failed: %s", e)
            raise
