# InvestoChat Production Setup Guide

**Last Updated**: 2025-01-17
**Target**: HNI Lead Generation & Qualification for Luxury Real Estate in NCR, India

---

## Overview

This guide walks through deploying InvestoChat with the complete lead qualification and CRM system.

**What You're Deploying**:
- WhatsApp chatbot for HNI property queries
- 4-question lead qualification flow (budget, area, timeline, unit preference)
- Airtable CRM for partner to manage leads
- Automatic broker handoff for qualified leads
- Commission tracking (₹2.5L per ₹5Cr deal)

**Target**: 3 deals/month = ₹7.5L revenue/month

---

## Prerequisites

### Required Accounts
- [ ] PostgreSQL database (Neon, Supabase, or Railway)
- [ ] OpenAI API key
- [ ] Airtable account (Free or Plus plan)
- [ ] WhatsApp Business API (Wati Growth plan recommended at ₹4,999/month)
- [ ] DeepInfra API key (for OCR processing)

### Local Requirements
- Python 3.10+
- Docker (optional, for local development)
- Git

---

## Step 1: Database Setup

### 1.1 Apply Main Schema (if not already done)

```bash
cd InvestoChat_Build

# Apply main schema (projects, documents, facts, ocr_pages tables)
docker compose exec ingest python setup_db.py schema

# OR if running locally without Docker:
python setup_db.py schema
```

### 1.2 Apply Qualification Schema

This creates the lead qualification, conversation history, deals, and brokers tables.

```bash
# Using Docker
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /app/schema_qualification.sql

# OR directly with psql (replace with your DATABASE_URL)
psql $DATABASE_URL < schema_qualification.sql
```

**Expected Output**:
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
...
```

### 1.3 Verify Tables Created

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```

You should see:
- `projects`
- `documents`
- `facts`
- `ocr_pages`
- `lead_qualification` ← NEW
- `conversation_history` ← NEW
- `deals` ← NEW
- `brokers` ← NEW
- `lead_assignments` ← NEW

### 1.4 Add Sample Brokers

The schema automatically inserts 3 sample brokers. Update with real broker data:

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

```sql
-- Update broker 1 with real data
UPDATE brokers
SET name = 'Rajesh Kumar',
    email = 'rajesh@yourcompany.com',
    phone = '+919876543210',
    whatsapp_number = '+919876543210',
    areas_of_expertise = ARRAY['Gurgaon Sector 89', 'DLF Garden City']
WHERE id = 1;

-- Add more brokers
INSERT INTO brokers (name, email, phone, whatsapp_number, areas_of_expertise) VALUES
('Priya Sharma', 'priya@yourcompany.com', '+919876543220', '+919876543220', ARRAY['Noida Extension', 'Greater Noida']);
```

---

## Step 2: Install Dependencies

### 2.1 Update Requirements

```bash
cd InvestoChat_Build

# Install new dependencies
pip install pyairtable python-dotenv

# OR if using Docker, rebuild container
docker compose build ingest
docker compose up -d ingest
```

### 2.2 Verify Installation

```python
python -c "import pyairtable; print('pyairtable installed:', pyairtable.__version__)"
```

---

## Step 3: Airtable CRM Setup

### 3.1 Create Airtable Base

1. Go to [airtable.com](https://airtable.com) and sign in
2. Click "Create a base" → "Start from scratch"
3. Name it: **InvestoChat CRM**

### 3.2 Create Tables

Create 4 tables with these exact names and fields:

#### Table 1: Qualified Leads

**Table Name**: `Qualified Leads`

**Fields** (click "+" to add):
1. `Phone` - Phone number (primary field)
2. `Name` - Single line text
3. `Budget` - Single line text
4. `Area Preference` - Single line text
5. `Timeline` - Single line text
6. `Unit Type` - Single line text
7. `Status` - Single select with options:
   - 🔥 Qualified - Pending Assignment
   - 👤 Assigned to Broker
   - 📞 Broker Contacted
   - 🏢 Site Visit Scheduled
   - 💰 Negotiating
   - ✅ Deal Closed
   - ❌ Lost
8. `Qualification Score` - Number (0-4)
9. `Qualified Date` - Date
10. `Assigned Broker` - Single line text
11. `Assigned Date` - Date
12. `Source` - Single line text
13. `Notes` - Long text

#### Table 2: Deals

**Table Name**: `Deals`

**Fields**:
1. `Phone` - Phone number (primary field)
2. `Lead Name` - Single line text
3. `Project` - Single line text
4. `Unit Type` - Single line text
5. `Deal Value (₹)` - Currency (INR)
6. `Broker Commission (₹)` - Currency (INR)
7. `InvestoChat Commission (₹)` - Currency (INR)
8. `Closed Date` - Date
9. `Broker` - Single line text

#### Table 3: Brokers

**Table Name**: `Brokers`

**Fields**:
1. `Name` - Single line text (primary field)
2. `Phone` - Phone number
3. `WhatsApp Number` - Phone number
4. `Status` - Single select (Active, Inactive)
5. `Areas of Expertise` - Long text

#### Table 4: Activity Log

**Table Name**: `Activity Log`

**Fields**:
1. `Phone` - Phone number (primary field)
2. `Activity Type` - Single select (Qualified, Broker Request, Assigned, Site Visit, Deal Closed)
3. `Description` - Long text
4. `Timestamp` - Date and time

### 3.3 Get Airtable Credentials

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Click "Create new token"
3. Name: **InvestoChat Integration**
4. Scopes:
   - `data.records:read`
   - `data.records:write`
5. Access: Select your **InvestoChat CRM** base
6. Click "Create token" and copy it

7. Get your Base ID:
   - Open your base
   - Click "Help" → "API documentation"
   - Base ID is shown at the top (starts with `app...`)

### 3.4 Add to Environment Variables

Add to `InvestoChat_Build/.env.local`:

```bash
# Airtable CRM
AIRTABLE_API_KEY=patXXXXXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

### 3.5 Test Airtable Integration

```bash
cd InvestoChat_Build
python -c "
from airtable_crm import sync_qualified_lead
test_lead = {
    'phone': '+919999999999',
    'name': 'Test User',
    'budget': '₹3-5 Cr',
    'area_preference': 'Gurgaon Sector 89',
    'timeline': '1-3 months',
    'unit_preference': '3BHK',
    'qualification_score': 4
}
record_id = sync_qualified_lead(test_lead)
print('Test lead synced to Airtable:', record_id)
"
```

Check your Airtable base - you should see the test lead in "Qualified Leads" table!

---

## Step 4: WhatsApp Business API Setup

### Option A: Wati (Recommended for HNI Platform)

**Cost**: ₹4,999/month (Growth plan)
**Why**: Professional image, CRM features, broadcast campaigns, analytics

1. Sign up at [wati.io](https://wati.io)
2. Choose "Growth" plan
3. Connect your WhatsApp Business number
4. Get webhook credentials:
   - Go to Settings → Integrations → Webhooks
   - Set webhook URL: `https://your-domain.com/whatsapp/webhook`
   - Copy API key

5. Add to `.env.local`:
```bash
WHATSAPP_VERIFY_TOKEN=your_wati_verify_token
WHATSAPP_ACCESS_TOKEN=your_wati_api_key
WHATSAPP_PHONE_NUMBER_ID=your_wati_phone_id
```

### Option B: Direct Meta WhatsApp Business API

**Cost**: ₹0.36 per conversation (1000 messages free/month)
**Why**: Lower cost for pilot, but requires more setup

Follow: [Meta WhatsApp Business Setup Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

---

## Step 5: Environment Configuration

### 5.1 Complete `.env.local` File

Create or update `InvestoChat_Build/.env.local`:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/investochat

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini

# DeepInfra (for OCR)
DEEPINFRA_API_KEY=...

# Airtable CRM
AIRTABLE_API_KEY=patXXXXXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# WhatsApp (Wati or Direct)
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
DEFAULT_PROJECT_ID=1

# Rate Limiting
API_RATE_LIMIT=30
WHATSAPP_RATE_LIMIT=12
RATE_LIMIT_WINDOW=60
```

### 5.2 Validate Configuration

```bash
python test_env.py --verbose
```

Expected output:
```
✓ PASSED (12 checks)
RESULT: ALL TESTS PASSED ✓
```

---

## Step 6: Deploy API Service

### Option A: Railway (Recommended)

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Deploy:
```bash
cd InvestoChat_Build
railway login
railway init
railway up
```

3. Add environment variables in Railway dashboard
4. Note your Railway URL: `https://your-app.railway.app`

### Option B: Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: investochat-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn service:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      # ... add all other env vars
```

2. Connect to GitHub and deploy

### Option C: Local Testing

```bash
cd InvestoChat_Build
uvicorn service:app --reload --host 0.0.0.0 --port 8000
```

Then use ngrok for webhook testing:
```bash
ngrok http 8000
# Copy the https:// URL for WhatsApp webhook
```

---

## Step 7: Configure WhatsApp Webhook

### 7.1 Set Webhook URL

In your WhatsApp platform (Wati or Meta):

1. Set webhook URL: `https://your-domain.com/whatsapp/webhook`
2. Set verify token: (same as `WHATSAPP_VERIFY_TOKEN` in .env)
3. Subscribe to events: `messages`

### 7.2 Test Webhook

```bash
# Health check
curl https://your-domain.com/health
# Should return: {"status":"ok"}

# Test verify endpoint
curl "https://your-domain.com/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=YOUR_VERIFY_TOKEN"
# Should return: test123
```

---

## Step 8: Test Lead Qualification Flow

### 8.1 End-to-End Test

Send messages from WhatsApp to your business number:

**Test Sequence**:

1. **Initial Query** (to trigger qualification):
   ```
   User: What is the price for 3BHK at Godrej SORA?
   Bot: [Answers from RAG system]
   ```

2. **Second Query** (triggers qualification start):
   ```
   User: What are the payment plans?
   Bot: Great! I can see you're interested. To connect you with the best advisor,
        I'd like to ask you a few quick questions (takes just 1 minute).

        💰 What is your investment budget range?

        Examples:
        • ₹2-3 Crore
        • ₹3-5 Crore
        • ₹5+ Crore
   ```

3. **Answer Questions**:
   ```
   User: ₹3-5 Crore
   Bot: ✅ Got it!

        📍 Which areas are you considering for investment?

   User: Gurgaon Sector 89
   Bot: ✅ Got it!

        📅 When are you planning to invest?

   User: 1-3 months
   Bot: ✅ Got it!

        🏠 What unit configuration are you looking for?

   User: 3BHK
   Bot: 🎉 Perfect! I have all the information I need.

        📊 Your Investment Profile:
        💰 Budget: ₹3-5 Crore
        📍 Location: Gurgaon Sector 89
        📅 Timeline: 1-3 months
        🏠 Unit Type: 3BHK

        Would you like to speak with an advisor now?
   ```

4. **Broker Handoff**:
   ```
   User: Yes
   Bot: 🎯 Perfect! I'm connecting you with our investment advisor now.

        One of our experts will reach out within 2 hours...
   ```

### 8.2 Verify in Airtable

After step 3 (all questions answered):
1. Open your Airtable base
2. Check "Qualified Leads" table
3. You should see the new lead with:
   - Phone: +919999999999
   - Name: (from WhatsApp profile)
   - Budget: ₹3-5 Crore
   - Status: 🔥 Qualified - Pending Assignment

After step 4 (broker request):
- Status should update to: 📞 Requested Broker Call
- Activity Log should show "Broker Request"

### 8.3 Check Database

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

```sql
-- Check lead qualification
SELECT phone, name, budget, area_preference, qualification_score, is_qualified
FROM lead_qualification
ORDER BY created_at DESC
LIMIT 5;

-- Check conversation history
SELECT phone, message_type, LEFT(message_text, 50) as message, created_at
FROM conversation_history
WHERE phone = '+919999999999'
ORDER BY created_at DESC;

-- Check qualification stats
SELECT
    COUNT(*) as total_leads,
    COUNT(CASE WHEN is_qualified THEN 1 END) as qualified,
    AVG(qualification_score) as avg_score
FROM lead_qualification;
```

---

## Step 9: Add Real Projects

### 9.1 Add Projects to Database

```bash
docker compose exec ingest python setup_db.py projects-add \
  --name "Godrej SORA" --slug "godrej-sora" --whatsapp "+919876543210"
```

### 9.2 Process Brochures

```bash
cd InvestoChat_Build

# OCR processing
python process_pdf.py brochures/Godrej_SORA.pdf outputs --dpi 220

# Ingest
python ingest.py --project-id 1 \
  --source "Godrej_SORA.pdf" \
  --ocr-json outputs/Godrej_SORA/Godrej_SORA.jsonl \
  --min-len 200
```

### 9.3 Add HNI-Focused Facts

```bash
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "price_per_sqft" \
  --value "₹12,500-15,000 per sq.ft. (varies by floor)" \
  --source-page "p.8"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "possession_date" \
  --value "December 2026 (36 months from booking)" \
  --source-page "p.3"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "rera_number" \
  --value "RC/REP/HARERA/GGM/767/499/2023/48" \
  --source-page "p.2"

docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "payment_plan_summary" \
  --value "CLP: 20-80 (20% booking, 80% on possession) | PLP: 10-10-80" \
  --source-page "p.12"
```

See `docs/HNI_DEPLOYMENT_GUIDE.md` for complete list of recommended facts.

---

## Step 10: Partner Training (Airtable Dashboard)

### 10.1 Share Access

1. In Airtable, click "Share" (top right)
2. Add partner's email
3. Set permission: **Creator** (can edit and configure)

### 10.2 Daily Workflow for Partner

**Morning Check** (5 minutes):
1. Open Airtable → Qualified Leads table
2. Filter: Status = "🔥 Qualified - Pending Assignment"
3. For each new lead:
   - Click dropdown in "Assigned Broker" column
   - Select best broker based on area expertise
   - Status auto-updates to "👤 Assigned to Broker"

**Broker Assignment**:
- Partner calls broker: "New qualified lead for you: [Name], [Budget], [Area], [Timeline]"
- Broker contacts lead within 2 hours
- Partner updates status: "📞 Broker Contacted"

**Follow-up**:
- When site visit scheduled: Update to "🏢 Site Visit Scheduled"
- When negotiating: Update to "💰 Negotiating"
- When deal closes: Update to "✅ Deal Closed"

**Deal Logging**:
1. Go to "Deals" table
2. Click "+" to add record
3. Fill in:
   - Phone, Lead Name, Project, Unit Type
   - Deal Value: ₹50000000 (for ₹5Cr)
   - Broker Commission: ₹1000000 (2% = ₹10L)
   - InvestoChat Commission: ₹250000 (25% of ₹10L = ₹2.5L)
   - Closed Date
4. Commission auto-syncs to accounting

### 10.3 Mobile Access

Partner can manage leads from phone:
1. Download Airtable app (iOS/Android)
2. Sign in
3. Open InvestoChat CRM base
4. Get push notifications for new qualified leads (set up in Airtable Automations)

---

## Step 11: Monitoring & Analytics

### 11.1 Key Metrics to Track

**Daily**:
- New qualified leads (target: 1-2/day)
- Response time to broker requests (target: < 2 hours)
- Conversion rate: queries → qualified leads (target: 10-15%)

**Weekly**:
- Site visits scheduled (target: 3-5/week)
- Deals in negotiation
- Bot accuracy ("Not in documents" rate < 5%)

**Monthly**:
- Deals closed (target: 3/month = ₹7.5L commission)
- ROI: Commission ÷ Costs (target: 10x+)

### 11.2 Airtable Dashboard

Create views in Airtable:

**View 1: Pending Assignment**
- Filter: Status = "🔥 Qualified - Pending Assignment"
- Sort: Qualified Date (newest first)
- Group by: Timeline (Immediate, 1-3 months, etc.)

**View 2: Active Pipeline**
- Filter: Status IN ("👤 Assigned", "📞 Contacted", "🏢 Site Visit", "💰 Negotiating")
- Sort: Assigned Date
- Color-code by Status

**View 3: This Month's Deals**
- Table: Deals
- Filter: Closed Date >= Start of month
- Sum: InvestoChat Commission (shows monthly revenue)

### 11.3 Database Analytics

```sql
-- Daily qualified leads
SELECT DATE(qualified_at), COUNT(*)
FROM lead_qualification
WHERE is_qualified = TRUE
GROUP BY DATE(qualified_at)
ORDER BY DATE(qualified_at) DESC
LIMIT 7;

-- Qualification conversion rate
SELECT
    COUNT(DISTINCT phone) as total_users,
    COUNT(DISTINCT CASE WHEN is_qualified THEN phone END) as qualified,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN is_qualified THEN phone END) / COUNT(DISTINCT phone), 1) as conversion_pct
FROM lead_qualification;

-- Monthly revenue
SELECT
    DATE_TRUNC('month', closed_at) as month,
    COUNT(*) as deals_closed,
    SUM(investochat_commission) as total_commission
FROM deals
WHERE status = 'closed'
GROUP BY DATE_TRUNC('month', closed_at)
ORDER BY month DESC;
```

---

## Step 12: Launch Checklist

### Pre-Launch
- [ ] Database schema applied (main + qualification)
- [ ] All environment variables configured
- [ ] Airtable base created with 4 tables
- [ ] Airtable credentials tested
- [ ] WhatsApp webhook connected and verified
- [ ] At least 2-3 real projects ingested
- [ ] HNI facts added for each project
- [ ] Real broker data in database
- [ ] End-to-end qualification flow tested
- [ ] Partner trained on Airtable dashboard

### Launch Day
- [ ] Send test message to 3-5 test numbers
- [ ] Monitor logs for errors
- [ ] Partner checks Airtable for test leads
- [ ] Soft launch: Share with 10-20 HNI contacts
- [ ] Monitor first 24 hours closely

### Week 1
- [ ] Daily check: qualified leads count
- [ ] Collect feedback from partner
- [ ] Fix any "Not in documents" gaps
- [ ] Optimize facts/tables based on real queries
- [ ] Target: 5-10 qualified leads

### Month 1
- [ ] Track qualification → site visit conversion
- [ ] Measure broker response time
- [ ] First deal target: 1-2 bookings
- [ ] ROI validation: Commission vs costs

---

## Troubleshooting

### Qualification Not Starting
**Symptom**: User asks 3+ questions but never gets qualification flow

**Fix**:
```sql
-- Check conversation count
SELECT phone, COUNT(*) as message_count
FROM conversation_history
WHERE message_type = 'user'
GROUP BY phone;

-- If count >= 2 but qualification_score = 0:
SELECT * FROM lead_qualification WHERE phone = '+919999999999';

-- Check should_start_qualification logic in lead_qualification.py:226
```

### Airtable Not Syncing
**Symptom**: Lead qualifies in database but not in Airtable

**Fix**:
```bash
# Check Airtable credentials
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
print('API Key set:', bool(os.getenv('AIRTABLE_API_KEY')))
print('Base ID set:', bool(os.getenv('AIRTABLE_BASE_ID')))
"

# Check logs
tail -f logs/service.log | grep Airtable

# Manual sync test
python -c "from airtable_crm import sync_qualified_lead; ..."
```

### WhatsApp Messages Not Received
**Symptom**: User sends message, bot doesn't respond

**Fix**:
1. Check webhook logs: `tail -f logs/service.log`
2. Verify webhook URL in WhatsApp platform settings
3. Test webhook directly:
```bash
curl -X POST https://your-domain.com/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry": [{"changes": [{"value": {"messages": [{"type": "text", "from": "+919999999999", "text": {"body": "test"}}]}}]}]}'
```

### "Not in documents" Rate High
**Symptom**: >10% of queries return "Not in the documents"

**Fix**: See `docs/HNI_DEPLOYMENT_GUIDE.md` section on populating facts table

---

## Support

### Documentation
- `docs/HNI_DEPLOYMENT_GUIDE.md` - HNI-specific optimization
- `docs/IMPROVEMENTS_SUMMARY.md` - Technical improvements made
- `CLAUDE.md` - Developer guide for code changes

### Quick Commands Reference
```bash
# Check system health
python test_env.py --verbose

# Test retrieval
python main.py --rag "What is the price?" --project-id 1

# Check database
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# View logs
tail -f logs/service.log

# Restart service
docker compose restart ingest
```

---

## Next Steps After Launch

### Week 2-4: Optimization
- Add more HNI-focused facts based on real queries
- Implement WhatsApp broadcast for new project launches
- Create automated broker assignment (area expertise matching)
- Build simple analytics dashboard

### Month 2-3: Scale
- Add 5-10 more projects
- Integrate with property listing APIs
- Implement lead scoring (hot/warm/cold)
- Add email integration for follow-ups
- Create partner mobile app (React Native)

### Quarter 2: Advanced Features
- Multi-language support (Hindi/English)
- Voice message support
- Video brochure sharing
- Automated site visit scheduling (calendar integration)
- Referral tracking and rewards

---

**Ready to deploy?** Start with Step 1 (Database Setup) and work through each step. Reach out if you hit any blockers!
