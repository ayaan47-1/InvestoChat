# OCR Pages Table Analysis

**Date**: 2025-11-11
**Total Rows**: 268
**SQL Export**: ocr_pages.sql (6,922 lines)

## Summary: ✅ Data Looks Good!

The `ocr_pages` table is properly populated with all 6 projects. The data structure is correct and ready for SQL-based retrieval (USE_OCR_SQL=1 mode).

## Data Distribution by Project

| Project | Pages | Project Name in DB | Notes |
|---------|-------|-------------------|-------|
| **Trevoc 56** | 102 | `'Trevoc 56'` | ✅ Largest PDF, good content coverage |
| **Estate 360** | 67 | `'Estate 360'` | ✅ Complete brochure |
| **The Sanctuaries** | 41 | `'The Sanctuaries'` | ✅ Payment plan on p.31 |
| **TARC Ishva** | 33 | `'Tarc Ishva'` | ✅ (Note: Capitalization) |
| **Project 1** | 16 | `'Project 1'` | ✅ Smaller brochure |
| **Godrej Sora** | 9 | `'Godrej Sora'` | ⚠️ Only unit plans, minimal text |

**Total**: 268 pages ✅

## Schema Structure

```sql
INSERT INTO "ocr_pages"
  ("id", "source_pdf", "page", "image_path", "text", "created_at", "project", "tags")
```

### Key Observations

✅ **`project` column is populated** for all rows
- This enables project filtering in SQL queries
- Format: `'Estate 360'`, `'Trevoc 56'`, `'The Sanctuaries'`, etc.

⚠️ **`tags` column is mostly NULL**
- Only 3 rows have tags populated:
  - Estate 360 p.12: `'amenities'`
  - The Sanctuaries p.?: `'location'`
  - Trevoc 56 p.?: `'payment'`
- This is not a blocker - tags are optional metadata

✅ **`source_pdf` paths are consistent**
- Format: `/app/brochures/{ProjectName}.pdf`
- No issues with path formatting

✅ **`image_path` structure is correct**
- Format: `/app/outputs/{ProjectName}/images/{ProjectName}_p{page:04d}.png`
- All images properly referenced

## Content Quality Analysis

### Good Content Examples

**The Sanctuaries p.31** (Payment Plan):
```
EOI: 5%
Allotment & ATS (within 30 days): 25%
Prior to Registry (within 60 days): 50%
Registry and Possession (within 90 days): 20%
```
✅ Rich, structured data with tables

**Estate 360 p.9** (Intergenerational living):
```
Indian culture has always been rooted in certain values —
togetherness, belonging and learning from our elders...
```
✅ Detailed descriptive content

**Trevoc 56 p.30** (Unit configs):
```
3 BHK (Type B) with carpet area of 128.68 sq. mtr. (1385 sq. ft.),
saleable area of 245.45 sq. mtr. (2642 sq. ft.)...
```
✅ Technical specifications captured accurately

### Sparse Content Examples

**Estate 360 p.13**:
```
A closer look at Estate 360
```
⚠️ Title page only - this explains why it scored 0.259 but returned "Not in documents"

**Godrej Sora p.2**:
```
UNIT PLANS
```
⚠️ Many pages are just headers - PDF contains mostly architectural drawings

## Issues Found (Minor)

### 1. ⚠️ Inconsistent Project Name Capitalization

**In `ocr_pages` table:**
- `'Tarc Ishva'` (Title case)
- `'Trevoc 56'`
- `'The Sanctuaries'`
- `'Estate 360'`
- `'Godrej Sora'`
- `'Project 1'`

**In `PROJECT_HINTS` (main.py:22-33):**
```python
"tarc ishva": "TARC_Ishva.pdf",  # lowercase in hints
"ishva": "TARC_Ishva.pdf",
```

**Impact**: Project filtering via `--project "TARC Ishva"` should still work because:
- SQL uses ILIKE (case-insensitive)
- PROJECT_HINTS has multiple variations

**Recommendation**: Ensure PROJECT_HINTS covers common variations:
```python
PROJECT_HINTS = {
    "tarc ishva": "TARC_Ishva.pdf",
    "tarc": "TARC_Ishva.pdf",
    "ishva": "TARC_Ishva.pdf",
    # Add these:
    "Tarc Ishva": "TARC_Ishva.pdf",  # Match DB capitalization
    "TARC Ishva": "TARC_Ishva.pdf",
}
```

### 2. ⚠️ Tags Column Underutilized

Only 3 rows out of 268 have tags populated. Tags could improve:
- Intent detection in `intent_tag()` function
- Priority sorting in ORDER BY clauses
- Semantic categorization

**Potential Tags:**
- `'payment'` - payment plans, pricing, CLP/PLP
- `'amenities'` - facilities, features, clubs
- `'location'` - address, connectivity, landmarks
- `'units'` - BHK configurations, sizes
- `'legal'` - RERA, approvals, disclaimers

**Not critical** - system works fine without tags, but could enhance precision.

### 3. ⚠️ Godrej Sora Limited Content

**Problem**: Godrej SORA PDF contains mostly architectural unit plans with minimal text.

**Evidence**:
- Only 9 pages total
- Pages like "UNIT PLANS", "TOWER 1", "TOWER 2"
- RERA number visible on p.1 but not extracted as searchable text

**Impact**: Queries like "payment plan for Godrej Sora" return "Not in documents"

**Solutions**:
1. **Add curated fact**:
   ```bash
   docker compose exec ingest python setup_db.py facts-upsert \
     --project-id 4 \
     --key "rera_number" \
     --value "RC/REP/HARERA/GGM/976/708/2025/79" \
     --source-page "p.1"
   ```

2. **Re-OCR with higher DPI** if RERA text was missed
3. **Supplement with external data** for payment plans

## Verification Queries

### Check Project Distribution
```sql
SELECT project, COUNT(*) as pages
FROM ocr_pages
GROUP BY project
ORDER BY pages DESC;
```

Expected output:
```
Trevoc 56        | 102
Estate 360       | 67
The Sanctuaries  | 41
Tarc Ishva      | 33
Project 1        | 16
Godrej Sora      | 9
```

### Find Empty/Short Pages
```sql
SELECT source_pdf, page, LENGTH(text) as len, LEFT(text, 80) as preview
FROM ocr_pages
WHERE LENGTH(text) < 50
ORDER BY len ASC
LIMIT 10;
```

### Check for NULL Projects (Should be 0)
```sql
SELECT COUNT(*) FROM ocr_pages WHERE project IS NULL;
```

Expected: `0`

## Recommendations

### 1. ✅ No Immediate Action Required
The `ocr_pages` table is working correctly. Your current RAG tests showed:
- Payment plan queries work (The Sanctuaries)
- Unit configuration queries work (Trevoc 56)
- Amenities queries work (TARC Ishva, Estate 360)

### 2. 📊 Populate `documents` Table for Better Results
Since you only have "The Sanctuaries" in the `documents` table (22 chunks), ingest the others:

```bash
# Create remaining projects
docker compose exec ingest python setup_db.py projects-add --name "Trevoc 56" --slug "trevoc-56"
docker compose exec ingest python setup_db.py projects-add --name "TARC Ishva" --slug "tarc-ishva"
docker compose exec ingest python setup_db.py projects-add --name "Godrej Sora" --slug "godrej-sora"
docker compose exec ingest python setup_db.py projects-add --name "Estate 360" --slug "estate-360"
docker compose exec ingest python setup_db.py projects-add --name "Project 1" --slug "project-1"

# Ingest all (IDs 2-6 assuming Sanctuaries is 1)
for id in 2 3 4 5 6; do
  case $id in
    2) proj="Trevoc_56" ;;
    3) proj="TARC_Ishva" ;;
    4) proj="Godrej_SORA" ;;
    5) proj="Estate_360" ;;
    6) proj="Project_1" ;;
  esac

  docker compose exec ingest python ingest.py \
    --project-id $id \
    --source "${proj}.pdf" \
    --ocr-json "/app/outputs/${proj}/${proj}.jsonl"
done
```

### 3. 🏷️ Optional: Add Tags for High-Value Pages

Only if you want to improve priority sorting:

```sql
-- Tag payment plan pages
UPDATE ocr_pages
SET tags = 'payment'
WHERE text ILIKE '%payment plan%' OR text ILIKE '%CLP%' OR text ILIKE '%PLP%';

-- Tag amenity pages
UPDATE ocr_pages
SET tags = 'amenities'
WHERE text ILIKE '%amenities%' OR text ILIKE '%facilities%' OR text ILIKE '%club%';

-- Tag RERA/legal pages
UPDATE ocr_pages
SET tags = 'legal'
WHERE text ILIKE '%RERA%' OR text ILIKE '%registration%' OR text ILIKE '%disclaimer%';
```

### 4. 🔍 Monitor Project Name Matching

If you encounter issues with `--project` filtering, check PROJECT_HINTS mapping matches DB values:

```python
# Add to main.py:22-33 if needed
"Tarc Ishva": "TARC_Ishva.pdf",  # Match DB capitalization
```

## Conclusion

### ✅ What's Working
- All 268 pages properly ingested
- Project column populated for all rows
- Text content extracted (where available)
- SQL-based retrieval functional

### ⚠️ Minor Issues (Non-blocking)
- Tags column mostly empty (optional feature)
- Godrej Sora has minimal text content (PDF limitation)
- Project name capitalization varies (handled by ILIKE)

### 🚀 Next Steps
1. **Priorit 1**: Ingest remaining projects into `documents` table for vector search
2. **Priority 2**: Add curated facts for Godrej Sora (RERA, etc.)
3. **Priority 3**: Optionally add tags for better intent detection

**Overall Assessment**: 🟢 **Data is healthy and ready for production use!**
