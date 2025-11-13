"""Text processing utilities"""

import re
from typing import List, Set


def strip_tags(s: str) -> str:
    """Remove HTML/XML tags from string"""
    return re.sub(r'<[^>]+>', '', s)


def tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase word set"""
    text_lower = text.lower()
    # Keep alphanumeric and common separators
    tokens = re.findall(r'\w+', text_lower)
    return set(tokens)


def normalize(ctx: str) -> str:
    """
    Enhanced text normalization for RAG retrieval context.
    Handles smart quotes, currency symbols, units, and formatting.
    """
    ctx = strip_tags(ctx)

    # Smart quotes normalization
    ctx = ctx.replace('"', '"').replace('"', '"')
    ctx = ctx.replace(''', "'").replace(''', "'")

    # Currency normalization (Rs./Rs/INR → ₹, remove spaces after ₹)
    ctx = re.sub(r'\bRs\.?\s*', '₹', ctx, flags=re.IGNORECASE)
    ctx = re.sub(r'\bINR\s*', '₹', ctx, flags=re.IGNORECASE)
    ctx = re.sub(r'₹\s+', '₹', ctx)

    # Unit normalization
    ctx = re.sub(r'\b(sq\.?\s*ft\.?|sqft|sft)\b', 'sq.ft.', ctx, flags=re.IGNORECASE)
    ctx = re.sub(r'\b(sq\.?\s*m\.?|sqm)\b', 'sq.m.', ctx, flags=re.IGNORECASE)

    # BHK normalization (bhk, b.h.k, B.H.K → BHK)
    ctx = re.sub(r'\bb\.?\s*h\.?\s*k\.?\b', 'BHK', ctx, flags=re.IGNORECASE)

    # Whitespace normalization
    ctx = re.sub(r'\s+', ' ', ctx)

    return ctx.strip()


def keyword_terms(question: str) -> List[str]:
    """Extract keyword terms from question for SQL matching"""
    ql = question.lower()

    # Extract quoted phrases
    quoted = re.findall(r'"([^"]+)"', question)

    # Extract capitalized terms (likely proper nouns/project names)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question)

    # Extract domain-specific terms
    domain_terms = []
    important_keywords = [
        'payment plan', 'construction linked', 'possession linked',
        'clp', 'plp', 'rera', 'carpet area', 'super area', 'built-up area',
        'bhk', 'possession', 'booking', 'down payment', 'emi'
    ]

    for keyword in important_keywords:
        if keyword in ql:
            domain_terms.append(keyword)

    # Combine all
    terms = quoted + capitalized + domain_terms

    # Add individual words if no special terms found
    if not terms:
        words = re.findall(r'\b\w{4,}\b', ql)  # Words 4+ chars
        terms = words[:5]  # Limit to 5 words

    return terms
