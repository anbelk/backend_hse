from fastapi import Request, HTTPException
import logging

from src.repositories import UserRepository, AdRepository

logger = logging.getLogger(__name__)


async def get_model_manager(request: Request):
    model_manager = getattr(request.app.state, "model_manager", None)

    if model_manager is None or model_manager.model is None:
        logger.error("Model manager not initialized in app.state")
        raise HTTPException(status_code=503, detail="Model service is not available")

    return model_manager


async def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.user_repository


async def get_ad_repository(request: Request) -> AdRepository:
    return request.app.state.ad_repository
