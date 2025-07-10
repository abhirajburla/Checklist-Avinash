"""
Reference Extraction and Validation
Validates and improves document reference extraction from construction documents
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .logger_config import LoggerConfig
except ImportError:
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

class ReferenceType(Enum):
    """Types of document references"""
    SHEET_NUMBER = "sheet_number"
    SPECIFICATION_SECTION = "specification_section"
    PAGE_NUMBER = "page_number"
    DIVISION_CODE = "division_code"

@dataclass
class ValidationResult:
    """Result of reference validation"""
    is_valid: bool
    confidence: float
    corrected_value: Optional[str]
    error_message: Optional[str]
    validation_details: Dict[str, Any]

class ReferenceValidator:
    """Validates and corrects document references"""
    
    def __init__(self):
        # CSI MasterFormat divisions (00-49)
        self.csi_divisions = {
            '00': 'Procurement and Contracting Requirements',
            '01': 'General Requirements',
            '02': 'Existing Conditions',
            '03': 'Concrete',
            '04': 'Masonry',
            '05': 'Metals',
            '06': 'Wood, Plastics, and Composites',
            '07': 'Thermal and Moisture Protection',
            '08': 'Openings',
            '09': 'Finishes',
            '10': 'Specialties',
            '11': 'Equipment',
            '12': 'Furnishings',
            '13': 'Special Construction',
            '14': 'Conveying Equipment',
            '15': 'Reserved',
            '16': 'Reserved',
            '17': 'Reserved',
            '18': 'Reserved',
            '19': 'Reserved',
            '20': 'Reserved',
            '21': 'Fire Suppression',
            '22': 'Plumbing',
            '23': 'HVAC',
            '24': 'Reserved',
            '25': 'Integrated Automation',
            '26': 'Electrical',
            '27': 'Communications',
            '28': 'Electronic Safety and Security',
            '29': 'Reserved',
            '30': 'Reserved',
            '31': 'Earthwork',
            '32': 'Exterior Improvements',
            '33': 'Utilities',
            '34': 'Transportation',
            '35': 'Waterway and Marine Construction',
            '36': 'Reserved',
            '37': 'Reserved',
            '38': 'Reserved',
            '39': 'Reserved',
            '40': 'Process Integration',
            '41': 'Material Processing and Handling Equipment',
            '42': 'Process Heating, Cooling, and Drying Equipment',
            '43': 'Process Gas and Liquid Storage, Conditioning, and Disposal Equipment',
            '44': 'Pollution and Waste Control Equipment',
            '45': 'Industry-Specific Manufacturing Equipment',
            '46': 'Water and Wastewater Equipment',
            '47': 'Reserved',
            '48': 'Electrical Power Generation and Transmission Equipment',
            '49': 'Reserved'
        }
        
        # Common sheet number patterns
        self.sheet_patterns = [
            r'^[A-Z]\d+\.\d+$',  # A1.1, B2.3, etc.
            r'^[A-Z]-\d+$',      # A-01, S-02, etc.
            r'^[A-Z]\d+$',       # A1, S2, etc.
            r'^[A-Z]{2,}-\d+$',  # ARCH-01, STRUCT-02, etc.
            r'^\d+$',            # 1, 2, 3, etc.
        ]
        
        # Specification section patterns
        self.spec_patterns = [
            r'^\d{2}\s\d{2}\s\d{2}$',  # 03 30 00
            r'^\d{2}\.\d{2}\.\d{2}$',  # 03.30.00
            r'^\d{2}-\d{2}-\d{2}$',    # 03-30-00
        ]
        
        logger.info("ReferenceValidator initialized")
    
    def validate_sheet_number(self, sheet_number: str) -> ValidationResult:
        """Validate and correct sheet number"""
        
        if not sheet_number or not isinstance(sheet_number, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                corrected_value=None,
                error_message="Sheet number is empty or invalid type",
                validation_details={'type': 'sheet_number', 'input': sheet_number}
            )
        
        # Clean the input
        cleaned = sheet_number.strip().upper()
        
        # Check against patterns
        for pattern in self.sheet_patterns:
            if re.match(pattern, cleaned):
                return ValidationResult(
                    is_valid=True,
                    confidence=0.9,
                    corrected_value=cleaned,
                    error_message=None,
                    validation_details={
                        'type': 'sheet_number',
                        'pattern_matched': pattern,
                        'original': sheet_number,
                        'cleaned': cleaned
                    }
                )
        
        # Try to correct common issues
        corrected = self._correct_sheet_number(cleaned)
        if corrected and corrected != cleaned:
            return ValidationResult(
                is_valid=True,
                confidence=0.7,
                corrected_value=corrected,
                error_message=f"Corrected from '{cleaned}' to '{corrected}'",
                validation_details={
                    'type': 'sheet_number',
                    'original': sheet_number,
                    'cleaned': cleaned,
                    'corrected': corrected,
                    'correction_applied': True
                }
            )
        
        return ValidationResult(
            is_valid=False,
            confidence=0.0,
            corrected_value=None,
            error_message=f"Invalid sheet number format: {sheet_number}",
            validation_details={
                'type': 'sheet_number',
                'original': sheet_number,
                'cleaned': cleaned,
                'patterns_tried': self.sheet_patterns
            }
        )
    
    def validate_specification_section(self, spec_section: str) -> ValidationResult:
        """Validate and correct specification section"""
        
        if not spec_section or not isinstance(spec_section, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                corrected_value=None,
                error_message="Specification section is empty or invalid type",
                validation_details={'type': 'specification_section', 'input': spec_section}
            )
        
        # Clean the input
        cleaned = spec_section.strip()
        
        # Check against patterns
        for pattern in self.spec_patterns:
            if re.match(pattern, cleaned):
                # Validate division code
                division = cleaned.split()[0] if ' ' in cleaned else cleaned.split('.')[0] if '.' in cleaned else cleaned.split('-')[0]
                if division in self.csi_divisions:
                    return ValidationResult(
                        is_valid=True,
                        confidence=0.95,
                        corrected_value=cleaned,
                        error_message=None,
                        validation_details={
                            'type': 'specification_section',
                            'pattern_matched': pattern,
                            'division': division,
                            'division_name': self.csi_divisions[division],
                            'original': spec_section,
                            'cleaned': cleaned
                        }
                    )
        
        # Try to correct common issues
        corrected = self._correct_specification_section(cleaned)
        if corrected and corrected != cleaned:
            return ValidationResult(
                is_valid=True,
                confidence=0.8,
                corrected_value=corrected,
                error_message=f"Corrected from '{cleaned}' to '{corrected}'",
                validation_details={
                    'type': 'specification_section',
                    'original': spec_section,
                    'cleaned': cleaned,
                    'corrected': corrected,
                    'correction_applied': True
                }
            )
        
        return ValidationResult(
            is_valid=False,
            confidence=0.0,
            corrected_value=None,
            error_message=f"Invalid specification section format: {spec_section}",
            validation_details={
                'type': 'specification_section',
                'original': spec_section,
                'cleaned': cleaned,
                'patterns_tried': self.spec_patterns
            }
        )
    
    def validate_page_number(self, page_number: str) -> ValidationResult:
        """Validate page number"""
        
        if not page_number or not isinstance(page_number, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                corrected_value=None,
                error_message="Page number is empty or invalid type",
                validation_details={'type': 'page_number', 'input': page_number}
            )
        
        # Clean the input
        cleaned = page_number.strip()
        
        # Check if it's a valid page number
        if re.match(r'^\d+$', cleaned):
            page_num = int(cleaned)
            if 1 <= page_num <= 10000:  # Reasonable page number range
                return ValidationResult(
                    is_valid=True,
                    confidence=0.9,
                    corrected_value=cleaned,
                    error_message=None,
                    validation_details={
                        'type': 'page_number',
                        'page_number': page_num,
                        'original': page_number,
                        'cleaned': cleaned
                    }
                )
        
        return ValidationResult(
            is_valid=False,
            confidence=0.0,
            corrected_value=None,
            error_message=f"Invalid page number: {page_number}",
            validation_details={
                'type': 'page_number',
                'original': page_number,
                'cleaned': cleaned
            }
        )
    
    def _correct_sheet_number(self, sheet_number: str) -> Optional[str]:
        """Attempt to correct sheet number format"""
        
        # Remove extra spaces and normalize
        cleaned = re.sub(r'\s+', '', sheet_number)
        
        # Common corrections
        corrections = {
            'A1': 'A1.1',
            'A2': 'A2.1',
            'S1': 'S-01',
            'S2': 'S-02',
            'M1': 'M-01',
            'M2': 'M-02',
            'E1': 'E-01',
            'E2': 'E-02',
        }
        
        if cleaned in corrections:
            return corrections[cleaned]
        
        # Try to add missing separators
        if re.match(r'^[A-Z]\d{2,}$', cleaned):
            # A01 -> A-01
            return f"{cleaned[0]}-{cleaned[1:]}"
        
        return None
    
    def _correct_specification_section(self, spec_section: str) -> Optional[str]:
        """Attempt to correct specification section format"""
        
        # Remove extra spaces and normalize
        cleaned = re.sub(r'\s+', '', spec_section)
        
        # Try to format as XX XX XX
        if re.match(r'^\d{6}$', cleaned):
            return f"{cleaned[:2]} {cleaned[2:4]} {cleaned[4:6]}"
        
        # Try to format as XX.XX.XX
        if re.match(r'^\d{2}\d{2}\d{2}$', cleaned):
            return f"{cleaned[:2]}.{cleaned[2:4]}.{cleaned[4:6]}"
        
        return None
    
    def validate_references(self, references: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """Validate all references in a result item"""
        
        validation_results = {}
        
        # Validate sheet numbers
        sheet_numbers = references.get('sheet_references', [])
        if isinstance(sheet_numbers, str):
            sheet_numbers = [sheet_numbers] if sheet_numbers else []
        
        sheet_validations = []
        for sheet_num in sheet_numbers:
            validation = self.validate_sheet_number(sheet_num)
            sheet_validations.append(validation)
        
        validation_results['sheet_references'] = {
            'validations': sheet_validations,
            'all_valid': all(v.is_valid for v in sheet_validations),
            'confidence': sum(v.confidence for v in sheet_validations) / len(sheet_validations) if sheet_validations else 0.0
        }
        
        # Validate specification sections
        spec_sections = references.get('spec_references', [])
        if isinstance(spec_sections, str):
            spec_sections = [spec_sections] if spec_sections else []
        
        spec_validations = []
        for spec_section in spec_sections:
            validation = self.validate_specification_section(spec_section)
            spec_validations.append(validation)
        
        validation_results['spec_references'] = {
            'validations': spec_validations,
            'all_valid': all(v.is_valid for v in spec_validations),
            'confidence': sum(v.confidence for v in spec_validations) / len(spec_validations) if spec_validations else 0.0
        }
        
        return validation_results
    
    def validate_batch_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and correct all references in batch results"""
        
        validated_results = []
        
        for result in results:
            validated_result = result.copy()
            
            # Validate references if item was found
            if result.get('found', False):
                references = {
                    'sheet_references': result.get('sheet_number', '').split(', ') if result.get('sheet_number') else [],
                    'spec_references': result.get('spec_section', '').split(', ') if result.get('spec_section') else []
                }
                
                validation_results = self.validate_references(references)
                
                # Apply corrections
                corrected_sheet_numbers = []
                for validation in validation_results['sheet_references']['validations']:
                    if validation.is_valid and validation.corrected_value:
                        corrected_sheet_numbers.append(validation.corrected_value)
                
                corrected_spec_sections = []
                for validation in validation_results['spec_references']['validations']:
                    if validation.is_valid and validation.corrected_value:
                        corrected_spec_sections.append(validation.corrected_value)
                
                # Update result with corrected references
                validated_result['sheet_number'] = ', '.join(corrected_sheet_numbers)
                validated_result['spec_section'] = ', '.join(corrected_spec_sections)
                
                # Add validation metadata
                validated_result['validation_metadata'] = {
                    'sheet_confidence': validation_results['sheet_references']['confidence'],
                    'spec_confidence': validation_results['spec_references']['confidence'],
                    'overall_confidence': (validation_results['sheet_references']['confidence'] + 
                                         validation_results['spec_references']['confidence']) / 2
                }
                
                # Adjust confidence if validation failed
                if not validation_results['sheet_references']['all_valid'] or not validation_results['spec_references']['all_valid']:
                    validated_result['confidence'] = 'MEDIUM'  # Downgrade confidence if validation issues
            
            validated_results.append(validated_result)
        
        return validated_results 