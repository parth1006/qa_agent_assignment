"""
Main FastAPI Application - QA Agent Backend

This is the main entry point for the FastAPI backend server.
It includes all routes, middleware, and configuration.

"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sys

from backend.config import settings, print_config_summary
from backend.routes import ingestion_router, agent_router
from backend.routes.test_data_routes import router as test_data_router


# ===== LOGGING CONFIGURATION =====

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)

# Add file logging
logger.add(
    settings.LOG_FILE,
    rotation="10 MB",
    retention="1 week",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


# ===== FASTAPI APP =====

app = FastAPI(
    title="QA Agent API",
    description="""
    Autonomous QA Agent for Test Case and Selenium Script Generation
    
    This API provides endpoints for:
    - Document ingestion and knowledge base management
    - RAG-powered test case generation
    - Selenium script generation with HTML analysis
    
    ## Features
    - Upload and parse multiple document formats (TXT, MD, JSON, PDF, HTML, DOCX)
    - Build searchable knowledge base with vector embeddings
    - Generate test cases from documentation using LLM
    - Generate executable Selenium Python scripts
    - Source attribution for all generated content
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ===== MIDDLEWARE =====

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "message": "Internal server error"
        }
    )


# ===== STARTUP/SHUTDOWN EVENTS =====

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Starting QA Agent API...")
    
    # Print configuration summary
    print_config_summary()
    
    # Ensure directories exist
    settings.ensure_directories_exist()
    logger.info("✅ Directories verified")
    
    # Warm up services (this initializes singletons)
    try:
        from backend.services import get_ingestion_service, get_agent_service
        
        logger.info("Warming up Ingestion Service...")
        get_ingestion_service()
        logger.success("✅ Ingestion Service ready")
        
        logger.info("Warming up Agent Service...")
        get_agent_service()
        logger.success("✅ Agent Service ready")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        logger.warning("⚠️  Some services may not be available")
    
    logger.success("🎉 QA Agent API is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Shutting down QA Agent API...")
    
    # Save knowledge base before shutdown
    try:
        from backend.services import get_ingestion_service
        ingestion = get_ingestion_service()
        ingestion.save_knowledge_base()
        logger.info("✅ Knowledge base saved")
    except Exception as e:
        logger.error(f"Error saving knowledge base: {e}")
    
    logger.info("✅ Shutdown complete")


# ===== ROOT ENDPOINTS =====

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "QA Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "ingestion": "/ingestion/*",
            "agent": "/agent/*",
            "test_data": "/test-data/*"
        }
    }


@app.get("/health")
async def health_check():
    """
    Overall health check endpoint.
    
    Returns status of all services.
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check ingestion service
    try:
        from backend.services import get_ingestion_service
        ingestion = get_ingestion_service()
        stats = ingestion.get_knowledge_base_stats()
        
        health_status["services"]["ingestion"] = {
            "status": "healthy",
            "total_vectors": stats['total_vectors']
        }
    except Exception as e:
        health_status["services"]["ingestion"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check agent service
    try:
        from backend.services import get_agent_service
        agent = get_agent_service()
        
        health_status["services"]["agent"] = {
            "status": "healthy",
            "model": agent.llm_client.model
        }
    except Exception as e:
        health_status["services"]["agent"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/config")
async def get_config():
    """
    Get current configuration (non-sensitive values only).
    
    Returns publicly safe configuration information.
    """
    return {
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dim": settings.EMBEDDING_DIM,
        "llm_model": settings.GROQ_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "rag_top_k": settings.RAG_TOP_K,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "allowed_extensions": settings.ALLOWED_EXTENSIONS
    }


# ===== INCLUDE ROUTERS =====

app.include_router(ingestion_router)
app.include_router(agent_router)
app.include_router(test_data_router)


# ===== RUN SERVER =====

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    
    # When running as 'python -m backend.main', __name__ will be '__main__'
    # So we need to explicitly set the app string
    uvicorn.run(
        app,  # Pass app object directly instead of string
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )