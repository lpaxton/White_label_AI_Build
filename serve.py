#!/usr/bin/env python3
"""
Simple HTTP Server for the Persona Finder
Serves the HTML files and acts as a CORS proxy for Ollama requests
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import sys
from urllib.error import URLError
from bs4 import BeautifulSoup
import re

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Handle CORS proxy requests to Ollama
        if self.path.startswith('/api/'):
            self.proxy_to_ollama()
        else:
            super().do_GET()
    
    def do_POST(self):
        # Handle article extraction requests
        if self.path == '/api/extract-article':
            self.handle_article_extraction()
        # Handle CORS proxy requests to Ollama
        elif self.path.startswith('/api/'):
            self.proxy_to_ollama()
        else:
            super().do_POST()

    def proxy_to_ollama(self):
        try:
            # Construct Ollama URL
            ollama_url = f"http://localhost:11434{self.path}"
            
            # Handle GET requests (like /api/tags)
            if self.command == 'GET':
                req = urllib.request.Request(ollama_url)
            else:
                # Handle POST requests (like /api/generate)
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else None
                req = urllib.request.Request(
                    ollama_url,
                    data=post_data,
                    headers={'Content-Type': 'application/json'} if post_data else {}
                )
            
            # Make request to Ollama
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                
            # Send response back to client
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_data)
            print(f"✅ Proxied {self.command} {self.path} to Ollama successfully")
            
        except URLError as e:
            # Ollama not available
            print(f"❌ Cannot connect to Ollama: {e}")
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'error': f'Cannot connect to Ollama: {str(e)}'
            }).encode('utf-8')
            self.wfile.write(error_response)
            
        except Exception as e:
            # Other error
            print(f"❌ Proxy error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'error': f'Proxy error: {str(e)}'
            }).encode('utf-8')
            self.wfile.write(error_response)

    def handle_article_extraction(self):
        """Handle article content extraction requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("No request body provided")
            
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            url = request_data.get('url')
            options = request_data.get('options', {})
            
            if not url:
                raise ValueError("URL is required")
            
            print(f"🔍 Extracting article from: {url}")
            
            # Fetch the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # Extract and clean article content
            result = self.extract_article_content(html, url, options)
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response_data = json.dumps(result).encode('utf-8')
            self.wfile.write(response_data)
            
            print(f"✅ Successfully extracted article content ({result['wordCount']} words)")
            
        except Exception as e:
            print(f"❌ Article extraction error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = json.dumps({
                'success': False,
                'error': f'Article extraction failed: {str(e)}'
            }).encode('utf-8')
            self.wfile.write(error_response)

    def extract_article_content(self, html, url, options):
        """Extract and clean article content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find article content
        article = soup.find('article')
        
        if not article:
            # Fallback selectors
            fallbacks = [
                soup.select_one('main article'),
                soup.select_one('.article-content'),
                soup.select_one('.post-content'),
                soup.select_one('.entry-content'),
                soup.select_one('main'),
                soup.select_one('.content'),
                soup.select_one('#content'),
                soup.select_one('.main-content')
            ]
            
            for element in fallbacks:
                if element:
                    article = element
                    break
        
        if not article:
            raise Exception('No article content found. The page may not have an <article> tag or standard content structure.')
        
        # Clone the article content for cleaning
        content = BeautifulSoup(str(article), 'html.parser')
        
        # Apply cleaning options
        if options.get('removeLinks', True):
            # Remove <a> tags but keep their text content
            for link in content.find_all('a'):
                link.replace_with(link.get_text())
        
        if options.get('removeCallouts', True):
            # Remove div elements with class "Call-Out-Part" or similar
            callout_selectors = [
                'div.Call-Out-Part',
                'div.call-out-part',
                'div.callout',
                '.Call-Out-Part',
                '.call-out-part',
                '.callout',
                'div.article-head-container--author',
                '.article-head-container--author'
            ]
            for selector in callout_selectors:
                for element in content.select(selector):
                    element.decompose()
        
        if options.get('removeViewpoints', True):
            # Remove paragraphs that start with "Read <em>Viewpoints:</em>"
            for p in content.find_all('p'):
                p_text = p.get_text().strip()
                # Check if paragraph starts with "Read Viewpoints:"
                if p_text.startswith('Read Viewpoints:'):
                    p.decompose()
                    continue
                
                # Check for HTML structure: Read <em>Viewpoints:</em>
                em_tags = p.find_all('em')
                for em in em_tags:
                    if em.get_text().strip().lower() in ['viewpoints:', 'viewpoints']:
                        # Check if this em tag is preceded by "Read"
                        prev_text = ''
                        for prev_sibling in em.previous_siblings:
                            if hasattr(prev_sibling, 'strip'):
                                prev_text += prev_sibling.strip()
                        
                        if prev_text.lower().endswith('read') or 'read' in prev_text.lower():
                            p.decompose()
                            break
        
        if options.get('removeImages', False):
            # Remove images and figures
            for element in content.find_all(['img', 'figure', 'picture']):
                element.decompose()
        
        # Always remove scripts, styles, and other unwanted elements
        for element in content.find_all(['script', 'style', 'noscript', 'iframe']):
            element.decompose()
        
        # Get clean text and HTML
        clean_text = content.get_text()
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        
        # Get formatted HTML if preserving formatting
        clean_html = str(content) if options.get('preserveFormatting', True) else clean_text
        
        # Calculate statistics
        words = clean_text.split()
        word_count = len([w for w in words if w.strip()])
        char_count = len(clean_text)
        reading_time = max(1, round(word_count / 200))  # ~200 words per minute
        
        # Get page title
        title_element = soup.find('title')
        title = title_element.get_text().strip() if title_element else 'Unknown Title'
        
        return {
            'success': True,
            'url': url,
            'title': title,
            'cleanText': clean_text,
            'cleanHTML': clean_html,
            'wordCount': word_count,
            'charCount': char_count,
            'readingTime': reading_time,
            'extractedAt': json.dumps(None)  # Will be set by JavaScript
        }

def main():
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 8000.")
    
    with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
        print(f"🚀 Server starting on http://localhost:{port}")
        print(f"📁 Serving files from current directory")
        print(f"🔗 Open http://localhost:{port}/enhanced-persona-finder.html")
        print(f"� Open http://localhost:{port}/article-extractor.html")
        print(f"�🔧 CORS proxy available for Ollama requests")
        print(f"🗂️ Article extraction API available at /api/extract-article")
        print(f"💡 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()