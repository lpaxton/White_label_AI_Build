#!/usr/bin/env python3
"""
FCAT MongoDB Atlas Client Module
Provides connection and CRUD operations for the FCAT articles collection.
Part of the aRCHie content pipeline.
"""

import os
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
