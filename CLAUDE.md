# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InvestoChat is a real estate brochure RAG (Retrieval-Augmented Generation) system that processes PDF brochures using OCR, stores them in PostgreSQL with pgvector, and provides a FastAPI service for querying property information via API and WhatsApp webhook.

## Architecture

### Data Pipeline Flow
1. **OCR Processing** (`process_pdf.py`): PDF → DeepInfra OLMoCR API → JSONL (per-page text extraction)
2. **Text Cleaning** (`cleaner.py`): Removes brochure chrome, redacts PII, normalizes formatting
3. **Ingestion** (`ingest.py`): JSONL → OpenAI embeddings → PostgreSQL (documents table with pgvector)
4. **Retrieval** (`main.py`): Multi-path retrieval system with vector search and SQL fallbacks

### Database Schema (PostgreSQL + pgvector)
- **projects**: Real estate projects with metadata, slug, WhatsApp routing
- **documents**: Chunked brochure text with vector(1536) embeddings for semantic search
- **facts**: Curated key-value pairs for high-precision answers (e.g., "possession_date")
- **ocr_pages**: Raw OCR text with pg_trgm trigram indexing for SQL-based retrieval

### Retrieval Strategy (main.py)
The system uses a **conditional multi-path retrieval** approach:
- **Facts-first path**: If `USE_OCR_SQL != "1"`, tries vector search on facts table first (threshold: 0.75 similarity)
- **Document vector search**: Falls back to documents table with pgvector cosine similarity
- **SQL ILIKE/pg_trgm path**: If `USE_OCR_SQL == "1"` or vector search fails, uses PostgreSQL text search with keyword extraction and trigram matching on ocr_pages table
- **MMR diversification**: All paths use Maximal Marginal Relevance to reduce redundancy in retrieved chunks

The keyword extraction logic (`keyword_terms`) prioritizes domain-specific phrases like "payment plan", "construction linked", "clp", "plp" for payment-related queries.

### API Service (service.py)
- **FastAPI** with three main endpoints:
  - `/ask`: Full RAG pipeline (retrieve + LLM answer generation)
  - `/retrieve`: Context-only retrieval (no LLM)
  - `/whatsapp/webhook`: WhatsApp Business API integration
- **Guards** (`guards.py`): Rate limiting (API: 30/min, WhatsApp: 12/min) and PII detection
- **Project routing**: WhatsApp phone numbers mapped to project_ids via `workspace/whatsapp_routes.json`
- **Telemetry** (`telemetry.py`): Logs all interactions (channel, user_id, question, answer, mode, latency)

## Common Commands

### Database Setup

**IMPORTANT**: Always apply schema first before any other operations!

```bash
# Step 1: Apply database schema (creates tables: projects, documents, facts, ocr_pages)
docker compose exec ingest python setup_db.py schema

# Step 2: List existing projects
docker compose exec ingest python setup_db.py projects-list

# Step 3: Add a new project
docker compose exec ingest python setup_db.py projects-add \
  --name "The Sanctuaries" --slug "sanctuaries" --whatsapp "+1234567890"

# Step 4 (Optional): Add curated facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q4 2025" --source-page "p.12"
```

**Troubleshooting**: If you get "relation does not exist" errors, run schema setup first.

### Docker Environment
```bash
docker-compose up -d db adminer                    # Start PostgreSQL + Adminer (localhost:8080)
docker-compose up -d ingest                        # Start ingest container (manual exec required)
docker exec -it investochat-ingest bash            # Enter container for ingestion work
```

### Environment Configuration Testing
```bash
# Validate .env configuration (checks required variables, formats, etc.)
python test_env.py                  # Run all validation checks (concise output)
python test_env.py --verbose        # Run with detailed output

# What it checks:
# - Required variables: DATABASE_URL, OPENAI_API_KEY
# - Recommended variables: DEEPINFRA_API_KEY, CHAT_MODEL, EMBEDDING_MODEL
# - Format validation: DATABASE_URL format, API key formats
# - Numeric ranges: TOP_K, TIMEOUT_S, rate limits
# - WhatsApp configuration completeness
# - Lists all optional variables when in verbose mode

# Example output (passing):
# ✓ PASSED (10 checks)
# RESULT: ALL TESTS PASSED ✓

# Example output (with issues):
# ✗ ERRORS (1):
#   - Required variable OPENAI_API_KEY is not set
# ⚠ WARNINGS (2):
#   - Recommended variable CHAT_MODEL is not set
# RESULT: FAILED ✗
```

**Note**: The test automatically loads `.env` or `.env.local` from the `InvestoChat_Build/` directory.

### OCR Processing
```bash
# Process single PDF or directory
python process_pdf.py brochures/Godrej_SORA.pdf outputs --dpi 220
python process_pdf.py brochures outputs --merge-md  # All PDFs with merged markdown

# Environment: DEEPINFRA_API_KEY, OLMOCR_MODEL (default: allenai/olmOCR-2-7B-1025)
```

### Ingestion
```bash
# Manual ingestion (from OCR JSONL)
python ingest.py --project-id 1 --source "Godrej_SORA.pdf" --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl --min-len 200

# Automated ingestion (watches brochures/ directory)
python auto_ingest.py --project-id 1               # Single project for all files
python auto_ingest.py --project-map workspace/projects.json --loop 60  # Watch mode with project mapping
```

### Testing Retrieval
```bash
# Test retrieval modes
python main.py --show "What is the price?" -k 5 --project-id 1
python main.py --rag "What are the payment plans?" --project-id 1

# Toggle retrieval mode via environment
USE_OCR_SQL=1 python main.py --rag "question"      # Force SQL path
USE_OCR_SQL=0 python main.py --rag "question"      # Force vector path

# Docker exec examples
docker compose exec -e USE_OCR_SQL=1 ingest python main.py --rag "What is the payment plan?" -k 5
docker compose exec ingest python main.py --show "payment plan" -k 10 --project "Sanctuaries"
```

### Running the API Service
```bash
cd InvestoChat_Build
uvicorn service:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "What is the possession date?", "project_id": 1, "k": 3}'
```

## Debugging "Not in the documents" Responses

When queries return "Not in the documents", troubleshoot in this order:

### 1. Verify Data Exists
```bash
# Check if ocr_pages table has data (for USE_OCR_SQL=1 path)
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT source_pdf, COUNT(*) FROM ocr_pages GROUP BY source_pdf;"

# Check documents table (for vector search path)
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT source_path, COUNT(*) FROM documents GROUP BY source_path;"

# Verify project IDs and names
docker compose exec ingest python setup_db.py projects-list
```

### 2. Test Without Project Filtering
```bash
# Remove --project flag to search all projects
docker compose exec -e USE_OCR_SQL=1 ingest python main.py --rag "payment plan" -k 10

# If this works, the project name mapping is the issue
# Check PROJECT_HINTS in main.py:22-33 matches your PDF filenames
```

### 3. Enable Debug Mode
```bash
# See extracted keywords and search terms
docker compose exec -e USE_OCR_SQL=1 -e DEBUG_RAG=1 ingest \
  python main.py --show "payment plan" -k 10 --project "Sanctuaries"

# This prints the tokenized keywords used for matching
```

### 4. Check Exact PDF Filename Match
The `--project` flag uses PROJECT_HINTS to filter by source_pdf/source_path. Common mismatches:
- Database has: `The_Sanctuaries.pdf` but query uses `"Sanctuaries"` (should work)
- Database has: `The_Sanctuaries_by_32ND.pdf` (won't match)
- Database has: `the-sanctuaries.pdf` (case-insensitive ILIKE should still match)

```bash
# Find actual filenames in database
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT DISTINCT source_pdf FROM ocr_pages WHERE source_pdf ILIKE '%sanctuar%';"
```

### 5. Try Broader Search Terms
```bash
# Use simpler, more common terms
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --rag "payment" -k 10 --project "Sanctuaries"

# Or remove project filter and increase k
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --rag "payment plan" -k 20
```

### 6. Switch Retrieval Modes
```bash
# Try vector search instead of SQL (if documents table is populated)
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "What is the payment plan for The Sanctuaries?" --project "Sanctuaries"

# Vector search is better for semantic queries, SQL better for exact terms
```

### 7. Inspect Retrieved Context
```bash
# Use --show instead of --rag to see raw retrieved chunks
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --show "payment plan" -k 10 --project "Sanctuaries"

# If chunks are returned but --rag says "not found", the LLM is filtering them out
# This means context is irrelevant to the question
```

### Common Fixes

**Problem**: Project name not matching
```bash
# Check PROJECT_HINTS dictionary (main.py:22-33)
# Add mapping if missing:
"sanctuaries": "The_Sanctuaries.pdf",
"the sanctuaries": "The_Sanctuaries.pdf",
```

**Problem**: Data not in ocr_pages table
```bash
# The ocr_pages table is populated separately from documents
# Check if you need to ingest into ocr_pages or use vector search instead
USE_OCR_SQL=0  # Switch to vector search on documents table
```

**Problem**: Keywords not matching text
```bash
# Payment plan queries auto-expand (main.py:320-322)
# But other queries might need manual keyword tuning
# Try more specific terms: "CLP", "PLP", "construction linked", "possession linked"
```

**Problem**: Chunks too small
```bash
# Increase overfetch to get more context before MMR filtering
python main.py --rag "question" -k 5  # Default overfetch is 48
# Payment queries auto-increase overfetch to 96 (main.py:321)
```

**Problem**: Very low similarity scores (< 0.1) with USE_OCR_SQL=1
```bash
# Low pg_trgm scores mean weak text matching
# Solution 1: Populate documents table and use vector search instead
docker compose exec ingest python ingest.py --project-id <ID> \
  --source "The_Sanctuaries.pdf" --ocr-json outputs/The_Sanctuaries/*.jsonl

# Then switch to vector search
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "payment plan" -k 5 --project "Sanctuaries"

# Solution 2: Check if the text actually contains "payment plan"
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT page, LEFT(text, 200) FROM ocr_pages WHERE source_pdf ILIKE '%sanctuar%' AND text ILIKE '%payment%' LIMIT 5;"
```

## Key Environment Variables

Required in `InvestoChat_Build/.env`:
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/investochat`)
- `OPENAI_API_KEY`: For embeddings (text-embedding-3-small) and chat completions
- `OPENAI_BASE_URL`: Optional custom OpenAI API endpoint
- `DEEPINFRA_API_KEY`: For OLMoCR vision model (process_pdf.py)

Optional:
- `USE_OCR_SQL`: "1" to prefer SQL retrieval over vector search
- `DEBUG_RAG`: "1" to print tokenized keywords and search terms
- `CHAT_MODEL`: Default chat model (default: gpt-4.1-mini)
- `DEFAULT_PROJECT_ID`: Fallback project for unmapped WhatsApp numbers
- `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Business API credentials
- `API_RATE_LIMIT`, `WHATSAPP_RATE_LIMIT`, `RATE_LIMIT_WINDOW`: Rate limiting config

## RAG Prompts

### Answer Generation Prompt (main.py:380-387)
```python
prompt = (
    "You are a retrieval summarizer. Use only the facts in <context>. "
    "If only partial details are present, return the partial payment steps you can verify and say 'partial'. "
    "If nothing relevant is present, reply exactly: 'Not in the documents.'"
    f"{source_hint}\n"  # Added when all chunks from same source
    f"<context>\n{ctx}\n</context>\n"
    f"Question: {q}\nAnswer:"
)
```

### OCR Extraction Prompt (process_pdf.py:53-57)
```python
PROMPT = (
    "You are an OCR engine. Task: transcribe the page image exactly. "
    "Do not add content. Preserve reading order. Use Markdown tables when the page contains tables. "
    "For lists, keep bullets. For headings, keep line breaks. Return only the transcription."
)
```

## Development Notes

### Adding a New Project
1. Add project to database: `python setup_db.py projects-add --name "New Project" --slug "new-project"`
2. Place brochures in `brochures/new-project/`
3. Run OCR: `python process_pdf.py brochures/new-project outputs`
4. Ingest: `python ingest.py --project-id <id> --source "brochure.pdf" --ocr-json outputs/...`
5. (Optional) Add WhatsApp routing: Update `workspace/whatsapp_routes.json` with `{"+phone": project_id}`
6. (Optional) Add PROJECT_HINTS mapping in main.py if using `--project` flag for queries

### Retrieval Path Selection
- **Vector search** works best for semantic queries ("Tell me about amenities")
- **SQL ILIKE/pg_trgm** works better for exact term matching ("What is the RERA number?")
- Payment plan queries automatically increase k and overfetch due to domain logic (main.py:320-322)
- Project-specific queries use `PROJECT_HINTS` dictionary (main.py:22-33) to filter source_pdf

### Text Cleaning Philosophy (cleaner.py)
- Designed for OCR output only (not for curated database fields)
- Preserves finance/legal terms: GST, PLC, IDC, EDC, Stamp duty, Registration, TDS, RERA
- Redacts PII: emails, phones, URLs → `[REDACTED]`
- Removes brochure chrome: headers, footers, "E-BROCHURE", "CONTACT", etc.
- Minimum chunk size: 200 characters (configurable via --min-len)

### MMR Parameters (main.py:158-172)
- `lambda_=0.75`: Balance between relevance (75%) and diversity (25%)
- Custom scoring considers: token overlap in text + metadata boost (source, project, section) + length normalization
- Protects against repetitive chunks from multi-page layouts

### Rate Limiting (guards.py)
- Implemented as in-memory sliding window (thread-safe with Lock)
- Returns `retry_after` seconds if limit exceeded
- Configurable per channel: API (30/min default), WhatsApp (12/min default)

## Known Issues & Fixes

### PostgreSQL "could not determine data type of parameter" Error
**Symptom**: `psycopg.errors.IndeterminateDatatype: could not determine data type of parameter $4`

**Cause**: In `retrieve_sql_ilike` and `retrieve_sql_trgm` functions (main.py), when the `tag` parameter is `None`, PostgreSQL cannot infer the data type for placeholders in the CASE expression.

**Fix**: Cast parameters to TEXT in SQL queries:
```python
# Before (causes error):
"ORDER BY (CASE WHEN %s IS NOT NULL AND tags = %s THEN 0 ELSE 1 END), s DESC"

# After (fixed):
"ORDER BY (CASE WHEN %s::TEXT IS NOT NULL AND tags = %s::TEXT THEN 0 ELSE 1 END), s DESC"
```

This issue was fixed in lines 224 and 276 of main.py.

### JSONL Format Ingestion Error
**Symptom**: `json.decoder.JSONDecodeError: Extra data: line 2 column 1 (char 233)`

**Cause**: The `process_pdf.py` script creates **JSONL format** (one JSON object per line), but the original `ingest.py` expected a single JSON object with a "pages" array (OlmOCR API format).

**Fix**: Updated `_read_olmocr_json()` function in ingest.py to auto-detect file format:
```python
def _read_olmocr_json(fp: Path) -> dict:
    """
    Read OCR JSON file. Handles two formats:
    1. JSONL (one JSON object per line) - from process_pdf.py
    2. Single JSON with pages array - from OlmOCR API
    """
    with open(fp, "r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)

        # Check if it's JSONL format
        try:
            first_obj = json.loads(first_line)
            if "pdf" in first_obj and "page" in first_obj and "text" in first_obj:
                # Convert JSONL to pages array
                pages = [json.loads(line) for line in f if line.strip()]
                return {"pages": pages}
        except:
            pass

        # Otherwise, treat as single JSON object
        f.seek(0)
        return json.load(f)
```

This fix allows ingestion to work with both `process_pdf.py` output and OlmOCR API responses.

### "Documents table missing" Error
**Symptom**: `[db] documents table missing; skipping vector search path.`

**Cause**: Database schema was not applied. The schema.sql file creates the `projects`, `documents`, `facts`, and `ocr_pages` tables.

**Fix**: Apply schema before any operations:
```bash
docker compose exec ingest python setup_db.py schema
```

After this, verify tables exist:
```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```
