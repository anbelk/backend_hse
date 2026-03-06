class ModelIsNotAvailable(Exception):
    pass


class ErrorInPrediction(Exception):
    pass


class AdvertisementNotFoundError(Exception):
    def __init__(self, item_id: int) -> None:
        super().__init__(f"Advertisement not found: item_id={item_id}")
        self.item_id = item_id
