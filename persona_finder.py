#!/usr/bin/env python3
"""
Persona-Based Article Finder
Find the most relevant Fidelity articles for specific user personas using AI analysis.
"""

import json
import requests
import argparse
import sys
from typing import List, Dict, Any
import time

class PersonaArticleFinder:
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
    
    def load_articles(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Load articles from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            print(f"✅ Loaded {len(articles)} articles from {json_file_path}")
            return articles
        except Exception as e:
            print(f"❌ Error loading articles: {e}")
            sys.exit(1)
    
    def analyze_articles_with_ai(self, persona: str, articles: List[Dict], max_results: int = 50) -> List[Dict]:
        """Analyze articles using AI to find best matches for persona"""
        
        # Prepare the prompt
        articles_text = []
        for i, article in enumerate(articles[:100]):  # Limit to first 100 to avoid token limits
            article_info = f"{i + 1}. Title: \"{article.get('title', 'No title')}\"\n"
            if article.get('description'):
                article_info += f"   Description: \"{article['description']}\"\n"
            article_info += f"   URL: {article.get('url', 'No URL')}"
            articles_text.append(article_info)
        
        prompt = f"""You are an expert financial advisor AI. Analyze the following articles and recommend the {max_results} most relevant ones for this persona:

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

        print("🤖 Analyzing articles with AI...")
        print(f"📊 Processing {len(articles_text)} articles for persona analysis...")
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"AI analysis failed (HTTP {response.status_code})")
            
            data = response.json()
            ai_response = data.get('response', '').strip()
            
            # Clean and parse the JSON response
            if ai_response.startswith('```'):
                ai_response = ai_response.replace('```json\n', '').replace('```', '')
            
            recommendations = json.loads(ai_response)
            
            # Validate and enhance recommendations
            valid_recommendations = []
            for rec in recommendations:
                if rec.get('title') and rec.get('url'):
                    rec['relevance_score'] = min(100, max(1, rec.get('relevance_score', 50)))
                    rec['explanation'] = rec.get('explanation', 'Relevant to your financial goals')
                    valid_recommendations.append(rec)

            # Sort by provided relevance (desc)
            valid_recommendations.sort(key=lambda r: r.get('relevance_score', 50), reverse=True)

            # Cap to requested max_results and apply a gentle rank-based decay so lower-ranked
            # items have lower relevance scores (down to ~30% of original at the bottom).
            max_r = max_results if max_results and max_results > 0 else len(valid_recommendations)
            decayed = []
            for i, rec in enumerate(valid_recommendations[:max_r]):
                if max_r > 1:
                    multiplier = 0.3 + 0.7 * (1 - (i / (max_r - 1)))
                else:
                    multiplier = 1.0
                rec_score = int(max(1, min(100, round(rec['relevance_score'] * multiplier))))
                rec['relevance_score'] = rec_score
                decayed.append(rec)

            print(f"✅ Found {len(decayed)} relevant articles (capped to {max_r})")
            return decayed
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI response: {e}")
            print(f"Raw response: {ai_response[:200]}...")
            return []
        except Exception as e:
            print(f"❌ AI analysis error: {e}")
            return []
    
    def display_results(self, recommendations: List[Dict], persona: str):
        """Display the results in a formatted way"""
        print("\n" + "="*80)
        print(f"🎯 PERSONA-BASED ARTICLE RECOMMENDATIONS")
        print("="*80)
        print(f"👤 Persona: {persona}")
        print(f"📚 Found {len(recommendations)} relevant articles")
        print("="*80)
        
        for i, article in enumerate(recommendations, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   🔗 {article['url']}")
            if article.get('description'):
                print(f"   📝 {article['description']}")
            print(f"   💡 Why relevant: {article['explanation']}")
            print(f"   📊 Relevance Score: {article['relevance_score']}%")
            print("-" * 80)
    
    def save_results(self, recommendations: List[Dict], persona: str, output_file: str):
        """Save results to JSON file"""
        output_data = {
            "persona": persona,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    parser = argparse.ArgumentParser(description="Find articles matching a specific persona using AI")
    parser.add_argument("json_file", help="Path to JSON file containing articles")
    parser.add_argument("persona", help="Description of the target persona")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of articles to return (default: 50)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL (default: http://localhost:11434)")
    parser.add_argument("--model", default="llama3.2", help="Ollama model to use (default: llama3.2)")
    parser.add_argument("--output", help="Output file path for results (optional)")
    
    args = parser.parse_args()
    
    # Initialize finder
    finder = PersonaArticleFinder(args.ollama_url, args.model)
    
    # Test Ollama connection
    print(f"🔗 Testing connection to Ollama at {args.ollama_url}...")
    if not finder.test_ollama_connection():
        print(f"❌ Cannot connect to Ollama at {args.ollama_url}")
        print("   Make sure Ollama is running and accessible")
        sys.exit(1)
    print("✅ Ollama connection successful")
    
    # Load articles
    articles = finder.load_articles(args.json_file)
    
    # Analyze with AI
    recommendations = finder.analyze_articles_with_ai(args.persona, articles, args.max_results)
    
    if not recommendations:
        print("❌ No relevant articles found. Try adjusting your persona description.")
        sys.exit(1)
    
    # Display results
    finder.display_results(recommendations, args.persona)
    
    # Save results if output file specified
    if args.output:
        finder.save_results(recommendations, args.persona, args.output)

if __name__ == "__main__":
    main()