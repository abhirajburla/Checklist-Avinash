#!/usr/bin/env python3
"""
Output Generator for Construction Checklist Matching System
Handles JSON formatting, progress tracking, and final output compilation
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    timestamp: str
    status: str
    message: str
    progress_percentage: float
    current_batch: int
    total_batches: int
    items_processed: int
    total_items: int
    found_items: int
    not_found_items: int

@dataclass
class ChecklistItem:
    """Individual checklist item structure (Phase 4)"""
    item_id: str
    category: str
    description: str
    found: bool
    confidence_score: float
    sheet_references: List[str]
    sheet_reasoning: str
    spec_references: List[str]
    spec_reasoning: str
    notes: str
    processing_time: float

@dataclass
class DocumentReference:
    """Document reference structure"""
    document_type: str  # "drawing" or "specification"
    filename: str
    sheet_number: Optional[str]
    section_number: Optional[str]
    page_count: int
    file_size: int
    upload_timestamp: str

@dataclass
class ProcessingMetadata:
    """Processing metadata structure"""
    process_id: str
    upload_id: str
    start_time: str
    end_time: Optional[str]
    total_processing_time: Optional[float]
    total_items: int
    found_items: int
    not_found_items: int
    success_rate: float
    system_version: str
    gemini_model: str

@dataclass
class FinalOutput:
    """Final output structure"""
    metadata: ProcessingMetadata
    documents: List[DocumentReference]
    checklist_results: List[ChecklistItem]
    summary: Dict[str, Any]
    generated_at: str

class OutputGenerator:
    """Handles output generation, progress tracking, and JSON formatting"""
    
    def __init__(self):
        self.config = Config()
        self.progress_trackers = {}
        self.output_cache = {}
        
        # Ensure results directory exists
        Path(self.config.RESULTS_FOLDER).mkdir(exist_ok=True)
        
        logger.info("OutputGenerator initialized")
    
    def create_progress_tracker(self, process_id: str, total_batches: int, total_items: int) -> str:
        """Create a new progress tracker for a process"""
        tracker_id = str(uuid.uuid4())
        
        self.progress_trackers[tracker_id] = {
            "process_id": process_id,
            "status": ProcessingStatus.PENDING.value,
            "total_batches": total_batches,
            "total_items": total_items,
            "current_batch": 0,
            "items_processed": 0,
            "found_items": 0,
            "not_found_items": 0,
            "start_time": datetime.now().isoformat(),
            "updates": [],
            "error": None
        }
        
        logger.info(f"Created progress tracker {tracker_id} for process {process_id}")
        return tracker_id
    
    def update_progress(self, tracker_id: str, batch_index: int, batch_results: List[Dict], 
                       status: str = "processing", error: Optional[str] = None) -> bool:
        """Update progress for a specific tracker"""
        if tracker_id not in self.progress_trackers:
            logger.error(f"Progress tracker {tracker_id} not found")
            return False
        
        tracker = self.progress_trackers[tracker_id]
        
        # Update batch progress
        if batch_results:
            tracker["current_batch"] = batch_index + 1
            tracker["items_processed"] += len(batch_results)
            
            # Count found/not found items
            found_count = sum(1 for item in batch_results if item.get("found", False))
            tracker["found_items"] += found_count
            tracker["not_found_items"] += len(batch_results) - found_count
        
        # Update status
        tracker["status"] = status
        if error:
            tracker["error"] = error
        
        # Calculate progress percentage
        if tracker["total_batches"] > 0:
            progress_percentage = (tracker["current_batch"] / tracker["total_batches"]) * 100
        else:
            progress_percentage = 0
        
        # Create progress update
        update = ProgressUpdate(
            timestamp=datetime.now().isoformat(),
            status=status,
            message=f"Processed batch {batch_index + 1}/{tracker['total_batches']}",
            progress_percentage=progress_percentage,
            current_batch=tracker["current_batch"],
            total_batches=tracker["total_batches"],
            items_processed=tracker["items_processed"],
            total_items=tracker["total_items"],
            found_items=tracker["found_items"],
            not_found_items=tracker["not_found_items"]
        )
        
        tracker["updates"].append(asdict(update))
        
        logger.info(f"Updated progress for {tracker_id}: {progress_percentage:.1f}% complete")
        return True
    
    def get_progress(self, tracker_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a tracker"""
        if tracker_id not in self.progress_trackers:
            return None
        
        tracker = self.progress_trackers[tracker_id]
        
        # Calculate current progress percentage
        if tracker["total_batches"] > 0:
            progress_percentage = (tracker["current_batch"] / tracker["total_batches"]) * 100
        else:
            progress_percentage = 0
        
        return {
            "tracker_id": tracker_id,
            "process_id": tracker["process_id"],
            "status": tracker["status"],
            "progress_percentage": progress_percentage,
            "current_batch": tracker["current_batch"],
            "total_batches": tracker["total_batches"],
            "items_processed": tracker["items_processed"],
            "total_items": tracker["total_items"],
            "found_items": tracker["found_items"],
            "not_found_items": tracker["not_found_items"],
            "start_time": tracker["start_time"],
            "error": tracker["error"],
            "latest_update": tracker["updates"][-1] if tracker["updates"] else None
        }
    
    def format_checklist_item(self, raw_item: Dict[str, Any]) -> ChecklistItem:
        """Format a raw checklist item into structured format (Phase 4)"""
        try:
            # If required fields are missing, treat as error
            if not raw_item.get("category") or not raw_item.get("description"):
                raise ValueError("Missing required fields for checklist item")
            return ChecklistItem(
                item_id=str(raw_item.get("item_id", "")),
                category=str(raw_item.get("category", "")),
                description=str(raw_item.get("description", "")),
                found=bool(raw_item.get("found", False)),
                confidence_score=float(raw_item.get("confidence_score", 0.0)),
                sheet_references=raw_item.get("sheet_references", []),
                sheet_reasoning=str(raw_item.get("sheet_reasoning", "")),
                spec_references=raw_item.get("spec_references", []),
                spec_reasoning=str(raw_item.get("spec_reasoning", "")),
                notes=str(raw_item.get("notes", "")),
                processing_time=float(raw_item.get("processing_time", 0.0))
            )
        except Exception as e:
            logger.error(f"Error formatting checklist item: {e}")
            # Return a default item
            return ChecklistItem(
                item_id=str(raw_item.get("item_id", "unknown")),
                category="error",
                description="Error formatting item",
                found=False,
                confidence_score=0.0,
                sheet_references=[],
                sheet_reasoning="Error occurred during formatting",
                spec_references=[],
                spec_reasoning="Error occurred during formatting",
                notes=f"Formatting error: {str(e)}",
                processing_time=0.0
            )
    
    def format_document_reference(self, raw_doc: Dict[str, Any]) -> DocumentReference:
        """Format a raw document reference into structured format"""
        try:
            return DocumentReference(
                document_type=str(raw_doc.get("type", "unknown")),
                filename=str(raw_doc.get("filename", "")),
                sheet_number=raw_doc.get("sheet_number"),
                section_number=raw_doc.get("section_number"),
                page_count=int(raw_doc.get("page_count", 0)),
                file_size=int(raw_doc.get("file_size", 0)),
                upload_timestamp=str(raw_doc.get("upload_timestamp", ""))
            )
        except Exception as e:
            logger.error(f"Error formatting document reference: {e}")
            return DocumentReference(
                document_type="error",
                filename="error",
                sheet_number=None,
                section_number=None,
                page_count=0,
                file_size=0,
                upload_timestamp=datetime.now().isoformat()
            )
    
    def compile_final_output(self, process_id: str, tracker_id: str, 
                           raw_results: Dict[str, Any], 
                           document_info: List[Dict[str, Any]]) -> FinalOutput:
        """Compile final output with proper JSON structure"""
        try:
            # Get tracker info
            tracker = self.progress_trackers.get(tracker_id, {})
            
            # Calculate processing time
            start_time = datetime.fromisoformat(tracker.get("start_time", datetime.now().isoformat()))
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Calculate success rate
            total_items = tracker.get("total_items", 0)
            found_items = tracker.get("found_items", 0)
            success_rate = (found_items / total_items * 100) if total_items > 0 else 0
            
            # Create metadata
            metadata = ProcessingMetadata(
                process_id=process_id,
                upload_id=raw_results.get("upload_id", ""),
                start_time=tracker.get("start_time", datetime.now().isoformat()),
                end_time=end_time.isoformat(),
                total_processing_time=total_time,
                total_items=total_items,
                found_items=found_items,
                not_found_items=tracker.get("not_found_items", 0),
                success_rate=success_rate,
                system_version="1.0.0",
                gemini_model=self.config.GEMINI_MODEL
            )
            
            # Format document references
            documents = [self.format_document_reference(doc) for doc in document_info]
            
            # Format checklist results
            checklist_results = []
            raw_checklist = raw_results.get("checklist_results", [])
            for item in raw_checklist:
                formatted_item = self.format_checklist_item(item)
                checklist_results.append(formatted_item)
            
            # Create summary
            summary = {
                "total_items_processed": total_items,
                "items_found": found_items,
                "items_not_found": tracker.get("not_found_items", 0),
                "success_rate_percentage": success_rate,
                "processing_time_seconds": total_time,
                "batches_processed": tracker.get("current_batch", 0),
                "total_batches": tracker.get("total_batches", 0),
                "documents_processed": len(documents),
                "drawings_count": len([d for d in documents if d.document_type == "drawing"]),
                "specifications_count": len([d for d in documents if d.document_type == "specification"])
            }
            
            # Create final output
            final_output = FinalOutput(
                metadata=metadata,
                documents=documents,
                checklist_results=checklist_results,
                summary=summary,
                generated_at=datetime.now().isoformat()
            )
            
            # Cache the output
            self.output_cache[process_id] = asdict(final_output)
            
            logger.info(f"Compiled final output for process {process_id}")
            return final_output
            
        except Exception as e:
            logger.error(f"Error compiling final output: {e}")
            raise
    
    def generate_json_output(self, process_id: str, pretty_print: bool = True) -> str:
        """Generate JSON output for download"""
        if process_id not in self.output_cache:
            raise ValueError(f"No output cached for process {process_id}")
        
        output_data = self.output_cache[process_id]
        
        if pretty_print:
            return json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(output_data, ensure_ascii=False)
    
    def save_output_to_file(self, process_id: str, filename: Optional[str] = None) -> str:
        """Save output to a JSON file"""
        if process_id not in self.output_cache:
            raise ValueError(f"No output cached for process {process_id}")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checklist_results_{process_id}_{timestamp}.json"
        
        filepath = Path(self.config.RESULTS_FOLDER) / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.output_cache[process_id], f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved output to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving output to file: {e}")
            raise
    
    def cleanup_tracker(self, tracker_id: str) -> bool:
        """Clean up a progress tracker"""
        if tracker_id in self.progress_trackers:
            del self.progress_trackers[tracker_id]
            logger.info(f"Cleaned up tracker {tracker_id}")
            return True
        return False
    
    def cleanup_output(self, process_id: str) -> bool:
        """Clean up cached output"""
        if process_id in self.output_cache:
            del self.output_cache[process_id]
            logger.info(f"Cleaned up output for process {process_id}")
            return True
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return {
            "active_trackers": len(self.progress_trackers),
            "cached_outputs": len(self.output_cache),
            "results_folder": self.config.RESULTS_FOLDER,
            "system_version": "1.0.0"
        } 