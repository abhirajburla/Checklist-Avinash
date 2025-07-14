import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
try:
    from .config import Config
    from .logger_config import LoggerConfig
except ImportError:
    from config import Config
    from logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

@dataclass
class TokenUsage:
    """Token usage information for a single API call"""
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    thoughts_tokens: int = 0  # For thinking models
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class CostBreakdown:
    """Cost breakdown for token usage"""
    input_cost: float
    output_cost: float
    cached_cost: float
    thoughts_cost: float = 0.0  # For thinking models
    total_cost: float = 0.0
    currency: str = "USD"

class TokenTracker:
    """Track token usage and calculate costs for Gemini API calls"""
    
    def __init__(self):
        self.config = Config()
        
        # Updated Gemini API pricing based on official documentation (as of 2025)
        # Source: https://ai.google.dev/gemini-api/docs/pricing
        self.pricing = {
            "gemini-2.5-flash": {
                "input": 0.15,      # $0.15 per 1M input tokens (text/image/video)
                "output": 0.60,     # $0.60 per 1M output tokens (non-thinking)
                "output_thinking": 3.50,  # $3.50 per 1M output tokens (thinking)
                "cached": 0.0375,   # $0.0375 per 1M cached tokens (text/image/video)
                "thoughts": 0.15    # Same as input for thinking models
            },
            "gemini-2.5-pro": {
                "input": 0.15,      # $0.15 per 1M input tokens (text/image/video)
                "output": 0.60,     # $0.60 per 1M output tokens (non-thinking)
                "output_thinking": 3.50,  # $3.50 per 1M output tokens (thinking)
                "cached": 0.0375,   # $0.0375 per 1M cached tokens (text/image/video)
                "thoughts": 0.15    # Same as input for thinking models
            },
            "gemini-1.5-flash": {
                "input": 0.075,     # $0.075 per 1M input tokens
                "output": 0.30,     # $0.30 per 1M output tokens
                "output_thinking": 0.30,  # Same as non-thinking for 1.5 models
                "cached": 0.025,    # $0.025 per 1M cached tokens
                "thoughts": 0.075   # Same as input for thinking models
            },
            "gemini-1.5-pro": {
                "input": 0.15,      # $0.15 per 1M input tokens
                "output": 0.60,     # $0.60 per 1M output tokens
                "output_thinking": 0.60,  # Same as non-thinking for 1.5 models
                "cached": 0.05,     # $0.05 per 1M cached tokens
                "thoughts": 0.15    # Same as input for thinking models
            }
        }
        
        # Model capabilities for thinking models
        self.thinking_models = {
            "gemini-2.5-flash": True,  # Supports thinking summaries and budget
            "gemini-2.5-pro": True,    # Supports thinking summaries only
            "gemini-1.5-flash": False, # No thinking support
            "gemini-1.5-pro": False    # No thinking support
        }
        
        # Session tracking
        self.session_usage = []
        self.total_session_cost = 0.0
        
        logger.info(f"TokenTracker initialized for model: {self.config.GEMINI_MODEL}")
        if self.is_thinking_model():
            logger.info(f"Model supports thinking mode: {self.thinking_models.get(self.config.GEMINI_MODEL, False)}")
    
    def is_thinking_model(self) -> bool:
        """Check if current model supports thinking mode"""
        return self.thinking_models.get(self.config.GEMINI_MODEL, False)
    
    def get_model_pricing(self) -> Dict[str, float]:
        """Get pricing for the current model"""
        model = self.config.GEMINI_MODEL
        return self.pricing.get(model, self.pricing["gemini-2.5-flash"])
    
    def calculate_cost(self, usage: TokenUsage, is_thinking: bool = False) -> CostBreakdown:
        """Calculate cost for token usage"""
        pricing = self.get_model_pricing()
        
        # Calculate costs (pricing is per 1M tokens)
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        
        # Use thinking output pricing if this is a thinking model and has thoughts tokens
        if is_thinking and usage.thoughts_tokens > 0:
            output_cost = (usage.output_tokens / 1_000_000) * pricing["output_thinking"]
        else:
            output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
            
        cached_cost = (usage.cached_tokens / 1_000_000) * pricing["cached"]
        thoughts_cost = (usage.thoughts_tokens / 1_000_000) * pricing["thoughts"]
        
        total_cost = input_cost + output_cost + cached_cost + thoughts_cost
        
        return CostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            cached_cost=cached_cost,
            thoughts_cost=thoughts_cost,
            total_cost=total_cost
        )
    
    def log_token_usage(self, usage: TokenUsage, operation: str = "API Call", is_thinking: bool = False):
        """Log token usage and cost information"""
        cost = self.calculate_cost(usage, is_thinking)
        
        # Log detailed information
        logger.info(f"🔢 TOKEN USAGE - {operation}")
        logger.info(f"   📥 Input tokens: {usage.input_tokens:,}")
        logger.info(f"   📤 Output tokens: {usage.output_tokens:,}")
        logger.info(f"   💾 Cached tokens: {usage.cached_tokens:,}")
        if usage.thoughts_tokens > 0:
            logger.info(f"   🧠 Thoughts tokens: {usage.thoughts_tokens:,}")
        logger.info(f"   💰 Input cost: ${cost.input_cost:.6f}")
        logger.info(f"   💰 Output cost: ${cost.output_cost:.6f}")
        logger.info(f"   💰 Cached cost: ${cost.cached_cost:.6f}")
        if cost.thoughts_cost > 0:
            logger.info(f"   💰 Thoughts cost: ${cost.thoughts_cost:.6f}")
        logger.info(f"   💰 Total cost: ${cost.total_cost:.6f}")
        
        # Log pricing information
        pricing = self.get_model_pricing()
        logger.info(f"   📊 Pricing (per 1M tokens):")
        logger.info(f"      Input: ${pricing['input']:.6f}")
        if is_thinking and usage.thoughts_tokens > 0:
            logger.info(f"      Output (thinking): ${pricing['output_thinking']:.6f}")
        else:
            logger.info(f"      Output: ${pricing['output']:.6f}")
        logger.info(f"      Cached: ${pricing['cached']:.6f}")
        if self.is_thinking_model():
            logger.info(f"      Thoughts: ${pricing['thoughts']:.6f}")
        
        # Add to session tracking
        self.session_usage.append({
            "operation": operation,
            "usage": usage,
            "cost": cost,
            "timestamp": usage.timestamp,
            "is_thinking": is_thinking
        })
        self.total_session_cost += cost.total_cost
        
        # Log session summary
        self.log_session_summary()
    
    def log_session_summary(self):
        """Log current session summary"""
        total_input = sum(u["usage"].input_tokens for u in self.session_usage)
        total_output = sum(u["usage"].output_tokens for u in self.session_usage)
        total_cached = sum(u["usage"].cached_tokens for u in self.session_usage)
        total_thoughts = sum(u["usage"].thoughts_tokens for u in self.session_usage)
        
        logger.info(f"📊 SESSION SUMMARY")
        logger.info(f"   🔢 Total calls: {len(self.session_usage)}")
        logger.info(f"   📥 Total input tokens: {total_input:,}")
        logger.info(f"   📤 Total output tokens: {total_output:,}")
        logger.info(f"   💾 Total cached tokens: {total_cached:,}")
        if total_thoughts > 0:
            logger.info(f"   🧠 Total thoughts tokens: {total_thoughts:,}")
        logger.info(f"   💰 Total session cost: ${self.total_session_cost:.6f}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary as dictionary"""
        total_input = sum(u["usage"].input_tokens for u in self.session_usage)
        total_output = sum(u["usage"].output_tokens for u in self.session_usage)
        total_cached = sum(u["usage"].cached_tokens for u in self.session_usage)
        total_thoughts = sum(u["usage"].thoughts_tokens for u in self.session_usage)
        
        return {
            "total_calls": len(self.session_usage),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cached_tokens": total_cached,
            "total_thoughts_tokens": total_thoughts,
            "total_cost": self.total_session_cost,
            "currency": "USD",
            "model": self.config.GEMINI_MODEL,
            "supports_thinking": self.is_thinking_model(),
            "calls": [
                {
                    "operation": u["operation"],
                    "input_tokens": u["usage"].input_tokens,
                    "output_tokens": u["usage"].output_tokens,
                    "cached_tokens": u["usage"].cached_tokens,
                    "thoughts_tokens": u["usage"].thoughts_tokens,
                    "cost": u["cost"].total_cost,
                    "timestamp": u["timestamp"],
                    "is_thinking": u.get("is_thinking", False)
                }
                for u in self.session_usage
            ]
        }
    
    def reset_session(self):
        """Reset session tracking"""
        self.session_usage = []
        self.total_session_cost = 0.0
        logger.info("🔄 Session tracking reset")
    
    def estimate_cost_for_tokens(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0, thoughts_tokens: int = 0, is_thinking: bool = False) -> CostBreakdown:
        """Estimate cost for given token counts"""
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            thoughts_tokens=thoughts_tokens
        )
        return self.calculate_cost(usage, is_thinking) 