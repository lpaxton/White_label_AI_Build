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

# Import FCAT modules (MongoDB Atlas + embedding service)
try:
    import fcat_db
    from embedding_service import generate_embedding, strip_html, build_embedding_metadata
    FCAT_AVAILABLE = True
except ImportError as e:
    FCAT_AVAILABLE = False
    print(f"Warning: FCAT modules not available ({e}). /api/save-to-fcat endpoint disabled.")

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
            'GET /api/rewrite/health': 'Rewrite API health check',
            'POST /api/save-to-fcat': 'Save processed article to MongoDB Atlas (FCAT)',
            'GET /api/fcat/status': 'FCAT MongoDB connection status',
            'POST /api/chat': 'Ask questions answered solely from the FCAT article database',
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

@app.route('/api/extract-article', methods=['POST'])
def extract_article():
    """
    Proxy-fetch a URL server-side and return the raw HTML.
    Avoids browser CORS restrictions and uses proper browser-like headers
    so that Fidelity's server returns the full page (including disclosure
    sections with <s-assigned-wrapper> eReview IDs).
    The client parses the HTML locally after receiving it.
    """
    try:
        import requests as req
        data = request.get_json()
        url = (data or {}).get('url', '').strip()
        if not url:
            return jsonify({'error': 'url is required'}), 400

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

        resp = req.get(url, headers=headers, timeout=20, allow_redirects=True)
        resp.raise_for_status()

        # Detect encoding and decode body correctly
        html = resp.content.decode(resp.apparent_encoding or 'utf-8', errors='replace')

        return jsonify({'success': True, 'html': html, 'url': url})

    except Exception as e:
        print(f'[extract-article] Error fetching {url}: {e}')
        return jsonify({'error': str(e)}), 500


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


# ============================================================
# FCAT MONGODB ATLAS ENDPOINTS
# ============================================================

@app.route('/api/save-to-fcat', methods=['POST'])
def save_to_fcat():
    """
    Save a processed article to MongoDB Atlas (FCAT database).

    Request body:
        - original_html: Raw HTML before neutralization
        - neutralized_html: Output of ClaudeRewriter
        - source_url: Original URL the article came from
        - source: "fidelity_cms" or "vendor_enrichment"
        - topics: List of topic tags (optional)
        - persona_tags: List of persona tags (optional)
        - categories: List of categories (optional)
        - difficulty_level: "beginner" | "intermediate" | "advanced" (optional)
        - pipeline_status: Pipeline status (default: "areview_pending")
    """
    if not FCAT_AVAILABLE:
        return jsonify({
            'error': 'FCAT modules not available. Install pymongo, openai, python-dotenv.',
            'fcat_available': False
        }), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Required fields
        neutralized_html = data.get('neutralized_html', '').strip()
        original_html = data.get('original_html', '').strip()
        source_url = data.get('source_url', '').strip()
        source = data.get('source', '').strip()
        origin_url = data.get('origin_url', None)  # Actual origin URL (may differ from source_url dedup key)

        if not neutralized_html:
            return jsonify({'error': 'neutralized_html is required'}), 400
        if not source_url:
            return jsonify({'error': 'source_url is required'}), 400
        if not source:
            return jsonify({'error': 'source is required'}), 400

        # Dedupe check
        if fcat_db.article_exists_by_url(source_url):
            return jsonify({
                'error': f'Article with source_url already exists: {source_url}',
                'duplicate': True
            }), 409

        # Generate plain text from neutralized HTML
        plain_text = strip_html(neutralized_html)

        # Generate embedding (non-blocking — returns None on failure)
        print(f"[save-to-fcat] Generating embedding for article from {source_url}...")
        vector = generate_embedding(plain_text)
        embedding_doc = build_embedding_metadata(vector)

        # Build the full article document
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        article_doc = {
            "source": source,
            "source_url": source_url,
            "origin_url": origin_url or None,
            "ereview_id": data.get('ereview_id', None),
            "ingest_date": now,
            "content": {
                "original_html": original_html,
                "neutralized_html": neutralized_html,
                "plain_text": plain_text,
            },
            "pipeline_status": data.get('pipeline_status', 'areview_pending'),
            "hitl_reviewed_by": None,
            "hitl_reviewed_at": None,
            "areview_approved_at": None,
            "taxonomy": {
                "categories": data.get('categories', []),
                "topics": data.get('topics', []),
                "persona_tags": data.get('persona_tags', []),
                "difficulty_level": data.get('difficulty_level', None),
            },
            "reading_grade_level": None,
            "white_label_ready": False,
            "associated_actions": [],
            "embedding": embedding_doc,
            "stats": {
                "views": 0,
                "completions": 0,
                "actions_taken": 0,
            },
            "created_at": now,
            "updated_at": now,
        }

        # Save to MongoDB Atlas
        article_id = fcat_db.save_article(article_doc)

        print(f"[save-to-fcat] Article saved successfully: {article_id}")

        return jsonify({
            'success': True,
            'article_id': article_id,
            'message': f'Article saved to FCAT database',
            'embedding_generated': vector is not None,
            'plain_text_length': len(plain_text),
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Save to FCAT failed: {str(e)}'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    DB-grounded chatbot endpoint.

    Retrieves relevant articles from the FCAT MongoDB database and passes
    their content to Claude with strict instructions to answer ONLY from
    that retrieved context.  No outside knowledge is used.

    Request body:
        - message: The user's question (required)
        - history: Array of {role, content} prior turns (optional, max 6)
    """
    if not FCAT_AVAILABLE:
        return jsonify({'error': 'FCAT modules not available'}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'message is required'}), 400

        history = data.get('history', [])

        # ── Retrieve relevant articles from the database ───────────────────
        # Try Atlas Vector Search first (semantic), fall back to keyword search
        articles = []
        query_vector = generate_embedding(user_message) if FCAT_AVAILABLE else None
        if query_vector:
            try:
                articles = fcat_db.vector_search_articles(query_vector, limit=10)
                print(f"[chat] Using vector search -> {len(articles)} candidates")
            except Exception as vec_err:
                print(f"[chat] Vector search unavailable ({vec_err}), falling back to text search")

        if not articles:
            articles = fcat_db.search_articles(user_message, limit=10)

        if not articles:
            return jsonify({
                'success': True,
                'answer': "The knowledge base doesn't contain any articles yet, or none matched your question. Please add articles to the database first.",
                'sources': [],
                'articles_used': 0,
            })

        # ── Build grounded context ─────────────────────────────────────────
        context_parts = []
        sources = []
        for i, article in enumerate(articles, 1):
            plain_text = (article.get('content') or {}).get('plain_text', '').strip()
            if not plain_text:
                continue
            # Cap individual article length to keep prompt manageable
            if len(plain_text) > 4000:
                plain_text = plain_text[:4000] + ' [...]'
            topics = (article.get('taxonomy') or {}).get('topics', [])
            display_url = article.get('origin_url') or article.get('source_url', '')
            context_parts.append(f'=== ARTICLE {i} ===\n{plain_text}')
            sources.append({
                'id': article['_id'],
                'source_url': display_url,
                'topics': topics,
            })

        if not context_parts:
            return jsonify({
                'success': True,
                'answer': "Articles were found in the database but contained no readable text.",
                'sources': [],
                'articles_used': 0,
            })

        grounded_context = "\n\n".join(context_parts)

        # ── Call Claude with strict grounding instructions ─────────────────
        from anthropic import Anthropic
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY is not configured on the server'}), 503

        client = Anthropic(api_key=api_key)

        SYSTEM_PROMPT = """\
You are a financial education assistant that operates under strict regulatory constraints.

YOU MAY ONLY USE THE ARTICLE CONTENT PROVIDED IN EACH MESSAGE TO ANSWER QUESTIONS.

MANDATORY RULES — NO EXCEPTIONS:
1. Base every answer exclusively on the article excerpts provided.  
   Do NOT use your training data, general knowledge, or any information
   not explicitly present in the provided articles.
2. If the provided articles do not contain sufficient information to answer
   the question, respond with exactly:
   "The available articles don\'t contain enough information to answer that question."
3. Do NOT speculate, infer beyond what is written, or fill gaps with outside knowledge.
4. Do NOT introduce any facts, statistics, or guidance not found in the articles.
5. Keep your tone clear, helpful, and professional.
6. Where relevant, indicate which article your answer draws from (e.g. "According to the article...").

This is a regulatory requirement. Violating these rules is not acceptable under any circumstances."""

        # Build message list — inject fresh context into every user turn
        # so the model always answers from the retrieved documents
        messages = []
        for turn in history[-6:]:
            if turn.get('role') in ('user', 'assistant'):
                messages.append({'role': turn['role'], 'content': turn['content']})

        grounded_user_message = (
            f"Below are the relevant articles retrieved from the knowledge base:\n\n"
            f"{grounded_context}\n\n"
            f"---\n\n"
            f"Using ONLY the article content above, please answer the following question:\n\n"
            f"{user_message}"
        )
        messages.append({'role': 'user', 'content': grounded_user_message})

        response = client.messages.create(
            model='claude-opus-4-5',
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        answer = response.content[0].text
        print(f"[chat] Answered using {len(context_parts)} article(s)")

        return jsonify({
            'success': True,
            'answer': answer,
            'sources': sources,
            'articles_used': len(context_parts),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500


@app.route('/api/fcat/status', methods=['GET'])
def fcat_status():
    """Health check for the FCAT MongoDB connection."""
    if not FCAT_AVAILABLE:
        return jsonify({'status': 'unavailable', 'reason': 'FCAT modules not installed'}), 503

    try:
        fcat_db.connect()
        return jsonify({
            'status': 'ok',
            'database': fcat_db.DATABASE_NAME,
            'collection': fcat_db.COLLECTION_NAME,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/fcat/backfill-embeddings', methods=['POST'])
def backfill_embeddings():
    """
    Generate embeddings for any articles in the DB that are missing them.
    Safe to call repeatedly. Processes up to `batch_size` articles per call
    (default 50) so it can be run incrementally without timing out.

    POST body (JSON, optional):
        { "batch_size": 50 }
    """
    if not FCAT_AVAILABLE:
        return jsonify({'error': 'FCAT modules not available'}), 503

    data = request.get_json(silent=True) or {}
    batch_size = int(data.get('batch_size', 50))
    if batch_size < 1 or batch_size > 500:
        return jsonify({'error': 'batch_size must be between 1 and 500'}), 400

    try:
        result = fcat_db.backfill_embeddings(batch_size=batch_size)
        return jsonify({'success': True, **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Backfill failed: {str(e)}'}), 500


@app.route('/api/fcat/vector-index-info', methods=['GET'])
def vector_index_info():
    """
    Returns the Atlas Vector Search index definition you need to create
    in the MongoDB Atlas UI to enable semantic search.
    """
    return jsonify({
        'instructions': (
            'Create a Vector Search index in MongoDB Atlas UI: '
            'Atlas → Your Cluster → Search → Create Search Index → JSON Editor'
        ),
        'index_name': 'vector_index',
        'database': 'fcat',
        'collection': 'articles',
        'index_definition': {
            'fields': [
                {
                    'type': 'vector',
                    'path': 'embedding.vector',
                    'numDimensions': 1536,
                    'similarity': 'cosine',
                }
            ]
        },
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
    print("")
    print("FCAT (MongoDB Atlas):")
    print("  POST /api/save-to-fcat - Save article to MongoDB Atlas")
    print("  GET /api/fcat/status - FCAT connection status")
    print("  POST /api/chat - DB-grounded chatbot (answers from database only)")
    if FCAT_AVAILABLE:
        print("  Status: FCAT modules loaded")
    else:
        print("  Status: FCAT modules not available (install pymongo, openai, python-dotenv)")
    print("\nStarting server on http://localhost:5000")

    ensure_upload_dir()
    app.run(host='0.0.0.0', port=5000, debug=True)