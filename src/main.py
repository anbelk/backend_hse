from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from src.model import ModelManager
from src.routes import prediction, health

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing model manager...")
        model_manager = ModelManager()
        await model_manager.initialize()
        
        app.state.model_manager = model_manager
        
        logger.info("Model manager initialized successfully")
    except Exception as e:
        logger.critical(f"Critical failure: Model could not be initialized: {str(e)}")
        raise
    
    yield
    
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
