"""
Structured Output Schemas for Gemini AI
Pydantic models for consistent and reliable JSON output from Gemini API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for matching results"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive matching"""
        if isinstance(value, str):
            upper_value = value.upper()
            for member in cls:
                if member.value == upper_value:
                    return member
        return None


class Discipline(str, Enum):
    """Construction disciplines"""
    ARCHITECTURAL = "Architectural"
    STRUCTURAL = "Structural"
    MECHANICAL = "Mechanical"
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    CIVIL = "Civil"
    LANDSCAPE = "Landscape"
    FIRE_PROTECTION = "Fire Protection"
    GENERAL = "General"


class SheetInfo(BaseModel):
    """Sheet information extracted from drawings"""
    sheet_number: str = Field(description="Sheet number (e.g., A1.1, S-01)")
    sheet_title: str = Field(description="Sheet title/name")
    discipline: Discipline = Field(description="Construction discipline")
    project_info: Optional[str] = Field(default=None, description="Project information")


class SpecificationInfo(BaseModel):
    """Specification information extracted from documents"""
    division: str = Field(description="CSI division number (e.g., 03)")
    section_code: Optional[str] = Field(default=None, description="CSI section code (e.g., 03 30 00)")
    title: str = Field(description="Specification title")
    page_number: Optional[str] = Field(default=None, description="Page number")
    extraction_confidence: ConfidenceLevel = Field(description="Confidence in extraction")


class ChecklistMatch(BaseModel):
    """Individual checklist item match result"""
    checklist_index: int = Field(description="Index of the checklist item in the batch")
    checklist_item: Dict[str, Any] = Field(description="Original checklist item data")
    found: bool = Field(description="Whether the item was found in documents")
    confidence: ConfidenceLevel = Field(description="Confidence level of the match")
    sheet_references: List[str] = Field(default_factory=list, description="Sheet numbers where found")
    spec_references: List[str] = Field(default_factory=list, description="Specification sections where found")
    notes: str = Field(description="Additional notes about the match")
    reasoning: str = Field(description="Detailed reasoning for the match")
    validation_score: float = Field(ge=0.0, le=1.0, description="Validation score (0.0 to 1.0)")


class BatchMatchResult(BaseModel):
    """Result of processing a batch of checklist items"""
    matches: List[ChecklistMatch] = Field(description="List of checklist item matches")
    total_items: int = Field(description="Total number of items in batch")
    found_count: int = Field(description="Number of items found")
    not_found_count: int = Field(description="Number of items not found")
    processing_time: float = Field(description="Processing time in seconds")
    model_used: str = Field(description="Gemini model used")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")


class DocumentSummary(BaseModel):
    """Summary of processed documents"""
    document_overview: str = Field(description="Comprehensive document overview")
    project_scope: str = Field(description="Description of project scope")
    key_systems: List[str] = Field(description="Key systems identified")
    major_specifications: List[str] = Field(description="Major specifications found")
    drawing_summary: str = Field(description="Drawing organization summary")


class SpecificationExtractionResult(BaseModel):
    """Result of specification extraction"""
    specifications: List[SpecificationInfo] = Field(description="List of extracted specifications")
    total_specifications: int = Field(description="Total number of specifications found")


class SheetExtractionResult(BaseModel):
    """Result of sheet information extraction"""
    sheet_number: str = Field(description="Extracted sheet number")
    sheet_title: str = Field(description="Extracted sheet title")
    discipline: Discipline = Field(description="Extracted discipline")
    project_info: Optional[str] = Field(default=None, description="Project information")


class ValidationResult(BaseModel):
    """Result of reference validation"""
    is_valid: bool = Field(description="Whether the reference is valid")
    confidence: float = Field(ge=0.0, le=1.0, description="Validation confidence")
    corrected_value: Optional[str] = Field(default=None, description="Corrected value if any")
    error_message: Optional[str] = Field(default=None, description="Error message if invalid")
    validation_details: Dict[str, Any] = Field(description="Detailed validation information")


class ProcessingMetadata(BaseModel):
    """Metadata about processing operations"""
    batch_size: int = Field(description="Number of items in batch")
    processing_time: float = Field(description="Processing time in seconds")
    confidence_threshold: float = Field(ge=0.0, le=1.0, description="Confidence threshold used")
    model_used: str = Field(description="Gemini model used")
    cache_hit: bool = Field(description="Whether cache was used")


class ErrorResponse(BaseModel):
    """Error response structure"""
    error: str = Field(description="Error message")
    reason: str = Field(description="Reason for error")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.LOW, description="Confidence level")
    validation_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation score")


# Schema configurations for Gemini structured output
class StructuredOutputSchemas:
    """Collection of schemas for different Gemini API calls"""
    
    @staticmethod
    def get_checklist_matching_schema() -> type[BatchMatchResult]:
        """Schema for checklist matching results"""
        return BatchMatchResult
    
    @staticmethod
    def get_specification_extraction_schema() -> type[SpecificationExtractionResult]:
        """Schema for specification extraction results"""
        return SpecificationExtractionResult
    
    @staticmethod
    def get_sheet_extraction_schema() -> type[SheetExtractionResult]:
        """Schema for sheet information extraction results"""
        return SheetExtractionResult
    
    @staticmethod
    def get_document_summary_schema() -> type[DocumentSummary]:
        """Schema for document summary results"""
        return DocumentSummary
    
    @staticmethod
    def get_validation_schema() -> type[ValidationResult]:
        """Schema for validation results"""
        return ValidationResult
    
    @staticmethod
    def get_error_schema() -> type[ErrorResponse]:
        """Schema for error responses"""
        return ErrorResponse


# Utility functions for schema validation
def validate_checklist_match(data: Dict[str, Any]) -> ChecklistMatch:
    """Validate and create a ChecklistMatch from raw data"""
    return ChecklistMatch(**data)


def validate_batch_result(data: Dict[str, Any]) -> BatchMatchResult:
    """Validate and create a BatchMatchResult from raw data"""
    return BatchMatchResult(**data)


def validate_specification_result(data: Dict[str, Any]) -> SpecificationExtractionResult:
    """Validate and create a SpecificationExtractionResult from raw data"""
    return SpecificationExtractionResult(**data)


def validate_sheet_result(data: Dict[str, Any]) -> SheetExtractionResult:
    """Validate and create a SheetExtractionResult from raw data"""
    return SheetExtractionResult(**data)


def validate_document_summary(data: Dict[str, Any]) -> DocumentSummary:
    """Validate and create a DocumentSummary from raw data"""
    return DocumentSummary(**data) 