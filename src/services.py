from src.schemas import AdModerationRequest

def moderate_ad(ad: AdModerationRequest) -> bool:
    if ad.is_verified_seller or ad.images_qty > 0:
        return True
    else:
        return False
