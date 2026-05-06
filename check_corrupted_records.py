#!/usr/bin/env python3
"""
Check if corrupted records have duplicate entries in the database.
This helps determine if we can safely delete corrupted records.
"""

import fcat_db

# The 7 corrupted MongoDB IDs
CORRUPTED_IDS = [
    "69f115a8a654072a9e36500f",
    "69f11604a654072a9e365012",
    "69f1161da654072a9e365013",
    "69f1163ba654072a9e365014",
    "69f1168da654072a9e365017",
    "69f116c5a654072a9e365019",
    "69f11713a654072a9e36501c",
]

def check_duplicates():
    """Check if these eReview IDs have other records."""
    fcat_db.connect()
    collection = fcat_db._get_collection()
    
    print("=" * 80)
    print("CHECKING FOR DUPLICATE eREVIEW IDs")
    print("=" * 80)
    print()
    
    for mongo_id in CORRUPTED_IDS:
        from bson.objectid import ObjectId
        doc = collection.find_one({"_id": ObjectId(mongo_id)})
        
        if not doc:
            print(f"❌ MongoDB ID {mongo_id} not found!")
            continue
        
        ereview_id = doc.get('ereview_id', 'No eReview ID')
        
        # Find all records with this eReview ID
        all_with_ereview = list(collection.find({"ereview_id": ereview_id}))
        
        print(f"MongoDB ID: {mongo_id}")
        print(f"eReview ID: {ereview_id}")
        print(f"Total records with this eReview ID: {len(all_with_ereview)}")
        
        if len(all_with_ereview) > 1:
            print(f"  ⚠️  DUPLICATES FOUND - Other MongoDB IDs:")
            for other_doc in all_with_ereview:
                other_id = str(other_doc['_id'])
                if other_id != mongo_id:
                    print(f"      - {other_id}")
        else:
            print(f"  ℹ️  No duplicates - this is the only record")
        
        print()
    
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("If duplicates exist: Check if the other copies are valid, then delete corrupted ones")
    print("If no duplicates: You'll need to re-ingest from source or fix the HTML manually")
    print()

if __name__ == "__main__":
    check_duplicates()
