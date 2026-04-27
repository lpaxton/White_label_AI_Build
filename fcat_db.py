#!/usr/bin/env python3
"""
FCAT MongoDB Atlas Client Module
Provides connection and CRUD operations for the FCAT articles collection.
Part of the aRCHie content pipeline.
"""

import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

load_dotenv()

# Module-level client (singleton pattern)
_client = None
_db = None

DATABASE_NAME = "fcat"
COLLECTION_NAME = "articles"
PROFILES_COLLECTION = "user_profiles"
ANALYTICS_COLLECTION = "profile_analytics"

VALID_STATUSES = {
    "ingested",
    "hitl_pending",
    "hitl_approved",
    "areview_pending",
    "published",
    "retired",
}


def connect():
    """
    Connect to MongoDB Atlas using MONGODB_URI environment variable.
    Returns the MongoClient instance. Reuses existing connection if available.
    """
    global _client, _db

    if _client is not None:
        return _client

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI environment variable is not set")

    print(f"[fcat_db] Connecting to MongoDB Atlas...")
    _client = MongoClient(uri, server_api=ServerApi('1'))

    # Verify connectivity
    _client.admin.command("ping")
    print("[fcat_db] Connected to MongoDB Atlas successfully")

    _db = _client[DATABASE_NAME]
    return _client


def _get_collection():
    """Get the articles collection, connecting if needed."""
    global _db
    if _db is None:
        connect()
    return _db[COLLECTION_NAME]


def save_article(article_data: dict) -> str:
    """
    Save a full article document to the articles collection.
    Returns the inserted _id as a string.
    """
    collection = _get_collection()

    now = datetime.now(timezone.utc)
    article_data.setdefault("created_at", now)
    article_data.setdefault("updated_at", now)
    article_data.setdefault("ingest_date", now)

    # Ensure stats defaults
    article_data.setdefault("stats", {
        "views": 0,
        "completions": 0,
        "actions_taken": 0,
    })

    # Ensure downstream flags defaults
    article_data.setdefault("white_label_ready", False)
    article_data.setdefault("associated_actions", [])

    result = collection.insert_one(article_data)
    print(f"[fcat_db] Article saved with _id: {result.inserted_id}")
    return str(result.inserted_id)


def update_article_status(article_id: str, status: str) -> bool:
    """
    Update the pipeline_status of an article by its _id.
    Returns True if the document was found and updated.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    collection = _get_collection()
    result = collection.update_one(
        {"_id": ObjectId(article_id)},
        {
            "$set": {
                "pipeline_status": status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    updated = result.modified_count > 0
    print(f"[fcat_db] update_article_status({article_id}, {status}) -> modified={updated}")
    return updated


def get_article_by_id(article_id: str) -> dict:
    """
    Retrieve a single article by its _id.
    Returns the document dict or None if not found.
    """
    collection = _get_collection()
    doc = collection.find_one({"_id": ObjectId(article_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def get_articles_by_status(status: str) -> list:
    """
    Retrieve all articles matching a given pipeline_status.
    Returns a list of document dicts.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    collection = _get_collection()
    cursor = collection.find({"pipeline_status": status}).sort("created_at", -1)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] get_articles_by_status({status}) -> {len(results)} articles")
    return results


def article_exists_by_url(source_url: str) -> bool:
    """
    Check if an article with the given source_url already exists (dedupe check).
    Returns True if a matching document is found.
    """
    collection = _get_collection()
    exists = collection.count_documents({"source_url": source_url}, limit=1) > 0
    print(f"[fcat_db] article_exists_by_url({source_url}) -> {exists}")
    return exists


def search_articles(query: str, limit: int = 5) -> list:
    """
    Search articles by query string.
    Attempts MongoDB $text search first (requires a text index); falls back to
    a multi-keyword regex scan of content.plain_text.
    Returns a list of document dicts (no embedding vectors — plain text + metadata only).
    """
    collection = _get_collection()
    projection = {
        "content.plain_text": 1,
        "source_url": 1,
        "origin_url": 1,
        "taxonomy": 1,
        "ereview_id": 1,
        "_id": 1,
    }

    # ── Primary: $text index search ──────────────────────────────────────────
    try:
        cursor = (
            collection
            .find({"$text": {"$search": query}}, {"score": {"$meta": "textScore"}, **projection})
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        if results:
            print(f"[fcat_db] search_articles (text index) -> {len(results)} results")
            return results
    except Exception:
        pass  # No text index configured — fall through to regex

    # ── Fallback: multi-keyword regex scan ───────────────────────────────────
    STOP_WORDS = {'what', 'is', 'are', 'the', 'how', 'does', 'do', 'can', 'a',
                  'an', 'in', 'of', 'to', 'for', 'and', 'or', 'it', 'its',
                  'this', 'that', 'with', 'from', 'be', 'was', 'has', 'have'}
    words = [w for w in re.split(r"\W+", query) if len(w) >= 2 and w.lower() not in STOP_WORDS]
    if not words:
        # fallback to all words if stop-word filtering removed everything
        words = [w for w in re.split(r"\W+", query) if len(w) >= 2]
    if not words:
        words = query.split()
    pattern = "|".join(re.escape(w) for w in words[:10])
    cursor = (
        collection
        .find({"content.plain_text": {"$regex": pattern, "$options": "i"}}, projection)
        .limit(limit)
    )
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] search_articles (regex fallback) -> {len(results)} results")
    return results


def get_all_articles_for_chat(limit: int = 50) -> list:
    """
    Fetch all articles (plain text + metadata, no vectors) for client-side
    ranking when no text/vector index is available.
    """
    collection = _get_collection()
    cursor = collection.find(
        {},
        {
            "content.plain_text": 1,
            "source_url": 1,
            "origin_url": 1,
            "taxonomy": 1,
            "ereview_id": 1,
            "_id": 1,
        }
    ).limit(limit)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] get_all_articles_for_chat -> {len(results)} articles")
    return results


def vector_search_articles(query_vector: list, limit: int = 10) -> list:
    """
    Search articles using MongoDB Atlas Vector Search (semantic similarity).
    Requires an Atlas Vector Search index named 'vector_index' on embedding.vector
    with 1536 dimensions and cosine similarity.
    Returns a list of document dicts sorted by descending similarity score.
    """
    collection = _get_collection()
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding.vector",
                "queryVector": query_vector,
                # numCandidates should be >= 10x limit for good recall
                "numCandidates": min(limit * 15, 500),
                "limit": limit,
            }
        },
        {
            "$project": {
                "content.plain_text": 1,
                "source_url": 1,
                "origin_url": 1,
                "taxonomy": 1,
                "ereview_id": 1,
                "_id": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    results = []
    for doc in collection.aggregate(pipeline):
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] vector_search_articles -> {len(results)} results")
    return results


def search_by_ereview(ereview_id: str, limit: int = 20) -> list:
    """
    Search articles by eReview ID (case-insensitive partial match).
    Returns a list of document dicts sorted by most recently ingested.
    """
    collection = _get_collection()
    projection = {
        "source_url": 1, "origin_url": 1, "ereview_id": 1,
        "pipeline_status": 1, "taxonomy": 1, "ingest_date": 1,
        "content.plain_text": 1, "_id": 1,
    }
    cursor = collection.find(
        {"ereview_id": {"$regex": re.escape(ereview_id.strip()), "$options": "i"}},
        projection,
    ).sort("ingest_date", -1).limit(limit)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] search_by_ereview({ereview_id!r}) -> {len(results)} results")
    return results


def search_by_tags(tags: list, limit: int = 20) -> list:
    """
    Search articles that contain ANY of the given tags across
    taxonomy.topics, taxonomy.categories, and taxonomy.persona_tags.
    Returns documents sorted by most recently ingested.
    """
    collection = _get_collection()
    projection = {
        "source_url": 1, "origin_url": 1, "ereview_id": 1,
        "pipeline_status": 1, "taxonomy": 1, "ingest_date": 1,
        "content.plain_text": 1, "_id": 1,
    }
    # Build case-insensitive regex patterns for each tag
    patterns = [re.compile(re.escape(t.strip()), re.IGNORECASE) for t in tags if t.strip()]
    if not patterns:
        return []
    cursor = collection.find(
        {"$or": [
            {"taxonomy.topics":       {"$in": patterns}},
            {"taxonomy.categories":   {"$in": patterns}},
            {"taxonomy.persona_tags": {"$in": patterns}},
        ]},
        projection,
    ).sort("ingest_date", -1).limit(limit)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] search_by_tags({tags}) -> {len(results)} results")
    return results


def search_by_title(title_query: str, limit: int = 20) -> list:
    """
    Search articles whose plain_text begins with (or contains) the given title
    string. Uses a case-insensitive regex on content.plain_text.
    Returns documents sorted by most recently ingested.
    """
    collection = _get_collection()
    projection = {
        "source_url": 1, "origin_url": 1, "ereview_id": 1,
        "pipeline_status": 1, "taxonomy": 1, "ingest_date": 1,
        "content.plain_text": 1, "_id": 1,
    }
    pattern = re.escape(title_query.strip())
    cursor = collection.find(
        {"content.plain_text": {"$regex": pattern, "$options": "i"}},
        projection,
    ).sort("ingest_date", -1).limit(limit)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    print(f"[fcat_db] search_by_title({title_query!r}) -> {len(results)} results")
    return results


def backfill_embeddings(batch_size: int = 50) -> dict:
    """
    Generate and store embeddings for articles that are missing them.
    Safe to call repeatedly — only processes articles without an embedding.vector.
    Returns a summary dict: {updated, failed, still_missing}.
    """
    from embedding_service import generate_embedding, build_embedding_metadata

    collection = _get_collection()

    # Find articles with no embedding vector yet
    cursor = collection.find(
        {"embedding.vector": {"$exists": False}},
        {"content.plain_text": 1, "_id": 1}
    ).limit(batch_size)

    docs = list(cursor)
    updated = 0
    failed = 0

    for doc in docs:
        plain_text = (doc.get("content") or {}).get("plain_text", "").strip()
        if not plain_text:
            failed += 1
            continue

        vector = generate_embedding(plain_text)
        if vector is None:
            failed += 1
            continue

        embedding_doc = build_embedding_metadata(vector)
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "embedding": embedding_doc,
                "updated_at": datetime.now(timezone.utc),
            }}
        )
        updated += 1

    still_missing = collection.count_documents({"embedding.vector": {"$exists": False}})
    print(f"[fcat_db] backfill_embeddings -> updated={updated}, failed={failed}, still_missing={still_missing}")
    return {"updated": updated, "failed": failed, "still_missing": still_missing}


# ============================================================
# USER PROFILES (Adaptive-Explainer)
# ============================================================

def _get_profiles_collection():
    """Get the user_profiles collection, connecting if needed."""
    global _db
    if _db is None:
        connect()
    return _db[PROFILES_COLLECTION]


def _get_analytics_collection():
    """Get the profile_analytics collection, connecting if needed."""
    global _db
    if _db is None:
        connect()
    return _db[ANALYTICS_COLLECTION]


def get_user_profile(user_id: str, session_id: str = None) -> dict | None:
    """
    Retrieve a user profile by user_id.
    If session_id is provided, prefer a profile matching both;
    otherwise return the most recently updated profile for that user.
    """
    collection = _get_profiles_collection()

    if session_id:
        doc = collection.find_one({"user_id": user_id, "session_id": session_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc

    # Fall back to most recent profile for this user
    doc = collection.find_one(
        {"user_id": user_id},
        sort=[("updated_at", -1)],
    )
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def upsert_user_profile(profile: dict) -> str:
    """
    Insert or update a user profile.
    Uses (user_id, session_id) as the compound key.
    Returns the document _id as a string.
    """
    collection = _get_profiles_collection()

    profile["updated_at"] = datetime.now(timezone.utc)

    result = collection.update_one(
        {"user_id": profile["user_id"], "session_id": profile["session_id"]},
        {"$set": profile},
        upsert=True,
    )

    doc_id = result.upserted_id or None
    if doc_id is None:
        # Document was updated, not inserted — fetch _id
        existing = collection.find_one(
            {"user_id": profile["user_id"], "session_id": profile["session_id"]},
            {"_id": 1},
        )
        doc_id = existing["_id"] if existing else None

    doc_id_str = str(doc_id) if doc_id else ""
    print(f"[fcat_db] upsert_user_profile({profile['user_id']}) -> {doc_id_str}")
    return doc_id_str


def delete_user_profile(user_id: str, session_id: str = None) -> bool:
    """
    Delete a user profile. If session_id is given, delete only that
    session's profile; otherwise delete all profiles for the user.
    """
    collection = _get_profiles_collection()

    query = {"user_id": user_id}
    if session_id:
        query["session_id"] = session_id

    result = collection.delete_many(query)
    deleted = result.deleted_count > 0
    print(f"[fcat_db] delete_user_profile({user_id}) -> deleted={result.deleted_count}")
    return deleted


def log_profile_analytics(event: dict) -> str:
    """
    Log a profiling analytics event.

    Expected event shape::

        {
            "timestamp": datetime,
            "user_id": str,
            "session_id": str,
            "event_type": str,   # "profile_update" | "calibration_applied" | "feedback_received"
            "profile_snapshot": dict,
            "query": str,
            "response_length": int,
            "jargon_count": int,
            "engagement_signal": str | None,
        }
    """
    collection = _get_analytics_collection()
    event.setdefault("timestamp", datetime.now(timezone.utc))
    result = collection.insert_one(event)
    return str(result.inserted_id)


def ensure_profile_indexes():
    """
    Create recommended indexes on the user_profiles collection.
    Safe to call repeatedly (indexes are idempotent).
    """
    collection = _get_profiles_collection()
    collection.create_index(
        [("user_id", 1), ("session_id", 1)],
        unique=True,
        name="user_session_unique",
    )
    collection.create_index("user_id", name="user_id_lookup")
    collection.create_index("updated_at", name="updated_at_sort")
    print("[fcat_db] user_profiles indexes ensured")
