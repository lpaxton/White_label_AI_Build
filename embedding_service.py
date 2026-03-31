#!/usr/bin/env python3
"""
Embedding Service for FCAT Pipeline
Generates text embeddings using OpenAI's text-embedding-3-small model.
Part of the aRCHie content pipeline.
"""

import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace to produce plain text."""
    from bs4 import BeautifulSoup
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_embedding(plain_text: str) -> list[float] | None:
    """
    Generate an embedding vector for the given plain text using OpenAI's API.

    Args:
        plain_text: The text to embed (should already be stripped of HTML).

    Returns:
        A list of 1536 floats, or None if embedding generation fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[embedding_service] WARNING: OPENAI_API_KEY not set — skipping embedding")
        return None

    if not plain_text or not plain_text.strip():
        print("[embedding_service] WARNING: Empty text provided — skipping embedding")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=plain_text,
        )

        vector = response.data[0].embedding
        print(f"[embedding_service] Generated embedding ({len(vector)} dimensions)")
        return vector

    except Exception as e:
        print(f"[embedding_service] ERROR generating embedding: {e}")
        return None


def build_embedding_metadata(vector: list[float] | None) -> dict:
    """
    Build the embedding subdocument for the article schema.
    Returns an empty dict if vector is None (embedding failed).
    """
    if vector is None:
        return {}

    return {
        "vector": vector,
        "model": EMBEDDING_MODEL,
        "generated_at": datetime.now(timezone.utc),
        "source_field": "content.plain_text",
    }
