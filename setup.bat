@echo off
REM ============================================
REM QA AGENT ASSIGNMENT - WINDOWS SETUP SCRIPT
REM ============================================

echo ==========================================
echo QA Agent Assignment - Windows Setup
echo ==========================================
echo.

REM ===== 1. CHECK PYTHON VERSION =====
echo [Step 1] Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo Python found!
echo.

REM ===== 2. CREATE VIRTUAL ENVIRONMENT =====
echo [Step 2] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    echo Virtual environment created!
)
echo.

REM ===== 3. ACTIVATE VIRTUAL ENVIRONMENT =====
echo [Step 3] Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated!
echo.

REM ===== 4. UPGRADE PIP =====
echo [Step 4] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo Pip upgraded!
echo.

REM ===== 5. INSTALL DEPENDENCIES =====
echo [Step 5] Installing dependencies...
echo This may take 5-10 minutes depending on your connection...
echo.
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo All dependencies installed!
echo.

REM ===== 6. CREATE DIRECTORIES =====
echo [Step 6] Creating required directories...
if not exist storage\faiss_index mkdir storage\faiss_index
if not exist storage\uploaded_files mkdir storage\uploaded_files
if not exist logs mkdir logs
if not exist backend\routes mkdir backend\routes
if not exist backend\services mkdir backend\services
if not exist backend\utils mkdir backend\utils
if not exist backend\vectorstore mkdir backend\vectorstore
if not exist backend\agents mkdir backend\agents
if not exist backend\models mkdir backend\models
if not exist frontend mkdir frontend
if not exist tests mkdir tests

REM Create .gitkeep files
type nul > storage\faiss_index\.gitkeep
type nul > storage\uploaded_files\.gitkeep
type nul > logs\.gitkeep

echo Directories created!
echo.

REM ===== 7. SETUP ENVIRONMENT VARIABLES =====
echo [Step 7] Setting up environment variables...
if exist .env (
    echo .env file already exists. Skipping...
) else (
    copy .env.example .env
    echo .env file created from template
    echo.
    echo IMPORTANT: Edit .env and add your GROQ_API_KEY
    echo Get your free API key from: https://console.groq.com/keys
)
echo.

REM ===== 8. CREATE __INIT__.PY FILES =====
echo [Step 8] Creating __init__.py files...
type nul > backend\__init__.py
type nul > backend\routes\__init__.py
type nul > backend\services\__init__.py
type nul > backend\utils\__init__.py
type nul > backend\vectorstore\__init__.py
type nul > backend\agents\__init__.py
type nul > backend\models\__init__.py
echo __init__.py files created!
echo.

REM ===== 9. VERIFY INSTALLATIONS =====
echo [Step 9] Verifying installations...
python -c "import fastapi, faiss, sentence_transformers, groq, streamlit, selenium; print('All critical packages imported successfully')"
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Some packages failed to import
    echo Please check the error messages above
    pause
)
echo.

REM ===== SETUP COMPLETE =====
echo ==========================================
echo SETUP COMPLETE!
echo ==========================================
echo.
echo NEXT STEPS:
echo.
echo 1. Edit .env file and add your GROQ_API_KEY:
echo    notepad .env
echo.
echo 2. Get your free Groq API key from:
echo    https://console.groq.com/keys
echo.
echo 3. Start the backend server (in a new terminal):
echo    venv\Scripts\activate
echo    cd backend
echo    uvicorn main:app --reload
echo.
echo 4. Start the frontend (in another new terminal):
echo    venv\Scripts\activate
echo    streamlit run frontend\streamlit_app.py
echo.
echo 5. Open your browser to:
echo    http://localhost:8501
echo.
echo ==========================================
echo For detailed instructions, see README.md
echo ==========================================
echo.
pause
