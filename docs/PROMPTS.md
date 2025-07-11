# Prompt Templates

## Overview

The Construction Checklist Matching System uses carefully crafted prompts to interact with Google Gemini AI for document analysis and checklist matching. These prompts are specifically designed for the construction industry and follow CSI (Construction Specifications Institute) standards.

## 🎯 Prompt Categories

### 1. Document Reference Extraction

#### Specification Reference Finding

**Purpose**: Extract division numbers, specification codes, and specification names from construction specification documents.

**Prompt Template**:
```
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
```

#### Sheet Information Extraction

**Purpose**: Extract sheet numbers, titles, and discipline information from construction drawings.

**Prompt Template**:
```
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
```

#### Enhanced Sheet Information Extraction (with Image)

**Purpose**: Extract comprehensive sheet information using both visual and text data.

**Prompt Template**:
```
You are analyzing a construction/architectural drawing page. I have provided you with both the image of the sheet extracted from it.

STEP 1: First, examine the IMAGE carefully, especially the title block area (usually in the bottom-right corner of the drawing).

STEP 2: Use both the visual information from the image below to extract accurate sheet information.

EXTRACTION TASK:
Extract FOUR types of information by looking at the title block in the image:

1. SHEET NUMBER: The alphanumeric identifier (like "A1.1", "S-01", "M-101", "E-02", etc.)
2. SHEET TITLE: The descriptive name that explains what the drawing shows
3. DISCIPLINE: The engineering discipline (full name, not abbreviation)
4. PROJECT INFO: Basic project information from the title block

VISUAL GUIDANCE:
- Look at the TITLE BLOCK in the image (typically bottom-right corner)
- Title blocks are usually bordered rectangular areas with organized text fields
- The sheet number is often in a dedicated box/field
- The sheet title is usually the main descriptive text in the title block
- Ignore room labels, dimension text, and drawing callouts scattered throughout the sheet

SHEET NUMBER examples:
- "A1.1", "A-101", "A001", "ARCH-01" (Architectural)
- "S-01", "S101", "S1", "STRUCT-01" (Structural) 
- "M-01", "M101", "MECH-01", "HVAC-01" (Mechanical)
- "E-01", "E101", "ELEC-1", "ELECTRICAL-01" (Electrical)
- "C-01", "C101", "CIVIL-01" (Civil)

SHEET TITLE examples:
- "SITE PLAN", "FLOOR PLAN", "ROOF PLAN", "FOUNDATION PLAN"
- "ELEVATIONS", "SECTIONS", "DETAILS", "SCHEDULES"
- "ENLARGED PLAN & ELEVATIONS", "STRUCTURAL FRAMING PLAN"

DISCIPLINE CLASSIFICATION (use FULL NAMES in response):
- A-prefix or ARCH → Use "Architectural"
- S-prefix or STRUCT → Use "Structural"
- M-prefix or MECH → Use "Mechanical"
- E-prefix or ELEC → Use "Electrical"
- C-prefix or CIVIL → Use "Civil"
- P-prefix or PLUMB → Use "Plumbing"
- L-prefix or LAND → Use "Landscape"
- FP-prefix or FIRE → Use "Fire Protection"
- If no clear prefix, use "General"

IMPORTANT:
- Prioritize what you see in the title block area of the IMAGE
- Use the OCR text to help identify and confirm what you see visually
- If you cannot find a sheet number, use an empty string: ""
- If you cannot find a sheet title, use: "Untitled Drawing"
- For discipline field, use FULL NAMES like "Architectural", "Structural", "Mechanical", etc.
- Focus on formal title block information, not room labels or dimension text

RESPONSE FORMAT:
Return your response in this exact JSON format:
{
  "sheet_number": "A1.1",
  "sheet_title": "FLOOR PLAN",
  "discipline": "Architectural",
  "project_info": "Project Name - Building A"
}
```

### 2. Checklist Matching Prompts

#### Basic Checklist Matching

**Purpose**: Match checklist items against document content to find references.

**Prompt Template**:
```
You are an AI assistant specialized in construction document analysis. Your task is to analyze the provided construction documents and match them against the given checklist items.

DOCUMENTS PROVIDED:
- Construction Drawings: [Drawing file information]
- Specifications: [Specification file information]

CHECKLIST ITEM TO ANALYZE:
[Checklist item details]

INSTRUCTIONS:
1. Analyze both the drawings and specifications for references to this checklist item
2. Look for direct mentions, related concepts, and implied references
3. Extract specific sheet numbers and specification sections where found
4. Provide confidence level (HIGH, MEDIUM, LOW) based on clarity of reference
5. Include reasoning for your assessment

RESPONSE FORMAT:
{
  "found": true/false,
  "sheet_number": "A1.1, S-01",
  "spec_section": "03 30 00",
  "notes": "Brief description of where found",
  "reasoning": "Explanation of why this matches",
  "confidence": "HIGH/MEDIUM/LOW"
}
```

#### Enhanced Checklist Matching with System Instructions

**Purpose**: Advanced checklist matching with construction-specific context and validation.

**Prompt Template**:
```
You are a construction document analysis expert with deep knowledge of:
- CSI MasterFormat specification standards
- Construction drawing conventions and symbols
- Building codes and industry standards
- Project management and quality control processes

Your task is to analyze construction documents and match them against checklist items with high accuracy and detailed reasoning.

ANALYSIS CONTEXT:
- Construction Drawings: [Drawing file with sheet information]
- Specifications: [Specification file with division/section information]
- Checklist Item: [Specific item to match]

MATCHING CRITERIA:
1. Direct References: Exact mentions or clear references
2. Related Concepts: Similar terminology or related processes
3. Implied References: Items that would logically be addressed
4. Cross-References: Connections between drawings and specifications

CONFIDENCE LEVELS:
- HIGH: Clear, direct reference with specific location
- MEDIUM: Related reference with some ambiguity
- LOW: Possible reference but unclear or indirect

RESPONSE FORMAT:
{
  "found": true/false,
  "sheet_number": "A1.1, S-01",
  "spec_section": "03 30 00",
  "notes": "Detailed description of where and how found",
  "reasoning": "Comprehensive explanation of matching logic",
  "confidence": "HIGH/MEDIUM/LOW",
  "validation_score": 0.95
}
```

### 3. Document Summary Prompts

#### Document Overview

**Purpose**: Generate comprehensive summaries of construction documents.

**Prompt Template**:
```
You are analyzing construction documents to provide a comprehensive overview.

DOCUMENTS:
- Drawings: [Drawing file information]
- Specifications: [Specification file information]

TASK:
Provide a detailed summary including:
1. Document types and general content
2. Key project information
3. Major systems and components
4. Notable specifications and requirements
5. Drawing sheet organization
6. Overall project scope

RESPONSE FORMAT:
{
  "document_overview": "Comprehensive summary",
  "project_scope": "Description of project scope",
  "key_systems": ["System 1", "System 2"],
  "major_specifications": ["Spec 1", "Spec 2"],
  "drawing_summary": "Drawing organization summary"
}
```

## 🔧 Prompt Engineering Principles

### 1. Construction Domain Expertise

All prompts are designed with construction industry knowledge:
- **CSI MasterFormat**: Standard specification organization
- **Drawing Conventions**: Standard architectural/engineering symbols
- **Industry Terminology**: Construction-specific language
- **Quality Standards**: Industry best practices and requirements

### 2. Structured Output

Prompts consistently request structured JSON responses:
- **Consistent Fields**: Standard response format across all prompts
- **Validation**: Built-in confidence scoring and validation
- **Error Handling**: Graceful handling of missing or unclear information
- **Extensibility**: Easy to add new fields as needed

### 3. Context Awareness

Prompts leverage multiple sources of information:
- **Multi-Document**: Analysis across drawings and specifications
- **Cross-Reference**: Connections between different document types
- **Visual + Text**: Combined analysis of images and text
- **Temporal Context**: Understanding of project phases and sequences

### 4. Confidence Scoring

Built-in confidence assessment:
- **HIGH**: Clear, direct references with specific locations
- **MEDIUM**: Related references with some ambiguity
- **LOW**: Possible references but unclear or indirect

## 📊 Response Formats

### Standard Response Structure

```json
{
  "found": true,
  "sheet_number": "A1.1, S-01",
  "spec_section": "03 30 00",
  "notes": "Found in structural drawings and concrete specifications",
  "reasoning": "Direct reference to concrete foundation requirements",
  "confidence": "HIGH",
  "validation_score": 0.95
}
```

### Error Response Structure

```json
{
  "error": "Unable to process document",
  "reason": "Document format not supported",
  "confidence": "LOW",
  "validation_score": 0.0
}
```

## 🛡️ Validation and Quality Control

### 1. Reference Validation

- **Format Checking**: Validate sheet numbers and specification codes
- **Pattern Matching**: Use regex patterns for standard formats
- **Cross-Reference**: Verify references exist in documents
- **Confidence Scoring**: Assess reliability of extracted information

### 2. Error Handling

- **Graceful Degradation**: Continue processing on partial failures
- **Default Values**: Provide sensible defaults for missing information
- **Error Reporting**: Clear error messages and reasons
- **Recovery**: Automatic retry and fallback mechanisms

### 3. Quality Metrics

- **Accuracy**: Measure against known correct references
- **Completeness**: Assess coverage of available information
- **Consistency**: Check for logical consistency across responses
- **Performance**: Monitor processing time and resource usage

## 🔄 Prompt Optimization

### 1. Performance Optimization

- **Token Efficiency**: Minimize prompt length while maintaining clarity
- **Batch Processing**: Optimize for processing multiple items
- **Caching**: Reuse successful prompt patterns
- **Parallel Processing**: Process multiple prompts simultaneously

### 2. Accuracy Improvement

- **Feedback Loop**: Learn from validation results
- **Prompt Refinement**: Iteratively improve prompt effectiveness
- **Domain Expertise**: Incorporate construction industry knowledge
- **Error Analysis**: Study and address common failure patterns

### 3. Adaptability

- **Document Types**: Adapt to different document formats
- **Project Types**: Adjust for different construction projects
- **Regional Standards**: Accommodate different building codes
- **Technology Evolution**: Update for new AI capabilities

## 📚 Best Practices

### 1. Prompt Design

- **Clear Instructions**: Explicit, unambiguous directions
- **Context Provision**: Provide relevant background information
- **Example Formatting**: Show expected input/output formats
- **Error Handling**: Include instructions for edge cases

### 2. Construction Knowledge

- **Industry Standards**: Reference relevant codes and standards
- **Terminology**: Use precise construction terminology
- **Process Understanding**: Consider construction workflows
- **Quality Focus**: Emphasize accuracy and reliability

### 3. System Integration

- **API Compatibility**: Ensure prompts work with Gemini API
- **Response Parsing**: Design for easy JSON parsing
- **Error Recovery**: Include fallback strategies
- **Monitoring**: Enable performance tracking and debugging

## 🎯 Future Enhancements

### 1. Advanced Prompting

- **Multi-Modal**: Enhanced image and text analysis
- **Contextual Memory**: Maintain context across multiple interactions
- **Adaptive Prompts**: Dynamic prompt adjustment based on results
- **Specialized Models**: Domain-specific fine-tuning

### 2. Construction Intelligence

- **Code Compliance**: Automatic building code checking
- **Best Practices**: Industry standard validation
- **Risk Assessment**: Identify potential issues and conflicts
- **Cost Estimation**: Integrate with cost analysis systems

### 3. User Experience

- **Natural Language**: More conversational interaction
- **Visual Feedback**: Enhanced result presentation
- **Interactive Refinement**: User-guided prompt adjustment
- **Learning System**: Continuous improvement from user feedback

---

These prompt templates provide a solid foundation for construction document analysis and checklist matching. They are designed to be robust, accurate, and adaptable to different project types and requirements. 