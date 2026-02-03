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
