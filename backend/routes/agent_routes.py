"""
Agent Routes - API Endpoints for QA Agents

This module provides FastAPI routes for:
- Test case generation
- Selenium script generation
- Agent health checks

"""

from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger

from backend.config import settings
from backend.services import get_agent_service


# ===== REQUEST/RESPONSE MODELS =====

class TestCaseRequest(BaseModel):
    """Request model for test case generation."""
    feature_description: str = Field(
        ...,
        description="Description of the feature to test",
        min_length=10,
        example="discount code functionality"
    )
    top_k_context: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant document chunks to retrieve"
    )


class TestCaseResponse(BaseModel):
    """Response model for test case generation."""
    success: bool
    test_cases: Optional[str] = None
    sources: List[str] = []
    query: str
    error: Optional[str] = None


class SeleniumScriptRequest(BaseModel):
    """Request model for Selenium script generation."""
    test_case: str = Field(
        ...,
        description="Test case description (can be JSON or plain text)",
        min_length=20
    )
    use_checkout_html: bool = Field(
        default=True,
        description="Whether to use the checkout.html file for HTML context"
    )
    html_file_path: Optional[str] = Field(
        default=None,
        description="Custom HTML file path (overrides checkout.html)"
    )
    top_k_context: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of relevant document chunks to retrieve"
    )


class SeleniumScriptResponse(BaseModel):
    """Response model for Selenium script generation."""
    success: bool
    script: Optional[str] = None
    sources: List[str] = []
    html_analyzed: bool = False
    error: Optional[str] = None


class FeatureTestCasesRequest(BaseModel):
    """Request model for generating all test cases for a feature."""
    feature_name: str = Field(
        ...,
        description="Name of the feature",
        min_length=3,
        example="Discount Code"
    )


class ExplainTestCaseRequest(BaseModel):
    """Request model for explaining a test case."""
    test_case: str = Field(..., description="Test case to explain", min_length=20)


# ===== ROUTER SETUP =====

router = APIRouter(
    prefix="/agent",
    tags=["QA Agent"],
    responses={404: {"description": "Not found"}},
)

# Get agent service
agent_service = get_agent_service()


# ===== ROUTES =====

@router.post("/generate-test-cases", response_model=TestCaseResponse)
async def generate_test_cases(request: TestCaseRequest):
    """
    Generate test cases for a feature using RAG.
    
    The agent retrieves relevant documentation and generates comprehensive
    test cases (both positive and negative) based on the context.
    
    Args:
        request: TestCaseRequest with feature description
        
    Returns:
        TestCaseResponse with generated test cases
    """
    logger.info(f"Generating test cases for: {request.feature_description[:50]}...")
    
    try:
        result = agent_service.generate_test_cases(
            feature_description=request.feature_description,
            top_k_context=request.top_k_context
        )
        
        if result.get('error'):
            return TestCaseResponse(
                success=False,
                test_cases=None,
                sources=result.get('sources', []),
                query=request.feature_description,
                error=result['error']
            )
        
        return TestCaseResponse(
            success=True,
            test_cases=result['test_cases'],
            sources=result['sources'],
            query=request.feature_description,
            error=None
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating test cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test case generation failed: {str(e)}"
        )


@router.post("/generate-selenium-script", response_model=SeleniumScriptResponse)
async def generate_selenium_script(request: SeleniumScriptRequest):
    """
    Generate Selenium Python script for a test case.
    
    The agent analyzes the HTML structure and generates a complete,
    executable Selenium script with proper selectors and assertions.
    
    Args:
        request: SeleniumScriptRequest with test case details
        
    Returns:
        SeleniumScriptResponse with generated script
    """
    logger.info("Generating Selenium script...")
    
    # Determine HTML file path
    html_path = None
    
    if request.html_file_path:
        html_path = Path(request.html_file_path)
        if not html_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"HTML file not found: {request.html_file_path}"
            )
    elif request.use_checkout_html:
        html_path = settings.CHECKOUT_HTML_PATH
        if not html_path.exists():
            logger.warning("checkout.html not found, proceeding without HTML context")
            html_path = None
    
    try:
        result = agent_service.generate_selenium_script(
            test_case=request.test_case,
            html_file_path=html_path,
            top_k_context=request.top_k_context
        )
        
        if result.get('error'):
            return SeleniumScriptResponse(
                success=False,
                script=None,
                sources=result.get('sources', []),
                html_analyzed=bool(html_path),
                error=result['error']
            )
        
        return SeleniumScriptResponse(
            success=True,
            script=result['script'],
            sources=result['sources'],
            html_analyzed=bool(html_path),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating Selenium script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Selenium script generation failed: {str(e)}"
        )


@router.post("/generate-all-test-cases", response_model=TestCaseResponse)
async def generate_all_test_cases(request: FeatureTestCasesRequest):
    """
    Generate all test cases (positive and negative) for a feature.
    
    Args:
        request: FeatureTestCasesRequest with feature name
        
    Returns:
        TestCaseResponse with all generated test cases
    """
    logger.info(f"Generating all test cases for feature: {request.feature_name}")
    
    try:
        result = agent_service.generate_all_test_cases_for_feature(
            feature_name=request.feature_name
        )
        
        if result.get('error'):
            return TestCaseResponse(
                success=False,
                test_cases=None,
                sources=result.get('sources', []),
                query=request.feature_name,
                error=result['error']
            )
        
        return TestCaseResponse(
            success=True,
            test_cases=result['test_cases'],
            sources=result['sources'],
            query=request.feature_name,
            error=None
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating all test cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test case generation failed: {str(e)}"
        )


@router.post("/explain-test-case")
async def explain_test_case(request: ExplainTestCaseRequest):
    """
    Get a plain English explanation of a test case.
    
    Args:
        request: ExplainTestCaseRequest with test case
        
    Returns:
        Explanation in plain English
    """
    logger.info("Explaining test case...")
    
    try:
        explanation = agent_service.explain_test_case(request.test_case)
        
        return {
            "success": True,
            "explanation": explanation,
            "test_case": request.test_case
        }
        
    except Exception as e:
        logger.error(f"❌ Error explaining test case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for agent service.
    
    Returns:
        Status information
    """
    try:
        # Check if LLM client is available
        llm_client = agent_service.llm_client
        stats = llm_client.get_usage_stats()
        
        return {
            "status": "healthy",
            "service": "agent",
            "llm_model": llm_client.model,
            "total_requests": stats['total_requests'],
            "ready": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "agent",
            "error": str(e),
            "ready": False
        }


@router.get("/supported-features")
async def get_supported_features():
    """
    Get list of features that can be tested based on knowledge base.
    
    Returns:
        Information about supported features
    """
    return {
        "message": "Query the knowledge base to discover available features",
        "example_queries": [
            "discount code functionality",
            "cart operations",
            "form validation",
            "shipping methods",
            "payment processing"
        ],
        "tip": "Use descriptive feature names for best results"
    }