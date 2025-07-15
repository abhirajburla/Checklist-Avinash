import logging
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import traceback
try:
    from .checklist_processor import ChecklistProcessor
    from .gemini_client import GeminiClient
    from .document_handler import DocumentHandler
    from .config import Config
    from .logger_config import LoggerConfig
    from .enhanced_batch_processor import EnhancedBatchProcessor, BatchStatus
    from .reference_validator import ReferenceValidator
    from .output_generator import OutputGenerator
except ImportError:
    from checklist_processor import ChecklistProcessor
    from gemini_client import GeminiClient
    from document_handler import DocumentHandler
    from config import Config
    from logger_config import LoggerConfig
    from enhanced_batch_processor import EnhancedBatchProcessor, BatchStatus
    from reference_validator import ReferenceValidator
    from output_generator import OutputGenerator

logger = LoggerConfig.get_logger(__name__)

class MatchingEngine:
    """Core matching logic engine with real Gemini integration"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.checklist_processor = ChecklistProcessor()
        self.document_handler = DocumentHandler()
        self.config = Config()
        
        # Initialize enhanced components
        self.enhanced_batch_processor = EnhancedBatchProcessor(gemini_client, self.config)
        self.reference_validator = ReferenceValidator()
        self.output_generator = OutputGenerator()
        
        # Initialize checklist processor
        self.checklist_processor.initialize()
        
        # In-memory storage for processing status (in production, use Redis/DB)
        self.processing_status = {}
        self.results_cache = {}
        
        logger.info("MatchingEngine initialized with enhanced batch processing, validation, and output generation")
    
    def process_checklist_matching(self, upload_id: str) -> Dict[str, Any]:
        """Start the checklist matching process with real document processing"""
        try:
            process_id = str(uuid.uuid4())
            
            total_items = self.checklist_processor.get_total_items()
            batches = self.checklist_processor.get_batch_count()
            
            # Initialize processing status
            self.processing_status[process_id] = {
                "status": "processing",
                "total_batches": batches,
                "completed_batches": 0,
                "total_items": total_items,
                "upload_id": upload_id,
                "error": None,
                "start_time": time.time()
            }
            
            # Create progress tracker
            tracker_id = self.output_generator.create_progress_tracker(process_id, batches, total_items)
            self.processing_status[process_id]["tracker_id"] = tracker_id
            
            # Start real processing
            self._process_documents(process_id, upload_id)
            
            return {
                "process_id": process_id,
                "total_items": total_items,
                "batches": batches
            }
            
        except Exception as e:
            logger.error(f"Error starting checklist matching: {e}")
            raise
    
    def _process_documents(self, process_id: str, upload_id: str):
        """Process documents and match checklist items"""
        import threading
        
        def process_work():
            try:
                status = self.processing_status[process_id]
                
                # Get uploaded files
                upload_info = self.document_handler.get_upload_files(upload_id)
                if not upload_info["success"]:
                    raise Exception(f"Could not get upload files: {upload_info['error']}")
                
                # Prepare file paths for Gemini
                all_files = upload_info["files"]["drawings"] + upload_info["files"]["specifications"]
                
                # Upload documents to Gemini with context caching
                upload_result = self.gemini_client.upload_documents(all_files)
                
                if not upload_result["success"]:
                    raise Exception(f"Failed to upload documents: {upload_result['error']}")
                
                cache_id = upload_result["cache_id"]
                logger.info(f"Documents uploaded successfully, cache_id: {cache_id}")
                
                # Skip document reference extraction for now to get to batch processing
                document_context = "Documents uploaded successfully, proceeding with batch processing"
                
                # Process batches with enhanced processor
                total_batches = status["total_batches"]
                all_results = []
                
                # Prepare all batches
                batches = []
                for batch_index in range(total_batches):
                    batch = self.checklist_processor.get_batch(batch_index)
                    if batch:
                        batches.append(batch)
                    else:
                        logger.warning(f"Empty batch at index {batch_index}")
                
                if batches:
                    # Process batches with enhanced processor and retry logic
                    # Get tracker ID for progress updates
                    tracker_id = self.processing_status[process_id].get("tracker_id")
                    
                    # Use enhanced batch processor with system instructions (synchronous version)
                    try:
                        batch_results = self.enhanced_batch_processor.process_multiple_batches_sync(
                            batches, cache_id, document_context, tracker_id, self.output_generator
                        )
                        
                        # Process batch results (they are lists of results, not BatchResult objects)
                        for batch_index, batch_result in enumerate(batch_results):
                            if isinstance(batch_result, list):
                                all_results.extend(batch_result)
                                self.processing_status[process_id]["completed_batches"] += 1
                                
                                # Update progress tracker
                                if tracker_id:
                                    self.output_generator.update_progress(
                                        tracker_id, batch_index, batch_result, "processing"
                                    )
                                    # Also update the global progress tracker dict if needed
                                    if hasattr(self.output_generator, 'progress_trackers'):
                                        self.output_generator.progress_trackers[tracker_id]["current_batch"] = batch_index + 1
                                        self.output_generator.progress_trackers[tracker_id]["status"] = "processing"
                                        self.output_generator.progress_trackers[tracker_id]["items_processed"] = len(all_results)
                                        self.output_generator.progress_trackers[tracker_id]["progress_percentage"] = ((batch_index + 1) / len(batch_results)) * 100
                            else:
                                logger.error(f"Batch {batch_index+1} returned unexpected result type: {type(batch_result)}")
                                # Update progress with error
                                if tracker_id:
                                    self.output_generator.update_progress(
                                        tracker_id, batch_index, [], "failed", f"Unexpected result type: {type(batch_result)}"
                                    )
                    except Exception as e:
                        logger.error(f"Exception in enhanced batch processor: {e}")
                        raise
                    
                    # Validate all references
                    validated_results = self.reference_validator.validate_batch_results(all_results)
                    all_results = validated_results
                    
                    logger.info(f"Completed processing with {len(all_results)} validated results")
                else:
                    logger.warning("No valid batches to process")
                
                # Mark as completed
                self.processing_status[process_id]["status"] = "completed"
                self.processing_status[process_id]["end_time"] = time.time()
                
                # Store results
                found_items = sum(1 for item in all_results if item.get("found", False))
                self.results_cache[process_id] = {
                    "total_items": len(all_results),
                    "found_items": found_items,
                    "not_found_items": len(all_results) - found_items,
                    "checklist_results": all_results,
                    "document_context": document_context,
                    "cache_id": cache_id,
                    "upload_id": upload_id
                }
                
                # Compile final output with structured JSON
                if tracker_id:
                    # Prepare document info for output
                    document_info = []
                    for file_path in all_files:
                        file_info = {
                            "type": "drawing" if file_path in upload_info["files"]["drawings"] else "specification",
                            "filename": Path(file_path).name,
                            "file_size": Path(file_path).stat().st_size,
                            "upload_timestamp": datetime.now().isoformat()
                        }
                        document_info.append(file_info)
                    
                    # Compile final output
                    clean_results = self.output_generator.compile_final_output(
                        process_id, tracker_id, self.results_cache[process_id], document_info
                    )
                    
                    # Update final progress
                    self.output_generator.update_progress(
                        tracker_id, len(batches) - 1, all_results, "completed"
                    )
                
                logger.info(f"Processing completed for {process_id}: {found_items}/{len(all_results)} items found")
                
            except Exception as e:
                logger.error(f"Error in document processing: {e}")
                self.processing_status[process_id]["status"] = "failed"
                self.processing_status[process_id]["error"] = str(e)
                self.processing_status[process_id]["end_time"] = time.time()
        
        # Start processing in background
        thread = threading.Thread(target=process_work)
        thread.daemon = True
        thread.start()
    
    def _create_document_context(self, references: Dict[str, Any]) -> str:
        """Create document context string for matching"""
        try:
            context_parts = []
            
            # Add summary
            if references.get("summary"):
                summary = references["summary"]
                context_parts.append(f"Document Summary: {summary.get('document_summary', 'No summary available')}")
                
                if summary.get("key_elements"):
                    context_parts.append(f"Key Elements: {', '.join(summary['key_elements'])}")
                
                if summary.get("major_systems"):
                    context_parts.append(f"Major Systems: {', '.join(summary['major_systems'])}")
            
            # Add drawing information
            if references.get("drawings"):
                context_parts.append("Drawings:")
                for drawing in references["drawings"]:
                    sheet_info = drawing.get("sheet_info", {})
                    sheet_num = sheet_info.get("sheet_number", "Unknown")
                    sheet_title = sheet_info.get("sheet_title", "Untitled")
                    discipline = sheet_info.get("discipline", "General")
                    context_parts.append(f"  - {drawing['file_name']}: Sheet {sheet_num} ({sheet_title}) - {discipline}")
            
            # Add specification information
            if references.get("specifications"):
                context_parts.append("Specifications:")
                for spec in references["specifications"]:
                    spec_info = spec.get("spec_info", {})
                    specs_list = spec_info.get("specifications", [])
                    if specs_list:
                        spec_codes = [s.get("section_code", "") for s in specs_list if s.get("section_code")]
                        context_parts.append(f"  - {spec['file_name']}: {', '.join(spec_codes)}")
                    else:
                        context_parts.append(f"  - {spec['file_name']}: No specification codes found")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error creating document context: {e}")
            return "Document context could not be created"
    
    def get_processing_status(self, process_id: str) -> Dict[str, Any]:
        """Get processing status"""
        if process_id not in self.processing_status:
            raise ValueError(f"Process ID not found: {process_id}")
        
        status = self.processing_status[process_id].copy()
        
        # Add timing information
        if "start_time" in status:
            elapsed = time.time() - status["start_time"]
            status["elapsed_seconds"] = round(elapsed, 2)
        
        # Add progress percentage
        if status["total_batches"] > 0:
            status["progress_percentage"] = round(
                (status["completed_batches"] / status["total_batches"]) * 100, 1
            )
        
        return status
    
    def get_results(self, process_id: str) -> Dict[str, Any]:
        """Get final results"""
        if process_id not in self.results_cache:
            raise ValueError(f"Results not found for process ID: {process_id}")
        
        return self.results_cache[process_id]
    
    def cleanup_process(self, process_id: str) -> bool:
        """Clean up process data and cache"""
        try:
            # Clean up results cache
            if process_id in self.results_cache:
                cache_id = self.results_cache[process_id].get("cache_id")
                if cache_id:
                    self.gemini_client.cleanup_cache(cache_id)
                del self.results_cache[process_id]
            
            # Clean up processing status
            if process_id in self.processing_status:
                del self.processing_status[process_id]
            
            logger.info(f"Cleaned up process: {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up process {process_id}: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "active_processes": len(self.processing_status),
            "cached_results": len(self.results_cache),
            "gemini_cache_info": self.gemini_client.get_cache_info(),
            "checklist_info": {
                "total_items": self.checklist_processor.get_total_items(),
                "batch_count": self.checklist_processor.get_batch_count()
            }
        } 