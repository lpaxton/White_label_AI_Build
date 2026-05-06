"""
Find duplicate eReview IDs in the FCAT database
"""
import fcat_db
from collections import defaultdict

def find_duplicates():
    """Find all duplicate eReview IDs in the database."""
    fcat_db.connect()
    collection = fcat_db.get_collection()
    
    # Get all articles with eReview IDs
    articles = list(collection.find(
        {"ereview_id": {"$exists": True, "$ne": None}},
        {"_id": 1, "ereview_id": 1, "ingest_date": 1, "pipeline_status": 1}
    ))
    
    # Group by eReview ID
    ereview_groups = defaultdict(list)
    for article in articles:
        ereview_id = article.get('ereview_id')
        if ereview_id:
            ereview_groups[ereview_id].append(article)
    
    # Find duplicates
    duplicates = {k: v for k, v in ereview_groups.items() if len(v) > 1}
    
    print(f"\nFound {len(duplicates)} eReview IDs with duplicates")
    print(f"Total duplicate records: {sum(len(v) for v in duplicates.values())}\n")
    
    # Show details
    for ereview_id, articles_list in sorted(duplicates.items()):
        print(f"\neReview ID: {ereview_id} ({len(articles_list)} copies)")
        for idx, article in enumerate(articles_list, 1):
            print(f"  {idx}. MongoDB ID: {article['_id']}")
            print(f"     Ingest Date: {article.get('ingest_date', 'N/A')}")
            print(f"     Status: {article.get('pipeline_status', 'N/A')}")
    
    return duplicates

if __name__ == '__main__':
    find_duplicates()
