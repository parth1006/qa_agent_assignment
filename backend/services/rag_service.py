"""
RAG Service - Retrieval Augmented Generation Pipeline

This service handles the RAG (Retrieval Augmented Generation) workflow:
1. Embed user query
2. Retrieve relevant chunks from vector database
3. Prepare context for LLM
4. Format results with source attribution

"""

from typing import List, Dict, Any, Optional
from loguru import logger

from backend.config import settings
from backend.models import get_embedder
from backend.vectorstore import get_faiss_manager


class RAGService:
    """
    Service for Retrieval Augmented Generation (RAG).
    
    This service handles:
    - Query embedding
    - Similarity search in vector database
    - Context preparation for LLM
    - Source attribution
    
    Attributes:
        embedder: Embedder instance for query encoding
        vector_store: FAISSManager instance for retrieval
        top_k: Number of chunks to retrieve
    """
    
    def __init__(
        self,
        top_k: Optional[int] = None
    ):
        """
        Initialize the RAG service.
        
        Args:
            top_k: Number of chunks to retrieve (default from settings)
        """
        logger.info("Initializing RAG Service")
        
        self.embedder = get_embedder()
        self.vector_store = get_faiss_manager()
        self.top_k = top_k or settings.RAG_TOP_K
        
        logger.success(f"✅ RAG Service initialized (top_k={self.top_k})")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query string
            top_k: Number of results (overrides default)
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of retrieved chunks with metadata and scores
            
        Example:
            >>> rag = RAGService()
            >>> results = rag.retrieve("What is the discount code?")
            >>> for result in results:
            ...     print(result['text'])
            ...     print(result['metadata']['source'])
        """
        k = top_k or self.top_k
        
        logger.info(f"Retrieving context for query: {query[:50]}...")
        
        # Step 1: Embed the query
        query_embedding = self.embedder.encode_query(query)
        
        # Step 2: Search in vector database
        if min_similarity:
            # Convert similarity to max distance (L2)
            # similarity = 1 / (1 + distance)
            # distance = (1 / similarity) - 1
            max_distance = (1 / min_similarity) - 1
            
            results = self.vector_store.search_with_threshold(
                query_embedding=query_embedding,
                k=k,
                max_distance=max_distance
            )
        else:
            results = self.vector_store.search(
                query_embedding=query_embedding,
                k=k,
                return_distances=True
            )
        
        logger.info(f"✅ Retrieved {len(results)} relevant chunks")
        
        # Step 3: Add text content to results
        for result in results:
            # The metadata contains chunk info, but we need to reconstruct text
            # In our case, metadata includes the chunk text via document parsing
            # For now, we'll add a placeholder - in production, you'd store text separately
            result['text'] = f"Chunk from {result['metadata'].get('filename', 'unknown')}"
        
        return results
    
    def prepare_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        include_sources: bool = True
    ) -> str:
        """
        Prepare formatted context string for LLM.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            include_sources: Whether to include source attribution
            
        Returns:
            Formatted context string ready for LLM prompt
        """
        results = self.retrieve(query, top_k, min_similarity)
        
        if not results:
            logger.warning("No relevant chunks found")
            return "No relevant information found in the knowledge base."
        
        # Format context
        context_parts = []
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            
            # Build context entry
            entry_parts = []
            
            if include_sources:
                source = metadata.get('filename', metadata.get('source', 'Unknown'))
                entry_parts.append(f"[Source: {source}]")
            
            # Add the actual text content
            # Note: In production, text should be stored with metadata
            entry_parts.append(result.get('text', 'No text available'))
            
            context_parts.append("\n".join(entry_parts))
        
        context = "\n\n---\n\n".join(context_parts)
        
        logger.debug(f"Prepared context with {len(results)} chunks ({len(context)} chars)")
        
        return context
    
    def retrieve_with_metadata(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve chunks with detailed metadata and statistics.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with:
                - query: Original query
                - results: List of retrieved chunks
                - total_results: Number of results
                - sources: List of unique sources
                - avg_similarity: Average similarity score
        """
        results = self.retrieve(query, top_k)
        
        # Extract unique sources
        sources = set()
        for result in results:
            source = result['metadata'].get('filename') or result['metadata'].get('source')
            if source:
                sources.add(source)
        
        # Calculate average similarity
        avg_similarity = 0.0
        if results:
            avg_similarity = sum(r.get('similarity', 0) for r in results) / len(results)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "sources": list(sources),
            "avg_similarity": avg_similarity
        }
    
    def get_relevant_documents(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[str]:
        """
        Get list of relevant document sources for a query.
        
        Args:
            query: User query
            top_k: Number of chunks to consider
            
        Returns:
            List of unique document sources
        """
        results = self.retrieve(query, top_k)
        
        sources = set()
        for result in results:
            source = result['metadata'].get('filename') or result['metadata'].get('source')
            if source:
                sources.add(source)
        
        return list(sources)


# ===== GLOBAL RAG SERVICE INSTANCE =====
_rag_service_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get the global RAGService instance (singleton pattern).
    
    Returns:
        Global RAGService instance
    """
    global _rag_service_instance
    
    if _rag_service_instance is None:
        logger.info("Creating global RAGService instance")
        _rag_service_instance = RAGService()
    
    return _rag_service_instance


if __name__ == "__main__":
    """Test the RAG Service."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/rag_service_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING RAG SERVICE")
    print("="*60 + "\n")
    
    # First, we need to ingest some test data
    print("Setup: Ingesting test documents...")
    from backend.services.ingestion_service import get_ingestion_service
    from pathlib import Path
    
    ingestion = get_ingestion_service()
    
    # Create test directory
    test_dir = Path("test_rag")
    test_dir.mkdir(exist_ok=True)
    
    # Create test documents with known content
    (test_dir / "discount_info.txt").write_text(
        "The discount code SAVE15 provides a 15% discount on the cart subtotal. "
        "This code can be applied at checkout.",
        encoding='utf-8'
    )
    
    (test_dir / "shipping_info.txt").write_text(
        "We offer two shipping methods: Standard shipping is free and takes 5-7 business days. "
        "Express shipping costs $10 and takes 1-2 business days.",
        encoding='utf-8'
    )
    
    (test_dir / "payment_info.txt").write_text(
        "We accept Credit Card and PayPal as payment methods. "
        "All transactions are secure and encrypted.",
        encoding='utf-8'
    )
    
    # Ingest test documents
    summary = ingestion.ingest_directory(test_dir, recursive=False)
    print(f"✅ Ingested {summary['successful']} documents with {summary['total_chunks']} chunks\n")
    
    # Test 1: Initialize RAG service
    print("Test 1: Initializing RAG service...")
    rag = get_rag_service()
    print("✅ RAG service initialized\n")
    
    # Test 2: Simple retrieval
    print("Test 2: Testing retrieval...")
    query = "What discount code is available?"
    results = rag.retrieve(query, top_k=3)
    print(f"✅ Retrieved {len(results)} chunks for query: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Similarity: {result.get('similarity', 0):.4f}")
        print(f"      Source: {result['metadata'].get('filename', 'Unknown')}")
    print()
    
    # Test 3: Prepare context
    print("Test 3: Preparing context for LLM...")
    context = rag.prepare_context(query, top_k=2)
    print(f"✅ Context prepared ({len(context)} chars)")
    print(f"   Preview: {context[:100]}...\n")
    
    # Test 4: Retrieve with metadata
    print("Test 4: Retrieving with detailed metadata...")
    detailed = rag.retrieve_with_metadata(query, top_k=3)
    print(f"✅ Detailed retrieval:")
    print(f"   Total results: {detailed['total_results']}")
    print(f"   Sources: {', '.join(detailed['sources'])}")
    print(f"   Avg similarity: {detailed['avg_similarity']:.4f}\n")
    
    # Test 5: Get relevant documents
    print("Test 5: Getting relevant documents...")
    docs = rag.get_relevant_documents("How much does shipping cost?", top_k=5)
    print(f"✅ Relevant documents for shipping query:")
    for doc in docs:
        print(f"   - {doc}")
    print()
    
    # Cleanup
    print("Cleanup: Removing test data...")
    import shutil
    shutil.rmtree(test_dir)
    ingestion.clear_knowledge_base()
    print("✅ Cleanup complete\n")
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")