"""AI/ML utilities for embeddings and chat"""

import os
from typing import List
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-mini")


def _embed(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts using OpenAI"""
    if not texts:
        return []

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
