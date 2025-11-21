"""
Streamlit Frontend - QA Agent Assignment

Simplified, minimal UI for end users.


"""

import streamlit as st
import requests
from pathlib import Path
import json
from typing import List, Optional

# ===== CONFIGURATION =====

BACKEND_URL = "https://parth4384-qa-agent-api.hf.space"

st.set_page_config(
    page_title="QA Agent - Test Case Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #764ba2;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #667eea;
        color: white;
        font-weight: bold;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #5568d3;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== HELPER FUNCTIONS =====

def check_backend_health() -> bool:
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_kb_stats() -> Optional[dict]:
    """Get knowledge base statistics."""
    try:
        response = requests.get(f"{BACKEND_URL}/ingestion/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def upload_documents(files: List) -> dict:
    """Upload documents to backend."""
    try:
        files_data = [("files", (file.name, file, file.type)) for file in files]
        response = requests.post(
            f"{BACKEND_URL}/ingestion/upload",
            files=files_data
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def generate_test_cases(feature_description: str, top_k: int = 5) -> dict:
    """Generate test cases using agent."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/agent/generate-test-cases",
            json={
                "feature_description": feature_description,
                "top_k_context": top_k
            }
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_selenium_script(test_case: str, use_checkout_html: bool = True, top_k: int = 3) -> dict:
    """Generate Selenium script using agent."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/agent/generate-selenium-script",
            json={
                "test_case": test_case,
                "use_checkout_html": use_checkout_html,
                "top_k_context": top_k
            }
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== MAIN APP =====

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">🤖 QA Test Case Generator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Upload documentation → Generate test cases → Get Selenium scripts</div>',
        unsafe_allow_html=True
    )
    
    # Check backend health
    if not check_backend_health():
        st.markdown(
            '<div class="error-box">'
            '❌ <strong>Backend server is not running!</strong><br>'
            'Please start the backend: <code>python -m backend.main</code>'
            '</div>',
            unsafe_allow_html=True
        )
        st.stop()
    
    # Sidebar - Knowledge Base Info
    with st.sidebar:
        st.markdown("### 📊 Knowledge Base")
        
        stats = get_kb_stats()
        if stats:
            total_vectors = stats.get("total_vectors", 0)
            
            # Custom metric cards
            st.markdown(
                f'<div class="metric-card">'
                f'<div style="font-size: 2rem; font-weight: bold;">{total_vectors}</div>'
                f'<div style="font-size: 0.9rem;">Document Chunks</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            if total_vectors == 0:
                st.warning("⚠️ No documents uploaded yet")
            else:
                st.success("✅ Knowledge base ready")
        else:
            st.error("❌ Unable to fetch stats")
        
        st.markdown("---")
        st.markdown("### ℹ️ How to Use")
        st.markdown("""
        1. **Upload** your documentation
        2. **Describe** the feature to test
        3. **Generate** test cases
        4. **Create** Selenium scripts
        5. **Download** your results
        """)
        
        st.markdown("---")
        st.caption("💡 Powered by RAG + LLM")
    
    # Main Content - Single Page Layout
    show_main_page()


def show_main_page():
    """Main page combining upload and agent functionality."""
    
    # Get current stats
    stats = get_kb_stats()
    total_vectors = stats.get("total_vectors", 0) if stats else 0
    
    # ===== SECTION 1: DOCUMENT UPLOAD =====
    st.markdown('<div class="section-header">📄 Step 1: Upload Documentation</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload your support documents (TXT, MD, JSON, PDF, HTML, DOCX)",
            type=["txt", "md", "json", "pdf", "html", "docx"],
            accept_multiple_files=True,
            key="file_uploader",
            help="Upload product documentation, API specs, UI guides, etc."
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        upload_button_disabled = not uploaded_files
        
        if st.button("🚀 Upload", disabled=upload_button_disabled, key="upload_btn"):
            with st.spinner("Processing documents..."):
                result = upload_documents(uploaded_files)
                
                if result.get("success"):
                    st.markdown(
                        f'<div class="success-box">'
                        f'✅ Successfully uploaded {result.get("files_processed", 0)} files<br>'
                        f'📦 Added {result.get("chunks_added", 0)} chunks to knowledge base'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.rerun()
                else:
                    st.markdown(
                        f'<div class="error-box">❌ {result.get("message", "Upload failed")}</div>',
                        unsafe_allow_html=True
                    )
    
    if uploaded_files:
        with st.expander("📎 Selected Files"):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size} bytes)")
    
    st.markdown("---")
    
    # ===== SECTION 2: TEST CASE GENERATION =====
    st.markdown('<div class="section-header">🤖 Step 2: Generate Test Cases</div>', unsafe_allow_html=True)
    
    if total_vectors == 0:
        st.markdown(
            '<div class="info-box">'
            '💡 <strong>Upload documents first</strong> to generate test cases based on your documentation.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            feature_description = st.text_area(
                "What feature do you want to test?",
                height=80,
                placeholder="Example: discount code functionality, user login flow, payment processing...",
                help="Describe the feature in natural language"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            top_k_test = st.number_input(
                "Context Chunks",
                min_value=1,
                max_value=10,
                value=5,
                help="More chunks = more context"
            )
        
        if st.button("🎯 Generate Test Cases", key="gen_test_btn"):
            if not feature_description or len(feature_description) < 10:
                st.error("⚠️ Please describe the feature (minimum 10 characters)")
            else:
                with st.spinner("🔄 Generating test cases... (10-20 seconds)"):
                    result = generate_test_cases(feature_description, top_k_test)
                    
                    if result.get("success"):
                        st.markdown(
                            '<div class="success-box">✅ Test cases generated successfully!</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Display sources
                        if result.get("sources"):
                            with st.expander("📚 Sources Used"):
                                for source in result.get("sources"):
                                    st.write(f"• {source}")
                        
                        # Display test cases
                        test_cases = result.get("test_cases", "")
                        
                        # Try to parse and display nicely
                        try:
                            test_cases_json = json.loads(test_cases)
                            if test_cases_json and len(test_cases_json) > 0:
                                st.markdown("**📋 Generated Test Cases:**")
                                st.json(test_cases_json)
                                
                                # Download button
                                st.download_button(
                                    label="💾 Download Test Cases (JSON)",
                                    data=test_cases,
                                    file_name="test_cases.json",
                                    mime="application/json"
                                )
                                
                                # Store in session state
                                st.session_state.last_test_cases = test_cases
                            else:
                                st.warning("⚠️ No test cases generated. Try a different feature description.")
                        except:
                            st.code(test_cases, language="json")
                            st.download_button(
                                label="💾 Download Test Cases",
                                data=test_cases,
                                file_name="test_cases.json",
                                mime="application/json"
                            )
                            st.session_state.last_test_cases = test_cases
                        
                    else:
                        st.markdown(
                            f'<div class="error-box">❌ {result.get("error", "Generation failed")}</div>',
                            unsafe_allow_html=True
                        )
    
    st.markdown("---")
    
    # ===== SECTION 3: SELENIUM SCRIPT GENERATION =====
    st.markdown('<div class="section-header">🔧 Step 3: Generate Selenium Script</div>', unsafe_allow_html=True)
    
    if total_vectors == 0:
        st.markdown(
            '<div class="info-box">'
            '💡 <strong>Upload documents first</strong> to generate Selenium scripts.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        test_case_input = st.text_area(
            "Paste your test case here",
            height=150,
            value=st.session_state.get("last_test_cases", ""),
            placeholder="Paste a test case from above or write your own...",
            help="Can be JSON format or plain text description"
        )
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            use_checkout = st.checkbox(
                "Analyze checkout.html for element selectors",
                value=True,
                help="Uses actual HTML structure for accurate selectors"
            )
        
        with col2:
            top_k_script = st.number_input(
                "Context",
                min_value=1,
                max_value=10,
                value=3
            )
        
        if st.button("⚙️ Generate Selenium Script", key="gen_script_btn"):
            if not test_case_input or len(test_case_input) < 20:
                st.error("⚠️ Please provide a test case (minimum 20 characters)")
            else:
                with st.spinner("🔄 Generating Selenium script... (15-25 seconds)"):
                    result = generate_selenium_script(test_case_input, use_checkout, top_k_script)
                    
                    if result.get("success"):
                        st.markdown(
                            '<div class="success-box">✅ Selenium script generated!</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Display script
                        script = result.get("script", "")
                        
                        # Clean up markdown code blocks
                        if script.startswith("```python"):
                            script = script.split("```python")[1].split("```")[0].strip()
                        elif script.startswith("```"):
                            script = script.split("```")[1].split("```")[0].strip()
                        
                        st.code(script, language="python")
                        
                        # Download button
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.download_button(
                                label="💾 Download Python Script",
                                data=script,
                                file_name="test_script.py",
                                mime="text/x-python"
                            )
                        with col2:
                            if result.get("html_analyzed"):
                                st.success("✅ HTML analyzed")
                            else:
                                st.info("ℹ️ No HTML analysis")
                        
                    else:
                        st.markdown(
                            f'<div class="error-box">❌ {result.get("error", "Generation failed")}</div>',
                            unsafe_allow_html=True
                        )


# ===== RUN APP =====

if __name__ == "__main__":
    # Initialize session state
    if "last_test_cases" not in st.session_state:
        st.session_state.last_test_cases = ""
    
    main()
