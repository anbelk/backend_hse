from contextlib import asynccontextmanager
import logging

import asyncpg
from fastapi import FastAPI

from app.config import Settings
from app.model import ModelManager
from app.routes import prediction, health, moderation
from app.repositories import UserRepository, AdRepository, ModerationRepository
from app.clients.kafka import create_kafka_producer
from app.telemetry.middleware import PrometheusMiddleware, metrics_endpoint
from app.telemetry.sentry import init_sentry

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    pool = None
    kafka_producer = None

    init_sentry(settings.sentry_dsn, settings.environment)

    try:
        model_manager = ModelManager()
        await model_manager.initialize()
        app.state.model_manager = model_manager

        pool = await asyncpg.create_pool(
            settings.database_dsn, min_size=2, max_size=10
        )
        app.state.user_repository = UserRepository(pool)
        app.state.ad_repository = AdRepository(pool)
        app.state.moderation_repository = ModerationRepository(pool)

        kafka_producer = create_kafka_producer(settings)
        await kafka_producer.start()
        app.state.kafka_producer = kafka_producer

        logger.info("Application started")
    except Exception as e:
        logger.critical("Critical failure: %s", str(e))
        raise

    yield

    if kafka_producer:
        await kafka_producer.stop()
    if pool:
        await pool.close()
    logger.info("Application stopped")


app = FastAPI(
    title="Ad Moderation Service",
    description="ML-powered service for detecting violations in advertisements",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware)

app.get("/metrics", include_in_schema=False)(metrics_endpoint)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to Ad Moderation Service API"}


app.include_router(health.router)
app.include_router(prediction.router)
app.include_router(moderation.router)
