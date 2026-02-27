from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import Annotated

from src.schemas import (
    AdModerationRequestSchema,
    AdModerationResponseSchema,
    SimplePredictRequestSchema,
)
from src.model import ModelManager
from src.dependencies import get_model_manager, get_ad_repository
from src.repositories import AdRepository

router = APIRouter()
logger = logging.getLogger(__name__)

ModelManagerDep = Annotated[ModelManager, Depends(get_model_manager)]
AdRepositoryDep = Annotated[AdRepository, Depends(get_ad_repository)]

@router.post("/predict", response_model=AdModerationResponseSchema)
async def predict(ad: AdModerationRequestSchema, model_manager: ModelManagerDep):
    try:
        logger.info("Processing seller_id=%s item_id=%s", ad.seller_id, ad.item_id)
        description_length = len(ad.description)
        logger.info(
            "Features is_verified=%s images_qty=%s description_length=%s category=%s",
            ad.is_verified_seller,
            ad.images_qty,
            description_length,
            ad.category,
        )
        result = await model_manager.predict(
            ad.is_verified_seller,
            ad.images_qty,
            description_length,
            ad.category
        )
        logger.info(
            "Prediction is_violation=%s probability=%s",
            result["is_violation"],
            result["probability"],
        )
        return result
    except ValueError as e:
        logger.error("Value error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
        raise HTTPException(status_code=404, detail="Ad not found")

    result = await model_manager.predict(
        row["is_verified"],
        row["images_qty"],
        len(row["description"]),
        row["category"],
    )
    return result
