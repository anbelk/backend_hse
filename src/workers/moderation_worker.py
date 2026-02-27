import asyncio
import json
import logging
import signal

import asyncpg
from aiokafka import AIOKafkaConsumer

from src.clients.kafka import KafkaProducerClient, create_kafka_producer
from src.config import Settings
from src.model import ModelManager
from src.repositories import AdRepository, ModerationRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def process_message(
    payload: dict,
    ad_repository: AdRepository,
    moderation_repository: ModerationRepository,
    model_manager: ModelManager,
    dlq_producer: KafkaProducerClient,
) -> None:
    item_id = payload.get("item_id")
    if item_id is None:
        raise ValueError(f"Missing item_id in message: {payload}")

    task_id = await moderation_repository.get_oldest_pending_by_item_id(item_id)
    if task_id is None:
        raise ValueError(f"No pending task for item_id={item_id}")

    row = await ad_repository.get_with_user_by_id(item_id)
    if row is None:
        error_msg = f"Ad not found: item_id={item_id}"
        await moderation_repository.update_failed(task_id, error_msg)
        await dlq_producer.send_to_dlq(payload, error_msg, retry_count=1)
        return

    result = await model_manager.predict(
        row["is_verified"],
        row["images_qty"],
        len(row["description"]),
        row["category"],
    )
    await moderation_repository.update_completed(
        task_id,
        is_violation=bool(result["is_violation"]),
        probability=float(result["probability"]),
    )
    logger.info("Processed task_id=%s item_id=%s", task_id, item_id)


async def run_worker() -> None:
    settings = Settings()
    pool = await asyncpg.create_pool(
        settings.database_dsn, min_size=1, max_size=5
    )
    ad_repository = AdRepository(pool)
    moderation_repository = ModerationRepository(pool)

    model_manager = ModelManager()
    await model_manager.initialize()

    dlq_producer = create_kafka_producer(settings, include_dlq=True)
    await dlq_producer.start()

    consumer = AIOKafkaConsumer(
        settings.kafka_moderation_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        group_id="moderation-worker",
        auto_offset_reset="earliest",
    )
    await consumer.start()

    shutdown = asyncio.Event()

    def on_signal() -> None:
        shutdown.set()

    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, on_signal)
        loop.add_signal_handler(signal.SIGINT, on_signal)
    except NotImplementedError:
        pass

    logger.info("Worker started, topic=%s", settings.kafka_moderation_topic)

    try:
        async for msg in consumer:
            if shutdown.is_set():
                break
            try:
                payload = json.loads(msg.value.decode())
            except json.JSONDecodeError as e:
                raw = msg.value.decode(errors="replace") if msg.value else ""
                try:
                    await dlq_producer.send_to_dlq(
                        {"raw": raw}, f"Invalid JSON: {e}", retry_count=0
                    )
                except Exception as send_err:
                    logger.exception("Failed to send invalid JSON to DLQ: %s", send_err)
                continue

            for attempt in range(1, settings.worker_max_retries + 1):
                try:
                    await process_message(
                        payload,
                        ad_repository,
                        moderation_repository,
                        model_manager,
                        dlq_producer,
                    )
                    break
                except ValueError as e:
                    error_msg = str(e)
                    task_id = await moderation_repository.get_oldest_pending_by_item_id(
                        payload.get("item_id") or 0
                    )
                    try:
                        if task_id is not None:
                            await moderation_repository.update_failed(task_id, error_msg)
                        await dlq_producer.send_to_dlq(payload, error_msg, retry_count=attempt)
                    except Exception as dlq_err:
                        logger.exception("Failed to update failed status or send to DLQ: %s", dlq_err)
                    break
                except Exception as e:
                    if attempt < settings.worker_max_retries:
                        logger.warning("Retry attempt %s: %s", attempt, e)
                        await asyncio.sleep(settings.worker_retry_delay_seconds)
                    else:
                        task_id = await moderation_repository.get_oldest_pending_by_item_id(
                            payload.get("item_id") or 0
                        )
                        try:
                            if task_id is not None:
                                await moderation_repository.update_failed(task_id, str(e))
                            await dlq_producer.send_to_dlq(
                                payload, str(e), retry_count=attempt
                            )
                        except Exception as dlq_err:
                            logger.exception("Failed to update failed status or send to DLQ: %s", dlq_err)
    finally:
        await consumer.stop()
        await dlq_producer.stop()
        await pool.close()
        logger.info("Worker stopped")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
