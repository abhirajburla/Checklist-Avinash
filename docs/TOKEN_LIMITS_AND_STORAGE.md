# Token Limits and JSON Storage Configuration

## Overview

This document describes the enhanced token limit configuration and JSON storage functionality that addresses timeout issues and JSON parsing failures in the checklist matching system.

## 🔧 Token Limit Configuration

### Increased Output Tokens

The system now uses significantly higher output token limits to prevent JSON truncation:

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_MAX_OUTPUT_TOKENS` | 65,536 (64K) | Maximum output tokens for Gemini API responses |

### Environment Variables

Add this to your `.env` file to customize the output token limit:

```bash
# Gemini Model Configuration
GEMINI_MAX_OUTPUT_TOKENS=65536  # 64K tokens (can be increased to 131072 for 128K)
```

### Why This Fixes the Issue

The previous limit of 8,192 tokens was too low for the large JSON responses generated when processing 50 checklist items at once. The new limit of 65,536 tokens allows for:

- Complete JSON responses without truncation
- Detailed reasoning and notes for each checklist item
- Multiple sheet and specification references
- Proper JSON structure completion

## 📁 JSON Storage System

### Overview

All Gemini API responses are now stored for debugging and analysis:

- **Successful responses**: Stored in `json_outputs/responses/`
- **Failed responses**: Stored in `json_outputs/failed/`
- **Combined responses**: Stored in `json_outputs/combined/`

### Storage Structure

```
json_outputs/
├── responses/
│   ├── checklist_matching_batch_000_20250714_140241_session_123.json
│   └── ...
├── failed/
│   ├── failed_checklist_matching_batch_000_20250714_140241_session_123.json
│   └── ...
└── combined/
    └── combined_checklist_matching_session_123_20250714_140241.json
```

### Storage Metadata

Each stored response includes:

```json
{
  "metadata": {
    "timestamp": "2025-07-14T14:02:41",
    "batch_index": 0,
    "operation": "checklist_matching",
    "success": true,
    "session_id": "session_123",
    "filepath": "path/to/file.json"
  },
  "response_text": "actual Gemini response",
  "custom_metadata": {
    "batch_size": 50,
    "cache_id": "cache_123",
    "model": "gemini-2.5-flash",
    "timeout_used": 300
  }
}
```

## 🚀 API Endpoints

### JSON Storage Management

```bash
# Get storage statistics
GET /json-storage/stats

# Clean up old files
POST /json-storage/cleanup

# Combine session responses
POST /json-storage/combine/{session_id}
```

### Token Usage Tracking

```bash
# Get token usage summary
GET /token-usage/summary

# Reset token tracking
POST /reset-token-tracking
```

## 🔍 Troubleshooting

### Common Issues

1. **JSON Parsing Errors**: Check `json_outputs/failed/` for truncated responses
2. **Timeout Issues**: Increase `GEMINI_API_TIMEOUT` in config
3. **Token Limit Issues**: Increase `GEMINI_MAX_OUTPUT_TOKENS` if responses are still truncated

### Debugging Steps

1. **Check Response Storage**:
   ```bash
   # List all stored responses
   ls json_outputs/responses/
   ls json_outputs/failed/
   ```

2. **Analyze Failed Responses**:
   ```python
   from src.json_storage import JSONStorage
   
   storage = JSONStorage()
   stats = storage.get_storage_stats()
   print(f"Failed responses: {stats['total_failed']}")
   ```

3. **Combine Session Data**:
   ```python
   # Combine all responses from a session
   combined_file = storage.combine_responses("session_123")
   ```

## 📊 Performance Impact

### Token Usage

With the increased output tokens:

- **Input tokens**: ~18K per batch (unchanged)
- **Output tokens**: Up to 64K per batch (increased from 8K)
- **Total cost increase**: ~8x for output tokens, but prevents fallback results

### Storage Requirements

- **Per response**: ~50-100KB
- **Per session (27 batches)**: ~2-3MB
- **Daily storage**: ~50-100MB (depending on usage)

## 🎯 Best Practices

1. **Monitor Storage**: Regularly clean up old JSON files
2. **Analyze Failures**: Review failed responses to identify patterns
3. **Adjust Limits**: Increase token limits if truncation persists
4. **Backup Important Data**: Archive important session data before cleanup

## 🔄 Migration Guide

### From Previous Version

1. **Update Configuration**:
   ```bash
   # Add to .env file
   GEMINI_MAX_OUTPUT_TOKENS=65536
   ```

2. **Create Storage Directories**:
   ```bash
   mkdir -p json_outputs/responses
   mkdir -p json_outputs/failed
   mkdir -p json_outputs/combined
   ```

3. **Test Configuration**:
   ```bash
   python test_increased_tokens.py
   ```

### Verification

After migration, verify:

- ✅ No more "finish_reason: 2" errors
- ✅ Complete JSON responses without truncation
- ✅ JSON storage working correctly
- ✅ Token tracking functioning properly

## 📈 Future Enhancements

1. **Adaptive Token Limits**: Automatically adjust based on response size
2. **Compression**: Compress stored JSON files to save space
3. **Database Storage**: Move from file-based to database storage
4. **Real-time Monitoring**: Web interface for monitoring storage and usage 