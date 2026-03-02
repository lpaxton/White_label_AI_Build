#!/usr/bin/env python3
"""
Article Generator Flask API Server
Provides REST API endpoints for the Article Generator web interface.
Includes Claude-powered Article Rewriter endpoints.
"""

import os
import json
import tempfile
import shutil
import time
from typing import List, Dict, Optional
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import traceback

# Import our Article Generator class
from article_generator import ArticleGenerator

# Import Claude Rewriter (optional - will work without it via client-side)
try:
    from claude_rewriter import ClaudeRewriter
    CLAUDE_REWRITER_AVAILABLE = True
except ImportError:
    CLAUDE_REWRITER_AVAILABLE = False
    print("Warning: claude_rewriter module not available. Rewrite API will require client-side processing.")

app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Configuration
UPLOAD_FOLDER = 'uploaded_articles'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max total upload size

# Global generator instance
generator = None
temp_articles_dir = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Article Generator API Server is running',
        'endpoints': {
            'POST /api/upload': 'Upload article files',
            'POST /api/setup-rag': 'Setup RAG database',
            'POST /api/test-ollama': 'Test Ollama connection',
            'POST /api/generate': 'Generate article',
            'POST /api/analyze-style': 'Analyze writing style',
            'GET /api/status': 'Get current status',
            'GET /api/health': 'Health check with model validation',
            'POST /api/rewrite': 'Rewrite article with Claude AI (brand neutralization)',
            'GET /api/rewrite/config': 'Get rewrite configuration',
            'GET /api/rewrite/health': 'Rewrite API health check'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check including model validation"""
    global generator, temp_articles_dir
    
    health_status = {
        'api_server': 'ok',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'rag_setup': False,
        'ollama_connection': 'unknown',
        'model_status': 'unknown',
        'articles_count': 0
    }
    
    # Check RAG status
    if generator and generator.articles_loaded:
        health_status['rag_setup'] = True
        
    # Check articles
    if temp_articles_dir and os.path.exists(temp_articles_dir):
        health_status['articles_count'] = len([f for f in os.listdir(temp_articles_dir) if f.endswith('.txt')])
    
    # Check Ollama connection and model
    if generator:
        try:
            import requests
            # Test basic connection
            response = requests.get(f"{generator.ollama_url}/api/tags", timeout=5)
            if response.ok:
                health_status['ollama_connection'] = 'ok'
                
                # Test current model
                test_response = requests.post(f"{generator.ollama_url}/api/generate", json={
                    "model": generator.model_name,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 5}
                }, timeout=15)
                
                if test_response.ok:
                    test_data = test_response.json()
                    if test_data.get('response', '').strip():
                        health_status['model_status'] = 'ok'
                        health_status['model_name'] = generator.model_name
                    else:
                        health_status['model_status'] = 'empty_response'
                else:
                    health_status['model_status'] = f'http_error_{test_response.status_code}'
            else:
                health_status['ollama_connection'] = f'http_error_{response.status_code}'
                
        except Exception as e:
            health_status['ollama_connection'] = 'failed'
            health_status['connection_error'] = str(e)
    
    return jsonify(health_status)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    global generator, temp_articles_dir
    
    status = {
        'rag_setup': generator is not None and generator.articles_loaded if generator else False,
        'articles_uploaded': temp_articles_dir is not None and os.path.exists(temp_articles_dir) and len(os.listdir(temp_articles_dir)) > 0,
        'upload_folder': UPLOAD_FOLDER,
        'temp_dir': temp_articles_dir
    }
    
    return jsonify(status)

@app.route('/api/upload', methods=['POST'])
def upload_articles():
    """Upload and store article files"""
    global temp_articles_dir
    
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        print(f"Processing upload request with {len(files)} files")
        
        # Create temporary directory for uploaded articles
        if temp_articles_dir and os.path.exists(temp_articles_dir):
            shutil.rmtree(temp_articles_dir)
        
        temp_articles_dir = tempfile.mkdtemp(prefix='article_generator_')
        
        uploaded_files = []
        total_size = 0
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_articles_dir, filename)
                
                # Save file
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Validate content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        word_count = len(content.split()) if content else 0
                except:
                    # Try different encoding
                    try:
                        with open(file_path, 'r', encoding='latin1') as f:
                            content = f.read().strip()
                            word_count = len(content.split()) if content else 0
                    except:
                        word_count = 0
                
                uploaded_files.append({
                    'filename': filename,
                    'size': file_size,
                    'word_count': word_count
                })
        
        if not uploaded_files:
            return jsonify({'error': 'No valid .txt files uploaded'}), 400
        
        result = {
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'files': uploaded_files,
            'total_files': len(uploaded_files),
            'total_size': total_size,
            'temp_dir': temp_articles_dir
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/setup-rag', methods=['POST'])
def setup_rag():
    """Initialize RAG database with uploaded articles"""
    global generator, temp_articles_dir
    
    try:
        if not temp_articles_dir or not os.path.exists(temp_articles_dir):
            return jsonify({'error': 'No articles uploaded. Please upload articles first.'}), 400
        
        data = request.get_json() or {}
        model_name = data.get('model', 'llama3.2')
        ollama_url = data.get('ollama_url', 'http://localhost:11434')
        
        # Initialize generator
        generator = ArticleGenerator(
            articles_dir=temp_articles_dir,
            model_name=model_name,
            ollama_url=ollama_url
        )
        
        # Load articles into RAG database
        stats = generator.load_articles(force_reload=True)
        
        result = {
            'message': 'RAG database setup complete',
            'stats': stats,
            'model': model_name,
            'ollama_url': ollama_url
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f'RAG setup failed: {str(e)}'
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/test-ollama', methods=['POST'])
def test_ollama():
    """Test connection to Ollama server"""
    try:
        data = request.get_json() or {}
        ollama_url = data.get('ollama_url', 'http://localhost:11434')
        model_name = data.get('model', 'llama3.2')
        
        # Test connection by getting available models
        import requests
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if not response.ok:
            return jsonify({
                'error': f'Ollama server returned HTTP {response.status_code}',
                'connected': False
            }), 400
        
        models_data = response.json()
        available_models = [model['name'] for model in models_data.get('models', [])]
        
        # Check if requested model is available
        model_available = any(model_name in model for model in available_models)
        
        result = {
            'connected': True,
            'available_models': available_models,
            'requested_model': model_name,
            'model_available': model_available,
            'ollama_url': ollama_url
        }
        
        if not model_available:
            result['warning'] = f'Model "{model_name}" not found. Available models: {", ".join(available_models)}'
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Cannot connect to Ollama: {str(e)}',
            'connected': False
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Ollama test failed: {str(e)}',
            'connected': False
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate_article():
    """Generate new article using RAG + Ollama"""
    global generator
    
    try:
        if not generator or not generator.articles_loaded:
            return jsonify({'error': 'RAG database not setup. Please setup RAG first.'}), 400
        
        data = request.get_json() or {}
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        num_examples = data.get('num_examples', 3)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 5000)  # Default to 5000 for longer content
        model = data.get('model', generator.model_name)  # Get model from request
        
        # Update generator model if different
        if model != generator.model_name:
            print(f"Switching model from {generator.model_name} to {model}")
            generator.model_name = model
            
        # Validate model before generation
        try:
            # Quick test to see if model responds
            import requests
            test_response = requests.post(f"{generator.ollama_url}/api/generate", json={
                "model": model,
                "prompt": "Test",
                "stream": False,
                "options": {"num_predict": 10}
            }, timeout=30)
            
            if not test_response.ok:
                raise Exception(f"Model '{model}' validation failed: HTTP {test_response.status_code}")
                
        except Exception as e:
            return jsonify({
                'error': f"Model '{model}' is not available or responding. Please: 1) Check if model is pulled (ollama pull {model}) 2) Try a different model 3) Restart Ollama. Error: {str(e)}"
            }), 400
        
        # Generate article using the correct method name
        start_time = time.time()
        
        content = generator.generate_content(
            prompt=prompt,
            num_examples=num_examples,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        generation_time = time.time() - start_time
        
        # Create result dictionary
        result = {
            'content': content,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'generation_time': round(generation_time, 2),
            'settings': {
                'prompt': prompt,
                'num_examples': num_examples,
                'temperature': temperature,
                'model': generator.model_name
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f'Article generation failed: {str(e)}'
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/analyze-style', methods=['POST'])
def analyze_style():
    """Analyze writing style of uploaded articles"""
    global generator
    
    try:
        if not generator or not generator.articles_loaded:
            return jsonify({'error': 'RAG database not setup. Please setup RAG first.'}), 400
        
        # Analyze style
        analysis = generator.analyze_style()
        
        return jsonify(analysis)
        
    except Exception as e:
        error_msg = f'Style analysis failed: {str(e)}'
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

# ============================================================
# ARTICLE REWRITER API ENDPOINTS (Claude-powered)
# ============================================================

@app.route('/api/rewrite', methods=['POST'])
def rewrite_article():
    """
    Rewrite article content to neutralize brand references using Claude AI.

    Request body:
        - html: HTML content to process
        - api_key: Claude API key
        - use_ai: Whether to use Claude AI (default: True)
        - brand: Brand to neutralize (default: "Fidelity")
        - remove_trademark_symbols: Remove trademark symbols (default: True)
        - remove_parenthetical_content: Remove parenthetical content (default: True)
        - remove_footnotes: Remove footnotes (default: True)
        - check_hyperlinks: Flag unmarked hyperlinks (default: True)
        - check_possessive_references: Flag possessive refs (default: True)
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        html_content = data.get('html', '').strip()
        api_key = data.get('api_key', '').strip()
        use_ai = data.get('use_ai', True)
        brand = data.get('brand', 'Fidelity')

        if not html_content:
            return jsonify({'error': 'No HTML content provided'}), 400

        if use_ai and not api_key:
            return jsonify({'error': 'Claude API key required for AI rewriting'}), 400

        # Build processing options
        processing_options = {
            'remove_trademark_symbols': data.get('remove_trademark_symbols', True),
            'remove_parenthetical_content': data.get('remove_parenthetical_content', True),
            'remove_footnotes': data.get('remove_footnotes', True),
            'check_hyperlinks': data.get('check_hyperlinks', True),
            'check_possessive_references': data.get('check_possessive_references', True)
        }

        if not CLAUDE_REWRITER_AVAILABLE:
            return jsonify({
                'error': 'Server-side rewriting not available. Please use client-side processing.',
                'use_client_side': True
            }), 503

        # Initialize rewriter with provided API key
        config = {
            'processing_options': processing_options
        }

        rewriter = ClaudeRewriter(api_key=api_key, config=config)

        # Process the content
        result = rewriter.process_html(html_content, use_ai=use_ai, brand=brand)

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Rewrite failed: {str(e)}'}), 500


@app.route('/api/rewrite/config', methods=['GET'])
def get_rewrite_config():
    """Get the default rewrite configuration."""
    if not CLAUDE_REWRITER_AVAILABLE:
        return jsonify({
            'error': 'Claude rewriter module not available',
            'default_config': {
                'brand_replacements': {
                    'Fidelity': {
                        'company_name': ['many major brokerages', 'reputable financial services firms'],
                        'products': {
                            'Fidelity Go': 'automated robo advisors',
                            'Fidelity Youth': 'custodial accounts for minors'
                        }
                    }
                }
            }
        })

    return jsonify({
        'config': ClaudeRewriter.DEFAULT_CONFIG,
        'available': True
    })


@app.route('/api/rewrite/health', methods=['GET'])
def rewrite_health():
    """Health check for the rewrite API."""
    return jsonify({
        'status': 'ok',
        'claude_rewriter_available': CLAUDE_REWRITER_AVAILABLE,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB per file.'}), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error occurred.'}), 500

if __name__ == '__main__':
    print("Starting Article Generator API Server...")
    print("Endpoints available:")
    print("  POST /api/upload - Upload article files")
    print("  POST /api/setup-rag - Setup RAG database")
    print("  POST /api/test-ollama - Test Ollama connection")
    print("  POST /api/generate - Generate article")
    print("  POST /api/analyze-style - Analyze writing style")
    print("  GET /api/status - Get system status")
    print("")
    print("Article Rewriter (Claude-powered):")
    print("  POST /api/rewrite - Rewrite article with Claude AI")
    print("  GET /api/rewrite/config - Get rewrite configuration")
    print("  GET /api/rewrite/health - Rewrite API health check")
    if CLAUDE_REWRITER_AVAILABLE:
        print("  Status: Claude Rewriter module loaded")
    else:
        print("  Status: Client-side processing only (module not available)")
    print("\nStarting server on http://localhost:5000")

    ensure_upload_dir()
    app.run(host='0.0.0.0', port=5000, debug=True)