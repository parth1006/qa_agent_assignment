"""
FAISS Manager Module - Vector Database Management

This module manages FAISS vector index for storing and retrieving
document embeddings with metadata.

"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import faiss
from loguru import logger

from backend.config import settings


class FAISSManager:
    """
    Manager for FAISS vector index with metadata support.
    
    This class handles:
    - Creating and loading FAISS indices
    - Adding embeddings with metadata
    - Similarity search with metadata retrieval
    - Persistent storage of index and metadata
    
    Attributes:
        index_path: Path to FAISS index file
        metadata_path: Path to metadata JSON file
        embedding_dim: Dimension of embeddings
        index: FAISS index instance
        metadata: List of metadata dictionaries
    """
    
    def __init__(
        self,
        index_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        embedding_dim: Optional[int] = None
    ):
        """
        Initialize FAISS manager.
        
        Args:
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load metadata
            embedding_dim: Dimension of embeddings
        """
        self.index_path = index_path or settings.get_faiss_index_path()
        self.metadata_path = metadata_path or settings.get_faiss_metadata_path()
        self.embedding_dim = embedding_dim or settings.EMBEDDING_DIM
        
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        
        logger.info(f"Initializing FAISS Manager (dim={self.embedding_dim})")
        
        # Try to load existing index, otherwise create new
        if self.index_path.exists() and self.metadata_path.exists():
            self.load()
        else:
            self._create_new_index()
    
    def _create_new_index(self) -> None:
        """
        Create a new FAISS index.
        
        Uses IndexFlatL2 for exact L2 distance search.
        For large datasets, consider IndexHNSWFlat for approximate search.
        """
        logger.info(f"Creating new FAISS index with dimension {self.embedding_dim}")
        
        # IndexFlatL2: Exact L2 distance (brute force but accurate)
        # For large datasets (>1M vectors), consider:
        # - IndexHNSWFlat (fast approximate search)
        # - IndexIVFFlat (inverted file index)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = []
        
        logger.success(f"✅ New FAISS index created (type: {type(self.index).__name__})")
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        metadata_list: List[Dict[str, Any]]
    ) -> None:
        """
        Add embeddings with metadata to the index.
        
        Args:
            embeddings: numpy array of shape (n, embedding_dim)
            metadata_list: List of metadata dicts (length must match n)
            
        Raises:
            ValueError: If shapes don't match or index not initialized
        """
        if self.index is None:
            raise ValueError("Index not initialized")
        
        if len(embeddings) != len(metadata_list):
            raise ValueError(
                f"Embeddings count ({len(embeddings)}) must match "
                f"metadata count ({len(metadata_list)})"
            )
        
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) must match "
                f"index dimension ({self.embedding_dim})"
            )
        
        # Convert to float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')
        
        # Add to index
        self.index.add(embeddings)
        
        # Add metadata
        self.metadata.extend(metadata_list)
        
        logger.info(
            f"✅ Added {len(embeddings)} embeddings to index "
            f"(total: {self.index.ntotal})"
        )
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        return_distances: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            return_distances: Whether to include distance scores
            
        Returns:
            List of result dictionaries with metadata and optional distances
            
        Example:
            >>> results = manager.search(query_emb, k=5)
            >>> for result in results:
            ...     print(result['metadata']['source'])
            ...     print(result['distance'])
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty, returning no results")
            return []
        
        # Ensure query is 2D float32 array
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        
        # Limit k to available vectors
        k = min(k, self.index.ntotal)
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        
        # Prepare results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS returns -1 for unfilled results
                continue
            
            result = {
                "metadata": self.metadata[idx],
                "index": int(idx)
            }
            
            if return_distances:
                result["distance"] = float(distance)
                # Convert L2 distance to similarity score (higher = more similar)
                result["similarity"] = float(1 / (1 + distance))
            
            results.append(result)
        
        logger.debug(f"Search returned {len(results)} results")
        return results
    
    def search_with_threshold(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        max_distance: Optional[float] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with distance/similarity threshold filtering.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to retrieve (before filtering)
            max_distance: Maximum L2 distance (lower = more similar)
            min_similarity: Minimum similarity score (higher = more similar)
            
        Returns:
            Filtered list of results
        """
        results = self.search(query_embedding, k=k, return_distances=True)
        
        # Filter by threshold
        filtered_results = []
        for result in results:
            if max_distance is not None and result["distance"] > max_distance:
                continue
            if min_similarity is not None and result["similarity"] < min_similarity:
                continue
            filtered_results.append(result)
        
        logger.debug(
            f"Filtered {len(results)} results to {len(filtered_results)} "
            f"based on thresholds"
        )
        return filtered_results
    
    def save(self) -> None:
        """
        Save FAISS index and metadata to disk.
        
        The index is saved as a binary file and metadata as JSON.
        """
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        logger.info(f"✅ FAISS index saved to {self.index_path}")
        
        # Save metadata as JSON
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Metadata saved to {self.metadata_path}")
    
    def load(self) -> None:
        """
        Load FAISS index and metadata from disk.
        
        Raises:
            FileNotFoundError: If index or metadata files don't exist
        """
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index not found: {self.index_path}")
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {self.metadata_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))
        logger.info(f"✅ FAISS index loaded from {self.index_path}")
        logger.info(f"   Index contains {self.index.ntotal} vectors")
        
        # Load metadata
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        logger.info(f"✅ Metadata loaded from {self.metadata_path}")
        logger.info(f"   Metadata contains {len(self.metadata)} entries")
        
        # Verify consistency
        if self.index.ntotal != len(self.metadata):
            logger.warning(
                f"⚠️  Index has {self.index.ntotal} vectors but "
                f"metadata has {len(self.metadata)} entries"
            )
    
    def clear(self) -> None:
        """
        Clear the index and metadata (does not delete files).
        """
        logger.info("Clearing FAISS index and metadata")
        self._create_new_index()
    
    def delete_files(self) -> None:
        """
        Delete index and metadata files from disk.
        """
        if self.index_path.exists():
            self.index_path.unlink()
            logger.info(f"🗑️  Deleted index file: {self.index_path}")
        
        if self.metadata_path.exists():
            self.metadata_path.unlink()
            logger.info(f"🗑️  Deleted metadata file: {self.metadata_path}")
        
        self.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "embedding_dim": self.embedding_dim,
            "index_type": type(self.index).__name__ if self.index else None,
            "metadata_count": len(self.metadata),
            "index_exists": self.index_path.exists(),
            "metadata_exists": self.metadata_path.exists()
        }
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all metadata entries.
        
        Returns:
            List of all metadata dictionaries
        """
        return self.metadata.copy()
    
    def get_metadata_by_index(self, idx: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific index.
        
        Args:
            idx: Index position
            
        Returns:
            Metadata dictionary or None if index out of range
        """
        if 0 <= idx < len(self.metadata):
            return self.metadata[idx]
        return None


# ===== GLOBAL FAISS MANAGER INSTANCE =====
_faiss_manager_instance: Optional[FAISSManager] = None


def get_faiss_manager() -> FAISSManager:
    """
    Get the global FAISS manager instance (singleton pattern).
    
    Returns:
        Global FAISSManager instance
    """
    global _faiss_manager_instance
    
    if _faiss_manager_instance is None:
        logger.info("Creating global FAISS manager instance")
        _faiss_manager_instance = FAISSManager()
    
    return _faiss_manager_instance


if __name__ == "__main__":
    """Test the FAISS Manager module."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/faiss_manager_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING FAISS MANAGER MODULE")
    print("="*60 + "\n")
    
    # Test 1: Create manager
    print("Test 1: Creating FAISS manager...")
    manager = FAISSManager(
        index_path=Path("test_index.faiss"),
        metadata_path=Path("test_metadata.json"),
        embedding_dim=384
    )
    print(f"✅ Manager created\n")
    
    # Test 2: Add embeddings
    print("Test 2: Adding embeddings...")
    # Create dummy embeddings
    n_docs = 10
    embeddings = np.random.randn(n_docs, 384).astype('float32')
    metadata = [
        {
            "text": f"Document {i}",
            "source": f"test_doc_{i}.txt",
            "chunk_id": i
        }
        for i in range(n_docs)
    ]
    
    manager.add_embeddings(embeddings, metadata)
    print(f"✅ Added {n_docs} embeddings\n")
    
    # Test 3: Search
    print("Test 3: Searching...")
    query_embedding = np.random.randn(384).astype('float32')
    results = manager.search(query_embedding, k=3)
    
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['metadata']['source']} (distance={result['distance']:.4f})")
    print()
    
    # Test 4: Save and load
    print("Test 4: Saving index...")
    manager.save()
    print("✅ Index saved\n")
    
    print("Test 5: Loading index...")
    new_manager = FAISSManager(
        index_path=Path("test_index.faiss"),
        metadata_path=Path("test_metadata.json"),
        embedding_dim=384
    )
    stats = new_manager.get_stats()
    print(f"✅ Index loaded:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Test 6: Cleanup
    print("Test 6: Cleaning up test files...")
    new_manager.delete_files()
    print("✅ Cleanup complete\n")
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")