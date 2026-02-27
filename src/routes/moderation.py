from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.schemas import (
    AsyncPredictRequestSchema,
    AsyncPredictResponseSchema,
    ModerationResultResponseSchema,
)
from src.clients.kafka import KafkaProducerClient
from src.repositories import AdRepository, ModerationRepository
from src.dependencies import get_ad_repository, get_moderation_repository, get_kafka_producer

router = APIRouter()

AdRepositoryDep = Annotated[AdRepository, Depends(get_ad_repository)]
ModerationRepositoryDep = Annotated[ModerationRepository, Depends(get_moderation_repository)]
KafkaProducerDep = Annotated[KafkaProducerClient, Depends(get_kafka_producer)]


@router.post("/async_predict", response_model=AsyncPredictResponseSchema)
async def async_predict(
    body: AsyncPredictRequestSchema,
    ad_repository: AdRepositoryDep,
    moderation_repository: ModerationRepositoryDep,
    kafka_producer: KafkaProducerDep,
) -> AsyncPredictResponseSchema:
    row = await ad_repository.get_with_user_by_id(body.item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Ad not found")

    task_id = await moderation_repository.create_pending(item_id=body.item_id)
    await kafka_producer.send_moderation_request(body.item_id)

    return AsyncPredictResponseSchema(
        task_id=task_id,
        status="pending",
        message="Moderation request accepted",
    )


@router.get("/moderation_result/{task_id}", response_model=ModerationResultResponseSchema)
async def get_moderation_result(
    task_id: int,
    moderation_repository: ModerationRepositoryDep,
) -> ModerationResultResponseSchema:
    row = await moderation_repository.get_by_id(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return ModerationResultResponseSchema(
        task_id=row["id"],
        status=row["status"],
        is_violation=row["is_violation"],
        probability=float(row["probability"]) if row["probability"] is not None else None,
        error_message=row["error_message"],
    )
