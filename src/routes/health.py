from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.dependencies import get_model_manager
from src.model import ModelManager

router = APIRouter(tags=["health"])

@router.get("/health", response_model=Dict[str, Any])
async def health_check(model_manager: ModelManager = Depends(get_model_manager)):
    return {
        "status": "healthy",
        "model_loaded": True
    }
