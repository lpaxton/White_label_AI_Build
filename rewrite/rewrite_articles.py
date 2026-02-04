#!/usr/bin/env python3
"""
Article Brand Neutralization Script
Processes HTML articles to replace brand-specific content with generic alternatives.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class ArticleRewriter:
    def __init__(self, config_path: str):
        """Initialize with configuration file."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.brand_replacements = self.config['brand_replacements']
        self.processing_options = self.config['processing_options']
        self.results = []
    
    def find_rewrite_spans(self, html_content: str) -> List[Tuple[str, int, int]]:
        """Find all spans with data-ai-rewrite attribute."""
        pattern = r'<span\s+data-ai-rewrite="true"[^>]*>(.*?)</span>'
        matches = []
        
        for match in re.finditer(pattern, html_content, re.DOTALL):
            matches.append((match.group(1), match.start(), match.end()))
        
        return matches
    
    def check_hyperlinks(self, html_content: str) -> List[Dict]:
        """Check for hyperlinks that might reference Fidelity products but aren't marked."""
        if not self.processing_options.get('check_hyperlinks', False):
            return []
        
        unmarked_links = []
        link_pattern = r'<a\s+[^>]*>(.*?)</a>'
        product_keywords = self.processing_options.get('product_link_keywords', [])
        
        for match in re.finditer(link_pattern, html_content, re.DOTALL):
            link_text = match.group(1)
            link_start = match.start()
            
            # Check if this link is inside a data-ai-rewrite span
            # Simple check: look backwards for the nearest span tag
            preceding_text = html_content[:link_start]
            in_rewrite_span = 'data-ai-rewrite="true"' in preceding_text[-200:] if len(preceding_text) > 200 else False
            
            # Check if link text contains product keywords
            if not in_rewrite_span:
                for keyword in product_keywords:
                    if keyword.lower() in link_text.lower():
                        unmarked_links.append({
                            'link_text': link_text[:100],
                            'keyword': keyword,
                            'position': link_start,
                            'type': 'product_link'
                        })
                        break
        
        return unmarked_links
    
    def check_possessive_references(self, html_content: str) -> List[Dict]:
        """Check for possessive references that imply Fidelity authorship (our, we, us)."""
        if not self.processing_options.get('check_possessive_references', False):
            return []
        
        possessive_refs = []
        possessive_patterns = self.processing_options.get('possessive_patterns', [])
        
        # Strip out content already in data-ai-rewrite spans to avoid duplicates
        # This is a simplified approach - just flag everything and let user review
        content_to_check = html_content
        
        for pattern in possessive_patterns:
            # Compile pattern with case-insensitive flag
            regex = re.compile(pattern, re.IGNORECASE)
            
            for match in regex.finditer(content_to_check):
                matched_text = match.group(0)
                position = match.start()
                
                # Check if this is inside a data-ai-rewrite span
                preceding_text = html_content[:position]
                
                # Look for the nearest data-ai-rewrite span before this position
                last_rewrite_start = preceding_text.rfind('data-ai-rewrite="true"')
                last_span_end = preceding_text.rfind('</span>')
                
                # If we're inside a rewrite span, skip it (already being handled)
                in_rewrite_span = last_rewrite_start > last_span_end and last_rewrite_start != -1
                
                if not in_rewrite_span:
                    possessive_refs.append({
                        'text': matched_text[:100],
                        'pattern': pattern[:50],
                        'position': position,
                        'type': 'possessive_reference'
                    })
        
        return possessive_refs
    
    def replace_brand_references(self, text: str, brand: str = "Fidelity") -> str:
        """Replace brand-specific references with generic alternatives."""
        replacements = self.brand_replacements.get(brand, {})
        
        # Replace specific statements first (more specific matches)
        if 'statements' in replacements:
            for original, replacement in replacements['statements'].items():
                text = text.replace(original, replacement)
        
        # Replace product names
        if 'products' in replacements:
            for product, generic in replacements['products'].items():
                text = text.replace(product, generic)
        
        # Replace remaining brand name occurrences
        if 'company_name' in replacements:
            # Use the first generic alternative
            generic_company = replacements['company_name'][0]
            text = text.replace(brand, generic_company)
        
        # Remove trademark symbols if configured
        if self.processing_options.get('remove_trademark_symbols', True):
            # Remove trademark tags (e.g., <sup>®</sup>)
            for tag in self.processing_options.get('remove_trademark_tags', []):
                text = text.replace(tag, '')
            
            # Remove standalone trademark symbols
            for symbol in self.processing_options.get('trademark_symbols', ['®', '™', '℠']):
                text = text.replace(symbol, '')
        
        # Remove parenthetical content if configured
        if self.processing_options.get('remove_parenthetical_content', True):
            # Remove content in parentheses including the parentheses
            text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
            # Clean up multiple spaces
            text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove footnote markers if configured
        if self.processing_options.get('remove_footnotes', True):
            # Remove superscript footnote markers like <sup>1</sup>, <sup>2</sup>, etc.
            text = re.sub(r'<sup>\d+</sup>', '', text)
            # Remove standalone footnote numbers at end of sentences
            text = re.sub(r'\d+\s*$', '', text)
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def process_article(self, article_config: Dict) -> Dict:
        """Process a single article."""
        start_time = datetime.now()
        
        try:
            # Read input file
            input_path = article_config['input_file']
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Find all rewrite spans
            spans = self.find_rewrite_spans(html_content)
            spans_processed = 0
            replacements_made = []
            
            # Check for unmarked hyperlinks
            unmarked_links = self.check_hyperlinks(html_content)
            
            # Check for possessive references
            possessive_refs = self.check_possessive_references(html_content)
            
            # Process each span
            for span_text, start_pos, end_pos in reversed(spans):
                # Extract the span HTML
                span_html = html_content[start_pos:end_pos]
                
                # Replace brand references in the text content
                new_text = self.replace_brand_references(span_text)
                
                if new_text != span_text:
                    # Reconstruct the span with new text
                    new_span = span_html.replace(span_text, new_text)
                    
                    # Replace in the full HTML
                    html_content = html_content[:start_pos] + new_span + html_content[end_pos:]
                    
                    spans_processed += 1
                    replacements_made.append({
                        'original': span_text[:100],
                        'new': new_text[:100]
                    })
            
            # Save output file
            output_dir = Path(self.config['config']['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / article_config['output_file']
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate result
            result = {
                'article_id': article_config['id'],
                'article_name': article_config['name'],
                'spans_found': len(spans),
                'spans_processed': spans_processed,
                'replacements_made': len(replacements_made),
                'unmarked_product_links': len(unmarked_links),
                'possessive_references_found': len(possessive_refs),
                'status': 'success',
                'processing_time': str(datetime.now() - start_time),
                'output_file': str(output_path),
                'details': replacements_made if self.config['reporting']['include_details'] else [],
                'unmarked_links': unmarked_links if unmarked_links else [],
                'possessive_references': possessive_refs if possessive_refs else []
            }
            
            # Build warnings list
            warnings = []
            if unmarked_links:
                warnings.append(
                    f"Found {len(unmarked_links)} unmarked hyperlinks that may reference Fidelity products"
                )
            if possessive_refs:
                warnings.append(
                    f"Found {len(possessive_refs)} possessive references (our/we/us) that imply Fidelity authorship"
                )
            
            if warnings:
                result['warnings'] = warnings
            
            return result
            
        except Exception as e:
            return {
                'article_id': article_config['id'],
                'article_name': article_config['name'],
                'status': 'error',
                'error_message': str(e),
                'processing_time': str(datetime.now() - start_time)
            }
    
    def process_all_articles(self) -> List[Dict]:
        """Process all articles in the configuration."""
        print(f"Processing {len(self.config['articles'])} articles...")
        
        for article in self.config['articles']:
            print(f"\nProcessing: {article['name']}")
            result = self.process_article(article)
            self.results.append(result)
            
            if result['status'] == 'success':
                print(f"✓ Success - {result['spans_processed']} spans rewritten")
                
                if result.get('unmarked_product_links', 0) > 0:
                    print(f"⚠️  Warning - {result['unmarked_product_links']} unmarked product links found")
                    if result.get('unmarked_links'):
                        print("   Review these links:")
                        for link in result['unmarked_links'][:3]:  # Show first 3
                            print(f"   - '{link['link_text'][:50]}...'")
                
                if result.get('possessive_references_found', 0) > 0:
                    print(f"⚠️  Warning - {result['possessive_references_found']} possessive references found (our/we/us)")
                    if result.get('possessive_references'):
                        print("   Review these phrases:")
                        for ref in result['possessive_references'][:3]:  # Show first 3
                            print(f"   - '{ref['text'][:50]}...'")
            else:
                print(f"✗ Error - {result.get('error_message', 'Unknown error')}")
        
        return self.results
    
    def generate_report(self):
        """Generate summary report."""
        if not self.config['config']['generate_report']:
            return
        
        output_dir = Path(self.config['config']['output_directory'])
        report_path = output_dir / self.config['reporting']['output_file']
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(self.results),
            'successful': sum(1 for r in self.results if r['status'] == 'success'),
            'failed': sum(1 for r in self.results if r['status'] == 'error'),
            'results': self.results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Report saved to: {report_path}")


def main():
    """Main execution function."""
    config_path = 'rewrite-config.json'
    
    rewriter = ArticleRewriter(config_path)
    rewriter.process_all_articles()
    rewriter.generate_report()
    
    print("\n✓ All articles processed!")


if __name__ == '__main__':
    main()
