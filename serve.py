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
        # Handle CORS proxy requests to Ollama
        if self.path.startswith('/api/'):
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
        print(f"🔧 CORS proxy available for Ollama requests")
        print(f"💡 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()