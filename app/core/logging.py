"""Configure application logging with loguru."""
import os
import sys
from loguru import logger
from app.core.config import Settings

def configure_logging(settings: Settings) -> None:
    """Configure loguru logger with application settings."""
    # Remove default handler
    logger.remove()
    
    # Add stdout handler with the configured log level
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler for persistent logging
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/agent.log",
        rotation="10 MB",  # Rotate file at 10MB
        compression="zip",  # Compress rotated files
        retention="1 week",  # Keep logs for 1 week
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        level=settings.log_level
    )
    
    # Configure error reporting
    logger.add(
        "logs/errors.log",
        rotation="1 day",
        compression="zip",
        retention="1 month",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        level="ERROR",
        filter=lambda record: record["level"].name == "ERROR"
    )
    
    # Log startup configuration
    logger.info(f"Logging configured with level: {settings.log_level}")
    logger.info(f"Log files will be stored in: {os.path.abspath('logs')}")
