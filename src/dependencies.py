import logging

from fastapi import HTTPException, Request

from src.clients.kafka import KafkaProducerClient
from src.model import ModelManager
from src.repositories import AdRepository, ModerationRepository, UserRepository

logger = logging.getLogger(__name__)


async def get_model_manager(request: Request) -> ModelManager:
    model_manager = getattr(request.app.state, "model_manager", None)

    if model_manager is None or model_manager.model is None:
        logger.error("Model manager not initialized")
        raise HTTPException(status_code=503, detail="Model service is not available")

    return model_manager


async def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.user_repository


async def get_ad_repository(request: Request) -> AdRepository:
    return request.app.state.ad_repository


async def get_moderation_repository(request: Request) -> ModerationRepository:
    return request.app.state.moderation_repository


async def get_kafka_producer(request: Request) -> KafkaProducerClient:
    return request.app.state.kafka_producer
