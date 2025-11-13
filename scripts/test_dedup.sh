#!/bin/bash
set -e

echo "🧪 Testing Header/Footer Deduplication Enhancement"
echo "=================================================="
echo ""

# Step 1: Check current state
echo "📊 Current state:"
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT COUNT(*) as chunks FROM documents WHERE source_path = 'Godrej_SORA.pdf';" 2>/dev/null

# Step 2: Delete old chunks
echo ""
echo "🗑️  Deleting old chunks..."
docker compose exec db psql -U investo_user -d investochat -c \
  "DELETE FROM documents WHERE source_path = 'Godrej_SORA.pdf';" 2>/dev/null

# Step 3: Re-ingest with deduplication
echo ""
echo "📥 Re-ingesting with deduplication enabled..."
echo ""
docker compose exec ingest python ingest.py \
  --project-id 1 \
  --source "Godrej_SORA.pdf" \
  --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl

# Step 4: Check new state
echo ""
echo "📊 After deduplication:"
docker compose exec db psql -U investo_user -d investochat -c \
  "SELECT COUNT(*) as chunks FROM documents WHERE source_path = 'Godrej_SORA.pdf';" 2>/dev/null

echo ""
echo "✅ Test complete!"
echo "Look for '[dedup] Found N repeated lines' in the output above"
