"""AI/ML utilities for embeddings and chat"""

import os
from typing import List
from functools import lru_cache
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-mini")


@lru_cache(maxsize=1000)
def _embed_single_cached(text: str) -> tuple:
    """
    Cache embeddings for individual text strings.
    Returns tuple (can be cached) instead of list.
    """
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text]
    )

    # Return as tuple (hashable for cache)
    return tuple(resp.data[0].embedding)


def _embed(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts using OpenAI (with caching for single queries)"""
    if not texts:
        return []

    # Use cache for single queries (most common case in RAG)
    if len(texts) == 1:
        cached_result = _embed_single_cached(texts[0])
        return [list(cached_result)]

    # Batch queries go directly to API (less common)
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return [d.embedding for d in resp.data]


def _chat(prompt: str, model: str = None) -> str:
    """Generate chat completion using OpenAI"""
    if model is None:
        model = CHAT_MODEL

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    return resp.choices[0].message.content


def _to_pgvector(vec: List[float]) -> str:
    """Convert embedding list to pgvector format string"""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
