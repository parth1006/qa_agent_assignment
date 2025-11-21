"""
Ingestion Routes - API Endpoints for Document Ingestion

This module provides FastAPI routes for:
- Uploading documents
- Building knowledge base
- Checking ingestion status
- Clearing knowledge base

"""

from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger

from backend.config import settings
from backend.services import get_ingestion_service


# ===== REQUEST/RESPONSE MODELS =====

class IngestionResponse(BaseModel):
    """Response model for ingestion operations."""
    success: bool
    message: str
    chunks_added: int = 0
    files_processed: int = 0
    details: Optional[dict] = None


class KnowledgeBaseStats(BaseModel):
    """Response model for knowledge base statistics."""
    total_vectors: int
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    index_exists: bool
    metadata_exists: bool


class IngestDirectoryRequest(BaseModel):
    """Request model for ingesting a directory."""
    directory_path: str = Field(default="data/support_docs", description="Path to directory")
    recursive: bool = Field(default=False, description="Search subdirectories")


class IngestTextRequest(BaseModel):
    """Request model for ingesting text directly."""
    text: str = Field(..., description="Text content to ingest", min_length=10)
    source: str = Field(default="direct_input", description="Source identifier")


class ClearKBRequest(BaseModel):
    """Request model for clearing knowledge base."""
    confirm: bool = Field(..., description="Must be true to confirm deletion")



# ===== ROUTER SETUP =====

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
    responses={404: {"description": "Not found"}},
)

# Get ingestion service
ingestion_service = get_ingestion_service()


# ===== ROUTES =====

@router.post("/upload", response_model=IngestionResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Documents to upload and ingest")
):
    """
    Upload and ingest multiple documents into the knowledge base.
    
    Supported formats: TXT, MD, JSON, PDF, HTML, DOCX
    
    Args:
        files: List of files to upload
        
    Returns:
        IngestionResponse with results
    """
    logger.info(f"Received {len(files)} files for ingestion")
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Ensure upload directory exists
    upload_dir = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded files
    saved_files = []
    for file in files:
        # Validate file extension
        if not settings.is_allowed_file(file.filename):
            logger.warning(f"Skipping unsupported file: {file.filename}")
            continue
        
        # Save file
        file_path = upload_dir / file.filename
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_files.append(file_path)
            logger.info(f"✅ Saved file: {file.filename}")
        except Exception as e:
            logger.error(f"❌ Error saving {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
    
    if not saved_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid files to process"
        )
    
    # Ingest files
    try:
        result = ingestion_service.ingest_files(saved_files)
        
        # Save knowledge base
        ingestion_service.save_knowledge_base()
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {result['successful']} files",
            chunks_added=result['total_chunks'],
            files_processed=result['successful'],
            details=result
        )
        
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/ingest-directory", response_model=IngestionResponse)
async def ingest_directory(request: IngestDirectoryRequest):
    """
    Ingest all documents from a directory.
    
    Args:
        request: IngestDirectoryRequest with directory path and recursive flag
        
    Returns:
        IngestionResponse with results
    """
    logger.info(f"Ingesting directory: {request.directory_path}")
    
    dir_path = Path(request.directory_path)
    if not dir_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: {request.directory_path}"
        )
    
    try:
        result = ingestion_service.ingest_directory(dir_path, recursive=request.recursive)
        
        if result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        # Save knowledge base
        ingestion_service.save_knowledge_base()
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {result['successful']} files from directory",
            chunks_added=result['total_chunks'],
            files_processed=result['successful'],
            details=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ingesting directory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory ingestion failed: {str(e)}"
        )


@router.post("/ingest-text", response_model=IngestionResponse)
async def ingest_text(request: IngestTextRequest):
    """
    Ingest raw text directly into the knowledge base.
    
    Args:
        request: IngestTextRequest with text content and source
        
    Returns:
        IngestionResponse with results
    """
    logger.info(f"Ingesting text directly (length: {len(request.text)} chars)")
    
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text too short (minimum 10 characters)"
        )
    
    try:
        result = ingestion_service.ingest_text_directly(
            text=request.text,
            metadata={"source": request.source, "type": "direct_text"}
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Text ingestion failed')
            )
        
        # Save knowledge base
        ingestion_service.save_knowledge_base()
        
        return IngestionResponse(
            success=True,
            message="Text ingested successfully",
            chunks_added=result['chunks_added'],
            files_processed=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ingesting text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text ingestion failed: {str(e)}"
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats():
    """
    Get statistics about the knowledge base.
    
    Returns:
        KnowledgeBaseStats with current statistics
    """
    try:
        stats = ingestion_service.get_knowledge_base_stats()
        return KnowledgeBaseStats(**stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/clear", response_model=IngestionResponse)
async def clear_knowledge_base(request: ClearKBRequest):
    """
    Clear the entire knowledge base.
    
    WARNING: This deletes all indexed documents!
    
    Args:
        request: Confirmation request (confirm must be true)
        
    Returns:
        IngestionResponse confirming deletion
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion by setting 'confirm' to true"
        )
    
    try:
        logger.warning("⚠️  Clearing knowledge base via API")
        ingestion_service.clear_knowledge_base()
        
        return IngestionResponse(
            success=True,
            message="Knowledge base cleared successfully",
            chunks_added=0,
            files_processed=0
        )
        
    except Exception as e:
        logger.error(f"❌ Error clearing knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear knowledge base: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for ingestion service.
    
    Returns:
        Status information
    """
    try:
        stats = ingestion_service.get_knowledge_base_stats()
        return {
            "status": "healthy",
            "service": "ingestion",
            "total_vectors": stats['total_vectors'],
            "ready": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "ingestion",
            "error": str(e),
            "ready": False
        }