# InvestoChat Quick Start - Wati Dashboard

**Goal:** Send WhatsApp broadcasts and auto-qualify leads in 30 minutes.

---

## ✅ Prerequisites

- [ ] PostgreSQL database running (Docker or cloud)
- [ ] OpenAI API key
- [ ] Wati account (sign up at wati.io)
- [ ] Public URL for your service (ngrok or Render)

---

## 🚀 Setup (4 Steps)

### **Step 1: Database Setup (5 minutes)**

```bash
cd InvestoChat_Build

# Apply main schema
docker compose exec ingest python setup_db.py schema

# Apply qualification schema
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /app/schema_qualification.sql

# Add your first project
docker compose exec ingest python setup_db.py projects-add \
  --name "The Sanctuaries" --slug "sanctuaries"

# Verify
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
# Should show: projects, documents, facts, ocr_pages, lead_qualification, etc.
```

### **Step 2: Deploy Service (10 minutes)**

**Option A: Local with ngrok (for testing)**
```bash
# Terminal 1: Start service
uvicorn service:app --host 0.0.0.0 --port 8000

# Terminal 2: Expose publicly
ngrok http 8000
# Copy URL: https://abc123.ngrok.io
```

**Option B: Render (for production)**
```bash
# 1. Push code to GitHub
# 2. Go to render.com → New Web Service
# 3. Connect GitHub repo
# 4. Build: pip install -r requirements.txt
# 5. Start: uvicorn service:app --host 0.0.0.0 --port $PORT
# 6. Add environment variables from .env.local
# 7. Deploy
# Copy URL: https://investochat.onrender.com
```

### **Step 3: Configure Wati (10 minutes)**

1. **Sign up:** Go to [wati.io](https://www.wati.io/) → Start Free Trial
2. **Choose plan:** Growth Plan (₹4,999/month)
3. **Setup WhatsApp:** Verify your business phone number
4. **Configure webhook:**
   - Wati Dashboard → Settings → Integrations → Webhook
   - **URL:** `https://your-domain.com/whatsapp/webhook`
   - **Verify Token:** (from `.env.local`: `WHATSAPP_VERIFY_TOKEN`)
   - Click **"Save & Verify"** → Should show ✅

### **Step 4: Test (5 minutes)**

```bash
# 1. Send test message from Wati to your phone
# 2. Reply: "What is the payment plan?"
# 3. Check logs - should see bot response

# Check service logs
docker compose logs -f

# Should see:
# [INFO] WhatsApp inbound from +91XXXXXXXXXX
# [INFO] ask project=1 mode=docs_expanded latency_ms=2341
```

**✅ If you receive a response:** Setup complete!

---

## 📤 Send Your First Broadcast (5 minutes)

### **1. Prepare Contacts**

Create `contacts.csv`:
```csv
name,phone,tags
Rahul Sharma,+919876543210,jan_campaign
Priya Gupta,+919876543211,jan_campaign
Amit Kumar,+918888888888,jan_campaign
```

### **2. Upload to Wati**

- Wati Dashboard → **Contacts** → **Import**
- Upload `contacts.csv`
- Map columns: Name → Name, Phone → Phone
- Click **"Import"**

### **3. Create Broadcast**

- Dashboard → **Broadcast** → **New Broadcast**
- **Message:**
  ```
  Hello {{name}}! 👋

  We have exclusive luxury properties in Gurgaon:
  ✨ Premium 3/4 BHK units
  🏗️ Ready to move-in
  💰 Starting ₹3.5Cr

  Reply "YES" for detailed brochure!

  - Team InvestoChat
  ```
- **Recipients:** Select tag `jan_campaign`
- **Send:** Click "Send Now"

### **4. Monitor Results**

- Dashboard → **Broadcast** → View metrics
- Dashboard → **Messages** → See replies

**Your chatbot handles all responses automatically!**

---

## 🎯 What Happens Next (Automatic)

### **User replies "YES"**
→ Bot starts 4-question qualification (budget, area, timeline, unit)

### **User asks question**
→ Bot answers from your documents with sources

### **Qualified lead requests broker**
→ Auto-syncs to Airtable, sends reference ID

**You just monitor Airtable and close deals!**

---

## 📋 Configuration Checklist

### **Required Environment Variables** (in `.env.local`)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/investochat

# OpenAI (for embeddings and chat)
OPENAI_API_KEY=sk-...

# WhatsApp Webhook (for Wati verification)
WHATSAPP_VERIFY_TOKEN=mySuperSecretToken123
DEFAULT_PROJECT_ID=1
```

### **Optional (if using Airtable CRM)**

```bash
AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

---

## 🔧 Troubleshooting

### **Webhook verification fails**

```bash
# 1. Check service is running
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# 2. Check verify token matches
# .env.local: WHATSAPP_VERIFY_TOKEN=ABC
# Wati webhook settings: Verify Token = ABC

# 3. Check URL is accessible
curl https://your-domain.com/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=ABC
# Should return: test
```

### **No response from bot**

```bash
# 1. Check project routing
cat workspace/whatsapp_routes.json
# Should map user's number to project ID
# OR set DEFAULT_PROJECT_ID in .env

# 2. Check data exists
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT COUNT(*) FROM documents WHERE project_id = 1;"
# Should be > 0

# 3. Check logs
docker compose logs -f
# Look for errors
```

### **Messages delivered but not triggering webhook**

- Wati Settings → Webhook → Check "Active" status
- Event subscription must include "Message Received"
- Test with manual curl (see WATI_SETUP_GUIDE.md)

---

## 📚 Full Documentation

- **Wati Setup:** `WATI_SETUP_GUIDE.md` (comprehensive guide)
- **Production Deployment:** `PRODUCTION_READY.md`
- **Airtable CRM:** `AIRTABLE_PARTNER_GUIDE.md`
- **Testing:** `TESTING_GUIDE.md`

---

## 💡 Pro Tips

1. **Best broadcast times:** 10 AM or 6 PM on weekdays
2. **Personalize:** Use `{{name}}` variable in messages
3. **Segment:** Tag contacts by interest/budget for targeted campaigns
4. **Monitor:** Check reply rates - aim for 7-10%
5. **Follow up:** Send 2nd message to non-responders after 3-5 days

---

## 🎉 Success Metrics

**After first broadcast to 100 contacts:**

- **Delivered:** 95-98 messages
- **Read:** 60-70 messages
- **Replied:** 7-10 users
- **Qualified:** 3-4 leads
- **Deals:** 0-1 (takes 1-2 weeks)

**Scale up after successful test!**

---

## ✅ You're Ready!

**Your workflow:**
1. Upload contacts to Wati (once)
2. Send broadcast via dashboard (5 minutes)
3. Monitor Airtable for qualified leads
4. Call qualified leads → Close deals

**System handles automatically:**
- Receiving messages
- Answering questions
- Qualifying leads
- Syncing to Airtable

**No coding. No complexity. Just revenue.** 🚀
