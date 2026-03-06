from pydantic import BaseModel, Field

class AdModerationRequestSchema(BaseModel):
    seller_id: int = Field(..., gt=0)
    is_verified_seller: bool
    item_id: int = Field(..., gt=0)
    name: str
    description: str
    category: int
    images_qty: int = Field(..., ge=0)

class AdModerationResponseSchema(BaseModel):
    is_violation: bool
    probability: float = Field(..., ge=0.0, le=1.0)


class SimplePredictRequestSchema(BaseModel):
    item_id: int = Field(..., gt=0)


class AsyncPredictRequestSchema(BaseModel):
    item_id: int = Field(..., gt=0)


class AsyncPredictResponseSchema(BaseModel):
    task_id: int
    status: str = "pending"
    message: str = "Moderation request accepted"


class ModerationResultResponseSchema(BaseModel):
    task_id: int
    status: str
    is_violation: bool | None = None
    probability: float | None = None
    error_message: str | None = None
