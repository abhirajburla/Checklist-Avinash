"""
JSON Storage Utility for Gemini API Responses
Stores all Gemini API responses for later processing and debugging
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class JSONStorage:
    """Store and manage Gemini API JSON responses"""
    
    def __init__(self):
        self.config = Config()
        self.storage_folder = Path(self.config.JSON_STORAGE_FOLDER)
        self.storage_folder.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.responses_folder = self.storage_folder / "responses"
        self.failed_folder = self.storage_folder / "failed"
        self.combined_folder = self.storage_folder / "combined"
        
        for folder in [self.responses_folder, self.failed_folder, self.combined_folder]:
            folder.mkdir(exist_ok=True)
        
        logger.info(f"JSONStorage initialized with folder: {self.storage_folder}")
    
    def store_response(
        self, 
        response_text: str, 
        batch_index: int, 
        operation: str = "checklist_matching",
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Store a Gemini API response"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if session_id is None:
                session_id = f"session_{int(time.time())}"
            
            # Determine folder based on success
            folder = self.responses_folder if success else self.failed_folder
            
            # Create filename
            filename = f"{operation}_batch_{batch_index:03d}_{timestamp}_{session_id}.json"
            filepath = folder / filename
            
            # Prepare storage data
            storage_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "batch_index": batch_index,
                    "operation": operation,
                    "success": success,
                    "session_id": session_id,
                    "filepath": str(filepath)
                },
                "response_text": response_text,
                "custom_metadata": metadata or {}
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Stored {operation} response for batch {batch_index} at {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error storing JSON response: {e}")
            return ""
    
    def store_failed_response(
        self, 
        response_text: str, 
        batch_index: int, 
        error: str,
        operation: str = "checklist_matching",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Store a failed Gemini API response with error details"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if session_id is None:
                session_id = f"session_{int(time.time())}"
            
            filename = f"failed_{operation}_batch_{batch_index:03d}_{timestamp}_{session_id}.json"
            filepath = self.failed_folder / filename
            
            # Prepare storage data
            storage_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "batch_index": batch_index,
                    "operation": operation,
                    "success": False,
                    "session_id": session_id,
                    "filepath": str(filepath),
                    "error": error
                },
                "response_text": response_text,
                "error_details": {
                    "error_message": error,
                    "response_length": len(response_text) if response_text else 0,
                    "has_json_start": response_text.startswith('{') if response_text else False,
                    "has_json_end": response_text.endswith('}') if response_text else False
                },
                "custom_metadata": metadata or {}
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Stored failed {operation} response for batch {batch_index} at {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error storing failed JSON response: {e}")
            return ""
    
    def combine_responses(self, session_id: str, operation: str = "checklist_matching") -> str:
        """Combine all responses from a session into a single file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_{operation}_{session_id}_{timestamp}.json"
            filepath = self.combined_folder / filename
            
            # Find all response files for this session
            response_files = []
            
            # Search in responses folder
            for file in self.responses_folder.glob(f"*{session_id}*.json"):
                response_files.append(file)
            
            # Search in failed folder
            for file in self.failed_folder.glob(f"*{session_id}*.json"):
                response_files.append(file)
            
            # Sort by batch index
            response_files.sort(key=lambda x: int(x.stem.split('_batch_')[1].split('_')[0]))
            
            # Combine all responses
            combined_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "operation": operation,
                    "total_files": len(response_files),
                    "filepath": str(filepath)
                },
                "responses": []
            }
            
            for file in response_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        combined_data["responses"].append(data)
                except Exception as e:
                    logger.warning(f"Error reading file {file}: {e}")
            
            # Save combined file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Combined {len(response_files)} responses into {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error combining responses: {e}")
            return ""
    
    def get_session_responses(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a specific session"""
        try:
            responses = []
            
            # Search in both folders
            for folder in [self.responses_folder, self.failed_folder]:
                for file in folder.glob(f"*{session_id}*.json"):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            responses.append(data)
                    except Exception as e:
                        logger.warning(f"Error reading file {file}: {e}")
            
            # Sort by batch index
            responses.sort(key=lambda x: x.get("metadata", {}).get("batch_index", 0))
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting session responses: {e}")
            return []
    
    def cleanup_old_files(self, days: int = 7) -> int:
        """Clean up files older than specified days"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            for folder in [self.responses_folder, self.failed_folder, self.combined_folder]:
                for file in folder.glob("*.json"):
                    if file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old JSON files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                "total_responses": len(list(self.responses_folder.glob("*.json"))),
                "total_failed": len(list(self.failed_folder.glob("*.json"))),
                "total_combined": len(list(self.combined_folder.glob("*.json"))),
                "storage_size_mb": 0,
                "folders": {
                    "responses": str(self.responses_folder),
                    "failed": str(self.failed_folder),
                    "combined": str(self.combined_folder)
                }
            }
            
            # Calculate total size
            total_size = 0
            for folder in [self.responses_folder, self.failed_folder, self.combined_folder]:
                for file in folder.glob("*.json"):
                    total_size += file.stat().st_size
            
            stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {} 