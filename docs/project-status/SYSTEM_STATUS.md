# InvestoChat System Status

**Last Updated**: 2025-01-14

---

## Current State

### Data Coverage
- **6 Projects**: The Sanctuaries, Trevoc 56, TARC Ishva, Godrej Sora, Estate 360, The Estate Residences
- **109 Document Chunks**: Page-level embeddings for semantic search
- **268 OCR Pages**: Full-text indexed for SQL fallback
- **81 Tables**: Standardized schema (payment_plan, unit_specs, pricing, amenities)
- **6 Curated Facts**: High-precision location/possession date answers

### Retrieval Performance

| Query Type | Score Range | Status |
|------------|-------------|--------|
| Location (factual) | 0.70-0.75 | ✅ Excellent (with curated facts) |
| Amenities (semantic) | 0.35-0.58 | ⚠️ Moderate |
| Tables (structured) | 0.60-0.68 | ✅ Good |
| Payment plans | Variable | ⚠️ Depends on data availability |

### Recent Improvements (This Week)

1. **Re-ingested 3 projects** with low coverage
   - Estate 360: 0 → 34 chunks (complete coverage)
   - Godrej Sora: 1 → 7 chunks (7x increase)
   - The Estate Residences: 3 → 6 chunks (2x increase)

2. **Added curated facts** for all projects
   - Location query scores: 0.26 → 0.75 (3x improvement)

3. **Standardized table schema**
   - All projects have payment_plan, unit_specs, pricing, amenities entries
   - Placeholders for missing data ("Not found in documents")
   - Real data ranks higher (0.60-0.68) than placeholders (0.50-0.57)

---

## Architecture

**Multi-Path Retrieval**:
1. **Facts** → Curated key-value pairs (0.75 threshold)
2. **Tables** → Structured data with type classification
3. **Documents** → Vector search on text chunks
4. **OCR Pages** → SQL ILIKE/pg_trgm fallback

**Tech Stack**:
- PostgreSQL + pgvector (cosine similarity)
- OpenAI text-embedding-3-small (1536 dims)
- gpt-4.1-mini (answer generation)
- FastAPI + WhatsApp webhook

---

## Known Limitations

1. **Semantic queries** have moderate scores (0.35-0.58)
   - Marketing language vs direct questions = semantic gap
   - Solution: Better chunking, query expansion, domain fine-tuning

2. **Some projects lack structured data**
   - Estate 360, TARC Ishva: No payment plan tables in brochures
   - Solution: Placeholders provide clear "not found" messages

3. **Images not indexed**
   - Floor plans exist but not searchable
   - Solution: CLIP embeddings or image captioning

---

## Next Steps

### High Priority
- [ ] Implement paragraph-level chunking (+20-30% accuracy)
- [ ] Add query expansion (+10-15% accuracy)
- [ ] Integrate tables into main.py retrieval pipeline

### Medium Priority
- [ ] Cross-encoder reranking (+10% accuracy)
- [ ] WhatsApp integration testing
- [ ] Image retrieval for floor plans

### Future (Research)
- [ ] Fine-tune embeddings on real estate data (+20-40% accuracy)
- [ ] Upgrade to text-embedding-3-large (+5-15% accuracy)
- [ ] Async processing for <500ms latency

---

## For Discussion

### What's Working Well ✅
- Curated facts solve factual queries elegantly
- Table standardization ensures consistent API responses
- Hybrid retrieval (vector + SQL) catches most queries

### What Needs Improvement ⚠️
- Semantic query scores still moderate
- Missing data handling could be more intelligent
- No multimodal retrieval (images)

### Key Question for Professor
"Should I prioritize domain fine-tuning (20-40% gain, high effort) or cross-encoder reranking (10% gain, medium effort) next?"
