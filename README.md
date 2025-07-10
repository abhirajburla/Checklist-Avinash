# 🔍 Checklist Matching System

A construction tech solution that automatically matches construction drawings and specifications against a master checklist to identify relevant items and their document references.

## 🏗️ Project Overview

This system helps General Contractors and Subcontractors by:
- Automatically processing construction drawings and specifications
- Matching content against a comprehensive master checklist (1,365+ items)
- Generating structured JSON output with document references
- Reducing manual effort in bid preparation and project planning

## 🚀 Features

- **Separate Document Upload**: Distinct upload areas for drawings and specifications
- **Gemini AI Integration**: Uses Google's Gemini API for document analysis and matching
- **Context Caching**: Efficient processing with Gemini's context caching for large documents
- **Batch Processing**: Processes checklist items in manageable batches (50 items at a time)
- **Progress Tracking**: Real-time progress monitoring with status updates
- **JSON Output**: Structured results matching the master checklist format
- **Reference Extraction**: Identifies sheet numbers and specification sections

## 📁 Project Structure

```
Checklist-Avinash/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── MASTER CHECKLIST_TEST_50.csv   # Test checklist data (50 items)
├── MASTER CHECKLIST.csv           # Full master checklist data (1,300+ items)
├── Prompts.txt                     # Existing prompts from scope builder
├── .env                           # Environment variables (contains GEMINI_API_KEY)
├── src/                           # Source code modules
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── checklist_processor.py     # Master checklist processing
│   ├── document_handler.py        # Document upload and processing
│   ├── gemini_client.py           # Gemini API integration
│   ├── matching_engine.py         # Core matching logic
│   └── prompt_templates.py        # Prompt templates for AI
├── templates/                     # HTML templates
│   └── index.html                 # Main upload interface
├── uploads/                       # Document uploads (created automatically)
├── cache/                         # Caching directory (created automatically)
└── results/                       # Processing results (created automatically)
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Gemini API key (set in .env file)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Checklist-Avinash
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Ensure your `.env` file contains:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Verify master checklist**
   - Ensure `MASTER CHECKLIST_TEST_50.csv` is in the project root (for testing)
   - For production, use `MASTER CHECKLIST.csv` (1,300+ items)
   - The file should contain columns: Category, Scope of Work, Checklist, Sector

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the interface**
   - Open your browser to `http://localhost:5000`

## 📊 Master Checklist Format

The system expects a CSV file with the following columns:
- **Category**: Pre-Bid, Pre-Award
- **Scope of Work**: CSI division codes (e.g., "02 40 00 Demolition")
- **Checklist**: Specific checklist item text
- **Sector**: Industrial, Housing, General

## 🔄 Processing Workflow

1. **Document Upload**
   - Users upload drawings and specifications separately
   - Files are validated (PDF only, max 800MB each)

2. **Document Processing**
   - Files are processed and cached using Gemini's context caching
   - Document references are extracted (sheet numbers, spec sections)

3. **Checklist Matching**
   - Master checklist is loaded and divided into batches of 50 items
   - Each batch is processed iteratively against the cached documents
   - AI matches checklist items to document content with high confidence

4. **Results Generation**
   - JSON output is generated maintaining master checklist order
   - Each item includes: category, scope_of_work, checklist, sheet_number, spec_section, notes, reasoning

## 📄 Output Format

```json
[
  {
    "row_id": 1,
    "category": "Pre-Bid",
    "scope_of_work": "02 40 00 Demolition",
    "checklist": "Backfill any remaining holes with approved structural fill",
    "sector": "Industrial",
    "sheet_number": "S-01, S-02",
    "spec_section": "02 40 00 Demolition",
    "notes": "",
    "reasoning": "Found in structural drawings and demolition specifications",
    "found": true
  }
]
```

## 🛠️ API Endpoints

- `GET /` - Main upload interface
- `POST /upload` - Upload documents
- `POST /process` - Start checklist processing
- `GET /status/<process_id>` - Get processing status
- `GET /results/<process_id>` - Get final results

## ⚙️ Configuration

Key configuration options in `src/config.py`:
- `BATCH_SIZE`: Number of checklist items per batch (default: 50)
- `MAX_CONTENT_LENGTH`: Maximum file size (default: 800MB)
- `GEMINI_MODEL`: Gemini model to use (default: gemini-2.5-pro)
- `ENABLE_CONTEXT_CACHING`: Enable/disable context caching (default: true)

## 🧪 Development Status

**Phase 1: Project Structure Setup** ✅ COMPLETED
- [x] Basic project structure created
- [x] Configuration management implemented
- [x] Master checklist processor created
- [x] HTML upload interface developed
- [x] Flask application skeleton ready

**Phase 2: Document Processing** 🔄 NEXT
- [ ] Document handler implementation
- [ ] Gemini client with context caching
- [ ] Prompt templates adaptation

**Phase 3: Matching Engine** 🔄 PENDING
- [ ] Core matching logic
- [ ] Batch processing implementation
- [ ] Progress tracking system

**Phase 4: Output Generation** 🔄 PENDING
- [ ] JSON formatting
- [ ] Results compilation
- [ ] Error handling

**Phase 5: Testing & Validation** 🔄 PENDING
- [ ] Unit tests
- [ ] Integration testing
- [ ] Performance optimization

## 📝 Notes

- The system uses existing prompts from `Prompts.txt` and adapts them for checklist matching
- Processing is designed to prevent AI hallucination by using strict master checklist items
- Context caching optimizes performance for large document sets
- All document references are extracted without page-level coordinates

## 🤝 Contributing

This is an internal project for Wyre AI's checklist matching system. For questions or contributions, please contact the development team.

## 📄 License

Internal project - All rights reserved. 