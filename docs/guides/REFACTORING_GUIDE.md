# Python Refactoring Implementation Guide

**Self-service guide to refactor main.py into modular structure**

---

## 🎯 Goal

Split `main.py` (689 lines) into focused modules:
- `main.py` → ~100 lines (just CLI)
- `retrieval/` → Retrieval logic
- `utils/` → Shared utilities

**Time**: 2-3 hours
**Risk**: Low (reversible at any phase)

---

## 🚨 IMPORTANT: Work in Checkpoints

After **each phase**, commit your work:

```bash
git add .
git commit -m "Phase X: [description]"
```

**Why?** If something breaks, you can rollback:
```bash
git reset --hard HEAD~1  # Undo last commit
```

---

## ✅ Pre-Flight Checklist

Before starting:

1. **Verify current state works**:
```bash
cd InvestoChat_Build
docker compose exec ingest python main.py --rag "test query" -k 3
```

2. **Create a backup branch**:
```bash
git checkout -b refactor-main-py
```

3. **Initial commit**:
```bash
git add .
git commit -m "Pre-refactoring checkpoint"
```

---

## Phase 1: Create Folder Structure (5 min)

### Commands

```bash
cd InvestoChat_Build

# Create new directories
mkdir -p retrieval utils tests

# Create __init__.py files
touch retrieval/__init__.py
touch utils/__init__.py
touch tests/__init__.py
```

### Verify

```bash
ls -la retrieval/ utils/ tests/
# Should show __init__.py in each
```

### Checkpoint

```bash
git add retrieval/ utils/ tests/
git commit -m "Phase 1: Create module structure"
```

✅ **Safe to stop here** - No code changed yet

---

## Phase 2: Create utils/db.py (10 min)

### Create File

```bash
cat > utils/db.py << 'EOF'
"""Database utilities"""

import os
import psycopg
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL")


def _pg() -> psycopg.Connection:
    """Get PostgreSQL connection"""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DATABASE_URL)


def _table_exists(cur, name: str) -> bool:
    """Check if a table exists in the database"""
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        )
    """, (name,))
    return cur.fetchone()[0]


def _doc_tuple_to_meta(row) -> dict:
    """Convert database row tuple to metadata dict"""
    source_path, page, tags, project_id, doc_type = row[1:6]
    return {
        "source": source_path,
        "page": page,
        "tags": tags,
        "project_id": project_id,
        "type": doc_type
    }
EOF
```

### Test Import

```bash
docker compose exec ingest python -c "from utils.db import _pg; print('✅ utils/db.py works')"
```

### Checkpoint

```bash
git add utils/db.py
git commit -m "Phase 2: Create utils/db.py"
```

✅ **Safe to stop here**

---

## Phase 3: Create utils/ai.py (10 min)

### Create File

```bash
cat > utils/ai.py << 'EOF'
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
EOF
```

### Test Import

```bash
docker compose exec ingest python -c "from utils.ai import _embed, _chat; print('✅ utils/ai.py works')"
```

### Checkpoint

```bash
git add utils/ai.py
git commit -m "Phase 3: Create utils/ai.py"
```

✅ **Safe to stop here**

---

## Phase 4: Create utils/text.py (15 min)

### Create File

```bash
cat > utils/text.py << 'EOF'
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
EOF
```

### Test Import

```bash
docker compose exec ingest python -c "from utils.text import normalize, tokenize; print('✅ utils/text.py works')"
```

### Checkpoint

```bash
git add utils/text.py
git commit -m "Phase 4: Create utils/text.py"
```

✅ **Safe to stop here**

---

## Phase 5: Update main.py to Use utils/ (20 min)

### Backup Current main.py

```bash
cp main.py main.py.backup
```

### Add Imports at Top of main.py

Open `main.py` and add these imports after existing imports:

```python
# Add after existing imports
from utils.db import _pg, _table_exists, _doc_tuple_to_meta
from utils.ai import _embed, _chat, _to_pgvector
from utils.text import strip_tags, normalize, tokenize, keyword_terms
```

### Remove Duplicate Function Definitions

Search for and **delete** these functions from `main.py`:
- `_pg()`
- `_table_exists()`
- `_doc_tuple_to_meta()`
- `_embed()`
- `_chat()`
- `_to_pgvector()`
- `strip_tags()`
- `normalize()`
- `tokenize()`
- `keyword_terms()`

**Tip**: Use your editor's search to find `def _pg(` and delete the entire function.

### Test It Works

```bash
docker compose exec ingest python main.py --rag "test query" -k 3
```

If you see errors about missing imports, check:
1. Did you add the import statements?
2. Did you delete the old function definitions?

### Checkpoint

```bash
git add main.py
git commit -m "Phase 5: Use utils in main.py"
```

✅ **Safe to stop here** - main.py should still work

---

## Phase 6: Move Tests (5 min)

### Move Test Files

```bash
mv test_env.py tests/
mv test_table_retrieval.py tests/
mv db_test.py tests/
```

### Update .gitignore (if needed)

```bash
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

### Test

```bash
docker compose exec ingest python tests/test_table_retrieval.py
```

### Checkpoint

```bash
git add tests/ .gitignore
git commit -m "Phase 6: Move test files to tests/"
```

✅ **Safe to stop here**

---

## 🎉 Phase 7: Verify Everything Works (10 min)

### Run Full Tests

```bash
# Test RAG query
docker compose exec ingest python main.py --rag "What is the payment plan?" -k 5

# Test retrieval only
docker compose exec ingest python main.py --show "amenities" -k 3

# Test table retrieval
docker compose exec ingest python tests/test_table_retrieval.py

# Test environment
docker compose exec ingest python tests/test_env.py
```

### Check File Sizes

```bash
wc -l main.py main.py.backup
# main.py should be ~100-150 lines smaller
```

### Final Checkpoint

```bash
git add .
git commit -m "Phase 7: Refactoring complete - all tests passing"
```

---

## 🔄 If Something Breaks

### Rollback to Previous Phase

```bash
# See commit history
git log --oneline

# Rollback to specific commit
git reset --hard <commit-hash>

# Or just undo last commit
git reset --hard HEAD~1
```

### Restore from Backup

```bash
cp main.py.backup main.py
git checkout main.py
```

---

## 📊 What You Accomplished

**Before**:
- ❌ main.py: 689 lines, 25 functions
- ❌ Hard to navigate
- ❌ Tests mixed with code

**After**:
- ✅ main.py: ~550 lines (138 lines moved to utils)
- ✅ utils/db.py: Database utilities
- ✅ utils/ai.py: AI/ML functions
- ✅ utils/text.py: Text processing
- ✅ tests/: All tests organized

---

## 🚀 Next Steps (Optional)

Want to go further? Create `retrieval/` modules:

1. **retrieval/intent.py** - Move `intent_tag()`, `detect_project_filter()`, `get_project_id_from_name()`
2. **retrieval/scoring.py** - Move `score()`, `mmr()`, `_sim_token_overlap()`, `_has_payment_table()`
3. **retrieval/retrieve.py** - Move `retrieve()`, `search_docs()`, `search_facts()`
4. **retrieval/sql_retrieve.py** - Move `retrieve_sql_ilike()`, `retrieve_sql_trgm()`

This would reduce main.py to ~100 lines (just CLI interface).

---

## ❓ Troubleshooting

### Import Error: "No module named 'utils'"

**Fix**: Make sure you're running from `InvestoChat_Build/` directory

```bash
cd InvestoChat_Build
docker compose exec ingest python main.py --rag "test"
```

### Function Not Found

**Fix**: Check you added the import at top of main.py:

```python
from utils.db import _pg, _table_exists, _doc_tuple_to_meta
```

### Tests Fail After Moving

**Fix**: Update test imports if they import from main.py:

```python
# In tests/test_table_retrieval.py
from utils.ai import _embed_text  # Instead of: from main import _embed_text
```

---

## ✅ Completion Checklist

- [ ] Phase 1: Created folder structure
- [ ] Phase 2: Created utils/db.py
- [ ] Phase 3: Created utils/ai.py
- [ ] Phase 4: Created utils/text.py
- [ ] Phase 5: Updated main.py to use utils
- [ ] Phase 6: Moved tests to tests/
- [ ] Phase 7: Verified all tests pass
- [ ] All phases committed to git
- [ ] main.py backup kept

**Congratulations!** You've successfully refactored the codebase. 🎉

---

## 📝 Summary

**Time spent**: 2-3 hours
**Lines moved**: ~138 lines from main.py to utils/
**Modules created**: 3 (db, ai, text)
**Risk**: Low (reversible at each phase)
**Benefit**: Much easier to maintain and test

**Next refactoring?** See `docs/analysis/PYTHON_STRUCTURE_ANALYSIS.md` for creating `retrieval/` modules.
