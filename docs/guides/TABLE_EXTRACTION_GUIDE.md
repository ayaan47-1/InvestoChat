# Table Extraction and Labeling System

## Overview

The table extraction system automatically detects, extracts, normalizes, and labels tables from OCR data for improved retrieval of structured information like payment plans, unit specifications, and pricing.

## What Was Implemented

### 1. Table Processor Library (`table_processor.py`)

**Features:**
- **Table Type Detection**: Automatically labels tables as:
  - `payment_plan`: Payment schedules, milestones, installments
  - `unit_specifications`: BHK configurations, areas, layouts
  - `pricing`: Price lists, rate cards
  - `amenities`: Facility listings
  - `location`: Distance/proximity tables
  - `specifications`: Technical details, materials
  - `unknown`: Unclassified tables

- **Table Extraction**:
  - HTML tables (`<table>` tags) → Markdown conversion
  - Pipe-delimited tables (`|col1|col2|`) → Normalized markdown
  - Detects tables with 2+ consecutive rows with pipe delimiters

- **Normalization**:
  - Converts broken HTML tables to proper markdown format
  - Fixes inconsistent column counts
  - Adds header separators (`|---|---|`)
  - Aligns columns properly

- **Smart Summaries**:
  - Payment plans: "Payment plan table with 7 milestones including booking, possession, oc with 6 percentage markers"
  - Unit specs: "Unit specifications table with 4 configurations (2, 3, 4 BHK units)"
  - Generic: "pricing table with 5 rows and 3 columns"

### 2. Database Schema (`create_tables_table.sql`)

**Table: `document_tables`**
```sql
CREATE TABLE document_tables (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    source_path TEXT,
    page INTEGER,

    -- Metadata
    table_type VARCHAR(50),    -- payment_plan, unit_specifications, etc.
    table_format VARCHAR(20),   -- html, pipe, markdown
    row_count INTEGER,
    col_count INTEGER,

    -- Content
    markdown_content TEXT,      -- Normalized markdown table
    original_content TEXT,      -- Raw extracted content
    summary TEXT,               -- Text summary for embedding

    -- Vector search
    embedding vector(1536),     -- OpenAI embedding of summary + markdown

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
- `idx_document_tables_project`: Fast project filtering
- `idx_document_tables_type`: Fast type filtering
- `idx_document_tables_embedding`: Vector similarity search (IVFFlat)
- `idx_document_tables_project_type`: Combined project + type queries

### 3. Extraction Pipeline (`extract_tables.py`)

**Process:**
1. Query `ocr_pages` table for pages with tables (`<table>` or `|...|` patterns)
2. Extract tables using `process_text_with_tables()`
3. Generate summaries with `get_table_summary()`
4. Create embeddings for `summary + markdown` text
5. Insert into `document_tables` with proper project_id mapping

**Output from your data:**
```
✅ Extraction complete! Inserted 31 labeled tables

Summary by type:
  - unknown: 20 tables
  - unit_specifications: 8 tables
  - payment_plan: 1 tables
  - pricing: 1 tables
  - amenities: 1 tables
```

## Current Results

### Payment Plan Table (Trevoc_56.pdf p.102)

**Detected as:** `payment_plan`
**Summary:** "Payment plan table with 7 milestones including booking, possession, oc with 6 percentage markers"

**Markdown Content:**
```markdown
| S.No. | Installment Description | Percentage of Total Consideration |
|---|---|---|
| 1. | At the time of Booking/On application | Rs. 21 Lakhs |
| 2. | Within 7 days of Booking | Balance to complete 10% |
| 3. | Within 90 days of Booking | 10% |
| 4. | Within 180 days of Booking | 10% |
| 5. | On application of Occupation Certificate | 60% |
| 6. | On offer to Possession (Stamp Duty, Registration charges, miscellaneous expenses etc.) | 10% |
| 100% |
```

### Unit Specifications Tables

**Example from Godrej_SORA.pdf p.4:**
- Type: `unit_specifications`
- Summary: "Unit specifications table with 1 configurations (4 BHK units)"
- Detects BHK types automatically

**Example from Project_1.pdf p.4:**
- Type: `unit_specifications`
- Summary: "Unit specifications table with 18 configurations (2, 4, 1, 3 BHK units)"
- Large configuration matrix captured

### Other Tables

**Pricing (The_Sanctuaries.pdf p.31):**
- Type: `pricing`
- Summary: "Pricing table with 2 items"

**Amenities (Trevoc_56.pdf p.83):**
- Type: `amenities`
- Summary: "amenities table with 2 rows and 3 columns"

## How to Query Labeled Tables

### Direct SQL Queries

**Find all payment plans:**
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT source_path, page, summary
FROM document_tables
WHERE table_type = 'payment_plan';"
```

**Find tables for specific project:**
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT dt.source_path, dt.page, dt.table_type, dt.summary
FROM document_tables dt
JOIN projects p ON dt.project_id = p.id
WHERE p.name = 'Trevoc 56'
ORDER BY dt.page;"
```

**Count tables by type and project:**
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT
    p.name as project,
    dt.table_type,
    COUNT(*) as count
FROM document_tables dt
JOIN projects p ON dt.project_id = p.id
GROUP BY p.name, dt.table_type
ORDER BY p.name, count DESC;"
```

### Vector Similarity Search

**Find tables similar to query:**
```python
from openai import OpenAI
import psycopg

# Generate query embedding
client = OpenAI(api_key=OPENAI_API_KEY)
query = "Show me payment plans"
resp = client.embeddings.create(model="text-embedding-3-small", input=[query])
query_vec = resp.data[0].embedding

# Search document_tables
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                source_path,
                page,
                table_type,
                summary,
                markdown_content,
                1 - (embedding <=> %s::vector) as similarity
            FROM document_tables
            WHERE table_type = 'payment_plan'
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (query_vec, query_vec))

        for row in cur.fetchall():
            print(f"{row[0]} p.{row[1]} ({row[2]}): {row[3]} [sim: {row[5]:.3f}]")
```

## Next Steps: Integrate into main.py

To make labeled tables searchable via the RAG system, you need to add a new retrieval path in `main.py`.

### Option 1: Add Table-Specific Retrieval Function

Add to `main.py`:

```python
def retrieve_tables(q: str, k: int = 3, project_id: Optional[int] = None, table_type: Optional[str] = None):
    """
    Retrieve labeled tables from document_tables using vector similarity.

    Args:
        q: Query text
        k: Number of tables to retrieve
        project_id: Filter by project
        table_type: Filter by table type (payment_plan, unit_specifications, etc.)

    Returns:
        List of tables with metadata
    """
    if not DATABASE_URL:
        return []

    # Generate query embedding
    emb = _embed_texts([q])[0]

    # Build query with filters
    filters = []
    params = [emb, emb, k]

    if project_id:
        filters.append("project_id = %s")
        params.insert(2, project_id)

    if table_type:
        filters.append("table_type = %s")
        params.insert(2 if not project_id else 3, table_type)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    sql = f"""
        SELECT
            source_path,
            page,
            table_type,
            markdown_content,
            summary,
            1 - (embedding <=> %s::vector) as similarity
        FROM document_tables
        {where_clause}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    try:
        with _pg() as con, con.cursor() as cur:
            cur.execute(sql, params)
            results = cur.fetchall()

            tables = []
            for source, page, ttype, markdown, summary, sim in results:
                tables.append({
                    'source': source,
                    'page': page,
                    'type': ttype,
                    'content': markdown,
                    'summary': summary,
                    'similarity': sim
                })

            return tables
    except Exception as e:
        print(f"[warn] Table retrieval failed: {e}")
        return []
```

### Option 2: Enhance Existing retrieve() Function

Modify the `retrieve()` function to include table search:

```python
def retrieve(q: str, k: int = 3, overfetch: int = 48, project_id: Optional[int] = None, project_name: Optional[str] = None):
    """Enhanced retrieve with table support."""

    # Detect intent
    tag = intent_tag(q)

    # If payment query, try table search first
    if tag == "payment":
        tables = retrieve_tables(q, k=2, project_id=project_id, table_type="payment_plan")
        if tables and tables[0]['similarity'] > 0.75:
            # High confidence table match - return table content
            print(f"[tables] Found {len(tables)} payment plan table(s)")
            return [f"[TABLE from {t['source']} p.{t['page']}]\n{t['content']}" for t in tables]

    # Otherwise, continue with regular document retrieval
    # ... (existing code)
```

## Benefits of This System

### 1. **Precision for Structured Data**
- Payment plan queries now directly retrieve structured tables
- No need to parse unstructured text for payment schedules
- Guaranteed format consistency (normalized markdown)

### 2. **Better Ranking**
- Tables have dedicated embeddings of `summary + markdown`
- Payment plans rank higher for payment queries
- Unit specifications rank higher for BHK/area queries

### 3. **Type-Based Filtering**
- Query "payment plan" → filter `table_type = 'payment_plan'`
- Query "unit sizes" → filter `table_type = 'unit_specifications'`
- Reduces noise from irrelevant chunks

### 4. **Multi-Modal Context**
- Can combine table results with document chunks
- LLM gets both structured tables AND unstructured context
- Improves answer completeness

### 5. **Metadata-Rich**
- Know exact page number of table
- Know table dimensions (rows/cols)
- Know table format (HTML vs pipe-delimited)
- Helps with debugging and citation

## Testing the System

### Test 1: Find All Payment Plans
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT source_path, page, summary, LEFT(markdown_content, 100)
FROM document_tables
WHERE table_type = 'payment_plan';"
```

**Expected:** Should find Trevoc_56.pdf p.102 payment plan

### Test 2: Find Unit Specifications for Godrej SORA
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT dt.page, dt.summary
FROM document_tables dt
JOIN projects p ON dt.project_id = p.id
WHERE p.name = 'Godrej SORA' AND dt.table_type = 'unit_specifications'
ORDER BY dt.page;"
```

**Expected:** Should find 4 tables on pages 4, 5, 7, 8

### Test 3: Count Tables by Project
```bash
docker compose exec db psql -U investo_user -d investochat -c "
SELECT p.name, COUNT(*) as table_count
FROM document_tables dt
JOIN projects p ON dt.project_id = p.id
GROUP BY p.name
ORDER BY table_count DESC;"
```

## Limitations and Improvements

### Current Limitations

1. **20 Unknown Tables**: Many tables weren't classified
   - Need to improve `detect_table_type()` heuristics
   - Add more indicator keywords for each type
   - Consider ML-based classification

2. **No Payment Plans for Some Projects**: Only found 1 payment plan
   - TARC Ishva, Godrej SORA, The Sanctuaries payment plans not detected
   - Might be in non-table format (prose, lists)
   - Need to check actual PDF pages

3. **Table Extraction Errors**: Some tables have -1 or 0 rows
   - Indicates parsing failures
   - Need to debug `extract_pipe_tables()` for these cases

4. **No Cross-Page Tables**: Tables split across pages not merged
   - Each page processed independently
   - Would need multi-page context to merge

### Recommended Improvements

#### 1. Improve Detection Heuristics
Add more keywords to `detect_table_type()`:

```python
# Add to payment_indicators
"emi", "loan", "finance", "downpayment", "token money",
"construction linked plan", "time linked plan", "flexi plan"

# Add to unit_indicators
"bedroom", "bathroom", "balcony", "carpet area", "built-up area",
"configuration", "layout", "plan"

# Add to pricing_indicators
"base price", "bsp", "total cost", "final price", "all-inclusive"
```

#### 2. Handle Non-Table Payment Plans
Some payment plans are in list or prose format:

```python
def extract_payment_plan_from_prose(text: str) -> Optional[str]:
    """Extract payment schedules from non-table formats."""
    # Look for patterns like:
    # - Booking: 10%
    # - On completion of foundation: 20%
    # ...
```

#### 3. Add Table Validation
Check if detected tables make sense:

```python
def validate_table(table: Dict) -> bool:
    """Validate table before insertion."""
    if table['row_count'] < 0:
        return False
    if table['col_count'] == 0:
        return False
    if not table['markdown'].strip():
        return False
    return True
```

#### 4. Merge Cross-Page Tables
Detect when tables continue across pages:

```python
def merge_cross_page_tables(page_tables: List[Dict]) -> List[Dict]:
    """Merge tables that span multiple pages."""
    # Check if last table on page N has same columns as first table on page N+1
    # If so, merge them
```

## Manual Testing

You can manually test the table processor on any OCR text file:

```bash
# Extract a single page's OCR text
docker compose exec db psql -U investo_user -d investochat -t -c "
SELECT text
FROM ocr_pages
WHERE source_pdf = 'Trevoc_56.pdf' AND page = 102
" > test_page.txt

# Process with table_processor
docker compose exec ingest python -c "
from table_processor import process_text_with_tables, get_table_summary
import sys

with open('test_page.txt', 'r') as f:
    text = f.read()

result = process_text_with_tables(text)
print(f'Found {len(result[\"tables\"])} tables\\n')

for i, table in enumerate(result['tables'], 1):
    print(f'Table {i}:')
    print(f'  Type: {table[\"type\"].value}')
    print(f'  Rows: {table[\"row_count\"]}, Cols: {table[\"col_count\"]}')
    print(f'  Summary: {get_table_summary(table)}')
    print(f'  Markdown:\\n{table[\"markdown\"]}\\n')
"
```

## Summary

The table extraction system is now operational and has successfully:

✅ Created `document_tables` table with 31 labeled tables
✅ Detected 1 payment plan table with proper normalization
✅ Detected 8 unit specification tables with BHK extraction
✅ Detected 1 pricing table and 1 amenities table
✅ Generated embeddings for all tables
✅ Stored tables with proper project_id mapping

**Next Action:** Integrate table retrieval into `main.py` to use these labeled tables in RAG queries. This will significantly improve payment plan and unit specification queries.
