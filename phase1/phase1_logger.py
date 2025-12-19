"""
Phase 1 Logging Module

Structured logging setup for Phase 1 exploration engine.
"""

import logging
import sys
from typing import Optional
from datetime import datetime

__version__ = "1.0.0"


class Phase1Logger:
    """Structured logging setup for Phase 1."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        format_type: str = "text"
    ) -> None:
        """
        Setup logging configuration.
        
        Args:
            log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
            log_file: Optional file to write logs to
            format_type: "text" or "json"
        """
        if self._initialized:
            return
        
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        
        # Formatter
        if format_type == "json":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self._initialized = True
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (usually __name__)
        
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(name)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    format_type: str = "text"
) -> None:
    """
    Setup phase 1 logging.
    
    Example:
        setup_logging("DEBUG", log_file="phase1.log")
        logger = logging.getLogger(__name__)
        logger.info("Message")
    
    Args:
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file: Optional file path for logs
        format_type: "text" or "json" format
    """
    logger_instance = Phase1Logger()
    logger_instance.setup(log_level, log_file, format_type)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Logger instance
    """
    return Phase1Logger.get_logger(name)
