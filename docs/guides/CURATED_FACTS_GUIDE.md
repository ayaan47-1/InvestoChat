# Curated Facts Guide

## What Are Curated Facts?

Curated facts are **high-precision key-value pairs** stored in the `facts` table with embeddings. They are checked **first** during retrieval with a high similarity threshold (0.75), ensuring accurate answers for critical information.

## When to Use Curated Facts

Use curated facts for:
- ✅ **RERA numbers** - Legal registration IDs
- ✅ **Possession dates** - Move-in timelines
- ✅ **Pricing** - Base prices, price per sqft
- ✅ **Contact information** - Sales office, developer details
- ✅ **Key features** - USPs that must be accurate
- ✅ **Payment milestones** - Exact payment schedules

**Don't use for**:
- ❌ General descriptions (use documents table)
- ❌ Variable information (unit availability)
- ❌ Content already in brochures (unless critical)

## How Facts Are Retrieved

From `main.py:363-365`:
```python
facts = search_facts(qvec, k=8, project_id=project_id)
if facts and facts[0][1].get("score", 0) >= 0.75:
    return {"mode":"facts", "answers":[facts[0][0]], "metas":[facts[0][1]]}
```

**Priority**: Facts → Documents → OCR Pages (SQL)

## Adding Curated Facts

### Basic Command
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id <ID> \
  --key "fact_name" \
  --value "The actual fact content" \
  --source-page "p.X"
```

### Example 1: Add RERA Number

**Godrej Sora RERA** (visible on page 1):
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 4 \
  --key "rera_number" \
  --value "RC/REP/HARERA/GGM/976/708/2025/79 dated August 25, 2025" \
  --source-page "p.1"
```

**TARC Ishva RERA**:
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 3 \
  --key "rera_number" \
  --value "Licence No. 128 of 2022 dated 24.08.2022 for 5.43263 acres in Sector 63A Gurugram" \
  --source-page "p.X"
```

### Example 2: Add Possession Date

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "possession_date" \
  --value "Ready for registration immediately. Registry and possession within 90 days of allotment." \
  --source-page "p.31"
```

### Example 3: Add Pricing Information

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "pricing" \
  --value "Base price is subject to revision. CLU Government fees 50L. Electricity connection as per actual." \
  --source-page "p.31" \
  --meta '{"currency": "INR", "unit": "lakh"}'
```

### Example 4: Add Payment Plan

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "payment_plan" \
  --value "EOI: 5%, Allotment & ATS (within 30 days): 25%, Prior to Registry (within 60 days): 50%, Registry and Possession (within 90 days): 20%. Total: 100%." \
  --source-page "p.31"
```

### Example 5: Add Location Details

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "location" \
  --value "DLF Phase 5, Manesar, Gurugram. Approximately 20 minutes from the proposed Disneyland India site." \
  --source-page "p.8"
```

### Example 6: Add Contact Information

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "contact" \
  --value "Sales Office: [REDACTED]. Developer: 32ND. Website: www.32nd.co" \
  --source-page "p.41" \
  --no-embed
```

**Note**: Use `--no-embed` for contact info you don't want semantically searchable.

### Example 7: Add Developer Information

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 2 \
  --key "developer" \
  --value "Developed by JHS Estate Ltd. Building plans approved by HSVP vide Memo No. 806 dated 29.07.2024. RERA registered." \
  --source-page "p.100"
```

## Using JSON Metadata

The `--meta` parameter accepts JSON for structured data:

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 2 \
  --key "unit_3bhk_type_b" \
  --value "3 BHK Type B: Carpet area 128.68 sq.mtr (1385 sq.ft), Saleable area 245.45 sq.mtr (2642 sq.ft), Balcony 58.41 sq.mtr (629 sq.ft)" \
  --source-page "p.30" \
  --meta '{"type": "unit_config", "bedrooms": 3, "carpet_sqft": 1385, "saleable_sqft": 2642}'
```

## Viewing Existing Facts

### List all facts for a project
```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT id, key, LEFT(value, 80) as value_preview FROM facts WHERE project_id = 1;"
```

### Search facts by keyword
```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT project_id, key, value FROM facts WHERE key ILIKE '%rera%' OR value ILIKE '%rera%';"
```

## Updating Facts

Use the same `facts-upsert` command - it will **overwrite** existing facts with the same `(project_id, key)`:

```bash
# First time
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q4 2025"

# Update (overwrites)
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q1 2026"
```

## Bulk Import Facts

For multiple facts, create a shell script:

**`add_facts.sh`**:
```bash
#!/bin/bash

# The Sanctuaries Facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "rera_number" \
  --value "RERA No: [To be added from brochure]" --source-page "p.1"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" \
  --value "Ready for registration immediately. Registry and possession within 90 days." \
  --source-page "p.31"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "payment_plan" \
  --value "EOI: 5%, Allotment & ATS: 25%, Pre-Registry: 50%, Registry & Possession: 20%" \
  --source-page "p.31"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "location" \
  --value "DLF Phase 5, Manesar, Gurugram. 20 minutes from proposed Disneyland India site." \
  --source-page "p.8"

# Trevoc 56 Facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 2 --key "rera_number" \
  --value "HARERA Registration No. RC/REP/HARERA/GCM/863/595/2024/90 dated 02.09.2024" \
  --source-page "p.100"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 2 --key "location" \
  --value "Sector 56, Gurugram. Site CH-13, 2.059 acres allotted by HSVP." \
  --source-page "p.100"

# TARC Ishva Facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 3 --key "rera_number" \
  --value "Licence No. 128 of 2022 dated 24.08.2022 for 5.43263 acres in Sector 63A" \
  --source-page "p.X"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 3 --key "location" \
  --value "Sector 63A, Gurugram. Four-side open residences." \
  --source-page "p.10"

# Godrej Sora Facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 4 --key "rera_number" \
  --value "RC/REP/HARERA/GGM/976/708/2025/79 dated August 25, 2025" \
  --source-page "p.1"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 4 --key "location" \
  --value "Sector 53, Gurugram" \
  --source-page "p.1"

echo "All facts added successfully!"
```

Run it:
```bash
chmod +x add_facts.sh
./add_facts.sh
```

## Testing Facts Retrieval

### Test if fact is retrieved
```bash
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "What is the RERA number for Godrej Sora?" --project-id 4
```

Expected output:
```
[mode] facts
RC/REP/HARERA/GGM/976/708/2025/79 dated August 25, 2025
```

### Test without project filter
```bash
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "What is the possession date for The Sanctuaries?" -k 5
```

## Facts vs Documents vs OCR Pages

| Feature | Facts | Documents | OCR Pages |
|---------|-------|-----------|-----------|
| **Priority** | 1st (checked first) | 2nd | 3rd (fallback) |
| **Threshold** | 0.75 (high precision) | Varies | pg_trgm score |
| **Use case** | Critical, exact info | General content | Keyword search |
| **Editability** | Easy to update | Re-ingest required | Fixed (OCR output) |
| **Query type** | Semantic (vector) | Semantic (vector) | Keyword (SQL) |

## Best Practices

### 1. Keep Facts Concise
✅ Good: "RERA No: RC/REP/HARERA/GGM/976/708/2025/79"
❌ Bad: "The RERA registration number for this project, which was issued by the Haryana Real Estate..."

### 2. Use Consistent Keys
```
rera_number (not rera, rera_no, registration_number)
possession_date (not possession, delivery_date)
payment_plan (not payment_schedule, payment_terms)
location (not address, location_details)
```

### 3. Include Units/Context
✅ "Base price: ₹2.5 Cr onwards"
❌ "2.5 Cr"

### 4. Source Pages Help Debugging
Always include `--source-page` so you can trace back to original content.

### 5. Update When Information Changes
Facts can be updated anytime without re-running ingestion:
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Updated: Q2 2026"
```

## Common Facts to Add

### Checklist per Project

- [ ] **RERA number** (legal requirement)
- [ ] **Location** (sector, city, landmarks)
- [ ] **Possession date** (timeline)
- [ ] **Payment plan** (if available)
- [ ] **Base pricing** (starting price)
- [ ] **Developer name** (company)
- [ ] **Contact info** (sales office, website)
- [ ] **Key amenities** (if critical USPs)
- [ ] **Unit configurations** (BHK types available)
- [ ] **Total area** (project size in acres)

## Monitoring Facts Usage

Add logging to see when facts are used:

```python
# In main.py retrieve() function, add after line 364:
if facts and facts[0][1].get("score", 0) >= 0.75:
    LOG.info(f"FACT USED: {facts[0][1].get('key')} (score: {facts[0][1].get('score')})")
    return {"mode":"facts", "answers":[facts[0][0]], "metas":[facts[0][1]]}
```

## Summary

**Where**: Use `setup_db.py facts-upsert` command
**When**: For critical, exact information that must be accurate
**Why**: Higher priority in retrieval (checked first with 0.75 threshold)
**How**: Via Docker exec or shell script for bulk import

**Next step**: Extract RERA numbers, possession dates, and payment plans from your brochures and add them as facts!
