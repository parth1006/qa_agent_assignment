"""
Configuration Management for QA Agent Assignment

This module provides centralized configuration using Pydantic Settings.
All environment variables are loaded from .env file and validated.

"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by creating a .env file in the project root.
    See .env.example for available configuration options.
    """
    
    # ===== PROJECT PATHS =====
    PROJECT_ROOT: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    SUPPORT_DOCS_DIR: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "support_docs"
    )
    CHECKOUT_HTML_PATH: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "checkout.html"
    )
    
    # ===== STORAGE PATHS =====
    FAISS_INDEX_DIR: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "storage" / "faiss_index"
    )
    UPLOAD_DIR: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "storage" / "uploaded_files"
    )
    LOG_FILE: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "logs" / "app.log"
    )
    
    # ===== LLM CONFIGURATION =====
    GROQ_API_KEY: str = Field(
        default="",
        description="Groq Cloud API key - get from https://console.groq.com/keys"
    )
    GROQ_MODEL: str = Field(
        default="llama-3.1-70b-versatile",
        description="Groq model to use for LLM inference"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0=deterministic, 1.0=creative)"
    )
    LLM_MAX_TOKENS: int = Field(
        default=4096,
        ge=256,
        le=8192,
        description="Maximum tokens for LLM response"
    )
    
    # ===== EMBEDDING CONFIGURATION =====
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence Transformer model for embeddings"
    )
    EMBEDDING_DIM: int = Field(
        default=384,
        description="Embedding dimension (384 for all-MiniLM-L6-v2)"
    )
    
    # ===== FAISS CONFIGURATION =====
    FAISS_INDEX_TYPE: str = Field(
        default="IndexFlatL2",
        description="FAISS index type (IndexFlatL2, IndexHNSWFlat, etc.)"
    )
    
    # ===== RAG CONFIGURATION =====
    RAG_TOP_K: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve for RAG"
    )
    RAG_SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for RAG (lower = more similar)"
    )
    
    # ===== TEXT CHUNKING CONFIGURATION =====
    CHUNK_SIZE: int = Field(
        default=1000,
        ge=100,
        le=2000,
        description="Chunk size for text splitting"
    )
    CHUNK_OVERLAP: int = Field(
        default=200,
        ge=0,
        le=500,
        description="Chunk overlap for context preservation"
    )
    
    # ===== FILE UPLOAD CONFIGURATION =====
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file upload size in MB"
    )
    ALLOWED_EXTENSIONS: list[str] = Field(
        default=["txt", "md", "json", "pdf", "html", "docx", "xlsx"],
        description="Allowed file extensions for upload"
    )
    
    # ===== BACKEND CONFIGURATION =====
    BACKEND_HOST: str = Field(default="0.0.0.0", description="FastAPI host")
    BACKEND_PORT: int = Field(default=8000, ge=1024, le=65535, description="FastAPI port")
    RELOAD: bool = Field(default=True, description="Enable hot reload (development)")
    
    # ===== FRONTEND CONFIGURATION =====
    STREAMLIT_PORT: int = Field(default=8501, ge=1024, le=65535)
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API URL for Streamlit"
    )
    
    # ===== LOGGING CONFIGURATION =====
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # ===== SELENIUM CONFIGURATION =====
    SELENIUM_IMPLICIT_WAIT: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Selenium implicit wait time in seconds"
    )
    SELENIUM_PAGE_LOAD_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Selenium page load timeout in seconds"
    )
    
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("GROQ_API_KEY")
    @classmethod
    def validate_groq_api_key(cls, v: str) -> str:
        """Validate that Groq API key is provided."""
        if not v or v == "":
            print("⚠️  WARNING: GROQ_API_KEY not set in .env file")
            print("   Get your free API key from: https://console.groq.com/keys")
            print("   The application may not work without it!")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper
    
    def ensure_directories_exist(self) -> None:
        """
        Create all required directories if they don't exist.
        Should be called during application startup.
        """
        directories = [
            self.FAISS_INDEX_DIR,
            self.UPLOAD_DIR,
            self.LOG_FILE.parent,
            self.DATA_DIR,
            self.SUPPORT_DOCS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    def is_allowed_file(self, filename: str) -> bool:
        """
        Check if file extension is allowed for upload.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file extension is allowed, False otherwise
        """
        if "." not in filename:
            return False
        extension = filename.rsplit(".", 1)[1].lower()
        return extension in self.ALLOWED_EXTENSIONS
    
    def get_faiss_index_path(self) -> Path:
        """Get the full path to the FAISS index file."""
        return self.FAISS_INDEX_DIR / "qa_agent.index"
    
    def get_faiss_metadata_path(self) -> Path:
        """Get the full path to the FAISS metadata file."""
        return self.FAISS_INDEX_DIR / "qa_agent_metadata.json"


# ===== GLOBAL SETTINGS INSTANCE =====
# This instance is imported throughout the application
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories_exist()


# ===== HELPER FUNCTIONS =====
def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    This function is useful for dependency injection in FastAPI routes.
    
    Returns:
        Global settings instance
    """
    return settings


def print_config_summary() -> None:
    """Print a summary of current configuration (for debugging)."""
    print("\n" + "="*60)
    print("QA AGENT CONFIGURATION SUMMARY")
    print("="*60)
    print(f"Project Root:        {settings.PROJECT_ROOT}")
    print(f"Data Directory:      {settings.DATA_DIR}")
    print(f"FAISS Index Dir:     {settings.FAISS_INDEX_DIR}")
    print(f"Upload Directory:    {settings.UPLOAD_DIR}")
    print(f"\nLLM Model:           {settings.GROQ_MODEL}")
    print(f"Embedding Model:     {settings.EMBEDDING_MODEL}")
    print(f"Embedding Dim:       {settings.EMBEDDING_DIM}")
    print(f"\nRAG Top K:           {settings.RAG_TOP_K}")
    print(f"Chunk Size:          {settings.CHUNK_SIZE}")
    print(f"Chunk Overlap:       {settings.CHUNK_OVERLAP}")
    print(f"\nBackend URL:         http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"Log Level:           {settings.LOG_LEVEL}")
    print(f"Groq API Key Set:    {'✅ Yes' if settings.GROQ_API_KEY else '❌ No'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test configuration
    print_config_summary()
    
    # Verify critical paths exist
    print("Verifying paths...")
    if settings.CHECKOUT_HTML_PATH.exists():
        print(f"✅ checkout.html found at {settings.CHECKOUT_HTML_PATH}")
    else:
        print(f"❌ checkout.html NOT found at {settings.CHECKOUT_HTML_PATH}")
    
    if settings.SUPPORT_DOCS_DIR.exists():
        docs = list(settings.SUPPORT_DOCS_DIR.glob("*"))
        print(f"✅ Found {len(docs)} support documents:")
        for doc in docs:
            print(f"   - {doc.name}")
    else:
        print(f"❌ Support docs directory NOT found")