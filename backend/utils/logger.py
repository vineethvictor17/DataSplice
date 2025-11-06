"""
Simple logging configuration for the backend.
"""

import logging
import sys

def setup_logger(name: str = "datasplice") -> logging.Logger:
    """
    Create and configure a logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Default logger instance
logger = setup_logger()

