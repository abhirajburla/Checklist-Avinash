import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration management for the checklist matching system"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Gemini API configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    # Only raise error if not in test mode
    if not GEMINI_API_KEY and not os.getenv('TEST_MODE'):
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
    
    # Model configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 800 * 1024 * 1024  # 800MB max file size
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Processing configuration
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))  # Process 50 checklist items at a time
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

    # Timeout configuration
    GEMINI_API_TIMEOUT = int(os.getenv('GEMINI_API_TIMEOUT', '300'))  # 5 minutes for Gemini API calls
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', '3600'))  # 60 minutes for overall processing
    BATCH_TIMEOUT = int(os.getenv('BATCH_TIMEOUT', '600'))  # 10 minutes per batch
    UPLOAD_TIMEOUT = int(os.getenv('UPLOAD_TIMEOUT', '300'))  # 5 minutes for file uploads

    # JSON storage configuration
    ENABLE_JSON_STORAGE = os.getenv('ENABLE_JSON_STORAGE', 'true').lower() == 'true'
    JSON_STORAGE_FOLDER = os.getenv('JSON_STORAGE_FOLDER', 'json_outputs')

    # Gemini model configuration
    GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '65536'))  # 64K tokens for large JSON responses
    
    # Phase 3 Enhanced Processing Configuration
    ENABLE_SYSTEM_INSTRUCTIONS = os.getenv('ENABLE_SYSTEM_INSTRUCTIONS', 'true').lower() == 'true'
    ENABLE_REFERENCE_VALIDATION = os.getenv('ENABLE_REFERENCE_VALIDATION', 'true').lower() == 'true'
    ENABLE_ENHANCED_BATCH_PROCESSING = os.getenv('ENABLE_ENHANCED_BATCH_PROCESSING', 'true').lower() == 'true'
    
    # Phase 4 Output Generation Configuration
    ENABLE_PROGRESS_TRACKING = os.getenv('ENABLE_PROGRESS_TRACKING', 'true').lower() == 'true'
    ENABLE_JSON_OUTPUT = os.getenv('ENABLE_JSON_OUTPUT', 'true').lower() == 'true'
    ENABLE_DOWNLOAD_FUNCTIONALITY = os.getenv('ENABLE_DOWNLOAD_FUNCTIONALITY', 'true').lower() == 'true'
    
    # Enhanced batch processing configuration
    MAX_CONCURRENT_BATCHES = int(os.getenv('MAX_CONCURRENT_BATCHES', '3'))
    BATCH_RETRY_DELAY = float(os.getenv('BATCH_RETRY_DELAY', '5.0'))  # Increased to 5s
    BATCH_BACKOFF_FACTOR = float(os.getenv('BATCH_BACKOFF_FACTOR', '3.0'))  # Increased to 3.0
    
    # Reference validation configuration
    MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', '0.7'))
    VALIDATION_STRICTNESS = os.getenv('VALIDATION_STRICTNESS', 'medium')  # low, medium, high
    
    # Cache configuration
    CACHE_FOLDER = os.getenv('CACHE_FOLDER', 'cache')
    RESULTS_FOLDER = os.getenv('RESULTS_FOLDER', 'results')
    
    # Context caching configuration
    ENABLE_CONTEXT_CACHING = os.getenv('ENABLE_CONTEXT_CACHING', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour cache TTL
    
    # Master checklist configuration
    MASTER_CHECKLIST_PATH = os.getenv('MASTER_CHECKLIST_PATH', 'MASTER TEMP.csv')
    
    # Document processing configuration
    MAX_DOCUMENT_PAGES = int(os.getenv('MAX_DOCUMENT_PAGES', '1000'))  # Gemini limit
    TOKENS_PER_PAGE = int(os.getenv('TOKENS_PER_PAGE', '258'))  # Gemini standard
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        if not filename:
            return False
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def get_file_size_limit_mb(self) -> float:
        """Get file size limit in MB"""
        return self.MAX_CONTENT_LENGTH / (1024 * 1024)
    
    # Token tracking configuration
    ENABLE_TOKEN_TRACKING = os.getenv('ENABLE_TOKEN_TRACKING', 'true').lower() == 'true'
    TOKEN_TRACKING_LOG_FILE = os.getenv('TOKEN_TRACKING_LOG_FILE', 'logs/token_usage.log')
    LOG_TOKEN_USAGE = os.getenv('LOG_TOKEN_USAGE', 'true').lower() == 'true'
    LOG_COST_BREAKDOWN = os.getenv('LOG_COST_BREAKDOWN', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        errors = []
        
        if not cls.GEMINI_API_KEY and not os.getenv('TEST_MODE'):
            errors.append("GEMINI_API_KEY or GOOGLE_API_KEY is required")
        
        if not os.path.exists(cls.MASTER_CHECKLIST_PATH) and not os.getenv('TEST_MODE'):
            errors.append(f"Master checklist file not found: {cls.MASTER_CHECKLIST_PATH}")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True 