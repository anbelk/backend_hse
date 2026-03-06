from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.dependencies import get_model_manager
from app.model import ModelManager

router = APIRouter(tags=["health"])

@router.get("/health", response_model=Dict[str, Any])
async def health_check(model_manager: ModelManager = Depends(get_model_manager)):
    return {
        "status": "healthy",
        "model_loaded": True
    }
