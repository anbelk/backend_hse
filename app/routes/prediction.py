import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import (
    AdModerationRequestSchema,
    AdModerationResponseSchema,
    SimplePredictRequestSchema,
)
from app.model import ModelManager
from app.dependencies import get_model_manager, get_ad_repository
from app.repositories import AdRepository
from app.exceptions import ModelIsNotAvailable, ErrorInPrediction, AdvertisementNotFoundError
from app.telemetry.sentry import capture_exception

router = APIRouter()
logger = logging.getLogger(__name__)

ModelManagerDep = Annotated[ModelManager, Depends(get_model_manager)]
AdRepositoryDep = Annotated[AdRepository, Depends(get_ad_repository)]


@router.post("/predict", response_model=AdModerationResponseSchema)
async def predict(ad: AdModerationRequestSchema, model_manager: ModelManagerDep):
    try:
        logger.info("Processing seller_id=%s item_id=%s", ad.seller_id, ad.item_id)
        description_length = len(ad.description)
        result = await model_manager.predict(
            ad.is_verified_seller,
            ad.images_qty,
            description_length,
            ad.category,
        )
        logger.info(
            "Prediction is_violation=%s probability=%s",
            result["is_violation"],
            result["probability"],
        )
        return result
    except ModelIsNotAvailable as e:
        capture_exception(e)
        logger.error("Model unavailable: %s", e)
        raise HTTPException(status_code=503, detail="Model service is not available")
    except ErrorInPrediction as e:
        capture_exception(e)
        logger.error("Prediction error: %s", e)
        raise HTTPException(status_code=500, detail="Error making prediction")


@router.post("/simple_predict", response_model=AdModerationResponseSchema)
async def simple_predict(
    body: SimplePredictRequestSchema,
    model_manager: ModelManagerDep,
    ad_repository: AdRepositoryDep,
):
    row = await ad_repository.get_with_user_by_id(body.item_id)
    if row is None:
        exc = AdvertisementNotFoundError(body.item_id)
        capture_exception(exc)
        raise HTTPException(status_code=404, detail="Ad not found")

    try:
        result = await model_manager.predict(
            row["is_verified"],
            row["images_qty"],
            len(row["description"]),
            row["category"],
        )
    except ModelIsNotAvailable as e:
        capture_exception(e)
        raise HTTPException(status_code=503, detail="Model service is not available")
    except ErrorInPrediction as e:
        capture_exception(e)
        raise HTTPException(status_code=500, detail="Error making prediction")

    return result
