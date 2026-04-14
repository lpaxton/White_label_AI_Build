#!/usr/bin/env python3
"""
Chunked Persona-Based Article Finder
Process multiple JSON chunks to find more diverse article recommendations
"""

import json
import requests
import argparse
import sys
import os
import glob
from typing import List, Dict, Any
import time

class ChunkedPersonaArticleFinder:
 def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2"):
 self.ollama_url = ollama_url.rstrip('/')
 self.model = model
 
 def test_ollama_connection(self) -> bool:
 """Test if Ollama is accessible"""
 try:
 response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
 return response.status_code == 200
 except:
 return False
 
 def load_chunk_files(self, chunks_dir: str) -> List[str]:
 """Find all chunk files in a directory"""
 chunk_files = []
 
 # Look for manifest file first
 manifest_path = os.path.join(chunks_dir, "manifest.json")
 if os.path.exists(manifest_path):
 try:
 with open(manifest_path, 'r', encoding='utf-8') as f:
 manifest = json.load(f)
 chunk_files = [os.path.join(chunks_dir, f) for f in manifest['chunk_files']]
 print(f" Found manifest with {len(chunk_files)} chunks")
 return chunk_files
 except Exception as e:
 print(f" Could not read manifest: {e}")
 
 # Fallback: search for chunk files by pattern
 patterns = [
 os.path.join(chunks_dir, "chunk_*.json"),
 os.path.join(chunks_dir, "*.json")
 ]
 
 for pattern in patterns:
 files = glob.glob(pattern)
 if files:
 chunk_files = sorted([f for f in files if 'manifest' not in f])
 print(f" Found {len(chunk_files)} chunk files by pattern")
 break
 
 return chunk_files
 
 def load_articles_from_chunk(self, chunk_file: str) -> List[Dict[str, Any]]:
 """Load articles from a single chunk file"""
 try:
 with open(chunk_file, 'r', encoding='utf-8') as f:
 articles = json.load(f)
 return articles
 except Exception as e:
 print(f" Error loading chunk {chunk_file}: {e}")
 return []
 
 def analyze_chunk_with_ai(self, persona: str, articles: List[Dict], chunk_name: str, results_per_chunk: int = 10) -> List[Dict]:
 """Analyze a single chunk with AI"""
 
 if not articles:
 return []
 
 # Prepare the prompt - use all articles in chunk since chunks are smaller
 articles_text = []
 for i, article in enumerate(articles):
 article_info = f"{i + 1}. Title: \"{article.get('title', 'No title')}\"\n"
 if article.get('description'):
 article_info += f" Description: \"{article['description']}\"\n"
 article_info += f" URL: {article.get('url', 'No URL')}"
 articles_text.append(article_info)
 
 prompt = f"""You are an expert financial advisor AI. Analyze the following articles and recommend the {results_per_chunk} most relevant ones for this persona:

PERSONA: {persona}

ARTICLES TO ANALYZE:
{chr(10).join(articles_text)}

Please respond with ONLY a JSON array of the most relevant articles, ranked by relevance. Include a relevance score (1-100) and brief explanation for each. Format:

[
 {{
 "title": "Article Title",
 "url": "Article URL", 
 "description": "Article description",
 "relevance_score": 95,
 "explanation": "Why this article is relevant to the persona"
 }}
]

Return only valid JSON, no other text."""

 print(f" Analyzing {chunk_name} ({len(articles)} articles)...")
 
 try:
 response = requests.post(
 f"{self.ollama_url}/api/generate",
 json={
 "model": self.model,
 "prompt": prompt,
 "stream": False
 },
 timeout=120 # 2 minute timeout per chunk
 )
 
 if response.status_code != 200:
 raise Exception(f"AI analysis failed (HTTP {response.status_code})")
 
 data = response.json()
 ai_response = data.get('response', '').strip()
 
 # Clean and parse the JSON response
 if ai_response.startswith('```'):
 ai_response = ai_response.replace('```json\n', '').replace('```', '')
 
 recommendations = json.loads(ai_response)
 
 # Validate recommendations
 valid_recommendations = []
 for rec in recommendations:
 if rec.get('title') and rec.get('url'):
 rec['relevance_score'] = min(100, max(1, rec.get('relevance_score', 50)))
 rec['explanation'] = rec.get('explanation', 'Relevant to your financial goals')
 rec['source_chunk'] = chunk_name
 valid_recommendations.append(rec)
 
 print(f" Found {len(valid_recommendations)} relevant articles from {chunk_name}")
 return valid_recommendations
 
 except json.JSONDecodeError as e:
 print(f" Error parsing AI response for {chunk_name}: {e}")
 return []
 except Exception as e:
 print(f" AI analysis error for {chunk_name}: {e}")
 return []
 
 def merge_and_deduplicate_results(self, all_results: List[List[Dict]], max_final_results: int) -> List[Dict]:
 """Merge results from all chunks and remove duplicates"""
 
 # Flatten all results
 merged = []
 for chunk_results in all_results:
 merged.extend(chunk_results)
 
 print(f" Collected {len(merged)} total recommendations from all chunks")
 
 # Deduplicate by URL (keep highest scoring version)
 url_to_best = {}
 for rec in merged:
 url = rec.get('url', '')
 if not url:
 continue
 
 if url not in url_to_best or rec['relevance_score'] > url_to_best[url]['relevance_score']:
 url_to_best[url] = rec
 
 deduplicated = list(url_to_best.values())
 print(f" After deduplication: {len(deduplicated)} unique articles")
 
 # Sort by relevance and apply final ranking decay
 deduplicated.sort(key=lambda r: r.get('relevance_score', 0), reverse=True)
 
 # Apply gentle decay to final rankings
 final_results = []
 max_r = min(max_final_results, len(deduplicated))
 for i, rec in enumerate(deduplicated[:max_r]):
 if max_r > 1:
 multiplier = 0.4 + 0.6 * (1 - (i / (max_r - 1))) # Less aggressive decay
 else:
 multiplier = 1.0
 rec_score = int(max(1, min(100, round(rec['relevance_score'] * multiplier))))
 rec['relevance_score'] = rec_score
 final_results.append(rec)
 
 return final_results
 
 def analyze_articles_chunked(self, persona: str, chunks_dir: str, max_results: int = 50) -> List[Dict]:
 """Analyze articles across multiple chunks"""
 
 chunk_files = self.load_chunk_files(chunks_dir)
 if not chunk_files:
 raise Exception(f"No chunk files found in {chunks_dir}")
 
 print(f" Processing {len(chunk_files)} chunk files")
 
 # Calculate results per chunk (aim for more diversity)
 results_per_chunk = max(5, min(15, max_results // len(chunk_files) + 2))
 print(f" Targeting ~{results_per_chunk} results per chunk")
 
 all_results = []
 for i, chunk_file in enumerate(chunk_files):
 chunk_name = os.path.basename(chunk_file)
 articles = self.load_articles_from_chunk(chunk_file)
 
 if articles:
 chunk_results = self.analyze_chunk_with_ai(persona, articles, chunk_name, results_per_chunk)
 all_results.append(chunk_results)
 else:
 print(f" Skipping empty chunk: {chunk_name}")
 
 # Small delay between chunks to be respectful
 if i < len(chunk_files) - 1:
 time.sleep(1)
 
 if not all_results:
 return []
 
 # Merge and deduplicate results
 final_results = self.merge_and_deduplicate_results(all_results, max_results)
 
 print(f" Final result: {len(final_results)} diverse articles selected")
 return final_results
 
 def display_results(self, recommendations: List[Dict], persona: str):
 """Display the results in a formatted way"""
 print("\n" + "="*80)
 print(f" CHUNKED PERSONA-BASED ARTICLE RECOMMENDATIONS")
 print("="*80)
 print(f" Persona: {persona}")
 print(f" Found {len(recommendations)} diverse articles")
 print("="*80)
 
 for i, article in enumerate(recommendations, 1):
 print(f"\n{i}. {article['title']}")
 print(f" {article['url']}")
 if article.get('description'):
 print(f" {article['description']}")
 print(f" Why relevant: {article['explanation']}")
 print(f" Relevance Score: {article['relevance_score']}%")
 if article.get('source_chunk'):
 print(f" Source: {article['source_chunk']}")
 print("-" * 80)
 
 def save_results(self, recommendations: List[Dict], persona: str, output_file: str):
 """Save results to JSON file"""
 output_data = {
 "persona": persona,
 "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
 "total_recommendations": len(recommendations),
 "processing_method": "chunked_analysis",
 "recommendations": recommendations
 }
 
 try:
 with open(output_file, 'w', encoding='utf-8') as f:
 json.dump(output_data, f, indent=2, ensure_ascii=False)
 print(f" Results saved to: {output_file}")
 except Exception as e:
 print(f" Error saving results: {e}")

def main():
 parser = argparse.ArgumentParser(description="Find articles using chunked processing for better diversity")
 parser.add_argument("chunks_dir", help="Directory containing chunk JSON files")
 parser.add_argument("persona", help="Description of the target persona")
 parser.add_argument("--max-results", type=int, default=50, help="Maximum number of articles to return (default: 50)")
 parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL (default: http://localhost:11434)")
 parser.add_argument("--model", default="llama3.2", help="Ollama model to use (default: llama3.2)")
 parser.add_argument("--output", help="Output file path for results (optional)")
 
 args = parser.parse_args()
 
 if not os.path.exists(args.chunks_dir):
 print(f" Chunks directory not found: {args.chunks_dir}")
 sys.exit(1)
 
 # Initialize finder
 finder = ChunkedPersonaArticleFinder(args.ollama_url, args.model)
 
 # Test Ollama connection
 print(f" Testing connection to Ollama at {args.ollama_url}...")
 if not finder.test_ollama_connection():
 print(f" Cannot connect to Ollama at {args.ollama_url}")
 print(" Make sure Ollama is running and accessible")
 sys.exit(1)
 print(" Ollama connection successful")
 
 # Analyze with chunked processing
 recommendations = finder.analyze_articles_chunked(args.persona, args.chunks_dir, args.max_results)
 
 if not recommendations:
 print(" No relevant articles found. Try adjusting your persona description.")
 sys.exit(1)
 
 # Display results
 finder.display_results(recommendations, args.persona)
 
 # Save results if output file specified
 if args.output:
 finder.save_results(recommendations, args.persona, args.output)

if __name__ == "__main__":
 main()