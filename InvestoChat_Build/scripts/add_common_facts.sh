#!/bin/bash
# Quick script to add common curated facts for all projects

echo "Adding curated facts..."

# The Sanctuaries (ID: 1)
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "location" \
  --value "The Sanctuaries is located in Sector 53, Gurugram, near Golf Course Extension Road." \
  --source-page "Location page"

# TARC Ishva (ID: 3) - Already has location fact
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 3 --key "possession_date" \
  --value "Possession expected in Q2 2027" \
  --source-page "Timeline page"

# Godrej Sora (ID: 4)
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 4 --key "location" \
  --value "Godrej Sora is located in Sector 63, Golf Course Extension Road, Gurugram." \
  --source-page "Location page"

# Estate 360 (ID: 5)
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 5 --key "location" \
  --value "Estate 360 is located in Sector 70, Golf Course Extension Road, Gurugram." \
  --source-page "Location page"

# The Estate Residences (ID: 6)
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 6 --key "location" \
  --value "The Estate Residences is located in Sector 102, Dwarka Expressway, Gurugram." \
  --source-page "Location page"

echo "✅ Curated facts added for all projects!"
