#!/usr/bin/env python3
"""
Claude-Powered Article Brand Neutralization Module
Uses Claude AI for intelligent brand-neutral content rewriting.
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from anthropic import Anthropic


class ClaudeRewriter:
    """Article rewriter that uses Claude AI for brand neutralization."""

    DEFAULT_CONFIG = {
        "brand_replacements": {
            "Fidelity": {
                "company_name": [
                    "many major brokerages",
                    "reputable financial services firms",
                    "leading financial institutions"
                ],
                "products": {
                    "Fidelity Go\u00ae": "automated robo advisors",
                    "Fidelity Youth\u00ae": "custodial accounts for minors"
                },
                "statements": {
                    "Fidelity suggests": "Financial experts recommend",
                    "Fidelity charges": "Many major brokerages charge",
                    "Fidelity offers": "Many providers offer",
                    "with Fidelity": "with your chosen brokerage",
                    "at Fidelity": "at major brokerages"
                }
            }
        },
        "processing_options": {
            "remove_trademark_symbols": True,
            "trademark_symbols": ["\u00ae", "\u2122", "\u2120"],
            "remove_trademark_tags": ["<sup>\u00ae</sup>", "<sup>\u2122</sup>", "<sup>\u2120</sup>", "<sup>SM</sup>"],
            "remove_parenthetical_content": False,
            "remove_footnotes": True,
            "check_hyperlinks": True,
            "check_possessive_references": True,
            "product_link_keywords": [
                "Fidelity Go", "Fidelity Youth", "our tools", "our calculator"
            ],
            "possessive_patterns": [
                r"our [\w\s]{1,30}(?:tool|calculator|planner|guide|glossary)",
                "we offer", "we provide", "we suggest", "we recommend",
                "contact us", "our company", "our firm", "our website"
            ]
        }
    }

    SYSTEM_PROMPT = """You are a professional content editor specializing in brand neutralization. Your task is to rewrite brand-specific content to make it generic and suitable for white-label distribution.

CRITICAL RULES:
1. ONLY modify the text content - preserve ALL HTML structure, attributes, and tags exactly
2. Replace brand names (like "Fidelity") with generic alternatives (like "many major brokerages" or "your chosen brokerage")
3. Replace product names with generic descriptions
4. Remove trademark symbols (®, ™, ℠)
5. Keep the same tone, style, and informational content
6. DO NOT add new information or change the meaning
7. DO NOT fix grammar, spelling, or improve the writing - only neutralize brand references
8. Maintain the same sentence structure when possible

When replacing brand references:
- Company name → "many major brokerages", "reputable financial services firms", "leading financial institutions", or "your chosen brokerage" (vary based on context)
- Product names → generic descriptions of what the product does
- "Fidelity offers" → "Many providers offer"
- "at Fidelity" → "at major brokerages"
- "with Fidelity" → "with your chosen brokerage"

Return ONLY the rewritten text with no explanations or additional commentary."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the Claude Rewriter.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")

        self.client = Anthropic(api_key=self.api_key)
        self.config = config or self.DEFAULT_CONFIG
        self.brand_replacements = self.config.get('brand_replacements', self.DEFAULT_CONFIG['brand_replacements'])
        self.processing_options = self.config.get('processing_options', self.DEFAULT_CONFIG['processing_options'])
        self.results = []

    def find_rewrite_spans(self, html_content: str) -> List[Tuple[str, int, int]]:
        """Find all spans with data-ai-rewrite attribute."""
        pattern = r'<span\s+data-ai-rewrite="true"[^>]*>(.*?)</span>'
        matches = []

        for match in re.finditer(pattern, html_content, re.DOTALL):
            matches.append((match.group(1), match.start(), match.end()))

        return matches

    def check_hyperlinks(self, html_content: str) -> List[Dict]:
        """Check for hyperlinks that might reference brand products but aren't marked."""
        if not self.processing_options.get('check_hyperlinks', False):
            return []

        unmarked_links = []
        link_pattern = r'<a\s+[^>]*>(.*?)</a>'
        product_keywords = self.processing_options.get('product_link_keywords', [])

        for match in re.finditer(link_pattern, html_content, re.DOTALL):
            link_text = match.group(1)
            link_start = match.start()

            # Check if this link is inside a data-ai-rewrite span
            preceding_text = html_content[:link_start]
            in_rewrite_span = 'data-ai-rewrite="true"' in preceding_text[-200:] if len(preceding_text) > 200 else False

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
        """Check for possessive references that imply brand authorship."""
        if not self.processing_options.get('check_possessive_references', False):
            return []

        possessive_refs = []
        possessive_patterns = self.processing_options.get('possessive_patterns', [])

        for pattern in possessive_patterns:
            regex = re.compile(pattern, re.IGNORECASE)

            for match in regex.finditer(html_content):
                matched_text = match.group(0)
                position = match.start()

                # Check if inside a data-ai-rewrite span
                preceding_text = html_content[:position]
                last_rewrite_start = preceding_text.rfind('data-ai-rewrite="true"')
                last_span_end = preceding_text.rfind('</span>')
                in_rewrite_span = last_rewrite_start > last_span_end and last_rewrite_start != -1

                if not in_rewrite_span:
                    possessive_refs.append({
                        'text': matched_text[:100],
                        'pattern': pattern[:50],
                        'position': position,
                        'type': 'possessive_reference'
                    })

        return possessive_refs

    def clean_text(self, text: str) -> str:
        """Apply post-processing cleanup to rewritten text."""
        # Remove trademark symbols if configured
        if self.processing_options.get('remove_trademark_symbols', True):
            for tag in self.processing_options.get('remove_trademark_tags', []):
                text = text.replace(tag, '')
            for symbol in self.processing_options.get('trademark_symbols', ['\u00ae', '\u2122', '\u2120']):
                text = text.replace(symbol, '')

        # Remove parenthetical content if configured
        if self.processing_options.get('remove_parenthetical_content', True):
            text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

        # Remove footnote markers if configured
        if self.processing_options.get('remove_footnotes', True):
            text = re.sub(r'<sup>\d+</sup>', '', text)
            text = re.sub(r'\d+\s*$', '', text)
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    def rewrite_with_claude(self, text: str, brand: str = "Fidelity") -> str:
        """
        Use Claude to intelligently rewrite brand-specific content.

        Args:
            text: The text content to rewrite
            brand: The brand to neutralize (default: Fidelity)

        Returns:
            Rewritten text with brand references neutralized
        """
        if not text.strip():
            return text

        # Build context about brand replacements
        brand_info = self.brand_replacements.get(brand, {})
        replacement_context = f"""
Brand to neutralize: {brand}
Company name alternatives: {', '.join(brand_info.get('company_name', ['major brokerages']))}
Product replacements: {json.dumps(brand_info.get('products', {}), indent=2)}
Statement replacements: {json.dumps(brand_info.get('statements', {}), indent=2)}
"""

        user_prompt = f"""Rewrite the following text to remove all references to "{brand}" and make it brand-neutral:

{replacement_context}

Text to rewrite:
{text}

Return ONLY the rewritten text, nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=self.SYSTEM_PROMPT
            )

            rewritten = response.content[0].text.strip()
            # Apply post-processing cleanup
            rewritten = self.clean_text(rewritten)
            return rewritten

        except Exception as e:
            print(f"Claude API error: {e}")
            # Fall back to rule-based replacement
            return self.rule_based_replace(text, brand)

    def rule_based_replace(self, text: str, brand: str = "Fidelity") -> str:
        """Fallback rule-based replacement when Claude is unavailable."""
        replacements = self.brand_replacements.get(brand, {})

        # Replace specific statements first
        if 'statements' in replacements:
            for original, replacement in replacements['statements'].items():
                text = text.replace(original, replacement)

        # Replace product names
        if 'products' in replacements:
            for product, generic in replacements['products'].items():
                text = text.replace(product, generic)

        # Replace remaining brand name occurrences
        if 'company_name' in replacements:
            generic_company = replacements['company_name'][0]
            text = text.replace(brand, generic_company)

        # Apply cleanup
        text = self.clean_text(text)

        return text

    def process_html(self, html_content: str, use_ai: bool = True, brand: str = "Fidelity") -> Dict:
        """
        Process HTML content and rewrite marked spans.

        Args:
            html_content: The HTML content to process
            use_ai: Whether to use Claude AI (True) or rule-based replacement (False)
            brand: The brand to neutralize

        Returns:
            Dict with processed HTML and statistics
        """
        start_time = datetime.now()

        # Find all rewrite spans
        spans = self.find_rewrite_spans(html_content)
        spans_processed = 0
        replacements_made = []

        # Check for unmarked hyperlinks
        unmarked_links = self.check_hyperlinks(html_content)

        # Check for possessive references
        possessive_refs = self.check_possessive_references(html_content)

        # Process each span (in reverse to preserve positions)
        for span_text, start_pos, end_pos in reversed(spans):
            span_html = html_content[start_pos:end_pos]

            # Rewrite the content
            if use_ai:
                new_text = self.rewrite_with_claude(span_text, brand)
            else:
                new_text = self.rule_based_replace(span_text, brand)

            if new_text != span_text:
                # Reconstruct the span with new text
                new_span = span_html.replace(span_text, new_text)
                html_content = html_content[:start_pos] + new_span + html_content[end_pos:]

                spans_processed += 1
                replacements_made.append({
                    'original': span_text[:200],
                    'rewritten': new_text[:200]
                })

        # Build warnings list
        warnings = []
        if unmarked_links:
            warnings.append(f"Found {len(unmarked_links)} unmarked hyperlinks that may reference brand products")
        if possessive_refs:
            warnings.append(f"Found {len(possessive_refs)} possessive references (our/we/us) that may imply brand authorship")

        result = {
            'html': html_content,
            'spans_found': len(spans),
            'spans_processed': spans_processed,
            'replacements_count': len(replacements_made),
            'replacements': replacements_made,
            'unmarked_links': unmarked_links,
            'possessive_references': possessive_refs,
            'warnings': warnings,
            'processing_time': str(datetime.now() - start_time),
            'method': 'claude_ai' if use_ai else 'rule_based'
        }

        return result

    def process_url_content(self, html_content: str, use_ai: bool = True, brand: str = "Fidelity") -> Dict:
        """
        Process raw article content (not pre-marked).
        Claude will identify and rewrite brand references throughout.

        Args:
            html_content: The HTML content to process
            use_ai: Whether to use Claude AI
            brand: The brand to neutralize

        Returns:
            Dict with processed content and statistics
        """
        start_time = datetime.now()

        if not use_ai:
            return {
                'error': 'Raw content processing requires AI mode',
                'html': html_content
            }

        # For raw content, we send the whole thing to Claude
        system_prompt = """You are a professional content editor specializing in brand neutralization.
Your task is to rewrite brand-specific content to make it generic and suitable for white-label distribution.

CRITICAL RULES:
1. Preserve ALL HTML structure, attributes, tags, and formatting exactly
2. ONLY change text content that references the brand
3. Replace brand names with generic alternatives
4. Remove trademark symbols (®, ™, ℠)
5. Keep the same tone, style, and informational content
6. DO NOT add new information or change the meaning
7. DO NOT fix grammar or improve the writing

Return the complete HTML with brand references neutralized."""

        brand_info = self.brand_replacements.get(brand, {})

        user_prompt = f"""Neutralize all references to "{brand}" in this HTML content.

Brand replacement guidelines:
- Company name → use: {', '.join(brand_info.get('company_name', ['major brokerages']))}
- Product replacements: {json.dumps(brand_info.get('products', {}), indent=2)}
- Statement replacements: {json.dumps(brand_info.get('statements', {}), indent=2)}

HTML content to process:
{html_content}

Return the complete neutralized HTML:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt
            )

            processed_html = response.content[0].text.strip()

            # Count approximate replacements by comparing
            original_brand_count = html_content.lower().count(brand.lower())
            new_brand_count = processed_html.lower().count(brand.lower())

            result = {
                'html': processed_html,
                'original_brand_references': original_brand_count,
                'remaining_brand_references': new_brand_count,
                'estimated_replacements': original_brand_count - new_brand_count,
                'processing_time': str(datetime.now() - start_time),
                'method': 'claude_ai_full'
            }

            return result

        except Exception as e:
            return {
                'error': f'Claude API error: {str(e)}',
                'html': html_content,
                'processing_time': str(datetime.now() - start_time)
            }

    def update_config(self, new_config: Dict):
        """Update configuration settings."""
        if 'brand_replacements' in new_config:
            self.brand_replacements.update(new_config['brand_replacements'])
        if 'processing_options' in new_config:
            self.processing_options.update(new_config['processing_options'])
        self.config.update(new_config)


def main():
    """Demo/test function."""
    # Test with sample content
    sample_html = '''
    <div class="article">
        <h1>Getting Started with Investing</h1>
        <p>Welcome to our guide on investing.</p>
        <p><span data-ai-rewrite="true">Fidelity offers a wide range of investment options.
        With Fidelity, you can start investing with as little as $1.
        Fidelity Go® is our automated robo advisor that makes investing easy.</span></p>
        <p>Learn more about different investment types below.</p>
    </div>
    '''

    try:
        rewriter = ClaudeRewriter()
        result = rewriter.process_html(sample_html)

        print("=" * 60)
        print("CLAUDE REWRITER TEST")
        print("=" * 60)
        print(f"\nSpans found: {result['spans_found']}")
        print(f"Spans processed: {result['spans_processed']}")
        print(f"Method: {result['method']}")
        print(f"Processing time: {result['processing_time']}")
        print("\nRewritten HTML:")
        print(result['html'])

        if result['replacements']:
            print("\nReplacements made:")
            for r in result['replacements']:
                print(f"  Original: {r['original'][:80]}...")
                print(f"  Rewritten: {r['rewritten'][:80]}...")

        if result['warnings']:
            print("\nWarnings:")
            for w in result['warnings']:
                print(f"  - {w}")

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ANTHROPIC_API_KEY environment variable to test.")


if __name__ == '__main__':
    main()
