# InvestoChat

A real estate brochure RAG (Retrieval-Augmented Generation) system that processes PDF brochures using OCR, stores them in PostgreSQL with pgvector, and provides a FastAPI service for querying property information via API and WhatsApp webhook.

## 🏗️ Architecture

**Data Pipeline**: PDF → OCR (DeepInfra OLMoCR) → Text Cleaning → PostgreSQL + pgvector → RAG Retrieval

**Components**:
- **OCR Processing**: `process_pdf.py` - Extracts text from PDFs using vision models
- **Text Cleaning**: `cleaner.py` - Removes brochure chrome, redacts PII
- **Ingestion**: `ingest.py` - Generates embeddings and stores in PostgreSQL
- **Table Extraction**: `extract_tables.py` - Detects, labels, and stores structured tables
- **RAG Service**: `main.py` - Multi-path retrieval with vector search + SQL fallbacks
- **API Service**: `service.py` - FastAPI endpoints for queries and WhatsApp integration

## 📁 Project Structure

```
InvestoChat/
├── CLAUDE.md                      # Claude Code instructions (DO NOT MOVE)
├── README.md                      # This file
│
├── InvestoChat_Build/             # Main application code
│   ├── process_pdf.py             # OCR processing
│   ├── cleaner.py                 # Text normalization
│   ├── ingest.py                  # Database ingestion
│   ├── main.py                    # RAG retrieval system
│   ├── service.py                 # FastAPI service
│   ├── extract_tables.py          # Table extraction pipeline
│   ├── table_processor.py         # Table processing library
│   ├── test_table_retrieval.py    # Table retrieval tests
│   ├── test_env.py                # Environment validation
│   ├── guards.py                  # Rate limiting & PII detection
│   ├── telemetry.py               # Usage logging
│   ├── setup_db.py                # Database setup utilities
│   ├── .env                       # Environment variables
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Docker image definition
│   │
│   ├── brochures/                 # PDF input directory
│   ├── outputs/                   # OCR output (JSONL)
│   ├── db/                        # PostgreSQL data (Docker volume)
│   └── frontend/                  # React frontend (if applicable)
│
├── scripts/                       # Utility scripts
│   ├── fix_projects.sh            # Fix project ID assignments
│   ├── reingest_all.sh            # Re-ingest all PDFs with deduplication
│   └── test_dedup.sh              # Test deduplication on single file
│
├── docs/                          # Documentation
│   ├── setup/                     # Setup and installation guides
│   │   ├── SETUP_COMPLETE.md
│   │   ├── FRONTEND_SETUP.md
│   │   └── INGESTION_COMPLETE.md
│   │
│   ├── guides/                    # User guides and how-tos
│   │   ├── QUICK_REFERENCE.md     # Quick command reference
│   │   ├── QUICK_COMMANDS.md      # Common operations
│   │   ├── TESTING_GUIDE.md       # Testing instructions
│   │   ├── CURATED_FACTS_GUIDE.md # Curated facts system
│   │   ├── IMAGE_SUPPORT_GUIDE.md # Image processing
│   │   ├── TABLE_EXTRACTION_GUIDE.md # Table extraction usage
│   │   └── N8N_AUTOMATION_GUIDE.md   # n8n workflow automation
│   │
│   └── analysis/                  # Analysis and enhancement docs
│       ├── ENHANCEMENT_ANALYSIS.md    # RAG enhancement analysis
│       ├── TIER1_ENHANCEMENTS.md      # Implemented enhancements
│       ├── OCR_PAGES_ANALYSIS.md      # OCR quality analysis
│       ├── RAG_TEST_RESULTS.md        # Retrieval test results
│       └── TABLE_SYSTEM_COMPLETE.md   # Table system implementation
│
├── docker-compose.yml             # Docker services configuration
└── .gitignore
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
cd InvestoChat_Build
cp .env.example .env  # Create from template
# Edit .env with your API keys:
# - DATABASE_URL
# - OPENAI_API_KEY
# - DEEPINFRA_API_KEY
```

### 2. Start Services

```bash
docker-compose up -d db adminer
```

### 3. Apply Database Schema

```bash
docker compose exec ingest python setup_db.py schema
```

### 4. Process a PDF

```bash
# OCR processing
docker compose exec ingest python process_pdf.py brochures/YourProject.pdf outputs --dpi 220

# Ingest to database
docker compose exec ingest python ingest.py \
  --project-id 1 \
  --source "YourProject.pdf" \
  --ocr-json outputs/YourProject/YourProject.jsonl

# Extract tables
docker compose exec ingest python extract_tables.py
```

### 5. Test Retrieval

```bash
docker compose exec ingest python main.py \
  --rag "What is the payment plan?" \
  --project "YourProject" \
  -k 5
```

## 📚 Documentation

### Getting Started
- [Setup Complete](docs/setup/SETUP_COMPLETE.md) - Initial setup verification
- [Ingestion Complete](docs/setup/INGESTION_COMPLETE.md) - Ingestion pipeline guide
- [Frontend Setup](docs/setup/FRONTEND_SETUP.md) - Frontend configuration

### User Guides
- [Quick Reference](docs/guides/QUICK_REFERENCE.md) - Command quick reference
- [Quick Commands](docs/guides/QUICK_COMMANDS.md) - Common operations
- [Testing Guide](docs/guides/TESTING_GUIDE.md) - How to test the system
- [Table Extraction Guide](docs/guides/TABLE_EXTRACTION_GUIDE.md) - Table processing usage
- [n8n Automation Guide](docs/guides/N8N_AUTOMATION_GUIDE.md) - Workflow automation
- [Curated Facts Guide](docs/guides/CURATED_FACTS_GUIDE.md) - High-precision answers
- [Image Support Guide](docs/guides/IMAGE_SUPPORT_GUIDE.md) - Image processing

### Technical Analysis
- [Enhancement Analysis](docs/analysis/ENHANCEMENT_ANALYSIS.md) - RAG improvement analysis
- [Tier 1 Enhancements](docs/analysis/TIER1_ENHANCEMENTS.md) - Implemented improvements
- [OCR Pages Analysis](docs/analysis/OCR_PAGES_ANALYSIS.md) - OCR quality metrics
- [RAG Test Results](docs/analysis/RAG_TEST_RESULTS.md) - Retrieval performance
- [Table System Complete](docs/analysis/TABLE_SYSTEM_COMPLETE.md) - Table extraction results

## 🛠️ Common Commands

### Database Management
```bash
# List projects
docker compose exec ingest python setup_db.py projects-list

# Add project
docker compose exec ingest python setup_db.py projects-add \
  --name "Project Name" --slug "project-slug"

# Add curated fact
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q4 2025"
```

### Query System
```bash
# RAG query with answer generation
docker compose exec ingest python main.py --rag "Your question" -k 5

# Retrieval only (no LLM)
docker compose exec ingest python main.py --show "Your query" -k 10

# Project-specific query
docker compose exec ingest python main.py \
  --rag "What amenities are available?" \
  --project "Godrej SORA"
```

### API Service
```bash
cd InvestoChat_Build
uvicorn service:app --reload --host 0.0.0.0 --port 8000

# Test endpoint
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the price?", "project_id": 1, "k": 3}'
```

## 🔧 Utility Scripts

Located in `scripts/` directory:

- **`fix_projects.sh`** - Fix duplicate documents and reassign correct project IDs
- **`reingest_all.sh`** - Re-ingest all PDFs with deduplication enabled
- **test_dedup.sh** - Test header/footer deduplication on single file

## 🧪 Testing

```bash
# Test environment variables
docker compose exec ingest python test_env.py

# Test table retrieval
docker compose exec ingest python test_table_retrieval.py

# Run RAG tests
docker compose exec ingest python main.py --rag "payment plan" -k 5
```

## 🗄️ Database Schema

**Tables**:
- `projects` - Real estate projects with metadata
- `documents` - Chunked brochure text with embeddings (vector 1536)
- `facts` - Curated key-value pairs for high-precision answers
- `ocr_pages` - Raw OCR text with pg_trgm trigram indexing
- `document_tables` - Extracted and labeled tables with embeddings

## 🔍 Retrieval Strategy

**Multi-Path Retrieval**:
1. **Facts-first path**: High-precision curated answers (similarity > 0.75)
2. **Table search**: Labeled tables for structured data (payment plans, unit specs)
3. **Document vector search**: Semantic similarity on embedded chunks
4. **SQL ILIKE/pg_trgm**: Keyword-based text search with trigrams
5. **MMR diversification**: Maximal Marginal Relevance reduces redundancy

**Intent Detection**: Automatically boosts:
- Payment queries → payment_plan tables (+8.0 score)
- Unit queries → unit_specifications tables
- Amenities queries → amenities tables

## 📊 Features

✅ **OCR Processing** - Vision model-based text extraction from PDFs
✅ **Text Cleaning** - PII redaction, header/footer deduplication, normalization
✅ **Vector Search** - pgvector cosine similarity with OpenAI embeddings
✅ **Table Extraction** - Automatic detection and labeling of structured tables
✅ **Multi-Project Support** - Filter queries by project name or ID
✅ **Curated Facts** - High-precision answers for common queries
✅ **WhatsApp Integration** - Business API webhook with rate limiting
✅ **API Service** - FastAPI with /ask, /retrieve, /whatsapp endpoints
✅ **Telemetry** - Usage logging and analytics
✅ **n8n Automation** - Workflow automation for batch processing

## 🔐 Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - For embeddings and chat completions
- `DEEPINFRA_API_KEY` - For OLMoCR vision model

Optional:
- `USE_OCR_SQL` - "1" to prefer SQL retrieval over vector search
- `CHAT_MODEL` - Default: gpt-4.1-mini
- `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` - WhatsApp API
- `API_RATE_LIMIT`, `WHATSAPP_RATE_LIMIT` - Rate limiting config

See `test_env.py` for full validation.

## 🤝 Contributing

When adding new documentation:
- **Setup guides** → `docs/setup/`
- **User guides** → `docs/guides/`
- **Analysis/enhancements** → `docs/analysis/`
- **Utility scripts** → `scripts/`
- **Claude instructions** → Keep in `CLAUDE.md` (root)

## 📝 License

[Your License Here]

## 🆘 Support

- Check `docs/guides/QUICK_REFERENCE.md` for command reference
- See `docs/analysis/` for performance analysis and improvements
- Review `CLAUDE.md` for detailed technical documentation

---

**Built with**: Python, PostgreSQL, pgvector, FastAPI, OpenAI, Docker
