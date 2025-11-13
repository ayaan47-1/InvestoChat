# Quick Command Reference

**Always run from:** `/Users/ayaan/Documents/GitHub/InvestoChat/`

```bash
# Change to correct directory first
cd /Users/ayaan/Documents/GitHub/InvestoChat
```

---

## 🔍 Test Queries

```bash
# Test payment intent
docker compose exec ingest python main.py --rag "What is the payment plan?" -k 5

# Test BHK normalization
docker compose exec ingest python main.py --rag "carpet area of 4 BHK" -k 5

# Test new keywords (booking amount, down payment)
docker compose exec ingest python main.py --rag "What is the booking amount?" -k 5

# Show raw retrieval (debug)
docker compose exec ingest python main.py --show "payment plan" -k 3

# With debug output
docker compose exec -e DEBUG_RAG=1 ingest python main.py --rag "payment plan" -k 5
```

---

## 📥 Re-ingest Single File

```bash
# Step 1: Delete old chunks
docker compose exec db psql -U investo_user -d investochat -c \
  "DELETE FROM documents WHERE source_path = 'Godrej_SORA.pdf';"

# Step 2: Re-ingest with deduplication
docker compose exec ingest python ingest.py \
  --project-id 1 \
  --source "Godrej_SORA.pdf" \
  --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl

# Step 3: Check result
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT COUNT(*) FROM documents WHERE source_path = 'Godrej_SORA.pdf';"
```

---

## 🔄 Re-ingest All Files

```bash
# Clear all documents
docker compose exec db psql -U investo_user -d investochat -c \
  "DELETE FROM documents WHERE project_id = 1;"

# Re-ingest all (will show deduplication messages)
for pdf in Godrej_SORA Trevoc_56 The_Sanctuaries TARC_Ishva Estate_360 Project_1; do
  echo "=== Ingesting ${pdf}.pdf ==="
  docker compose exec ingest python ingest.py \
    --project-id 1 \
    --source "${pdf}.pdf" \
    --ocr-json "outputs/${pdf}/${pdf}.jsonl"
  echo ""
done

# Check final counts
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_path, COUNT(*) as chunks FROM documents GROUP BY source_path ORDER BY chunks DESC;"
```

---

## 📄 Process NEW PDF

```bash
# Step 1: Run OCR on new PDF
docker compose exec ingest python process_pdf.py \
  brochures/NEW_FILE.pdf outputs --dpi 220

# Step 2: Ingest the OCR output
docker compose exec ingest python ingest.py \
  --project-id 1 \
  --source "NEW_FILE.pdf" \
  --ocr-json outputs/NEW_FILE/NEW_FILE.jsonl
```

---

## 🗄️ Database Queries

```bash
# Check document counts
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_path, COUNT(*) FROM documents GROUP BY source_path;"

# Find units by size
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_path, LEFT(text, 200) FROM documents WHERE text ILIKE '%sqft%' LIMIT 5;"

# Find payment plans
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_path, LEFT(text, 200) FROM documents WHERE text ILIKE '%payment%' LIMIT 5;"

# Check OCR pages count
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_pdf, COUNT(*) FROM ocr_pages GROUP BY source_pdf;"
```

---

## 🧪 Test Environment Setup

```bash
# Test environment variables
cd InvestoChat_Build
python3 test_env.py --verbose
cd ..
```

---

## 🐳 Docker Management

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f ingest

# Restart a service
docker compose restart ingest
```

---

## 💡 Quick Troubleshooting

### "command not found: docker"
```bash
# Check if Docker Desktop is running
# Or use: docker-compose instead of docker compose
```

### "FileNotFoundError"
```bash
# Make sure you're in /InvestoChat/ not /InvestoChat_Build/
cd /Users/ayaan/Documents/GitHub/InvestoChat
```

### "Not in the documents"
```bash
# Check what data exists first
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT source_path, COUNT(*) FROM documents GROUP BY source_path;"

# Use --show to see what's being retrieved
docker compose exec ingest python main.py --show "your query" -k 5
```

---

## 📊 Before/After Comparison

```bash
# Compare chunks before and after re-ingestion

# Before (current state):
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT SUM(COUNT(*)) as total_chunks FROM documents GROUP BY project_id;"

# Delete and re-ingest all (see commands above)

# After (with deduplication):
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT SUM(COUNT(*)) as total_chunks FROM documents GROUP BY project_id;"

# Expected: 10-20% fewer chunks due to header/footer removal
```

---

## 🎯 One-Command Test

Run this to verify everything is working:

```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat && \
docker compose exec ingest python main.py --rag "What is the payment plan?" -k 5
```

**Expected output:** Payment plan details with sources listed

---

## 📝 Notes

- **Always run from:** `/Users/ayaan/Documents/GitHub/InvestoChat/`
- **Python scripts are in:** `InvestoChat_Build/` (but run via docker exec)
- **PDFs are in:** `brochures/`
- **OCR outputs are in:** `outputs/`
- **Database:** PostgreSQL in Docker (port 5432)
- **Adminer:** http://localhost:8080 (if running)
