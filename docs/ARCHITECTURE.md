# System Architecture

## Overview

The Construction Checklist Matching System is built with a modular, scalable architecture that separates concerns and enables easy testing and maintenance. The system follows a pipeline-based approach for document processing and AI-powered analysis.

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Document       │    │   Gemini AI     │
│   (Flask)       │───▶│  Processing     │───▶│   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Configuration  │    │  Matching       │    │  Output         │
│  Management     │    │  Engine         │    │  Generation     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Core Components

### 1. Configuration Management (`src/config.py`)

**Purpose**: Centralized configuration management with environment-based settings.

**Key Features**:
- Environment variable loading with fallbacks
- Configuration validation
- Default value management
- Test mode support

**Configuration Options**:
```python
# API Configuration
GEMINI_API_KEY = "your_api_key"
GEMINI_MODEL = "gemini-2.5-pro"

# Processing Configuration
BATCH_SIZE = 50
MAX_RETRIES = 3
ENABLE_SYSTEM_INSTRUCTIONS = True
ENABLE_REFERENCE_VALIDATION = True

# File Configuration
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 800 * 1024 * 1024  # 800MB
```

### 2. Document Handler (`src/document_handler.py`)

**Purpose**: Validates, processes, and manages uploaded PDF documents.

**Key Features**:
- PDF file validation (type, size, content)
- Secure file storage with unique naming
- Metadata extraction
- Upload session management
- Automatic cleanup

**Processing Pipeline**:
```
Upload → Validation → Storage → Metadata Extraction → Gemini Upload
```

### 3. Gemini Client (`src/gemini_client.py`)

**Purpose**: Manages all interactions with the Gemini AI API.

**Key Features**:
- File upload to Gemini API
- Context caching based on file content hash
- Document analysis with construction-specific prompts
- Batch processing optimization
- Error handling and retry logic

**Caching Strategy**:
- MD5-based cache IDs for file content
- 48-hour cache lifetime (Gemini limit)
- Automatic cache cleanup
- Cache hit/miss tracking

### 4. Checklist Processor (`src/checklist_processor.py`)

**Purpose**: Loads and processes the master checklist file.

**Key Features**:
- Excel/CSV file loading
- Data cleaning and validation
- Batch creation for optimal processing
- Category and sector analysis
- Summary statistics generation

**Data Structure**:
```python
{
    "row_id": 1,
    "category": "Pre-Award",
    "scope_of_work": "General Requirements",
    "checklist": "Review contract documents",
    "sector": "General"
}
```

### 5. Matching Engine (`src/matching_engine.py`)

**Purpose**: Orchestrates the entire matching process.

**Key Features**:
- Document analysis coordination
- Batch processing management
- Progress tracking
- Result compilation
- Error handling and recovery

**Processing Flow**:
```
1. Load documents and checklist
2. Upload documents to Gemini
3. Extract document references
4. Process checklist in batches
5. Match items against references
6. Compile and validate results
7. Generate final output
```

### 6. Enhanced Batch Processor (`src/enhanced_batch_processor.py`)

**Purpose**: Handles batch processing with advanced features.

**Key Features**:
- Configurable batch sizes
- Retry logic with exponential backoff
- Progress tracking
- Error isolation
- Result aggregation

### 7. Reference Validator (`src/reference_validator.py`)

**Purpose**: Validates extracted document references for accuracy.

**Key Features**:
- Reference format validation
- Confidence scoring
- Cross-reference verification
- Error detection and correction

### 8. Output Generator (`src/output_generator.py`)

**Purpose**: Generates structured output with progress tracking.

**Key Features**:
- JSON formatting with construction-specific fields
- Progress tracking and status updates
- Download functionality
- Error handling and recovery
- Result compilation and validation

## 📊 Data Flow

### 1. Document Upload Flow
```
User Upload → File Validation → Secure Storage → Gemini Upload → Context Caching
```

### 2. Processing Flow
```
Checklist Loading → Batch Creation → Document Analysis → Reference Extraction → 
Item Matching → Validation → Result Compilation → Output Generation
```

### 3. Caching Flow
```
File Upload → MD5 Hash → Cache Check → Upload/Reuse → Context Storage
```

## 🔄 Processing Pipeline

### Phase 1: Document Preparation
1. **File Upload**: User uploads drawings and specifications
2. **Validation**: File type, size, and content validation
3. **Storage**: Secure file storage with unique naming
4. **Metadata Extraction**: Basic PDF information extraction

### Phase 2: AI Integration
1. **Gemini Upload**: Files uploaded to Gemini API
2. **Context Caching**: MD5-based caching for efficiency
3. **Document Analysis**: Sheet and specification reference extraction
4. **Reference Storage**: Cached references for batch processing

### Phase 3: Matching Process
1. **Checklist Loading**: Master checklist loaded and batched
2. **Batch Processing**: Items processed in configurable batches
3. **Reference Matching**: Items matched against extracted references
4. **Validation**: References validated for accuracy
5. **Result Compilation**: Results aggregated and formatted

### Phase 4: Output Generation
1. **Progress Tracking**: Real-time status updates
2. **Result Compilation**: All results combined
3. **JSON Formatting**: Structured output generation
4. **Download Preparation**: Results prepared for download

## 🛡️ Security Architecture

### File Security
- **Validation**: Strict PDF-only policy with size limits
- **Storage**: Unique file naming with upload session isolation
- **Access Control**: Secure file handling with proper permissions
- **Cleanup**: Automatic removal of temporary files

### API Security
- **Key Management**: Secure API key handling
- **Rate Limiting**: Respect for Gemini API limits
- **Error Handling**: Limited error information exposure
- **Input Validation**: Comprehensive input sanitization

### Data Security
- **Caching**: Secure cache management with expiration
- **Session Management**: Isolated processing sessions
- **Result Storage**: Secure result storage and cleanup

## 📈 Performance Architecture

### Optimization Strategies
- **Batch Processing**: Configurable batch sizes for optimal API usage
- **Context Caching**: Reuse uploaded documents across batches
- **Background Processing**: Non-blocking document analysis
- **Memory Management**: Efficient handling of large documents

### Scalability Features
- **Modular Design**: Easy to extend and modify
- **Configurable Parameters**: Adjustable for different workloads
- **Error Isolation**: Failures don't affect entire process
- **Resource Management**: Automatic cleanup and optimization

## 🔧 Configuration Architecture

### Environment-Based Configuration
```python
# Required
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Optional with defaults
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
```

### Validation and Fallbacks
- **Required Fields**: API key validation
- **Type Conversion**: Automatic type conversion with validation
- **Default Values**: Sensible defaults for all optional settings
- **Error Handling**: Clear error messages for configuration issues

## 🧪 Testing Architecture

### Test Structure
```
tests/
├── __init__.py
├── test_phase4.py      # Complete system tests
└── test_runner.py      # Test orchestration
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Error Testing**: Error condition validation

### Test Features
- **Isolation**: Independent test execution
- **Mocking**: API and file system mocking
- **Validation**: Result validation and verification
- **Reporting**: Detailed test reports with metrics

## 🚀 Deployment Architecture

### Production Requirements
- **Python 3.8+**: Modern Python features support
- **Flask**: Web framework for interface
- **Gemini API**: AI processing capabilities
- **File Storage**: Secure file handling
- **Environment Variables**: Configuration management

### Deployment Options
- **Local Development**: Direct Python execution
- **Docker Containerization**: Isolated deployment
- **Cloud Deployment**: AWS, GCP, or Azure
- **Load Balancing**: Multiple instance support

## 📊 Monitoring and Logging

### Logging Strategy
- **Structured Logging**: JSON-formatted logs
- **Level-Based**: Debug, Info, Warning, Error levels
- **Context Tracking**: Request and session tracking
- **Performance Metrics**: Timing and resource usage

### Monitoring Points
- **API Calls**: Gemini API usage and performance
- **File Processing**: Upload and processing metrics
- **Batch Processing**: Batch completion and error rates
- **User Interactions**: Upload and download patterns

## 🔄 Error Handling Architecture

### Error Categories
- **Validation Errors**: Input and configuration validation
- **API Errors**: Gemini API communication issues
- **Processing Errors**: Document processing failures
- **System Errors**: Infrastructure and resource issues

### Error Handling Strategy
- **Graceful Degradation**: Continue operation on partial failures
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Isolation**: Failures don't affect entire process
- **User Feedback**: Clear error messages and status updates

## 🎯 Future Architecture Considerations

### Scalability Enhancements
- **Database Integration**: Persistent storage for results
- **Queue System**: Asynchronous processing with queues
- **Microservices**: Service decomposition for scaling
- **Caching Layer**: Redis or similar for advanced caching

### Feature Extensions
- **Multi-Format Support**: Additional document formats
- **Advanced AI Models**: Integration with other AI services
- **Real-time Collaboration**: Multi-user support
- **Advanced Analytics**: Detailed processing analytics

---

This architecture provides a solid foundation for the Construction Checklist Matching System, enabling reliable, scalable, and maintainable document processing and AI-powered analysis. 