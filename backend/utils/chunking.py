"""
Chunking Module - Text Splitting with Metadata Preservation

This module provides utilities for splitting long text documents into
smaller chunks suitable for embedding and indexing.

"""

from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from backend.config import settings


class TextChunker:
    """
    Text chunking utility with metadata preservation.
    
    Uses RecursiveCharacterTextSplitter for intelligent text splitting
    that respects natural boundaries (paragraphs, sentences, etc.).
    
    Attributes:
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Overlap between chunks for context preservation
        splitter: LangChain text splitter instance
    """
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum chunk size (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
            separators: List of separators to split on (default: smart splitting)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Default separators (hierarchical splitting)
        # Tries to split on larger units first (paragraphs), then smaller (sentences)
        if separators is None:
            separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence breaks
                "! ",    # Sentence breaks
                "? ",    # Sentence breaks
                "; ",    # Clause breaks
                ", ",    # Phrase breaks
                " ",     # Word breaks
                ""       # Character breaks (fallback)
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )
        
        logger.info(
            f"Initialized TextChunker (size={self.chunk_size}, "
            f"overlap={self.chunk_overlap})"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to split
            metadata: Base metadata to attach to all chunks
            
        Returns:
            List of chunk dictionaries with:
                - text: Chunk text content
                - metadata: Combined metadata
                - chunk_id: Sequential chunk identifier
                
        Example:
            >>> chunker = TextChunker()
            >>> chunks = chunker.chunk_text(
            ...     "Long text...",
            ...     metadata={"source": "doc.txt"}
            ... )
            >>> for chunk in chunks:
            ...     print(chunk['text'][:50])
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Split text into chunks
        text_chunks = self.splitter.split_text(text)
        
        logger.debug(
            f"Split text into {len(text_chunks)} chunks "
            f"(original length: {len(text)} chars)"
        )
        
        # Prepare metadata
        base_metadata = metadata or {}
        
        # Create chunk objects with metadata
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = {
                "text": chunk_text,
                "metadata": {
                    **base_metadata,
                    "chunk_id": i,
                    "total_chunks": len(text_chunks),
                    "chunk_size": len(chunk_text)
                },
                "chunk_id": i
            }
            chunks.append(chunk)
        
        logger.info(f"✅ Created {len(chunks)} chunks from text")
        return chunks
    
    def chunk_document(
        self,
        document: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document dictionary (from DocumentParser).
        
        Args:
            document: Dictionary with 'text' and 'metadata' keys
            
        Returns:
            List of chunks with preserved and enhanced metadata
        """
        if not document.get('success', False):
            logger.warning(f"Document parsing failed, skipping chunking")
            return []
        
        text = document.get('text', '')
        metadata = document.get('metadata', {})
        
        return self.chunk_text(text, metadata=metadata)
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Combined list of all chunks from all documents
        """
        all_chunks = []
        
        for doc_idx, document in enumerate(documents):
            if not document.get('success', False):
                logger.warning(
                    f"Skipping document {doc_idx} (parsing failed)"
                )
                continue
            
            # Add document index to metadata
            doc_metadata = document.get('metadata', {}).copy()
            doc_metadata['document_index'] = doc_idx
            
            # Chunk the document
            chunks = self.chunk_text(
                document.get('text', ''),
                metadata=doc_metadata
            )
            
            all_chunks.extend(chunks)
        
        logger.info(
            f"✅ Created {len(all_chunks)} total chunks from "
            f"{len(documents)} documents"
        )
        return all_chunks
    
    def get_chunk_stats(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_characters": 0
            }
        
        chunk_sizes = [len(chunk['text']) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_characters": sum(chunk_sizes)
        }


# ===== GLOBAL TEXT CHUNKER INSTANCE =====
_text_chunker_instance: Optional[TextChunker] = None


def get_text_chunker() -> TextChunker:
    """
    Get the global TextChunker instance (singleton pattern).
    
    Returns:
        Global TextChunker instance
    """
    global _text_chunker_instance
    
    if _text_chunker_instance is None:
        logger.info("Creating global TextChunker instance")
        _text_chunker_instance = TextChunker()
    
    return _text_chunker_instance


if __name__ == "__main__":
    """Test the Chunking module."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/chunking_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING TEXT CHUNKING MODULE")
    print("="*60 + "\n")
    
    # Test 1: Initialize chunker
    print("Test 1: Initializing chunker...")
    chunker = get_text_chunker()
    print(f"✅ Chunker initialized:")
    print(f"   Chunk size: {chunker.chunk_size}")
    print(f"   Chunk overlap: {chunker.chunk_overlap}\n")
    
    # Test 2: Chunk simple text
    print("Test 2: Chunking simple text...")
    text = """This is a test document. It has multiple sentences.
    
This is a second paragraph. It also has multiple sentences. We want to test how the chunker handles this content.

This is a third paragraph. The chunker should split this intelligently based on natural boundaries like paragraph breaks and sentence breaks.
    """
    
    chunks = chunker.chunk_text(
        text,
        metadata={"source": "test.txt", "author": "Test"}
    )
    
    print(f"✅ Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        preview = chunk['text'][:60].replace('\n', ' ')
        print(f"   Chunk {i}: {preview}...")
        print(f"            Metadata: {chunk['metadata']}")
    print()
    
    # Test 3: Chunk statistics
    print("Test 3: Calculating chunk statistics...")
    stats = chunker.get_chunk_stats(chunks)
    print("✅ Chunk statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Test 4: Chunk long text
    print("Test 4: Chunking long text...")
    long_text = " ".join([f"Sentence {i}." for i in range(100)])
    
    long_chunks = chunker.chunk_text(long_text, metadata={"source": "long.txt"})
    print(f"✅ Long text split into {len(long_chunks)} chunks")
    print(f"   Original length: {len(long_text)} chars")
    print(f"   Average chunk size: {len(long_text) / len(long_chunks):.0f} chars\n")
    
    # Test 5: Custom chunk size
    print("Test 5: Testing custom chunk size...")
    small_chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    small_chunks = small_chunker.chunk_text(text)
    
    print(f"✅ With smaller chunk size:")
    print(f"   Created {len(small_chunks)} chunks (vs {len(chunks)} with default)")
    print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")