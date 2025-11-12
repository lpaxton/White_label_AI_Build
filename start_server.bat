@echo off
echo Starting Persona Finder Server...
echo.
echo This will start a local web server to avoid CORS issues
echo when using the AI-powered persona finder.
echo.
echo Once started, open: http://localhost:8000/enhanced-persona-finder.html
echo.
echo Press Ctrl+C to stop the server
echo.
python serve.py
pause