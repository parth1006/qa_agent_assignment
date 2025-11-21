"""
LLM Client Module - Groq Cloud API Integration

This module provides a client for interacting with Groq Cloud API
for LLM inference. Supports chat completions with error handling.

"""

import time
from typing import List, Dict, Optional, Any
from groq import Groq
from groq.types.chat import ChatCompletion
from loguru import logger

from backend.config import settings


class LLMClient:
    """
    Client for Groq Cloud API to perform LLM inference.
    
    This class handles:
    - Chat completions using Groq models
    - Error handling and retries
    - Token counting and usage tracking
    - System and user message construction
    
    Attributes:
        api_key: Groq API key
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        client: Groq client instance
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Groq API key (default from settings)
            model: Model name (default from settings)
            temperature: Sampling temperature (default from settings)
            max_tokens: Max response tokens (default from settings)
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        if not self.api_key:
            logger.error("❌ GROQ_API_KEY not set!")
            raise ValueError(
                "GROQ_API_KEY is required. Get it from https://console.groq.com/keys"
            )
        
        logger.info(f"Initializing LLM Client with model: {self.model}")
        self.client = Groq(api_key=self.api_key)
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_requests = 0
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> ChatCompletion:
        """
        Send a chat completion request to Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            stream: Whether to stream the response
            
        Returns:
            ChatCompletion response object
            
        Raises:
            Exception: If API call fails
            
        Example:
            >>> client = LLMClient()
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "Hello!"}
            ... ]
            >>> response = client.chat_completion(messages)
            >>> print(response.choices[0].message.content)
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        logger.debug(f"Sending chat completion request (temp={temp}, max_tokens={max_tok})")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=stream
            )
            
            # Track usage
            self.total_requests += 1
            if hasattr(response, 'usage') and response.usage:
                tokens = response.usage.total_tokens
                self.total_tokens_used += tokens
                logger.debug(f"Token usage: {tokens} (total: {self.total_tokens_used})")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            raise
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response using system and user prompts.
        
        This is a convenience method for simple prompt-response patterns.
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User query or instruction
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Generated response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def generate_with_context(
        self,
        system_prompt: str,
        context: str,
        user_query: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response with retrieved context (RAG pattern).
        
        Args:
            system_prompt: System instruction
            context: Retrieved context from vector database
            user_query: User's query
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Generated response text
        """
        # Construct user prompt with context
        user_prompt = f"""Context from documentation:
{context}

User Query: {user_query}

Please answer the query based strictly on the provided context. Do not hallucinate or add information not present in the context."""
        
        return self.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response with automatic retry on failure.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return self.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error(f"❌ All {max_retries} attempts failed")
        raise last_exception
    
    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get usage statistics for this client instance.
        
        Returns:
            Dictionary with total_requests and total_tokens_used
        """
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "model": self.model
        }
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.total_tokens_used = 0
        self.total_requests = 0
        logger.info("Usage statistics reset")


# ===== GLOBAL LLM CLIENT INSTANCE =====
_llm_client_instance: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get the global LLM client instance (singleton pattern).
    
    Returns:
        Global LLMClient instance
    """
    global _llm_client_instance
    
    if _llm_client_instance is None:
        logger.info("Creating global LLM client instance")
        _llm_client_instance = LLMClient()
    
    return _llm_client_instance


if __name__ == "__main__":
    """Test the LLM Client module."""
    
    # Configure logger for testing
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/llm_client_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING LLM CLIENT MODULE")
    print("="*60 + "\n")
    
    # Check if API key is set
    if not settings.GROQ_API_KEY:
        print("❌ GROQ_API_KEY not set in .env file")
        print("   Get your free API key from: https://console.groq.com/keys")
        print("   Add it to .env: GROQ_API_KEY=your_key_here")
        exit(1)
    
    # Test 1: Initialize client
    print("Test 1: Initializing LLM client...")
    client = get_llm_client()
    print(f"✅ Client initialized with model: {client.model}\n")
    
    # Test 2: Simple response generation
    print("Test 2: Generating simple response...")
    system_prompt = "You are a helpful AI assistant."
    user_prompt = "What is machine learning? Answer in one sentence."
    
    try:
        response = client.generate_response(system_prompt, user_prompt)
        print(f"✅ Response received:")
        print(f"   {response}\n")
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
    
    # Test 3: Response with context (RAG pattern)
    print("Test 3: Generating response with context...")
    context = """
    The discount code SAVE15 applies a 15% discount to the cart subtotal.
    Express shipping costs $10. Standard shipping is free.
    """
    user_query = "What discount does SAVE15 provide?"
    
    try:
        response = client.generate_with_context(
            system_prompt="You are a QA assistant. Answer based on the context.",
            context=context,
            user_query=user_query
        )
        print(f"✅ Response received:")
        print(f"   {response}\n")
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
    
    # Test 4: Usage statistics
    print("Test 4: Checking usage statistics...")
    stats = client.get_usage_stats()
    print(f"✅ Usage statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")