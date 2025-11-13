# InvestoChat Quick Reference

## Q1: Can the chatbot send images/maps via WhatsApp?

### Current Status: ❌ NO (text only)
The WhatsApp webhook only sends text responses.

### Your Database: ✅ HAS IMAGES
- `ocr_pages` table stores `image_path` for all 268 pages
- Images are in `/app/outputs/{Project}/images/{Project}_p{page}.png`

### To Enable Image Support:

**Quick Steps:**
1. Add `send_whatsapp_image()` function to `service.py`
2. Detect image intent ("show me", "floor plan", "map")
3. Query `ocr_pages` for relevant image
4. Mount static files: `app.mount("/images", StaticFiles(directory="/app/outputs"))`
5. Send image URL via WhatsApp API

**See**: `IMAGE_SUPPORT_GUIDE.md` for complete code

---

## Q2: How to add curated facts?

### Quick Command:
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id <ID> \
  --key "fact_name" \
  --value "The actual content" \
  --source-page "p.X"
```

### Example: Add RERA Number
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 4 \
  --key "rera_number" \
  --value "RC/REP/HARERA/GGM/976/708/2025/79" \
  --source-page "p.1"
```

### Where Facts Are Used:
- ✅ Checked **FIRST** during retrieval
- ✅ High threshold (0.75 similarity)
- ✅ Returns immediately if match found
- ✅ Priority: Facts → Documents → OCR Pages

### Common Facts to Add:
- **rera_number** - Legal registration
- **possession_date** - Move-in timeline
- **payment_plan** - Payment schedule
- **location** - Address, landmarks
- **pricing** - Base price, price per sqft
- **contact** - Sales office details
- **developer** - Company name

**See**: `CURATED_FACTS_GUIDE.md` for 20+ examples

---

## Project IDs (from database):
```
1 - The Sanctuaries
2 - Trevoc 56
3 - TARC Ishva
4 - Godrej Sora
5 - Estate 360
6 - Project 1
```

---

## Common Commands

### Add Single Fact
```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "possession_date" --value "Q4 2025" --source-page "p.31"
```

### View Facts
```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT project_id, key, LEFT(value, 60) FROM facts ORDER BY project_id;"
```

### Test Fact Retrieval
```bash
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "What is the RERA number?" --project-id 4
```

### Add Image Support (Static Files)
```python
# In service.py, after app creation:
from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="/app/outputs"), name="images")
```

### Test Image URL
```bash
# Start service
uvicorn service:app --host 0.0.0.0 --port 8000

# Access in browser
http://localhost:8000/images/The_Sanctuaries/images/The_Sanctuaries_p0001.png
```

---

## Documentation Files

- **IMAGE_SUPPORT_GUIDE.md** - Complete guide to adding image sending
- **CURATED_FACTS_GUIDE.md** - All about facts system
- **INGESTION_COMPLETE.md** - Post-ingestion status
- **SETUP_COMPLETE.md** - Setup and debugging
- **OCR_PAGES_ANALYSIS.md** - Database analysis
- **CLAUDE.md** - Full developer documentation

---

## Next Steps

### 1. Add Critical Facts (Priority 1)
Extract from brochures and add:
- RERA numbers for all 6 projects
- Possession dates (if available)
- Payment plans (The Sanctuaries confirmed, check others)

### 2. Enable Image Support (Priority 2)
- Mount static files in `service.py`
- Add intent detection
- Test with WhatsApp sandbox

### 3. Production Deployment (Priority 3)
- Set `USE_OCR_SQL=0` in `.env`
- Configure WhatsApp credentials
- Deploy to public server with HTTPS
- Map phone numbers to projects

---

## Support

If you need help:
- Check CLAUDE.md first
- Review specific guide (IMAGE_SUPPORT_GUIDE.md, etc.)
- Test queries with `--show` flag to debug
- Use `DEBUG_RAG=1` to see keyword extraction
