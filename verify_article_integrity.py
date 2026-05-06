#!/usr/bin/env python3
"""
Database Integrity Checker for FCAT Articles
Scans all articles and identifies mismatches between original_html and neutralized_html
by comparing extracted titles from both fields.
"""

import fcat_db
from bs4 import BeautifulSoup
import sys
from datetime import datetime

def extract_title_from_html(html):
    """Extract title from HTML using <title> or <h1> tag."""
    if not html or html == '<p>No original HTML available</p>' or html == '<p>No neutralized HTML available</p>':
        return None
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try <title> tag first
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)
        
        # Fallback to <h1>
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text(strip=True):
            return h1_tag.get_text(strip=True)
        
        return None
    except Exception as e:
        return f"Error parsing HTML: {str(e)}"

def check_article_integrity():
    """Scan all articles and report mismatches."""
    print("=" * 80)
    print("FCAT Database Article Integrity Check")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Get database connection
    fcat_db.connect()
    collection = fcat_db._get_collection()
    
    # Count total articles
    total_count = collection.count_documents({})
    print(f"Total articles in database: {total_count}")
    print()
    
    # Statistics
    scanned = 0
    mismatches = []
    missing_original = []
    missing_neutralized = []
    both_missing = []
    errors = []
    
    print("Scanning articles...")
    print("-" * 80)
    
    # Iterate through all articles
    cursor = collection.find({})
    
    for doc in cursor:
        scanned += 1
        
        # Progress indicator
        if scanned % 100 == 0:
            print(f"Scanned {scanned}/{total_count} articles...", end='\r')
        
        try:
            mongo_id = str(doc.get('_id', 'unknown'))
            ereview_id = doc.get('ereview_id', 'No eReview ID')
            
            # Get HTML content
            content = doc.get('content', {})
            original_html = content.get('original_html')
            neutralized_html = content.get('neutralized_html')
            
            # Extract titles
            original_title = extract_title_from_html(original_html)
            neutralized_title = extract_title_from_html(neutralized_html)
            
            # Categorize the result
            if not original_title and not neutralized_title:
                both_missing.append({
                    'mongo_id': mongo_id,
                    'ereview_id': ereview_id
                })
            elif not original_title:
                missing_original.append({
                    'mongo_id': mongo_id,
                    'ereview_id': ereview_id,
                    'neutralized_title': neutralized_title
                })
            elif not neutralized_title:
                missing_neutralized.append({
                    'mongo_id': mongo_id,
                    'ereview_id': ereview_id,
                    'original_title': original_title
                })
            elif original_title != neutralized_title:
                mismatches.append({
                    'mongo_id': mongo_id,
                    'ereview_id': ereview_id,
                    'original_title': original_title,
                    'neutralized_title': neutralized_title
                })
        
        except Exception as e:
            errors.append({
                'mongo_id': str(doc.get('_id', 'unknown')),
                'error': str(e)
            })
    
    print(f"\nScanned {scanned}/{total_count} articles.       ")
    print()
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total scanned:              {scanned}")
    print(f"Matching articles:          {scanned - len(mismatches) - len(missing_original) - len(missing_neutralized) - len(both_missing) - len(errors)}")
    print(f"Title mismatches:           {len(mismatches)} ⚠️")
    print(f"Missing original HTML:      {len(missing_original)}")
    print(f"Missing neutralized HTML:   {len(missing_neutralized)}")
    print(f"Both HTMLs missing:         {len(both_missing)}")
    print(f"Errors:                     {len(errors)}")
    print()
    
    # Detailed mismatch report
    if mismatches:
        print("=" * 80)
        print(f"TITLE MISMATCHES ({len(mismatches)} found)")
        print("=" * 80)
        for i, item in enumerate(mismatches, 1):
            print(f"\n{i}. MongoDB ID: {item['mongo_id']}")
            print(f"   eReview ID: {item['ereview_id']}")
            print(f"   Original:    \"{item['original_title'][:80]}\"")
            print(f"   Neutralized: \"{item['neutralized_title'][:80]}\"")
    
    # Missing original HTML
    if missing_original:
        print("\n" + "=" * 80)
        print(f"MISSING ORIGINAL HTML ({len(missing_original)} found)")
        print("=" * 80)
        for i, item in enumerate(missing_original[:10], 1):  # Show first 10
            print(f"{i}. MongoDB ID: {item['mongo_id']} | eReview: {item['ereview_id']}")
        if len(missing_original) > 10:
            print(f"... and {len(missing_original) - 10} more")
    
    # Missing neutralized HTML
    if missing_neutralized:
        print("\n" + "=" * 80)
        print(f"MISSING NEUTRALIZED HTML ({len(missing_neutralized)} found)")
        print("=" * 80)
        for i, item in enumerate(missing_neutralized[:10], 1):  # Show first 10
            print(f"{i}. MongoDB ID: {item['mongo_id']} | eReview: {item['ereview_id']}")
        if len(missing_neutralized) > 10:
            print(f"... and {len(missing_neutralized) - 10} more")
    
    # Errors
    if errors:
        print("\n" + "=" * 80)
        print(f"ERRORS ({len(errors)} found)")
        print("=" * 80)
        for i, item in enumerate(errors[:10], 1):
            print(f"{i}. MongoDB ID: {item['mongo_id']} | Error: {item['error']}")
        if len(errors) > 10:
            print(f"... and {len(errors) - 10} more")
    
    print("\n" + "=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return {
        'mismatches': mismatches,
        'missing_original': missing_original,
        'missing_neutralized': missing_neutralized,
        'both_missing': both_missing,
        'errors': errors
    }

if __name__ == "__main__":
    try:
        results = check_article_integrity()
        
        # Exit with error code if mismatches found
        if results['mismatches']:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
