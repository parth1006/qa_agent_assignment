"""
VectorStore Package

This package contains vector database management:
- FAISSManager: FAISS index manager with metadata support


"""

from backend.vectorstore.faiss_manager import FAISSManager, get_faiss_manager

__all__ = [
    "FAISSManager",
    "get_faiss_manager",
]