"""
Main application entry point
"""
import asyncio
import uvicorn
from contextlib import asynccontextmanager

from .logger import logger
from .database import init_db
from .scheduler import scheduler
from .api import app
from .config import Config


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Alarm Application...")
    
    # Initialize database
    init_db()
    
    # Start scheduler
    await scheduler.start()
    
    logger.info(f"API server running on {Config.API_HOST}:{Config.API_PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await scheduler.stop()


# Attach lifespan to app
app.router.lifespan_context = lifespan


def main():
    """Main application entry point"""
    uvicorn.run(
        "app.api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level="info",
        lifespan="on"
    )


if __name__ == "__main__":
    main()
