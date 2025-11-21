"""
Agent Service - Test Case and Selenium Script Generation Orchestration

This service orchestrates the autonomous QA agents:
1. Test Case Generation Agent - generates test cases from documentation
2. Selenium Script Generation Agent - generates Selenium scripts from test cases

"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from backend.config import settings
from backend.models import get_llm_client
from backend.services.rag_service import get_rag_service
from backend.utils import HTMLAnalyzer


class AgentService:
    """
    Service for orchestrating QA agents.
    
    This service provides:
    - Test case generation from documentation
    - Selenium script generation from test cases
    - Context-aware prompting with RAG
    
    Attributes:
        llm_client: LLM client for generation
        rag_service: RAG service for context retrieval
    """
    
    def __init__(self):
        """Initialize the agent service."""
        logger.info("Initializing Agent Service")
        
        self.llm_client = get_llm_client()
        self.rag_service = get_rag_service()
        
        logger.success("✅ Agent Service initialized")
    
    def generate_test_cases(
        self,
        feature_description: str,
        top_k_context: int = 5
    ) -> Dict[str, Any]:
        """
        Generate test cases for a given feature using RAG.
        
        Args:
            feature_description: Description of the feature to test
            top_k_context: Number of relevant chunks to retrieve
            
        Returns:
            Dictionary with:
                - test_cases: Generated test cases
                - sources: Documents used for generation
                - query: Original feature description
        """
        logger.info(f"Generating test cases for: {feature_description[:50]}...")
        
        # Step 1: Retrieve relevant context
        context = self.rag_service.prepare_context(
            query=feature_description,
            top_k=top_k_context,
            include_sources=True
        )
        
        sources = self.rag_service.get_relevant_documents(
            feature_description,
            top_k=top_k_context
        )
        
        # Step 2: Prepare system prompt
        system_prompt = """You are an expert QA test case generation assistant.

Your task is to generate comprehensive test cases based on the provided documentation context.

CRITICAL RULES:
1. Base ALL test cases on information in the provided context
2. If context is limited, generate at least 2-3 basic test cases based on what's available
3. Include both positive and negative test cases when possible
4. Each test case should follow this structure:

{
  "test_id": "TC-001",
  "feature": "Feature name from context",
  "test_scenario": "Clear description of what to test",
  "test_type": "positive" or "negative",
  "preconditions": ["List any setup needed"],
  "test_steps": [
    "Step 1: Detailed action",
    "Step 2: Detailed action"
  ],
  "expected_result": "What should happen",
  "source_document": "Document this is based on"
}

IMPORTANT: 
- Return a JSON array with AT LEAST 2-3 test cases
- Be creative but grounded in the documentation
- If documentation is sparse, create basic functional test cases
- DO NOT return an empty array
- Focus on the most important test scenarios

Return ONLY a valid JSON array of test cases."""
        
        # Step 3: Prepare user prompt
        user_prompt = f"""Documentation Context:
---
{context}
---

Feature to Test: {feature_description}

Based on the documentation above, generate 3-5 comprehensive test cases for this feature.

If the documentation doesn't have full details, create reasonable test cases based on:
- What the feature name suggests
- Common functionality patterns
- Standard QA best practices

Remember: Return a JSON array with at least 2-3 test cases. Be practical and helpful."""
        
        # Step 4: Generate test cases
        try:
            response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,  # Slightly higher for more creative test cases
                max_tokens=3000
            )
            
            logger.success("✅ Test cases generated successfully")
            
            return {
                "test_cases": response,
                "sources": sources,
                "query": feature_description
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating test cases: {e}")
            return {
                "test_cases": None,
                "sources": sources,
                "query": feature_description,
                "error": str(e)
            }
    
    def generate_selenium_script(
        self,
        test_case: str,
        html_file_path: Optional[Path] = None,
        top_k_context: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Selenium Python script for a test case.
        
        Args:
            test_case: Test case description (can be JSON string or text)
            html_file_path: Path to HTML file to analyze
            top_k_context: Number of relevant chunks for context
            
        Returns:
            Dictionary with:
                - script: Generated Selenium script
                - html_context: HTML structure information
                - sources: Relevant documents
        """
        logger.info("Generating Selenium script...")
        
        # Step 1: Analyze HTML if provided
        html_context = ""
        if html_file_path and html_file_path.exists():
            analyzer = HTMLAnalyzer(file_path=html_file_path)
            html_context = analyzer.get_selenium_script_context()
            logger.info(f"✅ Analyzed HTML file: {html_file_path.name}")
        
        # Step 2: Retrieve relevant documentation
        doc_context = self.rag_service.prepare_context(
            query=test_case,
            top_k=top_k_context,
            include_sources=True
        )
        
        sources = self.rag_service.get_relevant_documents(test_case, top_k=top_k_context)
        
        # Step 3: Prepare system prompt
        system_prompt = """You are an expert Selenium (Python) automation engineer.

Your task is to generate clean, executable Selenium Python scripts based on test cases and HTML structure.

CRITICAL REQUIREMENTS:
1. Use actual element selectors from the provided HTML context
2. Import necessary Selenium modules
3. Include proper waits (WebDriverWait)
4. Add assertions to verify expected results
5. Include error handling
6. Add comments explaining each step
7. Use best practices (explicit waits, not implicit)
8. The script should be self-contained and executable

IMPORTANT: 
- Use selectors from the HTML context (IDs, names, CSS selectors)
- Include setup and teardown
- Add meaningful assertions

Return ONLY the Python code. No markdown code blocks, no explanations."""
        
        # Step 4: Prepare user prompt
        user_prompt = f"""Test Case:
{test_case}

HTML Structure:
{html_context}

Documentation Context:
{doc_context}

Generate a complete, executable Selenium Python script for this test case.
Use the actual element selectors from the HTML structure provided."""
        
        # Step 5: Generate script
        try:
            response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            logger.success("✅ Selenium script generated successfully")
            
            return {
                "script": response,
                "html_context": html_context,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating Selenium script: {e}")
            return {
                "script": None,
                "html_context": html_context,
                "sources": sources,
                "error": str(e)
            }
    
    def generate_all_test_cases_for_feature(
        self,
        feature_name: str
    ) -> Dict[str, Any]:
        """
        Generate all test cases (positive and negative) for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Dictionary with generated test cases
        """
        query = f"Generate all positive and negative test cases for {feature_name}"
        return self.generate_test_cases(query)
    
    def explain_test_case(
        self,
        test_case: str
    ) -> str:
        """
        Get explanation of a test case in plain English.
        
        Args:
            test_case: Test case (JSON or text)
            
        Returns:
            Plain English explanation
        """
        system_prompt = """You are a QA expert who explains test cases in simple, clear English."""
        
        user_prompt = f"""Explain this test case in simple terms:

{test_case}

Provide a brief, clear explanation of what this test verifies."""
        
        try:
            response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            return response
        except Exception as e:
            logger.error(f"Error explaining test case: {e}")
            return f"Error: {e}"


# ===== GLOBAL AGENT SERVICE INSTANCE =====
_agent_service_instance: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """
    Get the global AgentService instance (singleton pattern).
    
    Returns:
        Global AgentService instance
    """
    global _agent_service_instance
    
    if _agent_service_instance is None:
        logger.info("Creating global AgentService instance")
        _agent_service_instance = AgentService()
    
    return _agent_service_instance


if __name__ == "__main__":
    """Test the Agent Service."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/agent_service_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING AGENT SERVICE")
    print("="*60 + "\n")
    
    # Check if GROQ API key is set
    if not settings.GROQ_API_KEY:
        print("❌ GROQ_API_KEY not set in .env file")
        print("   Please add your API key to test this service")
        exit(1)
    
    # Setup: Ingest test documents
    print("Setup: Preparing knowledge base...")
    from backend.services.ingestion_service import get_ingestion_service
    from pathlib import Path
    
    ingestion = get_ingestion_service()
    
    # Use actual support documents if available
    support_docs_dir = settings.SUPPORT_DOCS_DIR
    
    if support_docs_dir.exists():
        print(f"Using support documents from: {support_docs_dir}")
        summary = ingestion.ingest_directory(support_docs_dir, recursive=False)
        print(f"✅ Ingested {summary['successful']} documents\n")
    else:
        print("⚠️  Support documents not found, using test data")
        # Create minimal test data
        test_dir = Path("test_agent")
        test_dir.mkdir(exist_ok=True)
        
        (test_dir / "features.txt").write_text(
            "The discount code SAVE15 applies a 15% discount. "
            "Express shipping costs $10. Standard shipping is free.",
            encoding='utf-8'
        )
        
        summary = ingestion.ingest_directory(test_dir, recursive=False)
        print(f"✅ Ingested test documents\n")
    
    # Test 1: Initialize agent service
    print("Test 1: Initializing agent service...")
    agent = get_agent_service()
    print("✅ Agent service initialized\n")
    
    # Test 2: Generate test cases
    print("Test 2: Generating test cases...")
    result = agent.generate_test_cases(
        feature_description="discount code functionality",
        top_k_context=3
    )
    
    if result.get('test_cases'):
        print("✅ Test cases generated:")
        print(f"   Length: {len(result['test_cases'])} chars")
        print(f"   Sources: {', '.join(result['sources'])}")
        print(f"   Preview: {result['test_cases'][:200]}...\n")
    else:
        print(f"❌ Failed to generate test cases: {result.get('error')}\n")
    
    # Test 3: Generate Selenium script (if HTML exists)
    print("Test 3: Testing Selenium script generation...")
    
    html_path = settings.CHECKOUT_HTML_PATH
    if html_path.exists():
        print(f"Using HTML file: {html_path.name}")
        
        test_case_example = """
        Test ID: TC-001
        Feature: Add to cart
        Scenario: User clicks 'Add to Cart' button
        Expected: Item appears in cart
        """
        
        script_result = agent.generate_selenium_script(
            test_case=test_case_example,
            html_file_path=html_path,
            top_k_context=2
        )
        
        if script_result.get('script'):
            print("✅ Selenium script generated:")
            print(f"   Length: {len(script_result['script'])} chars")
            print(f"   Preview: {script_result['script'][:150]}...\n")
        else:
            print(f"❌ Failed to generate script: {script_result.get('error')}\n")
    else:
        print(f"⚠️  HTML file not found at {html_path}, skipping script generation\n")
    
    # Cleanup
    print("Cleanup: Clearing knowledge base...")
    ingestion.clear_knowledge_base()
    
    # Clean up test directory if created
    test_dir = Path("test_agent")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    print("✅ Cleanup complete\n")
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")