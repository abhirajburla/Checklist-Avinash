"""
Centralized Logging Configuration
Provides consistent logging setup across the entire application
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

class LoggerConfig:
    """Centralized logging configuration for the application"""
    
    # Log levels
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    @classmethod
    def setup_logging(cls, 
                     log_level: str = 'INFO',
                     log_file: Optional[str] = None,
                     console_output: bool = True,
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5) -> None:
        """
        Setup centralized logging configuration
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            console_output: Whether to output to console
            max_file_size: Maximum log file size in bytes
            backup_count: Number of backup log files to keep
        """
        
        # Get log level
        level = cls.LOG_LEVELS.get(log_level.upper(), logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Create handlers list
        handlers = []
        
        # Console handler (if enabled)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(simple_formatter)
            handlers.append(console_handler)
        
        # File handler (if specified)
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(detailed_formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add new handlers
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Set specific logger levels
        cls._configure_specific_loggers(level)
        
        # Log the setup
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Level: {log_level}, File: {log_file or 'None'}, Console: {console_output}")
    
    @classmethod
    def _configure_specific_loggers(cls, level: int) -> None:
        """Configure specific loggers with appropriate levels"""
        
        # Reduce noise from external libraries
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('google').setLevel(logging.WARNING)
        logging.getLogger('google.generativeai').setLevel(logging.WARNING)
        
        # Set application loggers to specified level
        app_loggers = [
            'src',
            'app',
            'checklist_processor',
            'document_handler', 
            'gemini_client',
            'matching_engine',
            'enhanced_batch_processor',
            'reference_validator',
            'output_generator',
            'config',
            'prompt_templates',
            'system_instructions',
            'schemas'
        ]
        
        for logger_name in app_loggers:
            logging.getLogger(logger_name).setLevel(level)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)
    
    @classmethod
    def setup_from_config(cls, config) -> None:
        """Setup logging from configuration object"""
        log_level = getattr(config, 'LOG_LEVEL', 'INFO')
        log_file = getattr(config, 'LOG_FILE', None)
        
        cls.setup_logging(
            log_level=log_level,
            log_file=log_file,
            console_output=True
        )

# Default setup function
def setup_default_logging():
    """Setup default logging configuration"""
    LoggerConfig.setup_logging(
        log_level='INFO',
        console_output=True
    )

# Export the main class and function
__all__ = ['LoggerConfig', 'setup_default_logging'] 