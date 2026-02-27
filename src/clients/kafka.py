import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

from src.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModerationMessage:
    item_id: int
    timestamp: str

    def to_json(self) -> str:
        return json.dumps({"item_id": self.item_id, "timestamp": self.timestamp})


class KafkaProducerClient:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        dlq_topic: str | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers.split(",")
        self._topic = topic
        self._dlq_topic = dlq_topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
        logger.info("Kafka producer stopped")

    async def send_moderation_request(self, item_id: int) -> None:
        if self._producer is None:
            raise RuntimeError("Producer not started")
        message = ModerationMessage(
            item_id=item_id,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        await self._producer.send_and_wait(self._topic, message.to_json().encode())
        logger.info("Sent moderation request item_id=%s", item_id)

    async def send_to_dlq(
        self,
        original_message: dict,
        error: str,
        retry_count: int = 1,
    ) -> None:
        if self._producer is None or self._dlq_topic is None:
            raise RuntimeError("Producer or DLQ not configured")
        payload = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "retry_count": retry_count,
        }
        await self._producer.send_and_wait(
            self._dlq_topic, json.dumps(payload).encode()
        )
        logger.warning("Sent to DLQ: %s", error)


def create_kafka_producer(
    settings: Settings | None = None,
    include_dlq: bool = False,
) -> KafkaProducerClient:
    settings = settings or Settings()
    return KafkaProducerClient(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_moderation_topic,
        dlq_topic=settings.kafka_dlq_topic if include_dlq else None,
    )
