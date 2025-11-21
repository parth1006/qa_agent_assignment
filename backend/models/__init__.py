"""
Models Package

This package contains the core AI/ML model interfaces:
- Embedder: Sentence Transformer for text embeddings
- LLMClient: Groq Cloud API client for LLM inference

"""

from backend.models.embedder import Embedder, get_embedder
from backend.models.llm_client import LLMClient, get_llm_client

__all__ = [
    "Embedder",
    "get_embedder",
    "LLMClient",
    "get_llm_client",
]