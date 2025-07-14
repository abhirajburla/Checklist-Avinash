# 🔢 Token Tracking & Cost Monitoring

This document explains the token tracking and cost monitoring system implemented in the Checklist Matching System.

## 📋 Overview

The token tracking system monitors all Gemini API calls and provides detailed cost breakdowns based on current Gemini pricing. This helps you understand and control your API usage costs.

## 🎯 Features

### ✅ What's Implemented

1. **Automatic Token Counting**: Tracks input, output, cached, and thoughts tokens for every API call
2. **Real-time Cost Calculation**: Calculates costs based on current Gemini pricing
3. **Thinking Model Support**: Tracks thoughts tokens for Gemini 2.5 models
4. **Detailed Logging**: Logs token usage with emojis for easy reading
5. **Session Tracking**: Aggregates usage across processing sessions
6. **REST API Endpoints**: Monitor usage via HTTP endpoints
7. **Configuration Options**: Enable/disable tracking features
8. **Cost Estimation**: Estimate costs for planning purposes

### 📊 Information Tracked

For each API call, the system tracks:
- **Input tokens**: Tokens in your prompts and documents
- **Output tokens**: Tokens in Gemini's responses
- **Cached tokens**: Tokens from context caching (if enabled)
- **Thoughts tokens**: Tokens used for thinking process (Gemini 2.5 models only)
- **Cost breakdown**: Separate costs for each token type
- **Total cost**: Sum of all costs
- **Operation type**: What the API call was for

## 💰 Pricing Information

The system uses current Gemini API pricing (as of 2025):

### Gemini 2.5 Flash
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens
- Cached tokens: $0.025 per 1M tokens
- Thoughts tokens: $0.075 per 1M tokens (same as input)
- **Thinking support**: ✅ Summaries and budget

### Gemini 2.5 Pro
- Input tokens: $0.15 per 1M tokens
- Output tokens: $0.60 per 1M tokens
- Cached tokens: $0.05 per 1M tokens
- Thoughts tokens: $0.15 per 1M tokens (same as input)
- **Thinking support**: ✅ Summaries only

### Gemini 1.5 Flash
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens
- Cached tokens: $0.025 per 1M tokens
- **Thinking support**: ❌ Not supported

### Gemini 1.5 Pro
- Input tokens: $0.15 per 1M tokens
- Output tokens: $0.60 per 1M tokens
- Cached tokens: $0.05 per 1M tokens
- **Thinking support**: ❌ Not supported

## 🧠 Thinking Models

Gemini 2.5 models support thinking mode, which generates full thoughts to improve response quality:

- **Gemini 2.5 Flash**: Supports thinking summaries and thinking budget
- **Gemini 2.5 Pro**: Supports thinking summaries only
- **Pricing**: Thoughts tokens are charged at the same rate as input tokens
- **Benefits**: Better reasoning and more accurate responses

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file to configure token tracking:

```bash
# Token tracking configuration
ENABLE_TOKEN_TRACKING=true
LOG_TOKEN_USAGE=true
LOG_COST_BREAKDOWN=true
```

### Configuration Options

- `ENABLE_TOKEN_TRACKING`: Enable/disable token tracking (default: true)
- `LOG_TOKEN_USAGE`: Log token usage details (default: true)
- `LOG_COST_BREAKDOWN`: Log cost breakdowns (default: true)

## 📝 Log Output Example

When token tracking is enabled, you'll see detailed logs like this:

```
🔢 TOKEN USAGE - Checklist Batch Matching
   📥 Input tokens: 15,234
   📤 Output tokens: 8,567
   💾 Cached tokens: 2,345
   🧠 Thoughts tokens: 1,234
   💰 Input cost: $0.001143
   💰 Output cost: $0.002570
   💰 Cached cost: $0.000059
   💰 Thoughts cost: $0.000093
   💰 Total cost: $0.003865
   📊 Pricing (per 1M tokens):
      Input: $0.000075
      Output: $0.000300
      Cached: $0.000025
      Thoughts: $0.000075

📊 SESSION SUMMARY
   🔢 Total calls: 5
   📥 Total input tokens: 45,234
   📤 Total output tokens: 25,567
   💾 Total cached tokens: 8,345
   🧠 Total thoughts tokens: 3,456
   💰 Total session cost: $0.012345
```

## 🌐 API Endpoints

### Get Token Usage Summary

```http
GET /token-usage
```

**Response:**
```json
{
  "success": true,
  "token_usage": {
    "total_calls": 5,
    "total_input_tokens": 45234,
    "total_output_tokens": 25567,
    "total_cached_tokens": 8345,
    "total_thoughts_tokens": 3456,
    "total_cost": 0.012345,
    "currency": "USD",
    "model": "gemini-2.5-flash",
    "supports_thinking": true,
    "calls": [
      {
        "operation": "Checklist Batch Matching",
        "input_tokens": 15234,
        "output_tokens": 8567,
        "cached_tokens": 2345,
        "thoughts_tokens": 1234,
        "cost": 0.003865,
        "timestamp": 1703123456.789
      }
    ]
  }
}
```

### Reset Token Tracking

```http
POST /reset-token-tracking
```

**Response:**
```json
{
  "success": true,
  "message": "Token tracking reset successfully"
}
```

## 🧪 Testing

Run the test script to see token tracking in action:

```bash
python test_token_tracking.py
```

This will demonstrate:
- Cost calculations for different token amounts
- Session tracking
- Pricing information
- Cost estimation examples
- Thinking model support

## 📈 Usage Examples

### Typical Costs

Here are some typical costs for common operations:

#### Small Document (1-2 pages)
- Input tokens: ~2,000
- Output tokens: ~1,000
- Total cost: ~$0.0003

#### Medium Document (5-10 pages)
- Input tokens: ~8,000
- Output tokens: ~4,000
- Total cost: ~$0.0012

#### Large Document (20+ pages)
- Input tokens: ~25,000
- Output tokens: ~12,000
- Total cost: ~$0.0037

#### Batch Processing (50 checklist items)
- Input tokens: ~15,000
- Output tokens: ~8,000
- Thoughts tokens: ~1,000 (if using thinking model)
- Total cost: ~$0.0038 (without thinking) or ~$0.0039 (with thinking)

### Cost Estimation

Use the cost estimation feature to plan your usage:

```python
from src.token_tracker import TokenTracker

tracker = TokenTracker()
cost = tracker.estimate_cost_for_tokens(
    input_tokens=1000000,    # 1M input tokens
    output_tokens=500000,    # 500K output tokens
    cached_tokens=100000,    # 100K cached tokens
    thoughts_tokens=50000    # 50K thoughts tokens (if using thinking model)
)

print(f"Estimated cost: ${cost.total_cost:.6f}")
```

## 🔍 Monitoring Best Practices

1. **Regular Monitoring**: Check token usage regularly via `/token-usage` endpoint
2. **Session Reset**: Reset tracking between different processing sessions
3. **Cost Planning**: Use cost estimation before large processing jobs
4. **Log Analysis**: Monitor logs for unusual token usage patterns
5. **Batch Optimization**: Consider batch sizes based on cost vs. performance
6. **Thinking Model Usage**: Monitor thoughts token usage for thinking models

## 🚨 Cost Alerts

Consider implementing cost alerts for:
- High token usage sessions (>$1.00)
- Unusual token ratios (very high input/output ratios)
- Rapid API calls (potential rate limiting)
- High thoughts token usage (thinking model optimization)

## 🔧 Integration Points

The token tracking is integrated into:

1. **GeminiClient**: All API calls are tracked automatically
2. **REST API**: Token usage endpoints for monitoring
3. **Logging**: Detailed token usage logs
4. **Configuration**: Environment-based settings

## 📚 References

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/models/gemini)
- [Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Thinking Models Guide](https://ai.google.dev/gemini-api/docs/thinking)
- [Long Context Guide](https://ai.google.dev/gemini-api/docs/long-context) 