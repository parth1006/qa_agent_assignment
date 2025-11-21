"""
Embedder Module - Sentence Transformer Wrapper

This module provides a wrapper around SentenceTransformer for generating
embeddings from text. Supports batch processing and caching.

"""

import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from loguru import logger

from backend.config import settings


class Embedder:
    """
    Wrapper for SentenceTransformer model to generate text embeddings.
    
    This class handles:
    - Loading pre-trained embedding models
    - Generating embeddings for single texts or batches
    - Normalizing embeddings for cosine similarity
    - Caching model instance
    
    Attributes:
        model_name: Name of the SentenceTransformer model
        model: Loaded SentenceTransformer instance
        embedding_dim: Dimension of generated embeddings
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the Embedder with a SentenceTransformer model.
        
        Args:
            model_name: Name of the model (default from settings)
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.embedding_dim = settings.EMBEDDING_DIM
        self.model = None
        
        logger.info(f"Initializing Embedder with model: {self.model_name}")
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Load the SentenceTransformer model.
        
        On first run, this will download the model (~80MB for all-MiniLM-L6-v2).
        Subsequent runs will load from cache.
        
        Raises:
            Exception: If model loading fails
        """
        try:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Verify embedding dimension
            test_embedding = self.model.encode(["test"], show_progress_bar=False)
            actual_dim = test_embedding.shape[1]
            
            if actual_dim != self.embedding_dim:
                logger.warning(
                    f"Expected embedding dim {self.embedding_dim}, "
                    f"but got {actual_dim}. Updating config."
                )
                self.embedding_dim = actual_dim
            
            logger.success(
                f"✅ Model loaded successfully. Embedding dimension: {self.embedding_dim}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of text strings
            batch_size: Batch size for processing multiple texts
            show_progress: Whether to show progress bar for batches
            normalize: Whether to normalize embeddings to unit length
            
        Returns:
            numpy array of embeddings
            - Shape: (embedding_dim,) for single text
            - Shape: (n_texts, embedding_dim) for multiple texts
            
        Example:
            >>> embedder = Embedder()
            >>> embedding = embedder.encode("Hello world")
            >>> embedding.shape
            (384,)
            >>> embeddings = embedder.encode(["Text 1", "Text 2"])
            >>> embeddings.shape
            (2, 384)
        """
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        logger.debug(f"Encoding {len(texts)} text(s)")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            
            # Return single embedding for single input
            if single_input:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error during encoding: {e}")
            raise
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query text for similarity search.
        
        This is a convenience method specifically for RAG query encoding.
        
        Args:
            query: Query text to encode
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        logger.debug(f"Encoding query: {query[:50]}...")
        return self.encode(query, normalize=True)
    
    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Encode multiple documents for indexing.
        
        This method is optimized for encoding large batches of documents
        during knowledge base construction.
        
        Args:
            documents: List of document texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            numpy array of shape (n_documents, embedding_dim)
        """
        logger.info(f"Encoding {len(documents)} documents with batch_size={batch_size}")
        
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress,
            normalize=True
        )
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        return self.embedding_dim
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "max_seq_length": self.model.max_seq_length,
            "model_type": type(self.model).__name__
        }
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0 to 1, higher = more similar)
        """
        # Ensure embeddings are normalized
        if np.linalg.norm(embedding1) != 1.0:
            embedding1 = embedding1 / np.linalg.norm(embedding1)
        if np.linalg.norm(embedding2) != 1.0:
            embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Cosine similarity is just dot product for normalized vectors
        similarity = np.dot(embedding1, embedding2)
        
        return float(similarity)


# ===== GLOBAL EMBEDDER INSTANCE =====
# Singleton pattern for efficiency - load model once
_embedder_instance: Embedder = None


def get_embedder() -> Embedder:
    """
    Get the global Embedder instance (singleton pattern).
    
    This ensures the model is loaded only once and reused across the application.
    
    Returns:
        Global Embedder instance
    """
    global _embedder_instance
    
    if _embedder_instance is None:
        logger.info("Creating global Embedder instance")
        _embedder_instance = Embedder()
    
    return _embedder_instance


if __name__ == "__main__":
    """Test the Embedder module."""
    
    # Configure logger for testing
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/embedder_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING EMBEDDER MODULE")
    print("="*60 + "\n")
    
    # Test 1: Load model
    print("Test 1: Loading model...")
    embedder = get_embedder()
    print(f"✅ Model loaded: {embedder.model_name}")
    print(f"   Embedding dimension: {embedder.embedding_dim}\n")
    
    # Test 2: Single text encoding
    print("Test 2: Encoding single text...")
    text = "This is a test document about machine learning."
    embedding = embedder.encode(text)
    print(f"✅ Input text: {text}")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   First 5 values: {embedding[:5]}\n")
    
    # Test 3: Batch encoding
    print("Test 3: Encoding batch of texts...")
    texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Natural language processing enables computers to understand text.",
        "Deep learning uses neural networks with multiple layers."
    ]
    embeddings = embedder.encode_documents(texts, show_progress=False)
    print(f"✅ Encoded {len(texts)} documents")
    print(f"   Embeddings shape: {embeddings.shape}\n")
    
    # Test 4: Similarity computation
    print("Test 4: Computing similarity...")
    query = "What is AI and machine learning?"
    query_embedding = embedder.encode_query(query)
    
    similarities = []
    for i, doc_embedding in enumerate(embeddings):
        sim = embedder.compute_similarity(query_embedding, doc_embedding)
        similarities.append((i, sim))
        print(f"   Doc {i}: similarity = {sim:.4f}")
    
    most_similar = max(similarities, key=lambda x: x[1])
    print(f"\n✅ Most similar document: Doc {most_similar[0]} (similarity={most_similar[1]:.4f})")
    print(f"   Content: {texts[most_similar[0]]}\n")
    
    # Test 5: Model info
    print("Test 5: Model information...")
    info = embedder.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")