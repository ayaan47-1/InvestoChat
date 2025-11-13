# Utility Scripts

Automation and maintenance scripts for InvestoChat.

## 📜 Available Scripts

### `fix_projects.sh`
**Purpose**: Fix duplicate documents and reassign correct project IDs

**What it does**:
1. Deletes all existing documents from database
2. Verifies/creates all projects (Godrej SORA, Trevoc 56, etc.)
3. Re-ingests each PDF with correct project_id mapping
4. Shows final document counts by project

**When to use**:
- After discovering duplicate documents with wrong project_ids
- When project assignments are incorrect
- To clean up and rebuild document database

**Usage**:
```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat
./scripts/fix_projects.sh
```

**Output**:
```
🧹 Step 1: Clean up ALL existing documents...
DELETE 150

📋 Step 2: Check existing projects...
 id |       name        |     slug
----+-------------------+---------------
  1 | The Sanctuaries   | sanctuaries
  2 | Trevoc 56         | trevoc-56
  ...

📥 Step 4: Re-ingest with CORRECT project IDs...
✅ Re-ingestion complete!

📊 Final document counts by project:
   project_name    |   source_path    | chunks
-------------------+------------------+--------
 Godrej SORA       | Godrej_SORA.pdf  |     25
 Trevoc 56         | Trevoc_56.pdf    |     25
```

---

### `reingest_all.sh`
**Purpose**: Re-ingest all PDFs with header/footer deduplication enabled

**What it does**:
1. Deletes existing documents
2. Re-runs `ingest.py` for all PDFs with deduplication
3. Shows before/after statistics

**When to use**:
- After implementing deduplication enhancements
- To apply new text cleaning logic to existing data
- When chunks have quality issues (repeated headers/footers)

**Usage**:
```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat
./scripts/reingest_all.sh
```

**Output**:
```
🧹 Cleaning up existing documents...
DELETE 150

📥 Re-ingesting with deduplication...

=== Godrej_SORA.pdf ===
[dedup] Found 8 repeated header/footer patterns
[dedup] Removed 38 repeated lines from 20 pages
✅ Inserted 25 chunks

Final stats:
 source_path    | chunks
----------------+--------
 Godrej_SORA.pdf|     25
 Trevoc_56.pdf  |     27
```

---

### `test_dedup.sh`
**Purpose**: Test header/footer deduplication on a single PDF

**What it does**:
1. Backs up existing documents for one PDF
2. Re-ingests that single PDF with deduplication
3. Shows deduplication statistics

**When to use**:
- To test deduplication on a specific problematic PDF
- Before running full re-ingestion
- To debug deduplication logic

**Usage**:
```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat

# Edit the script to specify which PDF to test
# Then run:
./scripts/test_dedup.sh
```

**Example Edit**:
```bash
# In test_dedup.sh, modify:
TEST_PDF="Godrej_SORA.pdf"
PROJECT_ID=4
```

**Output**:
```
Testing deduplication on: Godrej_SORA.pdf

🗄️ Backing up existing chunks...
Backup complete: 25 chunks

🧪 Testing deduplication...
[dedup] Found 8 repeated header/footer patterns:
  - "GODREJ PROPERTIES"
  - "www.godrejproperties.com"
  - "E-BROCHURE"

[dedup] Removed 38 repeated lines from 20 pages
✅ Inserted 25 chunks

📊 Results:
Before: 25 chunks (with repeated headers)
After:  25 chunks (headers removed, better quality)
```

---

## 🛠️ How to Create New Scripts

### Template for Maintenance Scripts

```bash
#!/bin/bash
# Description: What this script does
# Usage: ./scripts/my_script.sh

set -e  # Exit on error

echo "🔧 Starting task..."

# Your logic here
docker compose exec db psql -U investo_user -d investochat -c "
  -- Your SQL here
"

echo "✅ Task complete!"
```

### Best Practices

1. **Always use `set -e`** to exit on errors
2. **Add descriptive echo statements** for user feedback
3. **Test on small dataset first** before bulk operations
4. **Document prerequisites** (e.g., Docker must be running)
5. **Include usage examples** in comments
6. **Show before/after stats** for verification

---

## 🚨 Safety Notes

### Before Running Destructive Scripts

**fix_projects.sh** and **reingest_all.sh** DELETE ALL DOCUMENTS!

Always:
1. ✅ Backup your database first
2. ✅ Verify Docker containers are running
3. ✅ Check that OCR outputs exist in `outputs/` directory
4. ✅ Have API keys in `.env` (for re-embedding)

**Backup command**:
```bash
docker compose exec db pg_dump -U investo_user investochat > backup_$(date +%Y%m%d).sql
```

**Restore command** (if needed):
```bash
cat backup_20250112.sql | docker compose exec -T db psql -U investo_user -d investochat
```

---

## 📋 Common Use Cases

### Scenario 1: "My queries return wrong projects"
**Solution**: Run `fix_projects.sh` to reassign project IDs correctly

### Scenario 2: "Chunks have repeated headers/footers"
**Solution**: Run `reingest_all.sh` to apply deduplication

### Scenario 3: "One PDF has quality issues"
**Solution**: Run `test_dedup.sh` on that specific PDF

### Scenario 4: "I updated text cleaning logic"
**Solution**: Run `reingest_all.sh` to re-apply cleaning

---

## 🔗 Related Documentation

- [Quick Commands](../docs/guides/QUICK_COMMANDS.md) - Common operations
- [Tier 1 Enhancements](../docs/analysis/TIER1_ENHANCEMENTS.md) - Deduplication details
- [Setup Complete](../docs/setup/SETUP_COMPLETE.md) - Database setup

---

## 📝 Script Maintenance Log

| Script | Last Updated | Changes |
|--------|--------------|---------|
| fix_projects.sh | 2025-01-12 | Added project ID mapping for all PDFs |
| reingest_all.sh | 2025-01-12 | Added deduplication support |
| test_dedup.sh | 2025-01-12 | Initial version for testing dedup |

---

**Need to add a new script?** Create it here and document it in this README!
