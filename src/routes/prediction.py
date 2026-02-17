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
        logger.info(f"Processing request: seller_id={ad.seller_id}, item_id={ad.item_id}")
        
        description_length = len(ad.description)
        
        logger.info(
            f"Input features: is_verified={ad.is_verified_seller}, "
            f"images_qty={ad.images_qty}, description_length={description_length}, "
            f"category={ad.category}"
        )
        
        result = await model_manager.predict(
            ad.is_verified_seller,
            ad.images_qty,
            description_length,
            ad.category
        )
        
        logger.info(
            f"Prediction result: is_violation={result['is_violation']}, "
            f"probability={result['probability']}"
        )
        
        return result
    
    except ValueError as e:
        logger.error(f"Value error during prediction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
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
