"""
Logging setup with Logtail integration
"""
import logging
import os
import sys
from typing import Optional

try:
    from logtail import LogtailHandler
    LOGTAIL_AVAILABLE = True
except ImportError:
    LOGTAIL_AVAILABLE = False


def setup_logger() -> logging.Logger:
    """Setup logger with Logtail integration"""
    logger = logging.getLogger("alarms")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - Alarms: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Logtail handler
    logtail_token = os.getenv("LOGTAIL_TOKEN", "MD82ZsA4UX7nf4CSTvadtvfo")
    if logtail_token and LOGTAIL_AVAILABLE:
        try:
            logtail_handler = LogtailHandler(source_token=logtail_token)
            logtail_formatter = logging.Formatter('Alarms: %(message)s')
            logtail_handler.setFormatter(logtail_formatter)
            logger.addHandler(logtail_handler)
            logger.info("Logtail logging enabled")
        except Exception as e:
            logger.warning(f"Failed to setup Logtail: {e}")
    elif logtail_token and not LOGTAIL_AVAILABLE:
        logger.warning("Logtail token provided but logtail package not installed")
    
    return logger


# Global logger instance
logger = setup_logger()
