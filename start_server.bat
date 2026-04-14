@echo off
echo ========================================
echo    Article Generator - RAG + Ollama
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo ✓ Python is available

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [3/4] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama is not running on localhost:11434
    echo Please start Ollama first:
    echo   1. Download from https://ollama.ai
    echo   2. Run: ollama serve
    echo   3. Pull a model: ollama pull llama3.2
    echo.
    echo Continue anyway? Press any key or Ctrl+C to cancel...
    pause >nul
) else (
    echo ✓ Ollama is running
)

echo.
echo [4/4] Starting API server...
echo.
echo 🚀 Article Generator will be available at:
echo    - API Server: http://localhost:5000
echo    - Web Interface: Open article-generator.html in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py