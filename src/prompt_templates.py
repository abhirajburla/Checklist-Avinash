import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PromptTemplates:
    """Prompt templates for checklist matching system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_specification_extraction_prompt(self) -> str:
        """Get the specification reference extraction prompt"""
        return """
You are an AI assistant specialized in analyzing construction specification documents. Your task is to extract division numbers, specification codes, and specification names from the Table of Contents (TOC) of this construction specification document.

EXTRACTION RULES:
1. Look for the Table of Contents, Index, or similar section
2. Extract CSI division numbers (01, 02, 03, etc.) 
3. Extract specification section codes (like 01 11 00, 03 30 00, etc.)
4. Extract specification names/titles (like "Summary", "Cast-in-Place Concrete", etc.)
5. Focus on standard CSI format specifications
6. Ignore general document sections (Cover, Index, etc.)

COMMON CSI DIVISION PATTERNS:
- Division 00: Procurement and Contracting Requirements
- Division 01: General Requirements  
- Division 02: Existing Conditions
- Division 03: Concrete
- Division 04: Masonry
- Division 05: Metals
- Division 06: Wood, Plastics, and Composites
- Division 07: Thermal and Moisture Protection
- Division 08: Openings
- Division 09: Finishes
- Division 10: Specialties
- Division 11: Equipment
- Division 12: Furnishings
- Division 13: Special Construction
- Division 14: Conveying Equipment
- Division 15: Reserved
- Division 16: Reserved
- Division 17: Reserved
- Division 18: Reserved
- Division 19: Reserved
- Division 20: Reserved
- Division 21: Fire Suppression
- Division 22: Plumbing
- Division 23: HVAC
- Division 24: Reserved
- Division 25: Integrated Automation
- Division 26: Electrical
- Division 27: Communications
- Division 28: Electronic Safety and Security
- Division 29: Reserved
- Division 30: Reserved
- Division 31: Earthwork
- Division 32: Exterior Improvements
- Division 33: Utilities
- Division 34: Transportation
- Division 35: Waterway and Marine Construction

EXPECTED FORMATS TO LOOK FOR:
- "Division 03 - Concrete"
- "03 30 00 Cast-in-Place Concrete"
- "Section 09 91 23 Interior Painting"
- "09 00 00 FINISHES"

INSTRUCTIONS:
1. Scan through the provided text looking for table of contents patterns
2. Extract each specification entry that follows CSI format
3. Organize by division number
4. Include section codes when available
5. Provide clear specification names/titles

Important Notes:
- Focus on actual specification sections, not general document sections
- If no clear TOC is found, extract any specification-like entries
- Division numbers should be 2-digit format (01, 02, etc.)
- Section codes should follow CSI format when available
- Include page numbers if clearly indicated
- Set extraction_confidence to "High", "Medium", or "Low" based on clarity of the TOC

RESPONSE FORMAT:
Return your response in this exact JSON format:
{
  "specifications": [
    {
      "division": "03",
      "section_code": "03 30 00",
      "title": "Cast-in-Place Concrete",
      "page_number": "15",
      "extraction_confidence": "High"
    }
  ],
  "total_specifications": 1
}
"""
    
    def get_sheet_extraction_prompt(self) -> str:
        """Get the sheet title/name extraction prompt"""
        return """
You are analyzing a construction/architectural drawing page to extract sheet information.

INSTRUCTIONS:
Extract two types of information:

1. SHEET NUMBER: The alphanumeric identifier (like "A1.1", "S-01", "M-101", "E-02", etc.)
2. SHEET TITLE: The descriptive name that explains what the drawing shows

SHEET NUMBER examples:
- "A1.1", "A-101", "A001", "ARCH-01" (Architectural)
- "S-01", "S101", "S1", "STRUCT-01" (Structural) 
- "M-01", "M101", "MECH-01", "HVAC-01" (Mechanical)
- "E-01", "E101", "ELEC-1", "ELECTRICAL-01" (Electrical)

SHEET TITLE examples:
- "SITE PLAN", "FLOOR PLAN", "ROOF PLAN", "FOUNDATION PLAN"
- "ELEVATIONS", "SECTIONS", "DETAILS", "SCHEDULES"

IMPORTANT:
- If you cannot find a sheet number, use an empty string: ""
- If you cannot find a sheet title, use: "Untitled"
- Return empty array [] if no details found
- Look throughout the entire sheet for details, not just title blocks
- Pay attention to text near drawings, figures, and technical diagrams
- Return ONLY the JSON, no other text
- Clean up extracted text (remove extra spaces, proper capitalization)

RESPONSE FORMAT:
Return your response in this exact JSON format:
{
  "sheet_number": "A1.1",
  "sheet_title": "FLOOR PLAN",
  "discipline": "Architectural",
  "project_info": "Project Name - Building A"
}
"""
    
    def get_checklist_matching_prompt(self, checklist_batch: List[Dict], document_context: str) -> str:
        """Get the checklist matching prompt for a batch of items"""
        
        # Format checklist items for the prompt
        checklist_text = ""
        for i, item in enumerate(checklist_batch, 1):
            checklist_text += f"{i}. Category: {item['Category']}\n"
            checklist_text += f"   Scope: {item['Scope of Work']}\n"
            checklist_text += f"   Checklist: {item['Checklist']}\n"
            checklist_text += f"   Sector: {item['Sector']}\n\n"
        
        return f"""
You are an AI assistant specialized in construction document analysis. Your task is to match checklist items against the provided construction documents (drawings and specifications).

CRITICAL VALIDATION RULES:
1. ONLY reference sheet numbers, specification codes, or page numbers that ACTUALLY EXIST in the uploaded documents
2. DO NOT generate or invent any references that are not explicitly present in the documents
3. If you cannot find a specific sheet number or spec code in the documents, use empty arrays: []
4. Be extremely conservative - if in doubt, mark as "not found" rather than hallucinating references
5. Validate every reference against the actual document content before including it

DOCUMENT CONTEXT:
The following construction documents have been uploaded and processed:
{document_context}

CHECKLIST ITEMS TO MATCH:
{checklist_text}

MATCHING INSTRUCTIONS:
1. For each checklist item, determine if it is mentioned or referenced in the documents
2. Look for related concepts, not just exact phrase matches
3. Consider construction terminology, abbreviations, and industry standards
4. Focus on high-confidence matches only
5. Extract relevant document references (sheet numbers, spec sections) ONLY if they actually exist

MATCHING CRITERIA:
- HIGH CONFIDENCE: Direct mention or clear reference to the checklist item
- MEDIUM CONFIDENCE: Related concept or similar requirement
- LOW CONFIDENCE: Possible connection but unclear
- NO MATCH: Item not found in documents

REFERENCE EXTRACTION:
- For drawings: Extract sheet numbers ONLY if they actually exist (e.g., "A1.1", "S-01", "M-101")
- For specifications: Extract section codes ONLY if they actually exist (e.g., "03 30 00", "09 91 23")
- Include multiple references ONLY if they actually appear in multiple places
- If no specific references found, use empty arrays: []

RESPONSE FORMAT:
Return your response in this exact JSON format:
{{
  "matches": [
    {{
      "checklist_index": 1,
      "found": true,
      "confidence": "HIGH",
      "sheet_references": ["A1.1", "A1.2"],
      "spec_references": ["03 30 00"],
      "notes": "Found in architectural drawings and concrete specifications",
      "reasoning": "The checklist item about concrete work is directly referenced in the structural drawings and concrete specification section"
    }}
  ],
  "total_items": {len(checklist_batch)},
  "found_count": 0,
  "not_found_count": 0
}}

IMPORTANT:
- Only mark items as found if you have high confidence
- Provide clear reasoning for each match
- NEVER invent or generate references that don't exist in the uploaded documents
- If you cannot find specific sheet numbers or spec codes, use empty arrays: []
- Be extremely conservative - better to miss a match than to hallucinate references
"""
    
    def get_document_summary_prompt(self, file_paths: List[str]) -> str:
        """Get prompt for creating document summary"""
        return f"""
You are analyzing construction documents to create a summary for checklist matching.

DOCUMENT FILES:
{chr(10).join([f"- {path}" for path in file_paths])}

TASK:
Create a comprehensive summary of the construction documents that will be used for checklist matching.

INCLUDE:
1. Document types (drawings vs specifications)
2. Key construction elements mentioned
3. Major systems and components
4. Project scope and scale
5. Important specifications and requirements

FORMAT:
Provide a structured summary that can be used as context for matching checklist items against these documents.

RESPONSE FORMAT:
Return your response in this exact JSON format:
{{
  "document_summary": "Comprehensive summary of the construction documents...",
  "key_elements": ["element1", "element2", "element3"],
  "major_systems": ["system1", "system2"],
  "project_scope": "Description of project scope and scale"
}}
""" 