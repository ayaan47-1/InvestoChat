# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InvestoChat is a production-ready real estate lead generation and qualification platform that combines:
- **AI-Powered Property Q&A**: RAG (Retrieval-Augmented Generation) system for answering investment queries from PDF brochures
- **Lead Qualification**: Automated 4-question flow to qualify HNI (High Net Worth Individual) leads
- **CRM Integration**: Airtable sync for non-technical partner management
- **WhatsApp Business**: Complete webhook integration with automatic qualification and broker handoff
- **Commission Tracking**: Deal and commission tracking with auto-calculation (Broker 2% → InvestoChat 25%)

## Architecture

### Data Pipeline Flow
1. **OCR Processing** (`process_pdf.py`): PDF → DeepInfra OLMoCR API → JSONL (per-page text extraction)
2. **Text Cleaning** (`cleaner.py`): Removes brochure chrome, redacts PII, normalizes formatting
3. **Table Extraction** (`table_processor.py`, `extract_tables.py`, `standardize_tables.py`): Extracts and classifies tables (payment plans, pricing, unit specs) for enhanced retrieval
4. **Ingestion** (`ingest.py`): JSONL → OpenAI embeddings → PostgreSQL (documents + document_tables with pgvector)
5. **Retrieval** (`main.py`): Multi-path retrieval system with vector search and SQL fallbacks
6. **Lead Qualification** (`lead_qualification.py`): 4-question flow (budget, area, timeline, unit type) with conversation state machine
7. **CRM Sync** (`airtable_crm.py`): Qualified leads synced to Airtable for partner management

### Database Schema (PostgreSQL + pgvector)

**Core RAG Tables** (schema.sql):
- **projects**: Real estate projects with metadata, slug, WhatsApp routing
- **documents**: Chunked brochure text with vector(1536) embeddings for semantic search
- **facts**: Curated key-value pairs for high-precision answers (e.g., "possession_date")
- **ocr_pages**: Raw OCR text with pg_trgm trigram indexing for SQL-based retrieval
- **document_tables**: Extracted and labeled tables (payment_plan, unit_specifications, pricing, amenities) with embeddings for enhanced table retrieval

**Lead Qualification & CRM Tables** (schema_qualification.sql):
- **lead_qualification**: Lead data with 4 qualification answers (budget, area_preference, timeline, unit_preference), qualification score (0-4), conversation state
- **conversation_history**: Complete conversation log with retrieval context for analytics
- **deals**: Closed deals with auto-calculated commissions (broker_commission_amount, investochat_commission)
- **brokers**: Broker profiles with areas of expertise, performance metrics, active status
- **lead_assignments**: History of lead assignments to brokers with status tracking

**Database Triggers**:
- Auto-calculate qualification_score when answers are updated
- Auto-mark is_qualified = TRUE when score reaches 4
- Auto-calculate deal commissions based on deal_value and commission percentages
- Auto-update updated_at timestamps

### Retrieval Strategy (main.py)
The system uses a **conditional multi-path retrieval** approach:
- **Facts-first path**: If `USE_OCR_SQL != "1"`, tries vector search on facts table first (threshold: 0.75 similarity)
- **Document vector search**: Falls back to documents table with pgvector cosine similarity
- **SQL ILIKE/pg_trgm path**: If `USE_OCR_SQL == "1"` or vector search fails, uses PostgreSQL text search with keyword extraction and trigram matching on ocr_pages table
- **MMR diversification**: All paths use Maximal Marginal Relevance to reduce redundancy in retrieved chunks

The keyword extraction logic (`keyword_terms`) prioritizes domain-specific phrases like "payment plan", "construction linked", "clp", "plp" for payment-related queries.

### API Service (service.py)
- **FastAPI** with main endpoints:
  - `/ask`: Full RAG pipeline (retrieve + LLM answer generation)
  - `/retrieve`: Context-only retrieval (no LLM)
  - `/whatsapp/webhook`: WhatsApp Business API integration with lead qualification flow
  - `/images`: Static file serving for floor plan images and brochure pages
  - `/health`: Health check endpoint
- **Lead Qualification Flow** (integrated in WhatsApp webhook):
  1. User sends first message → Store in lead_qualification table
  2. After 2nd user message → Auto-start qualification (4 questions)
  3. When all 4 answered → Mark is_qualified = TRUE, sync to Airtable
  4. User says "YES"/"CONNECT" → Trigger broker handoff, update Airtable status
- **Guards** (`guards.py`): Rate limiting (API: 30/min, WhatsApp: 12/min) and PII detection
- **Project routing**: WhatsApp phone numbers mapped to project_ids via `workspace/whatsapp_routes.json`
- **Telemetry** (`telemetry.py`): Logs all interactions (channel, user_id, question, answer, mode, latency)
- **CRM Integration** (`airtable_crm.py`): Auto-sync qualified leads, update status, log activities

## Common Commands

### Database Setup

**IMPORTANT**: Always apply both schemas before any other operations!

```bash
# Step 1: Apply main RAG schema (creates tables: projects, documents, facts, ocr_pages, document_tables)
docker compose exec ingest python setup_db.py schema

# Step 2: Apply lead qualification schema (creates tables: lead_qualification, conversation_history, deals, brokers, lead_assignments)
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /app/schema_qualification.sql

# Step 3: Verify all tables exist
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
# Should show: projects, documents, facts, ocr_pages, document_tables, lead_qualification, conversation_history, deals, brokers, lead_assignments

# Step 4: List existing projects
docker compose exec ingest python setup_db.py projects-list

# Step 5: Add a new project
docker compose exec ingest python setup_db.py projects-add \
  --name "The Sanctuaries" --slug "sanctuaries" --whatsapp "+1234567890"

# Step 6 (Optional): Add curated facts using script
bash scripts/add_common_facts.sh

# Step 7 (Optional): Manually add specific facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q4 2025" --source-page "p.12"
```

**Troubleshooting**: If you get "relation does not exist" errors, run both schema setup commands first.

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

# Access floor plan images
curl http://localhost:8000/images/Estate_360/images/Estate_360_p0001.png
```

### Lead Qualification & CRM

**Lead Qualification Flow** (automated in WhatsApp webhook):
```python
# The 4 qualification questions (asked automatically after 2nd user message):
1. Budget: "💰 What is your investment budget range?" (e.g., ₹3-5 Crore)
2. Area: "📍 Which areas are you considering?" (e.g., Gurgaon Sector 89)
3. Timeline: "📅 When are you planning to invest?" (e.g., 1-3 months)
4. Unit Type: "🏠 What unit configuration?" (e.g., 3 BHK, Penthouse)

# Auto-qualification: When all 4 answered → is_qualified = TRUE, sync to Airtable
# Broker handoff: User says "YES"/"CONNECT" → Update status, log activity
```

**Testing Lead Qualification** (without WhatsApp):
```python
from lead_qualification import (
    get_or_create_lead, get_next_question,
    process_qualification_answer, should_start_qualification
)

# Create/get lead
lead = get_or_create_lead(phone="+919876543210", name="Test User")

# Check if should start qualification
should_start = should_start_qualification(lead)  # Returns True after 2 messages

# Get next question
question = get_next_question(lead)  # Returns next unanswered question

# Process answer
updated_lead = process_qualification_answer(
    phone="+919876543210",
    answer="₹3-5 Crore",
    question_key="budget"
)
```

**Airtable CRM Setup**:
```bash
# 1. Set environment variables in .env
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id

# 2. Create Airtable base with 4 tables (see AIRTABLE_PARTNER_GUIDE.md):
#    - Qualified Leads (Phone, Name, Budget, Area, Timeline, Unit Type, Status, Score)
#    - Deals (Lead, Project, Unit Type, Deal Value, Commission, Status)
#    - Brokers (Name, Phone, Email, Areas, Performance)
#    - Activity Log (Lead, Action, Notes, Timestamp)

# 3. Test sync
from airtable_crm import sync_qualified_lead

sync_qualified_lead({
    "phone": "+919876543210",
    "name": "Test User",
    "budget": "₹3-5 Crore",
    "area_preference": "Gurgaon Sector 89",
    "timeline": "1-3 months",
    "unit_preference": "3 BHK",
    "qualification_score": 4
})
```

**Querying Lead Data**:
```bash
# Get all qualified leads
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT phone, name, budget, area_preference, is_qualified, qualification_score FROM lead_qualification WHERE is_qualified = TRUE;"

# Get conversation history for a lead
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT message_type, message_text, created_at FROM conversation_history WHERE phone = '+919876543210' ORDER BY created_at;"

# Get broker performance
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT name, total_leads_assigned, total_deals_closed, conversion_rate FROM brokers WHERE is_active = TRUE;"
```

### Evaluation & Testing

**Run RAG Evaluation Suite**:
```bash
cd InvestoChat_Build

# Run all tests
python evaluate.py

# Run specific category
python evaluate.py --category payment  # Test payment queries
python evaluate.py --category pricing  # Test pricing queries
python evaluate.py --category amenities  # Test amenities queries

# Save detailed results
python evaluate.py --save workspace/eval_results/run_$(date +%Y%m%d_%H%M%S).json --verbose

# View evaluation results over time
ls -lh workspace/eval_results/
```

**Test Query File Format** (`workspace/test_queries.json`):
```json
{
  "queries": [
    {
      "id": "payment_001",
      "query": "What is the payment plan?",
      "category": "payment",
      "project_id": 1,
      "expected_mode": "tables",
      "expected_min_score": 0.7,
      "expected_keywords": ["CLP", "milestone", "booking"]
    }
  ]
}
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

**Required** in `InvestoChat_Build/.env`:
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/investochat`)
- `OPENAI_API_KEY`: For embeddings (text-embedding-3-small) and chat completions
- `DEEPINFRA_API_KEY`: For OLMoCR vision model (process_pdf.py)

**WhatsApp Integration** (required for webhook):
- `WHATSAPP_VERIFY_TOKEN`: Webhook verification token for WhatsApp Business API
- `WHATSAPP_ACCESS_TOKEN`: WhatsApp Business API access token
- `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Business phone number ID

**Airtable CRM** (optional, for partner management):
- `AIRTABLE_API_KEY`: Airtable personal access token
- `AIRTABLE_BASE_ID`: Base ID for your Airtable workspace

**Optional Configuration**:
- `OPENAI_BASE_URL`: Custom OpenAI API endpoint (for proxies/alternatives)
- `OPENAI_CHAT_MODEL`: Default chat model (default: gpt-4.1-mini)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `USE_OCR_SQL`: "1" to prefer SQL retrieval over vector search
- `DEBUG_RAG`: "1" to print tokenized keywords and search terms
- `DEFAULT_PROJECT_ID`: Fallback project for unmapped WhatsApp numbers
- `API_RATE_LIMIT`: API rate limit per minute (default: 30)
- `WHATSAPP_RATE_LIMIT`: WhatsApp rate limit per minute (default: 12)
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds (default: 60)
- `TOP_K`: Default number of chunks to retrieve (default: 3)
- `TIMEOUT_S`: Request timeout in seconds (default: 30)

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

### Table Extraction & Processing
- **Table Detection** (`table_processor.py`): Automatically detects table types (payment_plan, unit_specifications, pricing, amenities, location, specifications)
- **Extraction** (`extract_tables.py`): Extracts tables from OCR markdown output
- **Normalization** (`standardize_tables.py`): Converts tables to consistent markdown format
- **Storage**: Tables stored in `document_tables` with embeddings for semantic search
- **Retrieval Priority**: Payment plan queries prefer `document_tables` over generic documents

**Table Types**:
- `payment_plan`: Construction/possession linked payment plans (CLP/PLP)
- `unit_specifications`: Unit sizes, configurations, areas
- `pricing`: Price lists, rate cards, cost breakdowns
- `amenities`: Amenity lists and descriptions
- `location`: Location advantages, connectivity
- `specifications`: Technical specifications
- `unknown`: Unclassified tables

### Lead Qualification System
- **Trigger**: Automatically starts after user sends 2 messages (configurable in `lead_qualification.py`)
- **4 Questions**: Budget → Area → Timeline → Unit Preference
- **Validation**: Each answer validated before storing (budget must contain numbers/crore, unit must contain BHK/penthouse)
- **Scoring**: Auto-calculated (0-4) based on answered questions
- **Qualification**: `is_qualified = TRUE` when score reaches 4
- **Conversation State**: `initial` → `qualifying` → `qualified` → `connected_to_broker`
- **Database Triggers**: Auto-update qualification_score, is_qualified, qualified_at
- **Airtable Sync**: Triggers when is_qualified changes to TRUE

### Retrieval Path Selection
- **Vector search** works best for semantic queries ("Tell me about amenities")
- **SQL ILIKE/pg_trgm** works better for exact term matching ("What is the RERA number?")
- **Table-first retrieval**: Payment plan queries search `document_tables` first for structured data
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

### Commission Model & Deal Tracking
- **Standard Commission**: Broker receives 2% of deal value
- **InvestoChat Commission**: 25% of broker commission
- **Example**: ₹5 Cr deal → ₹10L broker commission → ₹2.5L InvestoChat commission
- **Auto-calculation**: Database triggers calculate commissions on insert/update
- **Deal Lifecycle**: `qualified` → `site_visit_scheduled` → `negotiating` → `closed` / `lost`
- **Tracking**: All deals stored in `deals` table with timestamps, status, and commission amounts
- **Reporting**: Airtable provides visual dashboards for deal pipeline and revenue tracking

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

## Additional Documentation

The following documentation files provide detailed setup and usage instructions:

**Setup & Deployment**:
- **SETUP.md**: Complete setup guide for development and production
- **QUICK_START.md**: 30-minute quick start guide for Wati dashboard and lead qualification
- **PRODUCTION_READY.md**: Production deployment summary and checklist
- **docs/HNI_DEPLOYMENT_GUIDE.md**: Deployment guide for HNI lead generation targeting

**Integration Guides**:
- **WATI_SETUP_GUIDE.md**: WhatsApp integration using Wati dashboard (no coding required)
- **AIRTABLE_PARTNER_GUIDE.md**: Airtable CRM setup for non-technical partners
- **docs/WHATSAPP_SETUP.md**: WhatsApp Business API setup

**Testing & Quality**:
- **TESTING_GUIDE.md**: Testing procedures and quality assurance
- **docs/analysis/IMPROVING_RETRIEVAL_ACCURACY.md**: Analysis and recommendations for retrieval accuracy

**Project Status**:
- **SUMMARY.md**: Academic project summary for professor review
- **docs/IMPROVEMENTS_SUMMARY.md**: Summary of improvements made to the system

Refer to these files for specific workflows, troubleshooting, and partner onboarding.