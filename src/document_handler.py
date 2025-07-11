import logging
import os
import uuid
from typing import List, Dict, Any, Tuple
from werkzeug.datastructures import FileStorage
from pathlib import Path
# import pypdf  # Temporarily disabled for compatibility
try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class DocumentHandler:
    """Handles document upload, validation, and processing"""
    
    def __init__(self):
        self.config = Config()
        self.upload_folder = Path(self.config.UPLOAD_FOLDER)
        self.upload_folder.mkdir(exist_ok=True)
        logger.info(f"DocumentHandler initialized with upload folder: {self.upload_folder}")
    
    def process_uploads(self, drawings: List[FileStorage], specifications: List[FileStorage]) -> Dict[str, Any]:
        """Process uploaded documents with validation and storage"""
        try:
            upload_id = str(uuid.uuid4())
            upload_dir = self.upload_folder / upload_id
            upload_dir.mkdir(exist_ok=True)
            
            processed_files = {
                "drawings": [],
                "specifications": [],
                "errors": []
            }
            
            # Process drawings
            for drawing in drawings:
                result = self._process_single_file(drawing, upload_dir, "drawing")
                if result["success"]:
                    processed_files["drawings"].append(result["file_info"])
                else:
                    processed_files["errors"].append(result["error"])
            
            # Process specifications
            for spec in specifications:
                result = self._process_single_file(spec, upload_dir, "specification")
                if result["success"]:
                    processed_files["specifications"].append(result["file_info"])
                else:
                    processed_files["errors"].append(result["error"])
            
            # Check if we have any valid files
            total_files = len(processed_files["drawings"]) + len(processed_files["specifications"])
            if total_files == 0:
                return {
                    "success": False,
                    "error": "No valid files were uploaded. Please check file format and size."
                }
            
            # Create upload summary
            upload_summary = {
                "upload_id": upload_id,
                "upload_dir": str(upload_dir),
                "total_files": total_files,
                "drawings_count": len(processed_files["drawings"]),
                "specifications_count": len(processed_files["specifications"]),
                "errors_count": len(processed_files["errors"]),
                "files": processed_files
            }
            
            logger.info(f"Upload processed successfully: {upload_summary}")
            
            return {
                "success": True,
                "upload_id": upload_id,
                "upload_summary": upload_summary,
                "message": f"Successfully processed {total_files} files"
            }
            
        except Exception as e:
            logger.error(f"Error processing uploads: {e}")
            return {
                "success": False,
                "error": f"Upload processing failed: {str(e)}"
            }
    
    def _process_single_file(self, file: FileStorage, upload_dir: Path, file_type: str) -> Dict[str, Any]:
        """Process a single uploaded file"""
        try:
            # Validate file
            validation_result = self._validate_file(file)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"{file.filename}: {validation_result['error']}"
                }
            
            # Generate unique filename
            filename = file.filename or "unknown_file"
            file_extension = Path(filename).suffix
            unique_filename = f"{file_type}_{uuid.uuid4().hex}{file_extension}"
            file_path = upload_dir / unique_filename
            
            # Save file
            file.save(str(file_path))
            
            # Extract PDF metadata
            pdf_info = self._extract_pdf_info(file_path)
            
            file_info = {
                "original_name": file.filename,
                "saved_name": unique_filename,
                "file_path": str(file_path),
                "file_size": file.content_length,
                "file_type": file_type,
                "pdf_info": pdf_info
            }
            
            logger.info(f"File processed successfully: {file.filename} -> {unique_filename}")
            
            return {
                "success": True,
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to process {file.filename}: {str(e)}"
            }
    
    def _validate_file(self, file: FileStorage) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check if file exists
        if not file or not file.filename:
            return {"valid": False, "error": "No file provided"}
        
        # Check file extension
        if not self.config.is_allowed_file(file.filename):
            return {
                "valid": False, 
                "error": f"Invalid file type. Only PDF files are allowed."
            }
        
        # Check file size
        max_size = self.config.MAX_CONTENT_LENGTH
        if file.content_length and file.content_length > max_size:
            max_size_mb = self.config.get_file_size_limit_mb()
            return {
                "valid": False,
                "error": f"File too large. Maximum size is {max_size_mb:.0f}MB"
            }
        
        return {"valid": True}
    
    def _extract_pdf_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic PDF information"""
        # Temporarily return basic info without PDF parsing
        try:
            # Get file size
            file_size = file_path.stat().st_size
            
            return {
                "pages": 1,  # Default assumption
                "title": file_path.name,
                "author": "",
                "subject": "",
                "creator": "",
                "file_size": file_size
            }
                
        except Exception as e:
            logger.warning(f"Could not extract PDF info from {file_path}: {e}")
            return {
                "pages": 1,
                "title": file_path.name,
                "author": "",
                "subject": "",
                "creator": "",
                "file_size": 0
            }
    
    def get_upload_files(self, upload_id: str) -> Dict[str, Any]:
        """Get information about uploaded files"""
        try:
            upload_dir = self.upload_folder / upload_id
            if not upload_dir.exists():
                return {"success": False, "error": "Upload not found"}
            
            files = {
                "drawings": [],
                "specifications": []
            }
            
            # Scan for drawing files
            for file_path in upload_dir.glob("drawing_*"):
                if file_path.is_file():
                    files["drawings"].append(str(file_path))
            
            # Scan for specification files
            for file_path in upload_dir.glob("specification_*"):
                if file_path.is_file():
                    files["specifications"].append(str(file_path))
            
            return {
                "success": True,
                "upload_id": upload_id,
                "upload_dir": str(upload_dir),
                "files": files
            }
            
        except Exception as e:
            logger.error(f"Error getting upload files: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_upload(self, upload_id: str) -> bool:
        """Clean up uploaded files"""
        try:
            upload_dir = self.upload_folder / upload_id
            if upload_dir.exists():
                import shutil
                shutil.rmtree(upload_dir)
                logger.info(f"Cleaned up upload: {upload_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up upload {upload_id}: {e}")
            return False 