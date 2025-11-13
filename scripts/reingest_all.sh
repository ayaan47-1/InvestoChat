#!/bin/bash
# Re-ingest all PDFs with deduplication enabled

set -e

echo "🧹 Clearing old documents..."
docker compose exec db psql -U investo_user -d investochat -c "DELETE FROM documents WHERE project_id = 1;"

echo ""
echo "📥 Re-ingesting all PDFs with deduplication..."
echo ""

echo "=== Godrej_SORA.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "Godrej_SORA.pdf" --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl
echo ""

echo "=== Trevoc_56.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "Trevoc_56.pdf" --ocr-json outputs/Trevoc_56/Trevoc_56.jsonl
echo ""

echo "=== The_Sanctuaries.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "The_Sanctuaries.pdf" --ocr-json outputs/The_Sanctuaries/The_Sanctuaries.jsonl
echo ""

echo "=== TARC_Ishva.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "TARC_Ishva.pdf" --ocr-json outputs/TARC_Ishva/TARC_Ishva.jsonl
echo ""

echo "=== Estate_360.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "Estate_360.pdf" --ocr-json outputs/Estate_360/Estate_360.jsonl
echo ""

echo "=== Project_1.pdf ==="
docker compose exec ingest python ingest.py --project-id 1 --source "Project_1.pdf" --ocr-json outputs/Project_1/Project_1.jsonl
echo ""

echo "✅ Re-ingestion complete!"
echo ""
echo "📊 Final document counts:"
docker compose exec db psql -U investo_user -d investochat -c "SELECT source_path, COUNT(*) as chunks FROM documents GROUP BY source_path ORDER BY chunks DESC;"
