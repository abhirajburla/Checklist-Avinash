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
import pandas as pd

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
    row_id: int
    category: str
    checklist: str
    scope_of_work: str
    sector: str
    found: bool
    confidence: str
    validation_score: float
    sheet_number: str
    spec_section: str
    notes: str
    reasoning: str

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
            if not raw_item.get("category") or not raw_item.get("checklist"):
                raise ValueError("Missing required fields for checklist item")
            return ChecklistItem(
                row_id=int(raw_item.get("row_id", 0)),
                category=str(raw_item.get("category", "")),
                checklist=str(raw_item.get("checklist", "")),
                scope_of_work=str(raw_item.get("scope_of_work", "")),
                sector=str(raw_item.get("sector", "")),
                found=bool(raw_item.get("found", False)),
                confidence=str(raw_item.get("confidence", "LOW")),
                validation_score=float(raw_item.get("validation_score", 0.0)),
                sheet_number=str(raw_item.get("sheet_number", "")),
                spec_section=str(raw_item.get("spec_section", "")),
                notes=str(raw_item.get("notes", "")),
                reasoning=str(raw_item.get("reasoning", ""))
            )
        except Exception as e:
            logger.error(f"Error formatting checklist item: {e}")
            # Return a default item
            return ChecklistItem(
                row_id=0,
                category="error",
                checklist="Error formatting item",
                scope_of_work="",
                sector="",
                found=False,
                confidence="LOW",
                validation_score=0.0,
                sheet_number="",
                spec_section="",
                notes=f"Formatting error: {str(e)}",
                reasoning="Error occurred during formatting"
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
                           document_info: List[Dict[str, Any]]) -> List[Dict]:
        """Compile final output with clean JSON structure"""
        try:
            # Get raw checklist results
            raw_checklist = raw_results.get("checklist_results", [])
            
            # Convert to clean format with all required fields
            clean_results = []
            for item in raw_checklist:
                clean_result = {
                    "row_id": item.get("row_id", 0),
                    "category": item.get("category", ""),
                    "scope_of_work": item.get("scope_of_work", ""),
                    "checklist": item.get("checklist", ""),
                    "sector": item.get("sector", ""),
                    "sheet_number": item.get("sheet_number", ""),
                    "spec_section": item.get("spec_section", ""),
                    "notes": item.get("notes", ""),
                    "reasoning": item.get("reasoning", ""),
                    "found": item.get("found", False),
                    "confidence": item.get("confidence", "LOW"),
                    "validation_score": item.get("validation_score", 0.0)
                }
                clean_results.append(clean_result)
            
            # Sort by row_id to maintain checklist order
            clean_results.sort(key=lambda x: x.get('row_id', 0))
            
            # Cache the clean output
            self.output_cache[process_id] = {
                "checklist_results": clean_results
            }
            
            logger.info(f"Compiled clean output for process {process_id} with {len(clean_results)} items")
            return clean_results
            
        except Exception as e:
            logger.error(f"Error compiling final output: {e}")
            raise
    
    def generate_clean_json_output(self, process_id: str, pretty_print: bool = True) -> str:
        """Generate clean JSON output with only essential fields for download"""
        if process_id not in self.output_cache:
            raise ValueError(f"No output cached for process {process_id}")
        
        output_data = self.output_cache[process_id]
        checklist_results = output_data.get("checklist_results", [])
        
        # The results are already in the correct format from enhanced batch processor
        # Just ensure they have all required fields and sort by row_id
        clean_results = []
        for item in checklist_results:
            # Ensure all required fields are present with defaults
            clean_result = {
                "row_id": item.get("row_id", 0),
                "category": item.get("category", ""),
                "scope_of_work": item.get("scope_of_work", ""),
                "checklist": item.get("checklist", ""),
                "sector": item.get("sector", ""),
                "sheet_number": item.get("sheet_number", ""),
                "spec_section": item.get("spec_section", ""),
                "notes": item.get("notes", ""),
                "reasoning": item.get("reasoning", ""),
                "found": item.get("found", False),
                "confidence": item.get("confidence", "LOW"),
                "validation_score": item.get("validation_score", 0.0)
            }
            clean_results.append(clean_result)
        
        # Sort by row_id to maintain checklist order
        clean_results.sort(key=lambda x: x.get('row_id', 0))
        
        if pretty_print:
            return json.dumps(clean_results, indent=2, ensure_ascii=False)
        else:
            return json.dumps(clean_results, ensure_ascii=False)
    
    def save_clean_output_to_file(self, process_id: str, filename: Optional[str] = None) -> str:
        """Save clean output to a JSON file with only essential fields"""
        if process_id not in self.output_cache:
            raise ValueError(f"No output cached for process {process_id}")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checklist_results_clean_{process_id}_{timestamp}.json"
        
        filepath = Path(self.config.RESULTS_FOLDER) / filename
        
        try:
            clean_json = self.generate_clean_json_output(process_id, pretty_print=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_json)
            
            logger.info(f"Saved clean output to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving clean output to file: {e}")
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
    
    def generate_excel_output(self, process_id: str, filename: Optional[str] = None) -> str:
        """Generate Excel output with specified columns from JSON data"""
        if process_id not in self.output_cache:
            raise ValueError(f"No output cached for process {process_id}")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checklist_results_{process_id}_{timestamp}.xlsx"
        
        filepath = Path(self.config.RESULTS_FOLDER) / filename
        
        try:
            # Get the cached output data
            output_data = self.output_cache[process_id]
            checklist_results = output_data.get("checklist_results", [])
            
            # Prepare data for Excel
            excel_data = []
            for item in checklist_results:
                excel_data.append({
                    "Row ID": item.get("row_id", ""),
                    "Category": item.get("category", ""),
                    "Scope of Work": item.get("scope_of_work", ""),
                    "Checklist": item.get("checklist", ""),
                    "Sector": item.get("sector", ""),
                    "Sheet Number": item.get("sheet_number", ""),
                    "Specification Reference": item.get("spec_section", ""),
                    "Notes": item.get("notes", ""),
                    "Reasoning": item.get("reasoning", ""),
                    "Found": item.get("found", False),
                    "Confidence": item.get("confidence", "LOW"),
                    "Validation Score": item.get("validation_score", 0.0)
                })
            
            # Create DataFrame and save to Excel
            df = pd.DataFrame(excel_data)
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Checklist Results', index=False)
                
                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Checklist Results']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Generated Excel output: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating Excel output: {e}")
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