"""
Ingestion Service - Document Processing Pipeline

This service orchestrates the complete document ingestion pipeline:
1. Parse documents (multiple formats)
2. Chunk text into smaller pieces
3. Generate embeddings
4. Store in FAISS vector database

"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.config import settings
from backend.models import get_embedder
from backend.vectorstore import get_faiss_manager
from backend.utils import get_document_parser, get_text_chunker


class IngestionService:
    """
    Service for ingesting documents into the knowledge base.
    
    This service handles the complete pipeline:
    - Document parsing (multi-format)
    - Text chunking with metadata
    - Embedding generation
    - Vector storage with metadata
    
    Attributes:
        parser: DocumentParser instance
        chunker: TextChunker instance
        embedder: Embedder instance
        vector_store: FAISSManager instance
    """
    
    def __init__(self):
        """Initialize the ingestion service with required components."""
        logger.info("Initializing Ingestion Service")
        
        self.parser = get_document_parser()
        self.chunker = get_text_chunker()
        self.embedder = get_embedder()
        self.vector_store = get_faiss_manager()
        
        logger.success("✅ Ingestion Service initialized")
    
    def ingest_file(
        self,
        file_path: Path,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single file into the knowledge base.
        
        Args:
            file_path: Path to the document file
            additional_metadata: Optional extra metadata to attach
            
        Returns:
            Dictionary with ingestion results:
                - success: Boolean
                - chunks_added: Number of chunks added
                - file_name: Name of the file
                - error: Error message (if failed)
        """
        logger.info(f"Ingesting file: {file_path.name}")
        
        try:
            # Step 1: Parse document
            doc_result = self.parser.parse(file_path, include_metadata=True)
            
            if not doc_result['success']:
                logger.error(f"Failed to parse {file_path.name}: {doc_result['error']}")
                return {
                    "success": False,
                    "chunks_added": 0,
                    "file_name": file_path.name,
                    "error": doc_result['error']
                }
            
            # Add additional metadata if provided
            if additional_metadata:
                doc_result['metadata'].update(additional_metadata)
            
            # Step 2: Chunk the document
            chunks = self.chunker.chunk_document(doc_result)
            
            if not chunks:
                logger.warning(f"No chunks created from {file_path.name}")
                return {
                    "success": False,
                    "chunks_added": 0,
                    "file_name": file_path.name,
                    "error": "No text content found"
                }
            
            # Step 3: Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.encode_documents(
                chunk_texts,
                batch_size=32,
                show_progress=False
            )
            
            # Step 4: Prepare metadata for storage
            metadata_list = [chunk['metadata'] for chunk in chunks]
            
            # Step 5: Add to vector store
            self.vector_store.add_embeddings(embeddings, metadata_list)
            
            logger.success(
                f"✅ Successfully ingested {file_path.name}: "
                f"{len(chunks)} chunks added"
            )
            
            return {
                "success": True,
                "chunks_added": len(chunks),
                "file_name": file_path.name,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Error ingesting {file_path.name}: {e}")
            return {
                "success": False,
                "chunks_added": 0,
                "file_name": file_path.name,
                "error": str(e)
            }
    
    def ingest_files(
        self,
        file_paths: List[Path],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest multiple files into the knowledge base.
        
        Args:
            file_paths: List of file paths
            additional_metadata: Optional metadata for all files
            
        Returns:
            Dictionary with aggregated results:
                - total_files: Total number of files
                - successful: Number of successful ingestions
                - failed: Number of failed ingestions
                - total_chunks: Total chunks added
                - results: List of individual file results
        """
        logger.info(f"Ingesting {len(file_paths)} files")
        
        results = []
        total_chunks = 0
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            result = self.ingest_file(file_path, additional_metadata)
            results.append(result)
            
            if result['success']:
                successful += 1
                total_chunks += result['chunks_added']
            else:
                failed += 1
        
        summary = {
            "total_files": len(file_paths),
            "successful": successful,
            "failed": failed,
            "total_chunks": total_chunks,
            "results": results
        }
        
        logger.info(
            f"✅ Ingestion complete: {successful}/{len(file_paths)} successful, "
            f"{total_chunks} total chunks added"
        )
        
        return summary
    
    def ingest_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory: Directory path
            recursive: Whether to search subdirectories
            file_extensions: List of extensions to include (None = all supported)
            
        Returns:
            Dictionary with ingestion summary
        """
        logger.info(f"Ingesting directory: {directory}")
        
        if not directory.exists() or not directory.is_dir():
            return {
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "total_chunks": 0,
                "results": [],
                "error": f"Directory not found: {directory}"
            }
        
        # Get supported extensions
        if file_extensions is None:
            file_extensions = list(self.parser.supported_extensions)
        
        # Find all files
        file_paths = []
        
        if recursive:
            for ext in file_extensions:
                file_paths.extend(directory.rglob(f"*.{ext}"))
        else:
            for ext in file_extensions:
                file_paths.extend(directory.glob(f"*.{ext}"))
        
        logger.info(f"Found {len(file_paths)} files to ingest")
        
        if not file_paths:
            return {
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "total_chunks": 0,
                "results": []
            }
        
        return self.ingest_files(file_paths)
    
    def ingest_text_directly(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ingest raw text directly (without parsing a file).
        
        Useful for ingesting HTML content, API responses, etc.
        
        Args:
            text: Text content to ingest
            metadata: Metadata to attach
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Ingesting text directly (length: {len(text)} chars)")
        
        try:
            # Step 1: Chunk the text
            chunks = self.chunker.chunk_text(text, metadata=metadata)
            
            if not chunks:
                return {
                    "success": False,
                    "chunks_added": 0,
                    "error": "No chunks created from text"
                }
            
            # Step 2: Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.encode_documents(
                chunk_texts,
                batch_size=32,
                show_progress=False
            )
            
            # Step 3: Prepare metadata
            metadata_list = [chunk['metadata'] for chunk in chunks]
            
            # Step 4: Add to vector store
            self.vector_store.add_embeddings(embeddings, metadata_list)
            
            logger.success(f"✅ Successfully ingested text: {len(chunks)} chunks added")
            
            return {
                "success": True,
                "chunks_added": len(chunks),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Error ingesting text: {e}")
            return {
                "success": False,
                "chunks_added": 0,
                "error": str(e)
            }
    
    def clear_knowledge_base(self) -> None:
        """
        Clear all data from the knowledge base.
        
        WARNING: This deletes all indexed documents!
        """
        logger.warning("⚠️  Clearing knowledge base")
        self.vector_store.clear()
        logger.info("✅ Knowledge base cleared")
    
    def save_knowledge_base(self) -> None:
        """Save the knowledge base to disk."""
        logger.info("Saving knowledge base")
        self.vector_store.save()
        logger.success("✅ Knowledge base saved")
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with stats
        """
        stats = self.vector_store.get_stats()
        
        # Add chunker stats
        stats['chunk_size'] = self.chunker.chunk_size
        stats['chunk_overlap'] = self.chunker.chunk_overlap
        
        return stats


# ===== GLOBAL INGESTION SERVICE INSTANCE =====
_ingestion_service_instance: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """
    Get the global IngestionService instance (singleton pattern).
    
    Returns:
        Global IngestionService instance
    """
    global _ingestion_service_instance
    
    if _ingestion_service_instance is None:
        logger.info("Creating global IngestionService instance")
        _ingestion_service_instance = IngestionService()
    
    return _ingestion_service_instance


if __name__ == "__main__":
    """Test the Ingestion Service."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/ingestion_service_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING INGESTION SERVICE")
    print("="*60 + "\n")
    
    # Test 1: Initialize service
    print("Test 1: Initializing service...")
    service = get_ingestion_service()
    print("✅ Service initialized\n")
    
    # Test 2: Create test files
    print("Test 2: Creating test files...")
    test_dir = Path("test_ingest")
    test_dir.mkdir(exist_ok=True)
    
    # Create test documents
    (test_dir / "doc1.txt").write_text(
        "This is the first test document. It contains information about machine learning.",
        encoding='utf-8'
    )
    (test_dir / "doc2.md").write_text(
        "# Second Document\n\nThis document discusses natural language processing.",
        encoding='utf-8'
    )
    (test_dir / "doc3.json").write_text(
        '{"topic": "AI", "content": "Artificial intelligence is transforming industries."}',
        encoding='utf-8'
    )
    
    print(f"✅ Created 3 test files in {test_dir}\n")
    
    # Test 3: Ingest single file
    print("Test 3: Ingesting single file...")
    result = service.ingest_file(test_dir / "doc1.txt")
    print(f"✅ Single file ingestion:")
    print(f"   Success: {result['success']}")
    print(f"   Chunks added: {result['chunks_added']}\n")
    
    # Test 4: Ingest directory
    print("Test 4: Ingesting entire directory...")
    summary = service.ingest_directory(test_dir, recursive=False)
    print(f"✅ Directory ingestion:")
    print(f"   Total files: {summary['total_files']}")
    print(f"   Successful: {summary['successful']}")
    print(f"   Total chunks: {summary['total_chunks']}\n")
    
    # Test 5: Ingest text directly
    print("Test 5: Ingesting text directly...")
    result = service.ingest_text_directly(
        text="This is direct text about deep learning and neural networks.",
        metadata={"source": "direct_input", "type": "text"}
    )
    print(f"✅ Direct text ingestion:")
    print(f"   Success: {result['success']}")
    print(f"   Chunks added: {result['chunks_added']}\n")
    
    # Test 6: Get stats
    print("Test 6: Getting knowledge base stats...")
    stats = service.get_knowledge_base_stats()
    print(f"✅ Knowledge base stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Test 7: Save knowledge base
    print("Test 7: Saving knowledge base...")
    service.save_knowledge_base()
    print("✅ Knowledge base saved\n")
    
    # Test 8: Cleanup
    print("Test 8: Cleaning up...")
    import shutil
    shutil.rmtree(test_dir)
    service.clear_knowledge_base()
    print("✅ Cleanup complete\n")
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")