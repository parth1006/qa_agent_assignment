"""
Test Data Service
Analyzes test cases and generates comprehensive test datasets
"""

import json
import re
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.utils.test_data_generator import get_test_data_generator, DataType
from backend.models.llm_client import get_llm_client


class TestDataService:
    """Service for generating test data from test cases"""
    
    def __init__(self):
        self.generator = get_test_data_generator()
        self.llm_client = get_llm_client()
        logger.info("Initializing Test Data Service")
    
    def extract_fields_from_test_case(self, test_case: str) -> List[Dict[str, Any]]:
        """Extract data fields from test case description using LLM"""
        
        system_prompt = """You are an expert at analyzing test cases and identifying data fields.

Analyze the test case and extract all data fields that would need test data.

For each field, determine:
1. Field name
2. Data type (email, phone, name, username, password, age, date, price, discount_code, url, address, zipcode, credit_card, text, number)
3. Whether it's required
4. Any constraints (min/max values, format, etc.)

Return ONLY a valid JSON array in this exact format:
[
  {
    "field_name": "email",
    "data_type": "email",
    "required": true,
    "constraints": {}
  },
  {
    "field_name": "age",
    "data_type": "age",
    "required": true,
    "constraints": {"min": 18, "max": 100}
  }
]

If no fields are found, return an empty array: []
"""
        
        user_prompt = f"""Test Case:
{test_case}

Extract all data fields from this test case."""
        
        try:
            response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1
            )
            
            # Clean response
            response_clean = response.strip()
            response_clean = re.sub(r'```json\n?', '', response_clean)
            response_clean = re.sub(r'```\n?', '', response_clean)
            
            fields = json.loads(response_clean)
            logger.success(f"✅ Extracted {len(fields)} fields from test case")
            return fields
            
        except Exception as e:
            logger.error(f"❌ Error extracting fields: {e}")
            # Fallback: extract common fields from text
            return self._fallback_field_extraction(test_case)
    
    def _fallback_field_extraction(self, test_case: str) -> List[Dict[str, Any]]:
        """Fallback method to extract fields using regex"""
        fields = []
        test_case_lower = test_case.lower()
        
        # Common field patterns
        field_patterns = {
            "email": r'\b(email|e-mail|mail)\b',
            "phone": r'\b(phone|mobile|telephone|tel)\b',
            "name": r'\b(name|username|user name)\b',
            "password": r'\b(password|pwd|pass)\b',
            "age": r'\b(age)\b',
            "discount": r'\b(discount|promo|coupon|code)\b',
            "price": r'\b(price|cost|amount)\b',
            "date": r'\b(date|dob|birth date)\b',
        }
        
        for field_name, pattern in field_patterns.items():
            if re.search(pattern, test_case_lower):
                fields.append({
                    "field_name": field_name,
                    "data_type": self.generator.detect_field_type(field_name).value,
                    "required": True,
                    "constraints": {}
                })
        
        logger.warning(f"⚠️  Using fallback extraction, found {len(fields)} fields")
        return fields
    
    def generate_dataset(
        self,
        test_case: str,
        num_valid: int = 5,
        num_invalid: int = 3,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate complete dataset for a test case"""
        
        logger.info(f"Generating dataset: {num_valid} valid, {num_invalid} invalid records")
        
        # Extract fields if not provided
        if fields is None:
            fields = self.extract_fields_from_test_case(test_case)
        
        if not fields:
            logger.warning("⚠️  No fields extracted, returning empty dataset")
            return {
                "valid_data": [],
                "invalid_data": [],
                "boundary_data": [],
                "fields": []
            }
        
        # Generate valid data
        valid_data = []
        for i in range(num_valid):
            record = {}
            for field in fields:
                field_name = field["field_name"]
                data_type = DataType(field["data_type"])
                constraints = field.get("constraints", {})
                
                value = self.generator.generate_for_field(
                    field_name=field_name,
                    field_type=data_type,
                    valid=True,
                    **constraints
                )
                record[field_name] = value
            
            valid_data.append(record)
        
        # Generate invalid data
        invalid_data = []
        for i in range(num_invalid):
            record = {}
            # Make one field invalid per record
            invalid_field_idx = i % len(fields)
            
            for idx, field in enumerate(fields):
                field_name = field["field_name"]
                data_type = DataType(field["data_type"])
                constraints = field.get("constraints", {})
                
                # Make this field invalid
                is_valid = (idx != invalid_field_idx)
                
                value = self.generator.generate_for_field(
                    field_name=field_name,
                    field_type=data_type,
                    valid=is_valid,
                    **constraints
                )
                record[field_name] = value
                
                # Add reason for invalid field
                if not is_valid:
                    record["_invalid_field"] = field_name
                    record["_reason"] = f"Invalid {field_name}"
            
            invalid_data.append(record)
        
        # Generate boundary data
        boundary_data = self._generate_boundary_values(fields)
        
        result = {
            "valid_data": valid_data,
            "invalid_data": invalid_data,
            "boundary_data": boundary_data,
            "fields": fields,
            "summary": {
                "total_valid": len(valid_data),
                "total_invalid": len(invalid_data),
                "total_boundary": len(boundary_data),
                "total_fields": len(fields)
            }
        }
        
        logger.success(f"✅ Generated dataset with {len(valid_data)} valid and {len(invalid_data)} invalid records")
        return result
    
    def _generate_boundary_values(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate boundary value test cases"""
        boundary_data = []
        
        for field in fields:
            field_name = field["field_name"]
            data_type = DataType(field["data_type"])
            constraints = field.get("constraints", {})
            
            # Generate boundary cases based on data type
            if data_type == DataType.AGE:
                min_age = constraints.get("min", 18)
                max_age = constraints.get("max", 100)
                
                boundary_cases = [
                    {field_name: min_age, "_case": "minimum_age"},
                    {field_name: max_age, "_case": "maximum_age"},
                    {field_name: min_age - 1, "_case": "below_minimum", "_invalid": True},
                    {field_name: max_age + 1, "_case": "above_maximum", "_invalid": True},
                ]
                boundary_data.extend(boundary_cases)
            
            elif data_type == DataType.PRICE:
                min_price = constraints.get("min", 1.0)
                max_price = constraints.get("max", 1000.0)
                
                boundary_cases = [
                    {field_name: min_price, "_case": "minimum_price"},
                    {field_name: max_price, "_case": "maximum_price"},
                    {field_name: 0.01, "_case": "very_small_price"},
                    {field_name: -1.0, "_case": "negative_price", "_invalid": True},
                ]
                boundary_data.extend(boundary_cases)
            
            elif data_type == DataType.TEXT:
                min_length = constraints.get("min_length", 1)
                max_length = constraints.get("max_length", 100)
                
                boundary_cases = [
                    {field_name: "a" * min_length, "_case": "minimum_length"},
                    {field_name: "a" * max_length, "_case": "maximum_length"},
                    {field_name: "", "_case": "empty_string", "_invalid": True},
                    {field_name: "a" * (max_length + 1), "_case": "exceeds_maximum", "_invalid": True},
                ]
                boundary_data.extend(boundary_cases)
        
        return boundary_data
    
    def generate_from_multiple_test_cases(
        self,
        test_cases: List[Dict[str, Any]],
        num_valid_per_case: int = 3,
        num_invalid_per_case: int = 2
    ) -> Dict[str, Any]:
        """Generate dataset from multiple test cases"""
        
        logger.info(f"Generating dataset from {len(test_cases)} test cases")
        
        all_valid_data = []
        all_invalid_data = []
        all_boundary_data = []
        all_fields = {}
        
        for idx, test_case in enumerate(test_cases):
            logger.info(f"Processing test case {idx + 1}/{len(test_cases)}")
            
            # Convert test case dict to string
            test_case_str = json.dumps(test_case, indent=2)
            
            dataset = self.generate_dataset(
                test_case=test_case_str,
                num_valid=num_valid_per_case,
                num_invalid=num_invalid_per_case
            )
            
            all_valid_data.extend(dataset["valid_data"])
            all_invalid_data.extend(dataset["invalid_data"])
            all_boundary_data.extend(dataset["boundary_data"])
            
            # Merge fields
            for field in dataset["fields"]:
                field_name = field["field_name"]
                if field_name not in all_fields:
                    all_fields[field_name] = field
        
        result = {
            "valid_data": all_valid_data,
            "invalid_data": all_invalid_data,
            "boundary_data": all_boundary_data,
            "fields": list(all_fields.values()),
            "summary": {
                "total_valid": len(all_valid_data),
                "total_invalid": len(all_invalid_data),
                "total_boundary": len(all_boundary_data),
                "total_fields": len(all_fields),
                "test_cases_processed": len(test_cases)
            }
        }
        
        logger.success(f"✅ Generated complete dataset from {len(test_cases)} test cases")
        return result


# Singleton instance
_test_data_service_instance: Optional[TestDataService] = None


def get_test_data_service() -> TestDataService:
    """Get or create singleton TestDataService instance"""
    global _test_data_service_instance
    if _test_data_service_instance is None:
        _test_data_service_instance = TestDataService()
    return _test_data_service_instance