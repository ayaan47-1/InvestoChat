# RAG System Test Results

Test Date: 2025-11-11
Database: 268 pages across 6 projects (USE_OCR_SQL=1 mode)

## Projects in Database
1. Estate_360.pdf
2. Godrej_SORA.pdf
3. Project_1.pdf
4. TARC_Ishva.pdf
5. The_Sanctuaries.pdf
6. Trevoc_56.pdf

## Test Results Summary

### ✅ Successful Queries

| Query | Project | Score | Result Quality |
|-------|---------|-------|----------------|
| Payment plan | The Sanctuaries | 0.051 | **Excellent** - Detailed breakdown (EOI 5%, Allotment 25%, etc.) |
| Amenities | The Sanctuaries | 0.055 | **Good** - General amenity description |
| Location | The Sanctuaries | 0.051 | **Excellent** - Specific location (DLF Phase 5, Manesar) |
| Possession date | The Sanctuaries | 0.047 | **Good** - Within 90 days at Registry |
| Unit configurations | Trevoc 56 | 0.304 | **Excellent** - Detailed 3BHK/4BHK specs with areas |
| Amenities | TARC Ishva | 0.045 | **Fair** - General description, lacks specifics |

### ❌ Failed Queries (Not in documents)

| Query | Project | Highest Score | Reason |
|-------|---------|---------------|--------|
| RERA number | The Sanctuaries | 0.019 | No RERA info in brochure |
| Price per sqft | The Sanctuaries | 0.026 | No pricing details available |
| Unit sizes | The Sanctuaries | 0.049 | No unit configuration info |
| Payment plan | Godrej Sora | N/A | PDF only contains unit plans |
| Location | Godrej Sora | N/A | PDF only contains unit plans |
| Payment options | Estate 360 | 0.259 | Retrieved page only has title, no content |

## Key Observations

### 1. Score Distribution
- **High confidence (>0.2)**: Trevoc 56 unit configs (0.304), Estate 360 title match (0.259)
- **Medium confidence (0.05-0.1)**: Most successful queries
- **Low confidence (<0.05)**: Failed queries or irrelevant matches

### 2. Content Availability Issues
- **Godrej SORA PDF**: Contains only unit layout plans (RERA number visible on page 1)
- **The Sanctuaries**: Missing RERA, pricing, and unit size details
- **Estate 360**: Sparse text content on many pages

### 3. Retrieval Mode Performance (USE_OCR_SQL=1)
**Strengths:**
- Good at exact term matching ("payment plan", "unit configurations")
- Works well when content uses same terminology as query
- Fast retrieval with pg_trgm indexes

**Weaknesses:**
- Low similarity scores overall (mostly <0.1)
- Poor semantic understanding
- Keyword-heavy queries perform better than natural language

### 4. Project Name Filtering
**Working correctly:**
- "The Sanctuaries" → filters to The_Sanctuaries.pdf
- "Trevoc" → filters to Trevoc_56.pdf
- "TARC Ishva" → filters to TARC_Ishva.pdf
- "Godrej Sora" → filters to Godrej_SORA.pdf
- "Estate 360" → filters to Estate_360.pdf

## Recommendations

### Immediate Improvements

1. **Populate the `documents` table with embeddings**
   ```bash
   # For each project, run:
   docker compose exec ingest python ingest.py \
     --project-id <ID> \
     --source "<PDF_NAME>.pdf" \
     --ocr-json /app/outputs/<PDF_NAME>/<PDF_NAME>.jsonl
   ```
   - Vector search (USE_OCR_SQL=0) will give much better semantic understanding
   - Should significantly improve queries like "amenities", "location", etc.

2. **Add curated facts for high-value queries**
   ```bash
   # Example: Add RERA number for Godrej Sora (visible on page 1)
   docker compose exec ingest python setup_db.py facts-upsert \
     --project-id <ID> \
     --key "rera_number" \
     --value "RC/REP/HARERA/GGM/976/708/2025/79" \
     --source-page "p.1"
   ```

3. **Check OCR quality for sparse pages**
   - Estate 360 page 13 only extracted "A closer look at Estate 360"
   - May need to re-run OCR with different settings or DPI

### Query Optimization Tips

**Better queries for current SQL mode:**
- ✅ "payment plan" (not "what is the payment plan")
- ✅ "unit configuration" (not "what are the unit sizes")
- ✅ "amenities list" (not "tell me about amenities")
- ✅ Use domain terms: CLP, PLP, possession, RERA, BHK, sqft

**For vector search mode (after populating documents):**
- Natural language queries will work much better
- Semantic queries like "luxury features" will match "premium amenities"
- Context-aware retrieval will understand intent

## Sample Good Queries to Try

```bash
# Payment-related (auto-increases k and overfetch)
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --rag "CLP payment schedule" -k 5 --project "The Sanctuaries"

# Unit details (works well with Trevoc)
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --rag "4 BHK carpet area" -k 5 --project "Trevoc"

# Cross-project comparison (without project filter)
docker compose exec -e USE_OCR_SQL=1 ingest python main.py \
  --rag "Which projects have 4 BHK units?" -k 10
```

## Next Steps

1. Set up database schema and create projects
2. Run full ingestion pipeline to populate documents table
3. Test with USE_OCR_SQL=0 (vector search)
4. Compare results between SQL and vector modes
5. Add curated facts for frequently asked questions
