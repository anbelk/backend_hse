from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os

import asyncpg

from src.model import ModelManager
from src.routes import prediction, health
from src.repositories import UserRepository, AdRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = None
    try:
        logger.info("Initializing model manager...")
        model_manager = ModelManager()
        await model_manager.initialize()
        app.state.model_manager = model_manager

        dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ad_moderation")
        if "?" in dsn:
            dsn = dsn.split("?")[0]
        pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
        app.state.user_repository = UserRepository(pool)
        app.state.ad_repository = AdRepository(pool)

        logger.info("Model manager and database initialized successfully")
    except Exception as e:
        logger.critical(f"Critical failure: {str(e)}")
        raise

    yield

    if pool:
        await pool.close()
    logger.info("Shutting down application")

app = FastAPI(
    title="Ad Moderation Service",
    description="ML-powered service for detecting violations in advertisements",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to Ad Moderation Service API"}

app.include_router(health.router)
app.include_router(prediction.router)
