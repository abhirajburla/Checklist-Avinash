import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class JSONCombiner:
    """Combine all JSON outputs (successful and failed) into a single, well-parsed JSON file"""
    
    def __init__(self):
        self.config = Config()
        self.json_storage = self.config.JSON_STORAGE_FOLDER
        
    def combine_all_json_outputs(self, session_id: str, process_id: str) -> Dict[str, Any]:
        """Combine all JSON outputs for a processing session into a single file"""
        try:
            logger.info(f"Combining JSON outputs for session: {session_id}, process: {process_id}")
            
            # Initialize combined structure
            combined_data = {
                "metadata": {
                    "session_id": session_id,
                    "process_id": process_id,
                    "combined_at": datetime.now().isoformat(),
                    "total_responses": 0,
                    "successful_responses": 0,
                    "failed_responses": 0,
                    "total_batches": 0
                },
                "successful_responses": [],
                "failed_responses": [],
                "summary": {
                    "total_tokens_used": 0,
                    "total_cost": 0.0,
                    "average_response_time": 0.0,
                    "success_rate": 0.0
                }
            }
            
            # Get all response files
            responses_dir = Path(self.json_storage) / "responses"
            failed_dir = Path(self.json_storage) / "failed"
            
            # Process successful responses
            if responses_dir.exists():
                # Look for files by reading their metadata to find the correct session
                # Files are named like: checklist_matching_batch_000_20250714_155535_session_1752488735.json
                # But we need to match by the actual session ID in the metadata
                response_files = []
                for file_path in responses_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            file_session_id = data.get("metadata", {}).get("session_id", "")
                            # Check if this file belongs to our session
                            if session_id in file_session_id or file_session_id in session_id:
                                response_files.append(file_path)
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path} to check session ID: {e}")
                        # Fallback: check filename pattern
                        if session_id in file_path.name or f"session_{session_id}" in file_path.name:
                            response_files.append(file_path)
                logger.info(f"Found {len(response_files)} successful response files")
                
                for file_path in sorted(response_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
                        
                        # Extract batch information from filename
                        batch_info = self._extract_batch_info(file_path.name)
                        
                        # Add metadata to response
                        response_data["_metadata"] = {
                            "file_name": file_path.name,
                            "batch_number": batch_info.get("batch_number"),
                            "timestamp": batch_info.get("timestamp"),
                            "file_size": file_path.stat().st_size
                        }
                        
                        combined_data["successful_responses"].append(response_data)
                        combined_data["metadata"]["successful_responses"] += 1
                        
                    except Exception as e:
                        logger.error(f"Error reading response file {file_path}: {e}")
            
            # Process failed responses
            if failed_dir.exists():
                # Look for files by reading their metadata to find the correct session
                # Files are named like: failed_checklist_matching_batch_000_20250714_155535_session_1752488735.json
                # But we need to match by the actual session ID in the metadata
                failed_files = []
                for file_path in failed_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            file_session_id = data.get("metadata", {}).get("session_id", "")
                            # Check if this file belongs to our session
                            if session_id in file_session_id or file_session_id in session_id:
                                failed_files.append(file_path)
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path} to check session ID: {e}")
                        # Fallback: check filename pattern
                        if session_id in file_path.name or f"session_{session_id}" in file_path.name:
                            failed_files.append(file_path)
                logger.info(f"Found {len(failed_files)} failed response files")
                
                for file_path in sorted(failed_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            failed_data = json.load(f)
                        
                        # Extract batch information from filename
                        batch_info = self._extract_batch_info(file_path.name)
                        
                        # Add metadata to failed response
                        failed_data["_metadata"] = {
                            "file_name": file_path.name,
                            "batch_number": batch_info.get("batch_number"),
                            "timestamp": batch_info.get("timestamp"),
                            "file_size": file_path.stat().st_size,
                            "error_type": failed_data.get("error_type", "unknown"),
                            "error_message": failed_data.get("error_message", "Unknown error")
                        }
                        
                        combined_data["failed_responses"].append(failed_data)
                        combined_data["metadata"]["failed_responses"] += 1
                        
                    except Exception as e:
                        logger.error(f"Error reading failed file {file_path}: {e}")
            
            # Calculate summary statistics
            combined_data["metadata"]["total_responses"] = (
                combined_data["metadata"]["successful_responses"] + 
                combined_data["metadata"]["failed_responses"]
            )
            
            if combined_data["metadata"]["total_responses"] > 0:
                combined_data["summary"]["success_rate"] = (
                    combined_data["metadata"]["successful_responses"] / 
                    combined_data["metadata"]["total_responses"]
                ) * 100
            
            # Calculate total tokens and cost from successful responses
            total_tokens = 0
            total_cost = 0.0
            response_times = []
            
            for response in combined_data["successful_responses"]:
                # Extract token usage if available
                if "token_usage" in response:
                    usage = response["token_usage"]
                    total_tokens += (
                        usage.get("input_tokens", 0) + 
                        usage.get("output_tokens", 0) + 
                        usage.get("cached_tokens", 0) + 
                        usage.get("thoughts_tokens", 0)
                    )
                    total_cost += usage.get("total_cost", 0.0)
                
                # Extract response time if available
                if "response_time" in response:
                    response_times.append(response["response_time"])
            
            combined_data["summary"]["total_tokens_used"] = total_tokens
            combined_data["summary"]["total_cost"] = total_cost
            
            if response_times:
                combined_data["summary"]["average_response_time"] = sum(response_times) / len(response_times)
            
            # Estimate total batches based on file patterns
            batch_numbers = set()
            for response in combined_data["successful_responses"]:
                if response["_metadata"]["batch_number"] is not None:
                    batch_numbers.add(response["_metadata"]["batch_number"])
            for response in combined_data["failed_responses"]:
                if response["_metadata"]["batch_number"] is not None:
                    batch_numbers.add(response["_metadata"]["batch_number"])
            
            combined_data["metadata"]["total_batches"] = len(batch_numbers)
            
            logger.info(f"Combined JSON created with {combined_data['metadata']['total_responses']} total responses")
            logger.info(f"Success rate: {combined_data['summary']['success_rate']:.2f}%")
            logger.info(f"Total tokens used: {combined_data['summary']['total_tokens_used']:,}")
            logger.info(f"Total cost: ${combined_data['summary']['total_cost']:.6f}")
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error combining JSON outputs: {e}")
            return {
                "error": f"Failed to combine JSON outputs: {str(e)}",
                "metadata": {
                    "session_id": session_id,
                    "process_id": process_id,
                    "combined_at": datetime.now().isoformat()
                }
            }
    
    def save_combined_json(self, combined_data: Dict[str, Any], session_id: str, process_id: str) -> str:
        """Save the combined JSON data to a file"""
        try:
            # Create combined directory if it doesn't exist
            combined_dir = Path(self.json_storage) / "combined"
            combined_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_session_{session_id}_process_{process_id}_{timestamp}.json"
            file_path = combined_dir / filename
            
            # Save with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Combined JSON saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving combined JSON: {e}")
            raise
    
    def get_combined_json_path(self, session_id: str, process_id: str) -> Optional[str]:
        """Get the path to the combined JSON file for a session/process"""
        try:
            combined_dir = Path(self.json_storage) / "combined"
            if not combined_dir.exists():
                return None
            
            # Look for the most recent combined file for this session/process
            pattern = f"combined_session_{session_id}_process_{process_id}_*.json"
            files = list(combined_dir.glob(pattern))
            
            if files:
                # Return the most recent file
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                return str(latest_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting combined JSON path: {e}")
            return None
    
    def _extract_batch_info(self, filename: str) -> Dict[str, Any]:
        """Extract batch information from filename"""
        try:
            # Actual format: checklist_matching_batch_000_20250714_155535_session_1752488735.json
            # or: failed_checklist_matching_batch_000_20250714_155535_session_1752488735.json
            parts = filename.replace('.json', '').split('_')
            
            batch_info = {}
            
            # Extract batch number
            if 'batch' in parts:
                batch_index = parts.index('batch')
                if batch_index + 1 < len(parts):
                    try:
                        batch_info["batch_number"] = int(parts[batch_index + 1])
                    except ValueError:
                        batch_info["batch_number"] = None
            
            # Extract timestamp (format: YYYYMMDD_HHMMSS)
            # Look for parts that match the timestamp pattern
            for i, part in enumerate(parts):
                if len(part) == 8 and part.isdigit() and i + 1 < len(parts):
                    # This might be the date part (YYYYMMDD)
                    next_part = parts[i + 1]
                    if len(next_part) == 6 and next_part.isdigit():
                        # This is the time part (HHMMSS)
                        try:
                            timestamp_str = f"{part}_{next_part}"
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            batch_info["timestamp"] = timestamp.isoformat()
                            break
                        except ValueError:
                            continue
            
            return batch_info
            
        except Exception as e:
            logger.warning(f"Error extracting batch info from filename {filename}: {e}")
            return {"batch_number": None, "timestamp": None}
    
    def cleanup_old_combined_files(self, max_age_hours: int = 24) -> int:
        """Clean up old combined JSON files"""
        try:
            combined_dir = Path(self.json_storage) / "combined"
            if not combined_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            deleted_count = 0
            
            for file_path in combined_dir.glob("combined_*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old combined file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting old file {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old combined JSON files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old combined files: {e}")
            return 0 