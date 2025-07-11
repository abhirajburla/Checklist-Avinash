# API Reference

## Overview

The Construction Checklist Matching System provides a RESTful API for document processing and checklist matching. This document describes all available endpoints, request/response formats, and data structures.

## 🔗 Base URL

```
http://localhost:5000
```

## 📋 Authentication

Currently, the API uses simple session-based authentication. All endpoints are accessible without authentication tokens.

## 🔧 Endpoints

### 1. Main Interface

#### GET `/`
**Description**: Main upload interface for the application.

**Response**: HTML page with upload forms.

**Example**:
```bash
curl http://localhost:5000/
```

### 2. Document Upload

#### POST `/upload`
**Description**: Upload construction drawings and specifications.

**Content-Type**: `multipart/form-data`

**Form Fields**:
- `drawing_file`: PDF file (optional)
- `spec_file`: PDF file (optional)

**Response**:
```json
{
  "success": true,
  "message": "Files uploaded successfully",
  "drawing_file": "uploads/session_123/drawing.pdf",
  "spec_file": "uploads/session_123/spec.pdf"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Invalid file type. Only PDF files are allowed."
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/upload \
  -F "drawing_file=@drawing.pdf" \
  -F "spec_file=@specification.pdf"
```

### 3. Document Processing

#### POST `/process-documents`
**Description**: Start the checklist matching process.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "company_id": "123",
  "project_id": "456"
}
```

**Response**:
```json
{
  "success": true,
  "process_id": "uuid-12345-67890",
  "message": "Processing started",
  "total_items": 1350,
  "batches": 27,
  "status": "processing"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "No documents uploaded. Please upload drawing and specification files first."
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/process-documents \
  -H "Content-Type: application/json" \
  -d '{"company_id": "123", "project_id": "456"}'
```

### 4. Processing Status

#### GET `/status/<process_id>`
**Description**: Get the current status of a processing job.

**Parameters**:
- `process_id`: UUID of the processing job

**Response**:
```json
{
  "success": true,
  "process_id": "uuid-12345-67890",
  "status": "processing",
  "progress": {
    "current_batch": 15,
    "total_batches": 27,
    "items_processed": 750,
    "total_items": 1350,
    "percentage": 55.6
  },
  "message": "Processing batch 15 of 27"
}
```

**Completed Status Response**:
```json
{
  "success": true,
  "process_id": "uuid-12345-67890",
  "status": "completed",
  "progress": {
    "current_batch": 27,
    "total_batches": 27,
    "items_processed": 1350,
    "total_items": 1350,
    "percentage": 100.0
  },
  "message": "Processing completed successfully"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Process not found"
}
```

**Example**:
```bash
curl http://localhost:5000/status/uuid-12345-67890
```

### 5. Results Download

#### GET `/results/<process_id>`
**Description**: Download the processing results.

**Parameters**:
- `process_id`: UUID of the processing job

**Response**: JSON file download with results.

**Example**:
```bash
curl -O http://localhost:5000/results/uuid-12345-67890
```

## 📊 Data Structures

### 1. Checklist Item

```json
{
  "row_id": 1,
  "category": "Pre-Award",
  "scope_of_work": "General Requirements",
  "checklist": "Review contract documents",
  "sector": "General"
}
```

### 2. Processing Result

```json
{
  "row_id": 1,
  "category": "Pre-Award",
  "scope_of_work": "General Requirements",
  "checklist": "Review contract documents",
  "sector": "General",
  "found": true,
  "sheet_number": "A1.1, S-01",
  "spec_section": "01 11 00",
  "notes": "Found in architectural and structural drawings",
  "reasoning": "Direct reference in contract documents section",
  "confidence": "HIGH",
  "validation_score": 0.95
}
```

### 3. Batch Information

```json
{
  "batch_id": 1,
  "start_index": 0,
  "end_index": 49,
  "items": 50,
  "status": "completed",
  "processing_time": 45.2,
  "success_count": 48,
  "error_count": 2
}
```

### 4. Processing Status

```json
{
  "process_id": "uuid-12345-67890",
  "status": "processing",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": null,
  "total_items": 1350,
  "total_batches": 27,
  "current_batch": 15,
  "items_processed": 750,
  "batches_completed": 15,
  "batches_failed": 0,
  "percentage": 55.6
}
```

## 🔄 Processing States

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Process created but not started |
| `processing` | Currently processing batches |
| `completed` | All batches processed successfully |
| `failed` | Process failed with errors |
| `cancelled` | Process was cancelled |

### Progress Tracking

The system tracks progress at multiple levels:

1. **Overall Progress**: Percentage of total items processed
2. **Batch Progress**: Current batch number and total batches
3. **Item Progress**: Number of items processed vs. total
4. **Time Tracking**: Start time, estimated completion time

## 🛡️ Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message description",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `INVALID_FILE_TYPE` | File type not supported | 400 |
| `FILE_TOO_LARGE` | File exceeds size limit | 400 |
| `NO_DOCUMENTS` | No documents uploaded | 400 |
| `PROCESS_NOT_FOUND` | Process ID not found | 404 |
| `API_ERROR` | Gemini API error | 500 |
| `PROCESSING_ERROR` | Internal processing error | 500 |

### Error Recovery

The system implements several error recovery mechanisms:

1. **Retry Logic**: Automatic retries with exponential backoff
2. **Graceful Degradation**: Continue processing on partial failures
3. **Error Isolation**: Failures don't affect entire process
4. **Detailed Logging**: Comprehensive error logging for debugging

## 📈 Performance Considerations

### Rate Limiting

- **Gemini API**: Respects Gemini API rate limits
- **File Uploads**: 800MB maximum per file
- **Concurrent Processing**: Up to 3 concurrent batches
- **Request Timeout**: 30 seconds for API calls

### Optimization Features

1. **Context Caching**: Reuse uploaded documents across batches
2. **Batch Processing**: Process items in configurable batches (default: 50)
3. **Background Processing**: Non-blocking document analysis
4. **Memory Management**: Efficient handling of large documents

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-pro` |
| `BATCH_SIZE` | Items per batch | `50` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `MAX_CONTENT_LENGTH` | Maximum file size | `800MB` |
| `UPLOAD_FOLDER` | File upload directory | `uploads` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |

### Request Limits

- **File Size**: 800MB per file
- **File Type**: PDF only
- **Concurrent Uploads**: 2 files (drawing + specification)
- **Processing Time**: Varies by document size and complexity

## 🧪 Testing

### Test Endpoints

The API includes several test endpoints for development:

#### GET `/test/health`
**Description**: Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### POST `/test/upload`
**Description**: Test file upload endpoint.

**Example**:
```bash
curl -X POST http://localhost:5000/test/upload \
  -F "file=@test.pdf"
```

### Mock Responses

For development and testing, the system can return mock responses:

```json
{
  "success": true,
  "process_id": "test-uuid",
  "mock_data": true,
  "results": [
    {
      "row_id": 1,
      "found": true,
      "sheet_number": "A1.1",
      "spec_section": "01 11 00",
      "confidence": "HIGH"
    }
  ]
}
```

## 📚 SDK Examples

### Python Client Example

```python
import requests
import json

class ChecklistMatchingClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_files(self, drawing_path=None, spec_path=None):
        files = {}
        if drawing_path:
            files['drawing_file'] = open(drawing_path, 'rb')
        if spec_path:
            files['spec_file'] = open(spec_path, 'rb')
        
        response = self.session.post(f"{self.base_url}/upload", files=files)
        return response.json()
    
    def start_processing(self, company_id, project_id):
        data = {
            "company_id": company_id,
            "project_id": project_id
        }
        response = self.session.post(
            f"{self.base_url}/process-documents",
            json=data
        )
        return response.json()
    
    def get_status(self, process_id):
        response = self.session.get(f"{self.base_url}/status/{process_id}")
        return response.json()
    
    def download_results(self, process_id, output_path):
        response = self.session.get(f"{self.base_url}/results/{process_id}")
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return response.status_code == 200

# Usage example
client = ChecklistMatchingClient()

# Upload files
result = client.upload_files("drawing.pdf", "spec.pdf")
print(result)

# Start processing
process = client.start_processing("123", "456")
process_id = process['process_id']

# Monitor progress
while True:
    status = client.get_status(process_id)
    print(f"Progress: {status['progress']['percentage']}%")
    if status['status'] == 'completed':
        break

# Download results
client.download_results(process_id, "results.json")
```

### JavaScript Client Example

```javascript
class ChecklistMatchingClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadFiles(drawingFile, specFile) {
        const formData = new FormData();
        if (drawingFile) formData.append('drawing_file', drawingFile);
        if (specFile) formData.append('spec_file', specFile);
        
        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    }
    
    async startProcessing(companyId, projectId) {
        const response = await fetch(`${this.baseUrl}/process-documents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_id: companyId,
                project_id: projectId
            })
        });
        return response.json();
    }
    
    async getStatus(processId) {
        const response = await fetch(`${this.baseUrl}/status/${processId}`);
        return response.json();
    }
    
    async downloadResults(processId) {
        const response = await fetch(`${this.baseUrl}/results/${processId}`);
        return response.blob();
    }
}

// Usage example
const client = new ChecklistMatchingClient();

// Upload files and start processing
async function processDocuments() {
    const drawingFile = document.getElementById('drawing-file').files[0];
    const specFile = document.getElementById('spec-file').files[0];
    
    // Upload files
    const uploadResult = await client.uploadFiles(drawingFile, specFile);
    console.log('Upload result:', uploadResult);
    
    // Start processing
    const processResult = await client.startProcessing('123', '456');
    const processId = processResult.process_id;
    
    // Monitor progress
    const interval = setInterval(async () => {
        const status = await client.getStatus(processId);
        console.log(`Progress: ${status.progress.percentage}%`);
        
        if (status.status === 'completed') {
            clearInterval(interval);
            
            // Download results
            const results = await client.downloadResults(processId);
            const url = URL.createObjectURL(results);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'results.json';
            a.click();
        }
    }, 5000);
}
```

## 🔄 WebSocket Support (Future)

Future versions may include WebSocket support for real-time progress updates:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'progress') {
        updateProgressBar(data.percentage);
    } else if (data.type === 'completed') {
        showResults(data.results);
    }
};
```

---

This API reference provides comprehensive documentation for integrating with the Construction Checklist Matching System. For additional support or questions, refer to the main documentation or create an issue in the repository. 