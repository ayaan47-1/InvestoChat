# InvestoChat Frontend Test Client

A simple, single-page HTML application for testing your InvestoChat RAG system.

## Features

✅ **Query Testing** - Send questions to your RAG API
✅ **Project Selection** - Filter by specific projects
✅ **Model Selection** - Choose different LLM models
✅ **Real-time Results** - See answers, sources, and latency
✅ **Mode Indicators** - See if answer came from facts, documents, or OCR
✅ **Source Attribution** - View which pages contributed to the answer
✅ **No Build Required** - Pure HTML/CSS/JS, open and use!

## Quick Start

### Step 1: Start the API Server

```bash
cd InvestoChat_Build
uvicorn service:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Step 2: Open the Frontend

**Option A: Double-click**
```bash
open frontend/index.html
# Or on Windows: start frontend/index.html
# Or on Linux: xdg-open frontend/index.html
```

**Option B: Serve with Python (recommended for production testing)**
```bash
cd frontend
python3 -m http.server 3000
```
Then open: http://localhost:3000

### Step 3: Test a Query

1. **Select a project** (optional) - e.g., "The Sanctuaries"
2. **Enter your question** - e.g., "What is the payment plan?"
3. **Click "Ask Question"** or press `Ctrl+Enter`
4. **View results** - Answer, sources, latency, and mode

## Interface Overview

### Query Settings
- **Project**: Filter to specific project or search all
- **Model**: Choose LLM (default: gpt-4.1-mini)
- **Results (k)**: Number of chunks to retrieve (1-10)
- **API Endpoint**: Change if running on different host/port

### Response Display
- **Answer**: The generated response from your RAG system
- **Mode Badge**:
  - 🟢 **facts** - Answer from curated facts (high precision)
  - 🔵 **docs** - Answer from documents table (vector search)
  - 🟡 **ocr_ilike/ocr_trgm** - Answer from OCR SQL search
- **Latency**: Total response time in milliseconds
- **Sources**: Pages used to generate the answer with similarity scores

## Sample Queries to Try

### Payment Plans
```
What is the payment plan for The Sanctuaries?
Tell me about payment options for Trevoc 56
What are the payment milestones?
```

### Unit Configurations
```
Which projects have 4 BHK units?
What are the unit sizes in Trevoc 56?
Show me 3 BHK configurations
```

### Amenities
```
What amenities are available in TARC Ishva?
Compare amenities across projects
Which project has the best facilities?
```

### Location
```
Where is The Sanctuaries located?
Tell me about the location of Godrej Sora
How far is it from the airport?
```

### General Information
```
What makes The Sanctuaries unique?
Tell me about the developer
When is possession?
```

## Troubleshooting

### Error: "Failed to fetch"
**Cause**: API server is not running or wrong endpoint

**Fix**:
```bash
# Verify API is running
curl http://localhost:8000/health

# Check the API endpoint in frontend settings
# Should be: http://localhost:8000
```

### Error: "CORS policy"
**Cause**: CORS middleware not added to FastAPI

**Fix**: Verify `service.py` has CORS middleware (already added in latest version)

### No Results / "Not in the documents"
**Possible causes**:
1. Project doesn't have that information
2. Wrong project selected
3. Documents table not populated

**Debug**:
```bash
# Test with CLI first
docker compose exec -e USE_OCR_SQL=0 ingest python main.py \
  --rag "Your question" --project-id 1

# Check database
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT project_id, COUNT(*) FROM documents GROUP BY project_id;"
```

### API Responds but Frontend Shows Error
**Cause**: Response format mismatch

**Debug**: Check browser console (F12) for error details

## API Endpoint Reference

The frontend calls `POST /ask` with this payload:

```json
{
  "question": "What is the payment plan?",
  "project_id": 1,
  "k": 5,
  "model": "gpt-4.1-mini"
}
```

Response format:
```json
{
  "answer": "The payment plan is...",
  "mode": "docs",
  "sources": [
    {
      "source": "The_Sanctuaries.pdf",
      "page": 31,
      "score": 0.845
    }
  ],
  "latency_ms": 1250
}
```

## Keyboard Shortcuts

- `Ctrl+Enter` - Submit query from textarea

## Customization

### Change Color Theme
Edit the CSS gradient in `index.html`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Add More Projects
Update the project dropdown:
```html
<option value="7">Your New Project</option>
```

### Change Default Question
Modify the textarea default value:
```html
<textarea id="question">Your default question here</textarea>
```

## Production Deployment

### Security Considerations

1. **Restrict CORS origins** in `service.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

2. **Add authentication** if needed:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/ask")
async def ask(payload: AskRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token
    ...
```

3. **Rate limiting** - Already implemented in `service.py` via `api_rate_limiter`

4. **HTTPS** - Deploy behind nginx or use cloud platform (Vercel, Netlify, etc.)

### Deploy Frontend

**Option 1: Static hosting (Vercel, Netlify)**
```bash
cd frontend
# Connect to Git and deploy
```

**Option 2: Serve with nginx**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/frontend;
    index index.html;
}
```

**Option 3: Serve from FastAPI**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

## Next Steps

Now that you have a working frontend:

1. ✅ Test various queries across all projects
2. ⏭️ Add image support (next in your workflow)
3. ⏭️ Extract and add curated facts
4. ⏭️ Deploy to production

See `IMAGE_SUPPORT_GUIDE.md` and `CURATED_FACTS_GUIDE.md` for next steps.

## Support

- Main docs: `CLAUDE.md`
- Quick reference: `QUICK_REFERENCE.md`
- API testing: Use browser DevTools (F12) → Network tab
