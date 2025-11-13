# Frontend Test Client - Quick Setup

## 🎉 What I Created for You

A beautiful, single-page test client for your InvestoChat RAG system!

**Features:**
- ✅ Clean, modern UI with gradient design
- ✅ Project selection dropdown
- ✅ Model selection (GPT-4o, GPT-4.1-mini, etc.)
- ✅ Real-time query testing
- ✅ Source attribution with similarity scores
- ✅ Mode indicators (facts/docs/ocr)
- ✅ Latency tracking
- ✅ No build tools required!

## 🚀 How to Use It

### Step 1: Start Your API Server

Open a terminal and run:

```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat/InvestoChat_Build
uvicorn service:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReloader
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Leave this terminal running**

### Step 2: Open the Frontend

Open a **new terminal** and run:

```bash
cd /Users/ayaan/Documents/GitHub/InvestoChat/InvestoChat_Build/frontend
python3 -m http.server 3000
```

**Expected output:**
```
Serving HTTP on :: port 3000 (http://[::]:3000/) ...
```

### Step 3: Open in Browser

Open your browser and go to:
```
http://localhost:3000
```

You should see a beautiful purple gradient interface with "🏘️ InvestoChat Test Client" header.

### Step 4: Test Your First Query!

1. **Select a project**: Choose "The Sanctuaries" from dropdown
2. **Enter question**: Type "What is the payment plan?"
3. **Click "Ask Question"** (or press Ctrl+Enter)
4. **See results!** Answer, sources, and latency

## 🎨 What You'll See

### Interface Elements

**Top Section (Settings):**
- Project selector (All Projects, The Sanctuaries, Trevoc 56, etc.)
- Model selector (Default, GPT-4o, GPT-4.1 Mini)
- Results count (k value: 1-10)
- API endpoint (default: http://localhost:8000)

**Middle Section (Query):**
- Large text area for your question
- Blue "Ask Question" button
- Loading spinner when processing

**Bottom Section (Results):**
- **Answer box**: The generated response with mode badge
- **Metadata cards**: Latency, source count, mode
- **Sources list**: All pages used with similarity scores

### Mode Badges
- 🟢 **facts** - Answer from curated facts (highest precision)
- 🔵 **docs** - Answer from vector search documents
- 🟡 **ocr_ilike/ocr_trgm** - Answer from SQL search

## 📝 Sample Queries

Copy these into the frontend:

### Test Curated Facts (once you add them)
```
What is the RERA number for Godrej Sora?
When is the possession date?
```

### Test Vector Search
```
Which projects have 4 BHK units?
Compare amenities across all projects
What makes The Sanctuaries unique?
```

### Test Project-Specific
```
What is the payment plan for The Sanctuaries?
Tell me about unit configurations in Trevoc 56
What amenities does TARC Ishva offer?
```

## 🔧 Troubleshooting

### Problem: "Failed to fetch" Error

**Cause:** API server not running

**Fix:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Should return: {"status":"ok"}
```

### Problem: Frontend Doesn't Load

**Cause:** Port 3000 already in use

**Fix:**
```bash
# Use different port
python3 -m http.server 8080

# Then open: http://localhost:8080
```

### Problem: CORS Error in Browser Console

**Cause:** CORS middleware not enabled (already fixed!)

**Fix:** Already added to `service.py` - restart your API server

### Problem: "Not in the documents" for Everything

**Cause:** Database not fully populated

**Fix:**
```bash
# Verify documents exist
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT project_id, COUNT(*) FROM documents GROUP BY project_id;"

# Should show 68 total chunks
```

## 📊 What Changed in Your Code

### service.py
Added CORS middleware for cross-origin requests:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### New Files Created
- `/frontend/index.html` - The test client
- `/frontend/README.md` - Detailed documentation

## 🎯 Your Development Workflow

Now you have everything set up! Here's the order you wanted:

### ✅ 1. Test Frontend (Current Step)
- [x] Frontend created
- [x] CORS enabled
- [ ] Test various queries
- [ ] Explore different projects

### ⏭️ 2. Add Image Support
See `IMAGE_SUPPORT_GUIDE.md` for:
- Adding `send_whatsapp_image()` function
- Image intent detection
- Serving images via static files
- Updating frontend to display images

### ⏭️ 3. Extract and Add Facts
See `CURATED_FACTS_GUIDE.md` for:
- Extracting RERA numbers from brochures
- Adding possession dates
- Adding payment plans
- Bulk import script

## 🚀 Next Steps

1. **Test the frontend now!** Try different queries and projects
2. **Check latency** - Should be 500-2000ms typical
3. **Verify sources** - Make sure similarity scores are reasonable (0.3-0.8)
4. **Note missing info** - Track what returns "Not in documents"

Once you're comfortable with the frontend, we'll:
1. Add image support so clients can request floor plans
2. Extract and add curated facts for critical information

## 💡 Tips

- Use `Ctrl+Enter` in the textarea to quickly submit queries
- Try both specific project queries and "All Projects" mode
- Watch the mode badges - "facts" mode (once you add facts) will be fastest
- Check browser DevTools (F12) → Console for any errors
- Monitor API terminal for request logs

## 📞 Ready to Continue?

Let me know when you're ready to:
1. **Add image support** - Enable sending floor plans/maps
2. **Extract facts** - Pull RERA numbers, dates, etc. from PDFs

**Enjoy testing your RAG system!** 🎉
