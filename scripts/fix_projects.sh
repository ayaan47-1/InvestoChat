#!/bin/bash
# Fix project assignments and re-ingest with correct project IDs

set -e

echo "🧹 Step 1: Clean up ALL existing documents..."
docker compose exec db psql -U investo_user -d investochat -c "DELETE FROM documents;"

echo ""
echo "📋 Step 2: Check existing projects..."
docker compose exec db psql -U investo_user -d investochat -c "SELECT id, name, slug FROM projects ORDER BY id;"

echo ""
echo "🏗️  Step 3: Create/verify projects..."

# Create projects if they don't exist
docker compose exec ingest python setup_db.py projects-add --name "Godrej SORA" --slug "godrej-sora" 2>/dev/null || echo "  ✓ Godrej SORA exists"
docker compose exec ingest python setup_db.py projects-add --name "Trevoc 56" --slug "trevoc-56" 2>/dev/null || echo "  ✓ Trevoc 56 exists"
docker compose exec ingest python setup_db.py projects-add --name "The Sanctuaries" --slug "sanctuaries" 2>/dev/null || echo "  ✓ The Sanctuaries exists"
docker compose exec ingest python setup_db.py projects-add --name "TARC Ishva" --slug "tarc-ishva" 2>/dev/null || echo "  ✓ TARC Ishva exists"
docker compose exec ingest python setup_db.py projects-add --name "Estate 360" --slug "estate-360" 2>/dev/null || echo "  ✓ Estate 360 exists"
docker compose exec ingest python setup_db.py projects-add --name "Project 1" --slug "project-1" 2>/dev/null || echo "  ✓ Project 1 exists"

echo ""
echo "📊 Current projects:"
docker compose exec db psql -U investo_user -d investochat -c "SELECT id, name, slug FROM projects ORDER BY id;"

echo ""
echo "📥 Step 4: Re-ingest with CORRECT project IDs..."
echo ""

# Map each PDF to its proper project ID
# You'll need to adjust these IDs based on the output above

echo "=== Godrej_SORA.pdf (project-id will be determined) ==="
# Find project ID for Godrej SORA
GODREJ_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'godrej-sora';" | tr -d ' ')
echo "Using project_id: $GODREJ_ID"
docker compose exec ingest python ingest.py --project-id $GODREJ_ID --source "Godrej_SORA.pdf" --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl
echo ""

echo "=== Trevoc_56.pdf ==="
TREVOC_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'trevoc-56';" | tr -d ' ')
echo "Using project_id: $TREVOC_ID"
docker compose exec ingest python ingest.py --project-id $TREVOC_ID --source "Trevoc_56.pdf" --ocr-json outputs/Trevoc_56/Trevoc_56.jsonl
echo ""

echo "=== The_Sanctuaries.pdf ==="
SANCT_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'sanctuaries';" | tr -d ' ')
echo "Using project_id: $SANCT_ID"
docker compose exec ingest python ingest.py --project-id $SANCT_ID --source "The_Sanctuaries.pdf" --ocr-json outputs/The_Sanctuaries/The_Sanctuaries.jsonl
echo ""

echo "=== TARC_Ishva.pdf ==="
TARC_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'tarc-ishva';" | tr -d ' ')
echo "Using project_id: $TARC_ID"
docker compose exec ingest python ingest.py --project-id $TARC_ID --source "TARC_Ishva.pdf" --ocr-json outputs/TARC_Ishva/TARC_Ishva.jsonl
echo ""

echo "=== Estate_360.pdf ==="
ESTATE_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'estate-360';" | tr -d ' ')
echo "Using project_id: $ESTATE_ID"
docker compose exec ingest python ingest.py --project-id $ESTATE_ID --source "Estate_360.pdf" --ocr-json outputs/Estate_360/Estate_360.jsonl
echo ""

echo "=== Project_1.pdf ==="
PROJ1_ID=$(docker compose exec db psql -U investo_user -d investochat -t -c "SELECT id FROM projects WHERE slug = 'project-1';" | tr -d ' ')
echo "Using project_id: $PROJ1_ID"
docker compose exec ingest python ingest.py --project-id $PROJ1_ID --source "Project_1.pdf" --ocr-json outputs/Project_1/Project_1.jsonl
echo ""

echo "✅ Re-ingestion complete!"
echo ""
echo "📊 Final document counts by project:"
docker compose exec db psql -U investo_user -d investochat -c "
SELECT
    p.name as project_name,
    d.source_path,
    COUNT(*) as chunks
FROM documents d
JOIN projects p ON d.project_id = p.id
GROUP BY p.name, d.source_path
ORDER BY p.name, d.source_path;
"

echo ""
echo "🎯 Now you can query specific projects!"
echo "Try: docker compose exec ingest python main.py --rag \"What is the payment plan?\" --project \"Godrej SORA\" -k 5"
