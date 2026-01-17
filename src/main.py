from fastapi import FastAPI
from src.schemas import AdModerationRequest, AdModerationResponse


app = FastAPI()

@app.post("/predict", response_model=AdModerationResponse)
async def predict(ad: AdModerationRequest):
    if ad.is_verified_seller or ad.images_qty > 0:
        is_approved = True
    else:
        is_approved = False
    return AdModerationResponse(is_approved=is_approved)