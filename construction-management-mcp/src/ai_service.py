"""
AI Service Layer for BuildBridge-MCP
Provides AI-powered construction management capabilities using OpenAI GPT-4
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import openai
import tiktoken
from openai import OpenAI, AsyncOpenAI

try:
    from .construction_prompts import ConstructionPrompts
except ImportError:
    from construction_prompts import ConstructionPrompts


@dataclass
class AIResponse:
    """Structured response from AI service"""
    content: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    model_used: str
    confidence_score: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: float
    timestamp: datetime


class TokenTracker:
    """Tracks token usage and costs for AI service"""
    
    # OpenAI pricing (as of 2024) - update as needed
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }
    
    def __init__(self):
        self.usage_history: List[TokenUsage] = []
        self.total_cost = 0.0
        
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on token usage"""
        if model not in self.PRICING:
            # Default to GPT-4 pricing for unknown models
            model = "gpt-4"
            
        pricing = self.PRICING[model]
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    def track_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> TokenUsage:
        """Track token usage and update total cost"""
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        self.total_cost += cost
        
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_estimate=cost,
            timestamp=datetime.now()
        )
        
        self.usage_history.append(usage)
        return usage
    
    def get_daily_summary(self) -> Dict:
        """Get summary of today's usage"""
        today = datetime.now().date()
        today_usage = [u for u in self.usage_history if u.timestamp.date() == today]
        
        if not today_usage:
            return {"total_tokens": 0, "total_cost": 0.0, "request_count": 0}
            
        return {
            "total_tokens": sum(u.total_tokens for u in today_usage),
            "total_cost": sum(u.cost_estimate for u in today_usage),
            "request_count": len(today_usage),
            "average_tokens_per_request": sum(u.total_tokens for u in today_usage) / len(today_usage)
        }


class AIService:
    """
    AI Service for construction management queries
    Supports both OpenAI GPT models with comprehensive error handling
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI service with configuration"""
        # Load environment variables from .env file if it exists
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass  # dotenv not available, continue without it
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.token_tracker = TokenTracker()
        self.construction_prompts = ConstructionPrompts()
        
        # Initialize OpenAI client
        api_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment variables")
            
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        
        # Configuration options with environment variable overrides
        self.model = os.getenv('AI_MODEL', config.get('model', 'gpt-4-turbo'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', config.get('max_tokens', 2000)))
        self.temperature = float(os.getenv('AI_TEMPERATURE', config.get('temperature', 0.1)))
        self.max_retries = int(os.getenv('AI_MAX_RETRIES', config.get('max_retries', 3)))
        self.retry_delay = float(os.getenv('AI_RETRY_DELAY', config.get('retry_delay', 1.0)))
        
        # Initialize tokenizer for token counting
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")  # Default encoding
            
        self.logger.info(f"AI Service initialized with model: {self.model}")
        self.logger.info(f"Configuration: max_tokens={self.max_tokens}, temperature={self.temperature}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    async def process_construction_query(
        self,
        query: str,
        context: Optional[str] = None,
        data_context: Optional[Dict] = None,
        query_type: str = "general"
    ) -> AIResponse:
        """
        Process construction management query with AI
        
        Args:
            query: User's query
            context: Additional context (file contents, etc.)
            data_context: Structured data context (spreadsheet data, etc.)
            query_type: Type of query (budget, schedule, safety, etc.)
        """
        start_time = time.time()
        
        try:
            # Build the prompt using construction-specific templates
            system_prompt = self.construction_prompts.get_system_prompt(query_type)
            user_prompt = self.construction_prompts.build_user_prompt(
                query=query,
                context=context,
                data_context=data_context,
                query_type=query_type
            )
            
            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Count tokens before sending
            prompt_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)
            
            # Make API call with retries
            response = await self._make_api_call_with_retry(messages)
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Track token usage
            completion_tokens = response.usage.completion_tokens
            usage = self.token_tracker.track_usage(
                self.model, prompt_tokens, completion_tokens
            )
            
            response_time = time.time() - start_time
            
            # Calculate confidence score based on response characteristics
            confidence_score = self._calculate_confidence_score(content, query_type)
            
            return AIResponse(
                content=content,
                tokens_used=usage.total_tokens,
                cost_estimate=usage.cost_estimate,
                response_time=response_time,
                model_used=self.model,
                confidence_score=confidence_score,
                metadata={
                    "query_type": query_type,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "has_context": context is not None,
                    "has_data_context": data_context is not None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing construction query: {str(e)}")
            # Return fallback response
            return AIResponse(
                content=f"I apologize, but I encountered an error processing your construction query: {str(e)}. Please try again or rephrase your question.",
                tokens_used=0,
                cost_estimate=0.0,
                response_time=time.time() - start_time,
                model_used=self.model,
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _make_api_call_with_retry(self, messages: List[Dict]) -> Any:
        """Make OpenAI API call with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=False
                )
                return response
                
            except openai.RateLimitError as e:
                self.logger.warning(f"Rate limit hit on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
                last_exception = e
                
            except openai.APIError as e:
                self.logger.error(f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                last_exception = e
                
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                last_exception = e
                break
        
        # If all retries failed, raise the last exception
        raise last_exception
    
    def _calculate_confidence_score(self, content: str, query_type: str) -> float:
        """Calculate confidence score based on response characteristics"""
        score = 0.5  # Base score
        
        # Check for construction-specific keywords
        construction_keywords = [
            'project', 'schedule', 'budget', 'cost', 'timeline', 'contractor',
            'material', 'labor', 'safety', 'permit', 'inspection', 'delivery',
            'completion', 'milestone', 'phase', 'site', 'construction', 'building'
        ]
        
        content_lower = content.lower()
        keyword_matches = sum(1 for keyword in construction_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.3)  # Up to 0.3 boost for keywords
        
        # Check for specific data mentions (numbers, dates, percentages)
        import re
        numbers = len(re.findall(r'\d+', content))
        dates = len(re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content))
        percentages = len(re.findall(r'\d+%', content))
        
        score += min((numbers + dates + percentages) * 0.02, 0.2)  # Up to 0.2 boost for data
        
        # Penalty for very short responses
        if len(content) < 50:
            score -= 0.2
        
        # Penalty for generic responses
        generic_phrases = ['i apologize', 'i cannot', 'i don\'t have', 'unable to']
        if any(phrase in content_lower for phrase in generic_phrases):
            score -= 0.3
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def get_usage_stats(self) -> Dict:
        """Get comprehensive usage statistics"""
        daily_summary = self.token_tracker.get_daily_summary()
        
        return {
            "daily_summary": daily_summary,
            "total_cost": self.token_tracker.total_cost,
            "total_requests": len(self.token_tracker.usage_history),
            "model": self.model,
            "configuration": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "max_retries": self.max_retries
            }
        }
    
    def export_usage_history(self, filepath: str):
        """Export usage history to JSON file"""
        history_data = [asdict(usage) for usage in self.token_tracker.usage_history]
        
        # Convert datetime objects to strings for JSON serialization
        for record in history_data:
            record['timestamp'] = record['timestamp'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump({
                "export_timestamp": datetime.now().isoformat(),
                "total_cost": self.token_tracker.total_cost,
                "usage_history": history_data
            }, f, indent=2)
        
        self.logger.info(f"Usage history exported to {filepath}")


# Factory function for easy instantiation
def create_ai_service(config: Dict[str, Any]) -> AIService:
    """Create and configure AI service instance"""
    return AIService(config)


# Convenience function for quick testing
async def test_ai_service():
    """Test function for AI service"""
    config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-4-turbo',
        'temperature': 0.1
    }
    
    if not config['openai_api_key']:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    ai_service = create_ai_service(config)
    
    test_query = "What are the key factors to consider when scheduling a construction project?"
    response = await ai_service.process_construction_query(test_query, query_type="schedule")
    
    print(f"Query: {test_query}")
    print(f"Response: {response.content}")
    print(f"Tokens used: {response.tokens_used}")
    print(f"Cost: ${response.cost_estimate:.4f}")
    print(f"Confidence: {response.confidence_score:.2f}")


if __name__ == "__main__":
    asyncio.run(test_ai_service())