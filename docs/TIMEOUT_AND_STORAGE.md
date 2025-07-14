# Timeout and JSON Storage Configuration

## Overview

This document describes the enhanced timeout configuration and JSON storage functionality that addresses timeout issues and JSON parsing failures in the checklist matching system.

## 🔧 Timeout Configuration

### New Timeout Settings

The system now includes configurable timeout settings to handle long-running operations:

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_TIMEOUT` | 300s (5 min) | Timeout for individual Gemini API calls |
| `PROCESSING_TIMEOUT` | 1800s (30 min) | Overall processing timeout for entire workflow |
| `BATCH_TIMEOUT` | 600s (10 min) | Timeout per batch processing |
| `UPLOAD_TIMEOUT` | 300s (5 min) | Timeout for file uploads |

### Environment Variables

Add these to your `.env` file to customize timeouts:

```bash
# Timeout Configuration
GEMINI_API_TIMEOUT=300      # 5 minutes for API calls
PROCESSING_TIMEOUT=1800     # 30 minutes for processing
BATCH_TIMEOUT=600          # 10 minutes per batch
UPLOAD_TIMEOUT=300         # 5 minutes for uploads
```

### Timeout Calculations

For the full dataset (1,350 items in 50-item batches = 27 batches):

- **Conservative estimate**: 2 minutes per batch = 54 minutes total
- **Processing timeout**: 30 minutes (configurable)
- **API timeout**: 5 minutes per call (configurable)

## 📁 JSON Storage System

### Overview

All Gemini API responses are now stored for debugging and later processing, addressing JSON parsing failures.

### Storage Structure

```
json_outputs/
├── responses/          # Successful API responses
├── failed/            # Failed/parsing error responses
└── combined/          # Combined session responses
```

### Features

1. **Automatic Storage**: Every Gemini response is stored before parsing
2. **Error Tracking**: Failed responses include detailed error information
3. **Session Management**: Responses grouped by processing session
4. **Metadata Tracking**: Includes batch info, timestamps, and configuration
5. **Cleanup**: Automatic cleanup of old files

### Configuration

```bash
# JSON Storage Configuration
ENABLE_JSON_STORAGE=true
JSON_STORAGE_FOLDER=json_outputs
```

## 🚀 New API Endpoints

### JSON Storage Management

#### Get Storage Statistics
```http
GET /json-storage/stats
```

Response:
```json
{
  "total_responses": 15,
  "total_failed": 3,
  "total_combined": 2,
  "storage_size_mb": 2.45,
  "folders": {
    "responses": "json_outputs/responses",
    "failed": "json_outputs/failed",
    "combined": "json_outputs/combined"
  }
}
```

#### Clean Up Old Files
```http
POST /json-storage/cleanup
Content-Type: application/json

{
  "days": 7
}
```

#### Combine Session Responses
```http
GET /json-storage/combine/{session_id}
```

#### Get Session Responses
```http
GET /json-storage/session/{session_id}
```

## 🔍 Debugging with JSON Storage

### Analyzing Failed Responses

1. **Check failed responses**:
   ```bash
   curl http://localhost:5000/json-storage/stats
   ```

2. **Examine specific failed response**:
   ```bash
   # Find failed response files
   ls json_outputs/failed/
   
   # Examine the JSON structure
   cat json_outputs/failed/failed_checklist_matching_batch_001_*.json
   ```

3. **Combine all responses from a session**:
   ```bash
   curl http://localhost:5000/json-storage/combine/session_1234567890
   ```

### Response File Format

Successful response:
```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00",
    "batch_index": 1,
    "operation": "checklist_matching",
    "success": true,
    "session_id": "session_1234567890",
    "filepath": "json_outputs/responses/checklist_matching_batch_001_20240115_103000_session_1234567890.json"
  },
  "response_text": "{\"matches\": [...]}",
  "custom_metadata": {
    "batch_size": 50,
    "cache_id": "abc123",
    "model": "gemini-2.5-flash",
    "timeout_used": 300
  }
}
```

Failed response:
```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00",
    "batch_index": 1,
    "operation": "checklist_matching",
    "success": false,
    "session_id": "session_1234567890",
    "filepath": "json_outputs/failed/failed_checklist_matching_batch_001_20240115_103000_session_1234567890.json",
    "error": "JSON parsing error: Unterminated string"
  },
  "response_text": "{\"matches\": [{\"checklist_index\": 1, \"found\": false, \"confidence\": \"NO MATCH\", \"sheet_references\": [], \"spec_references\": [], \"notes\": \"No information regarding carpet installation sequence relative to partitions was found in the provided mechanical drawings.\", \"reasoning\": \"The provided documents are mechanical drawings and do not contain specifications or details for carpet installation.\"}]",
  "error_details": {
    "error_message": "JSON parsing error: Unterminated string",
    "response_length": 1234,
    "has_json_start": true,
    "has_json_end": false
  },
  "custom_metadata": {
    "batch_size": 50,
    "cache_id": "abc123",
    "model": "gemini-2.5-flash",
    "timeout_used": 300,
    "json_error": "Unterminated string starting at: line 72 column 16 (char 3249)"
  }
}
```

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_timeout_and_storage.py
```

Expected output:
```
🚀 Testing Timeout and JSON Storage Functionality
============================================================
🔧 Testing Configuration...
  GEMINI_API_TIMEOUT: 300s
  PROCESSING_TIMEOUT: 1800s
  BATCH_TIMEOUT: 600s
  UPLOAD_TIMEOUT: 300s
  ENABLE_JSON_STORAGE: True
  JSON_STORAGE_FOLDER: json_outputs
  ✅ Configuration test passed

📁 Testing JSON Storage...
  Stored successful response: json_outputs/responses/test_operation_batch_001_*.json
  Stored failed response: json_outputs/failed/failed_test_operation_batch_002_*.json
  Storage stats: {'total_responses': 1, 'total_failed': 1, ...}
  ✅ JSON Storage test passed

🤖 Testing Gemini Client Integration...
  Model: gemini-2.5-flash
  API Timeout: 300s
  JSON Storage enabled: True
  ✅ Gemini Client integration test passed

⏱️  Testing Timeout Calculations...
  Total items: 1350
  Batch size: 50
  Total batches: 27
  Estimated time per batch: 120s
  Total estimated time: 3240s (54.0 minutes)
  Processing timeout: 1800s (30.0 minutes)
  ✅ Timeout calculation test passed

🧹 Testing Storage Cleanup...
  Cleaned up 0 old files
  ✅ Storage cleanup test passed

============================================================
✅ All tests passed!

📋 Summary:
  - Timeout settings increased significantly
  - JSON storage functionality working
  - All Gemini responses will be stored for debugging
  - New API endpoints available for storage management
```

## 🔧 Troubleshooting

### Common Issues

1. **Timeout Still Occurring**
   - Increase `PROCESSING_TIMEOUT` in `.env`
   - Check network connectivity to Gemini API
   - Monitor system resources

2. **JSON Parsing Failures**
   - Check stored responses in `json_outputs/failed/`
   - Look for incomplete JSON responses
   - Verify Gemini API response format

3. **Storage Space Issues**
   - Run cleanup: `POST /json-storage/cleanup`
   - Monitor storage usage: `GET /json-storage/stats`
   - Adjust cleanup frequency

### Monitoring

1. **Check processing status**:
   ```bash
   curl http://localhost:5000/status/{process_id}
   ```

2. **Monitor token usage**:
   ```bash
   curl http://localhost:5000/token-usage
   ```

3. **View storage statistics**:
   ```bash
   curl http://localhost:5000/json-storage/stats
   ```

## 📈 Performance Impact

### Benefits

- **Reduced Timeouts**: 5x increase in timeout values
- **Better Debugging**: All responses stored for analysis
- **Error Recovery**: Detailed error information for failed responses
- **Session Tracking**: Complete audit trail of processing

### Storage Requirements

- **Per response**: ~2-5KB (depending on batch size)
- **Full session**: ~50-100KB for 27 batches
- **Daily storage**: ~1-2MB for multiple sessions
- **Cleanup**: Automatic cleanup after 7 days (configurable)

## 🔄 Migration

### From Previous Version

1. **No breaking changes** - existing functionality preserved
2. **Automatic JSON storage** - enabled by default
3. **Increased timeouts** - applied automatically
4. **New endpoints** - optional, for debugging

### Configuration Migration

If you have custom timeout settings, update your `.env`:

```bash
# Old settings (if any)
# TIMEOUT=60

# New settings
GEMINI_API_TIMEOUT=300
PROCESSING_TIMEOUT=1800
BATCH_TIMEOUT=600
UPLOAD_TIMEOUT=300
ENABLE_JSON_STORAGE=true
 