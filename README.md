# 🤖 Autonomous QA Agent - Test Case & Selenium Script Generator

An intelligent QA automation system that generates comprehensive test cases and executable Selenium scripts from documentation using RAG (Retrieval-Augmented Generation) and LLMs.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)

## ✨ Features

- **📄 Multi-Format Document Ingestion**: Upload TXT, MD, JSON, PDF, HTML, DOCX files
- **🔍 RAG-Powered Context Retrieval**: Uses FAISS vector database with semantic search
- **🤖 AI Test Case Generation**: Generates comprehensive positive and negative test cases
- **🔧 Selenium Script Generation**: Creates executable Python Selenium scripts
- **📊 Knowledge Base Management**: Track document chunks and embeddings
- **🎨 User-Friendly UI**: Clean, minimal Streamlit interface
- **🚀 REST API**: FastAPI backend with complete API documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Groq API Key ([Get free key](https://console.groq.com))

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/qa-agent-assignment.git
cd qa-agent-assignment

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run Application

**Terminal 1 - Backend:**
```bash
python -m backend.main
# Runs at http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/streamlit_app.py
# Runs at http://localhost:8501
```

## 📖 Usage

1. **Upload Documents** - Upload your product specs, API docs, or UI guides
2. **Generate Test Cases** - Describe a feature and get comprehensive test cases
3. **Generate Selenium Scripts** - Convert test cases to executable Python code
4. **Download Results** - Get JSON test cases and Python scripts

## 🏗️ Architecture

```
Frontend (Streamlit) → Backend (FastAPI) → LLM (Groq Llama 3.3)
                              ↓
                    Vector Store (FAISS)
                    Embeddings (Sentence-Transformers)
```

## 📁 Project Structure

```
qa-agent-assignment/
├── backend/              # FastAPI backend
│   ├── main.py          # API entry point
│   ├── models/          # AI models
│   ├── services/        # Business logic
│   └── routes/          # API endpoints
├── frontend/            # Streamlit UI
│   └── streamlit_app.py
├── data/               # Sample documents
└── storage/            # Vector database
```

## 🌐 Live Demo

- **Frontend**: [Streamlit Cloud]() *(Add your URL)*
- **Backend API**: [Hugging Face Spaces]() *(Add your URL)*

## 🛠️ Technologies

- **FastAPI** - Backend framework
- **Streamlit** - Frontend UI
- **FAISS** - Vector search
- **Sentence-Transformers** - Embeddings
- **Groq** - LLM inference (Llama 3.3 70B)
- **LangChain** - Text processing

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

Built with Groq, FAISS, Sentence-Transformers, FastAPI, and Streamlit

---

⭐ Star this repo if you find it helpful!
