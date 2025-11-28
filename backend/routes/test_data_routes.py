"""
Test Data Routes
API endpoints for test data generation
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.services.test_data_service import get_test_data_service


# Initialize router
router = APIRouter(prefix="/test-data", tags=["Test Data Generation"])

# Get service instance
test_data_service = get_test_data_service()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class FieldDefinition(BaseModel):
    """Field definition for test data generation"""
    field_name: str = Field(..., description="Name of the field")
    data_type: str = Field(..., description="Data type (email, phone, name, etc.)")
    required: bool = Field(default=True, description="Whether field is required")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Field constraints")


class GenerateTestDataRequest(BaseModel):
    """Request model for generating test data"""
    test_case: str = Field(..., min_length=10, description="Test case description or JSON")
    num_valid: int = Field(default=5, ge=1, le=50, description="Number of valid records")
    num_invalid: int = Field(default=3, ge=0, le=50, description="Number of invalid records")
    fields: Optional[List[FieldDefinition]] = Field(None, description="Optional explicit field definitions")


class GenerateFromTestCasesRequest(BaseModel):
    """Request model for generating from multiple test cases"""
    test_cases: List[Dict[str, Any]] = Field(..., min_length=1, description="List of test cases")
    num_valid_per_case: int = Field(default=3, ge=1, le=20, description="Valid records per test case")
    num_invalid_per_case: int = Field(default=2, ge=0, le=20, description="Invalid records per test case")


class TestDataResponse(BaseModel):
    """Response model for test data generation"""
    success: bool = Field(..., description="Whether generation was successful")
    valid_data: List[Dict[str, Any]] = Field(..., description="Valid test data records")
    invalid_data: List[Dict[str, Any]] = Field(..., description="Invalid test data records")
    boundary_data: List[Dict[str, Any]] = Field(..., description="Boundary value test data")
    fields: List[Dict[str, Any]] = Field(..., description="Extracted field definitions")
    summary: Dict[str, int] = Field(..., description="Summary statistics")
    message: Optional[str] = Field(None, description="Additional message")


class ExtractFieldsRequest(BaseModel):
    """Request model for field extraction"""
    test_case: str = Field(..., min_length=10, description="Test case description")


class ExtractFieldsResponse(BaseModel):
    """Response model for field extraction"""
    success: bool = Field(..., description="Whether extraction was successful")
    fields: List[Dict[str, Any]] = Field(..., description="Extracted fields")
    count: int = Field(..., description="Number of fields extracted")


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/generate", response_model=TestDataResponse)
async def generate_test_data(request: GenerateTestDataRequest):
    """
    Generate test data from a test case description.
    
    Analyzes the test case to identify data fields, then generates:
    - Valid test data (positive cases)
    - Invalid test data (negative cases)
    - Boundary value test data
    
    Example:
    ```json
    {
      "test_case": "Test login with valid email and password",
      "num_valid": 5,
      "num_invalid": 3
    }
    ```
    """
    try:
        logger.info(f"Generating test data: {request.num_valid} valid, {request.num_invalid} invalid")
        
        # Convert fields if provided
        fields_dict = None
        if request.fields:
            fields_dict = [field.dict() for field in request.fields]
        
        # Generate dataset
        result = test_data_service.generate_dataset(
            test_case=request.test_case,
            num_valid=request.num_valid,
            num_invalid=request.num_invalid,
            fields=fields_dict
        )
        
        return TestDataResponse(
            success=True,
            valid_data=result["valid_data"],
            invalid_data=result["invalid_data"],
            boundary_data=result["boundary_data"],
            fields=result["fields"],
            summary=result["summary"],
            message=f"Generated {result['summary']['total_valid']} valid and {result['summary']['total_invalid']} invalid records"
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating test data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test data: {str(e)}"
        )


@router.post("/generate-from-test-cases", response_model=TestDataResponse)
async def generate_from_test_cases(request: GenerateFromTestCasesRequest):
    """
    Generate test data from multiple test cases.
    
    Processes multiple test cases and generates a consolidated dataset.
    
    Example:
    ```json
    {
      "test_cases": [
        {"test_id": "TC-001", "test_scenario": "Login with valid credentials"},
        {"test_id": "TC-002", "test_scenario": "Login with invalid email"}
      ],
      "num_valid_per_case": 3,
      "num_invalid_per_case": 2
    }
    ```
    """
    try:
        logger.info(f"Generating test data from {len(request.test_cases)} test cases")
        
        result = test_data_service.generate_from_multiple_test_cases(
            test_cases=request.test_cases,
            num_valid_per_case=request.num_valid_per_case,
            num_invalid_per_case=request.num_invalid_per_case
        )
        
        return TestDataResponse(
            success=True,
            valid_data=result["valid_data"],
            invalid_data=result["invalid_data"],
            boundary_data=result["boundary_data"],
            fields=result["fields"],
            summary=result["summary"],
            message=f"Generated dataset from {result['summary']['test_cases_processed']} test cases"
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating from test cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate from test cases: {str(e)}"
        )


@router.post("/extract-fields", response_model=ExtractFieldsResponse)
async def extract_fields(request: ExtractFieldsRequest):
    """
    Extract data fields from a test case description.
    
    Analyzes the test case and identifies all data fields that would need test data.
    
    Example:
    ```json
    {
      "test_case": "Test user registration with email, password, and age"
    }
    ```
    
    Returns field definitions including:
    - Field name
    - Data type
    - Required/optional
    - Constraints
    """
    try:
        logger.info("Extracting fields from test case")
        
        fields = test_data_service.extract_fields_from_test_case(request.test_case)
        
        return ExtractFieldsResponse(
            success=True,
            fields=fields,
            count=len(fields)
        )
        
    except Exception as e:
        logger.error(f"❌ Error extracting fields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract fields: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for test data service"""
    try:
        # Test the service
        test_result = test_data_service.generator.generate_email(valid=True)
        
        return {
            "status": "healthy",
            "service": "test_data_generation",
            "test_generation": "working" if test_result else "failed"
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "test_data_generation",
            "error": str(e)
        }


@router.get("/supported-types")
async def get_supported_types():
    """Get list of supported data types"""
    return {
        "supported_types": [
            "email",
            "phone",
            "name",
            "username",
            "password",
            "age",
            "date",
            "price",
            "discount_code",
            "url",
            "address",
            "zipcode",
            "credit_card",
            "text",
            "number"
        ],
        "description": "Data types supported for test data generation"
    }