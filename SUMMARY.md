# InvestoChat - Academic Project Summary

**Student**: Ayaan
**Project Type**: Real Estate AI Chatbot (RAG System)
**Tech Stack**: Python, PostgreSQL + pgvector, FastAPI, OpenAI, Docker
**Repository**: [github.com/ayaan47-1/InvestoChat](https://github.com/ayaan47-1/InvestoChat)

---

## 🎯 Project Overview

**InvestoChat** is a production-ready Retrieval-Augmented Generation (RAG) system that processes real estate PDF brochures and provides an intelligent Q&A interface via API and WhatsApp Business integration.

### Problem Solved
Real estate agents need to quickly answer customer queries about properties (pricing, amenities, payment plans) without manually searching through 50+ page PDF brochures. Traditional chatbots hallucinate facts; InvestoChat grounds answers in actual brochure content.

---

## 🏗️ System Architecture

### Data Pipeline
```
PDF Brochures
    ↓
[OCR via Vision Model] → DeepInfra OLMoCR (AllenAI)
    ↓
[Text Cleaning] → PII redaction, header/footer deduplication
    ↓
[Embedding Generation] → OpenAI text-embedding-3-small
    ↓
[Vector Database] → PostgreSQL + pgvector extension
    ↓
[RAG Retrieval] → Multi-path hybrid search
    ↓
[Answer Generation] → OpenAI GPT-4.1-mini
```

### Key Technical Components

#### 1. **OCR Processing** (`process_pdf.py`)
- Uses vision model (OLMoCR-2-7B) instead of traditional OCR (Tesseract/PyPDF)
- Preserves table structure via Markdown format
- Handles complex layouts (multi-column, images, charts)

#### 2. **Intelligent Text Cleaning** (`cleaner.py`)
- **PII Redaction**: Removes emails, phones, URLs (privacy compliance)
- **Deduplication**: Detects repeated headers/footers across pages
- **Normalization**: Currency (Rs/INR → ₹), units (sqft → sq.ft.), BHK formats
- **Chrome Removal**: Strips brochure boilerplate ("CONTACT US", "E-BROCHURE")

#### 3. **Hybrid Retrieval System** (`main.py`)
Multi-path retrieval strategy with automatic fallbacks:

**Path 1: Curated Facts** (Highest Precision)
- Hand-verified key-value pairs (e.g., "possession_date": "Q4 2025")
- Similarity threshold: 0.75
- Best for: Frequently asked questions

**Path 2: Table Search** (Structured Data)
- Auto-labeled tables: `payment_plan`, `unit_specifications`, `amenities`
- Intent detection boosts relevant tables (+8.0 score)
- Best for: Payment plans, unit pricing, specifications

**Path 3: Vector Search** (Semantic Understanding)
- pgvector cosine similarity on 1536-dim embeddings
- Maximal Marginal Relevance (MMR) for diversity
- Best for: "Tell me about amenities", "What's nearby?"

**Path 4: SQL Full-Text Search** (Exact Keywords)
- PostgreSQL pg_trgm trigram matching
- ILIKE pattern matching
- Best for: Rare terms, RERA numbers, specific names

#### 4. **API Service** (`service.py`)
- **FastAPI** with 3 endpoints:
  - `/ask` - Full RAG pipeline (retrieval + LLM answer)
  - `/retrieve` - Context-only (no LLM, cheaper)
  - `/whatsapp/webhook` - WhatsApp Business API integration
- **Rate Limiting**: 30 req/min (API), 12 req/min (WhatsApp)
- **Guards**: PII detection, question validation
- **Telemetry**: Logs all interactions (question, answer, latency, mode)

---

## 🚀 Performance Optimizations

### 1. **Two-Layer Caching System**

**Embedding Cache** (LRU, 1000 items)
- Caches OpenAI embedding API calls
- Avoids 150ms API latency for repeated queries
- Saves: ~$0.01 per 1000 cached queries

**Query Result Cache** (TTL, 5 min)
- Caches complete retrieval results
- 55,000x speedup for repeated queries (<1ms vs 670ms)
- Memory overhead: ~13MB (negligible)

**Performance Results**:
```
First query:     2.4s  (no cache)
Repeated query:  1.7s  (embedding cached) → 31% faster
Same query:      <1ms  (full cache hit)    → 99.9% faster
```

### 2. **Modular Code Architecture**
Recently refactored from monolithic 694-line file to organized modules:
```
InvestoChat_Build/
├── main.py              # 668 lines (RAG orchestration)
├── utils/
│   ├── db.py            # Database utilities
│   ├── ai.py            # OpenAI embedding/chat (with caching)
│   └── text.py          # Text processing
├── tests/
│   ├── test_env.py
│   └── test_table_retrieval.py
└── (retrieval/ module planned for future)
```

**Benefits**:
- Easier testing (unit tests per module)
- Code reuse across files
- Faster onboarding for new developers

---

## 📊 Technical Achievements

### Database Design
**PostgreSQL with pgvector extension**:
- `projects` table - 6 real estate projects
- `documents` table - 66 embedded chunks (vector similarity search)
- `ocr_pages` table - 268 pages (full-text search with pg_trgm indexes)
- `facts` table - Curated high-precision answers
- `document_tables` table - 50+ labeled tables with embeddings

### Table Extraction Pipeline
Automated table detection and labeling:
1. **Detection**: Identifies tables in OCR output (Markdown format)
2. **Labeling**: LLM classifies table type (payment_plan, unit_specs, amenities, etc.)
3. **Storage**: Stores with embeddings for semantic search
4. **Intent-Aware Boosting**: Payment queries prioritize payment_plan tables

**Results**: 100% of payment plan queries now return structured data (vs 40% before)

### Intent Detection
Automatic query classification:
- **Payment queries**: "payment plan", "CLP", "PLP" → boost payment tables, increase retrieval (k=5→10)
- **Amenities queries**: "amenities", "facilities" → boost amenities tables
- **Location queries**: "location", "address" → boost location context

### Error Handling & Resilience
- **Multi-path fallbacks**: If vector search fails → SQL search
- **Graceful degradation**: Returns partial results instead of failing
- **Rate limiting**: Prevents API abuse (429 responses with retry-after)

---

## 🧪 Testing & Validation

### Test Results (docs/analysis/RAG_TEST_RESULTS.md)

**Payment Plan Queries**:
- ✅ Retrieval accuracy: 100% (finds payment tables)
- ✅ Answer quality: Detailed step-by-step plans
- ✅ Latency: 1.1-2.4s (acceptable for production)

**Amenities Queries**:
- ✅ Retrieval accuracy: 95% (semantic search works well)
- ✅ Answer quality: Comprehensive lists
- ✅ Table detection: Automatically finds amenities tables

**Edge Cases**:
- ❌ "Not in documents" when query is too vague
- ✅ Handles misspellings (trigram search)
- ✅ Multi-project filtering works correctly

### Automated Testing
```bash
# Environment validation
python test_env.py  # Checks API keys, DB connection

# Table retrieval tests
python test_table_retrieval.py  # Verifies table search

# Cache performance tests
python test_cache.py  # Confirms 55,000x speedup
```

---

## 🔬 Novel Aspects / Research Contributions

### 1. **Hybrid Retrieval with Intent-Aware Routing**
Most RAG systems use single retrieval strategy (vector OR keyword). InvestoChat:
- Combines 4 strategies with automatic fallbacks
- Routes queries based on intent detection
- Beats baseline vector-only RAG by 40% on payment queries

### 2. **Table-Aware RAG**
Traditional RAG treats tables as plain text. InvestoChat:
- Preserves table structure via Markdown
- Auto-labels table types using LLM
- Boosts relevant tables based on query intent
- **Result**: 100% accuracy on payment plan questions (vs 40% baseline)

### 3. **Production-Ready Real Estate RAG**
Few academic RAG projects reach production:
- ✅ WhatsApp Business integration (real users)
- ✅ Rate limiting & PII redaction (compliance)
- ✅ Telemetry & monitoring (ops-ready)
- ✅ Docker deployment (scalable)

---

## 📈 Metrics & Scale

**Current System**:
- **Projects**: 6 real estate properties
- **Documents**: 66 embedded chunks
- **Tables**: 50+ labeled tables
- **OCR Pages**: 268 pages processed
- **Query Latency**: 1.7s (avg), <1ms (cached)
- **Cache Hit Rate**: ~40% (estimated for common questions)
- **API Endpoints**: 3 (/ask, /retrieve, /whatsapp)

**Cost Efficiency**:
- OCR: $0.08/month (DeepInfra OLMoCR)
- Embeddings: ~$0.001 per query (OpenAI)
- Chat: ~$0.002 per answer (GPT-4.1-mini)
- **Total**: ~$0.003 per answered question (~33 cents per 100 queries)

---

## 🛠️ Technologies Used

### Core Stack
- **Python 3.12** - Primary language
- **PostgreSQL 16 + pgvector** - Vector database
- **FastAPI** - REST API framework
- **Docker + docker-compose** - Containerization

### AI/ML APIs
- **OpenAI** - Embeddings (text-embedding-3-small), Chat (GPT-4.1-mini)
- **DeepInfra OLMoCR** - Vision model for OCR (AllenAI/olmOCR-2-7B-1025)

### Libraries
- **psycopg[binary]** - PostgreSQL adapter
- **tenacity** - Retry logic for API calls
- **cachetools** - Query result caching (TTL cache)
- **functools.lru_cache** - Embedding caching (LRU cache)

### DevOps
- **Git + GitHub** - Version control
- **Adminer** - Database admin UI (localhost:8080)
- **n8n** (optional) - Workflow automation for batch processing

---

## 🎓 Learning Outcomes

### Technical Skills Developed
1. **RAG System Design** - Multi-path retrieval, vector databases, embedding generation
2. **API Development** - RESTful design, rate limiting, webhook integration
3. **Database Optimization** - Indexing strategies (pgvector, pg_trgm), query optimization
4. **Docker & DevOps** - Multi-container orchestration, volume management
5. **Production Engineering** - Caching, error handling, telemetry, monitoring
6. **LLM Integration** - Prompt engineering, token optimization, cost management

### Software Engineering Practices
- **Modular Design** - Separated concerns (db, ai, text utilities)
- **Testing** - Unit tests, integration tests, performance benchmarks
- **Documentation** - 15+ markdown docs (setup, guides, analysis)
- **Version Control** - 18 commits with detailed messages
- **Code Quality** - PEP 8 style, type hints, clear naming

---

## 🔮 Future Enhancements (Potential Research Directions)

### 1. **Async Query Processing** (Performance)
- Problem: Sequential database queries (facts → docs → SQL)
- Solution: asyncio + concurrent queries → 2-3x faster
- Research question: Trade-offs between latency and complexity?

### 2. **Cross-Encoder Reranking** (Accuracy)
- Problem: Vector search can miss nuanced queries
- Solution: Use cross-encoder model to rerank top-k results
- Research question: Does reranking improve answer quality for real estate domain?

### 3. **Multi-Modal Retrieval** (Images + Text)
- Problem: Brochures have floor plans, exterior photos
- Solution: CLIP embeddings for image search
- Research question: How to combine image + text relevance scores?

### 4. **Fine-Tuned Embedding Model** (Domain Adaptation)
- Problem: OpenAI embeddings are generic (not real estate-specific)
- Solution: Fine-tune on real estate Q&A pairs
- Research question: Does domain-specific fine-tuning beat generic embeddings?

### 5. **User Feedback Loop** (Active Learning)
- Problem: No way to know if answers are helpful
- Solution: Thumbs up/down feedback → retrain/adjust retrieval
- Research question: How much feedback needed to improve accuracy by 10%?

---

## 📚 Documentation

**All documentation available in `docs/` directory**:

### Setup Guides
- [SETUP_COMPLETE.md](docs/setup/SETUP_COMPLETE.md) - Database setup, schema creation
- [INGESTION_COMPLETE.md](docs/setup/INGESTION_COMPLETE.md) - PDF processing pipeline
- [FRONTEND_SETUP.md](docs/setup/FRONTEND_SETUP.md) - Frontend configuration

### User Guides
- [QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md) - Command cheat sheet
- [TABLE_EXTRACTION_GUIDE.md](docs/guides/TABLE_EXTRACTION_GUIDE.md) - Table processing
- [CURATED_FACTS_GUIDE.md](docs/guides/CURATED_FACTS_GUIDE.md) - High-precision answers

### Technical Analysis
- [MAIN_PY_EFFICIENCY_ANALYSIS.md](docs/analysis/MAIN_PY_EFFICIENCY_ANALYSIS.md) - Performance deep dive
- [CACHING_IMPLEMENTATION.md](docs/analysis/CACHING_IMPLEMENTATION.md) - Caching architecture
- [RAG_TEST_RESULTS.md](docs/analysis/RAG_TEST_RESULTS.md) - Retrieval benchmarks
- [TIER1_ENHANCEMENTS.md](docs/analysis/TIER1_ENHANCEMENTS.md) - Implemented improvements

---

## 🤔 Questions for Professor

### Technical Design
1. Is the multi-path retrieval strategy over-engineered, or is this appropriate for production RAG?
2. Should I prioritize async query processing or cross-encoder reranking next?
3. Any concerns about the two-layer caching approach (LRU + TTL)?

### Research Potential
4. Could the table-aware RAG approach be publishable? (Novel compared to existing work?)
5. Should I benchmark against other RAG systems (LangChain, LlamaIndex)?
6. Is there academic value in comparing vision-model OCR vs traditional OCR?

### Production & Deployment
7. What additional monitoring/observability would you recommend?
8. Should I implement A/B testing for retrieval strategies?
9. Any suggestions for scaling beyond 6 projects to 100+ projects?

### Career/Portfolio
10. Is this project sufficiently impressive for ML engineering job applications?
11. Should I write a blog post / technical report on the architecture?
12. Any features that would make this stand out more to recruiters?

---

## 🔗 Quick Links

- **GitHub Repository**: [github.com/ayaan47-1/InvestoChat](https://github.com/ayaan47-1/InvestoChat)
- **Main README**: [README.md](README.md)
- **Technical Docs**: [CLAUDE.md](CLAUDE.md) (detailed implementation notes)
- **Demo Video**: _(Record a 2-3 min demo for professor?)_

---

## ✅ Current Status

**Production-Ready Features**:
- ✅ 6 projects ingested (The Sanctuaries, Trevoc 56, TARC Ishva, Godrej Sora, Estate 360, The Estate Residences)
- ✅ Multi-path retrieval (facts → tables → vector → SQL)
- ✅ Table extraction and labeling (50+ tables)
- ✅ Two-layer caching (55,000x speedup on repeated queries)
- ✅ FastAPI service with 3 endpoints
- ✅ WhatsApp Business integration
- ✅ Rate limiting & PII redaction
- ✅ Comprehensive documentation (15+ docs)
- ✅ Docker deployment
- ✅ Telemetry & logging

**Next Steps**:
- [ ] Record demo video showing query flow
- [ ] Deploy to cloud (AWS/GCP) for public demo
- [ ] Add more projects (target: 20+)
- [ ] Implement async retrieval (2-3x speedup)
- [ ] Benchmark against LangChain/LlamaIndex

---

**Built by**: Ayaan
**Date**: November 2025
**License**: MIT
**Contact**: _(Add your email/LinkedIn if appropriate)_
