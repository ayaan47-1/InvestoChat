# Wati Setup Guide - Dashboard Only

**Decision:** Using Wati Dashboard for broadcasts (no coding needed!)

---

## 🎯 Complete Flow

```
1. YOU: Send broadcast via Wati Dashboard
   └─> Upload contacts → Create message → Send

2. RECIPIENTS: Receive message on WhatsApp
   └─> Reply with questions or "YES"

3. WATI: Forwards replies to your webhook
   └─> Automatic (configured once)

4. YOUR CHATBOT: Handles everything automatically
   ├─> Qualification (4 questions: budget, area, timeline, unit)
   ├─> Property Q&A (answers from your documents)
   ├─> Broker handoff (when qualified lead requests)
   └─> Airtable sync (qualified leads)

5. RESULT: Qualified leads in Airtable for your team
```

**You only touch:** Wati Dashboard (upload & send)
**System handles:** Everything else automatically!

---

## 📋 Setup Checklist (Complete Once)

### **Part 1: Wati Account Setup**

- [ ] Sign up at [wati.io](https://www.wati.io/)
- [ ] Choose **Growth Plan** (₹4,999/month)
- [ ] Verify business phone number
- [ ] Complete WhatsApp Business Account setup
- [ ] Get Wati dashboard access

### **Part 2: Webhook Configuration**

- [ ] Deploy your FastAPI service (get public URL)
- [ ] In Wati: Settings → Webhook
- [ ] Enter webhook URL: `https://your-domain.com/whatsapp/webhook`
- [ ] Enter verify token (from your `.env.local`)
- [ ] Click "Save & Verify" (should show ✅ Connected)

### **Part 3: Test End-to-End**

- [ ] Send test message from Wati to your phone
- [ ] Reply with a question
- [ ] Check service logs - should see qualification start
- [ ] Verify lead appears in database
- [ ] Confirm Airtable sync (if configured)

**Once setup is complete, you never touch code again!**

---

## 🚀 Step-by-Step: Wati Account Setup

### **Step 1: Sign Up for Wati**

1. Visit [wati.io](https://www.wati.io/)
2. Click **"Start Free Trial"** (7 days free)
3. Enter business details:
   - Company name
   - Your email
   - Phone number
4. Complete signup

### **Step 2: Choose Plan**

1. Select **Growth Plan** (₹4,999/month)
   - **Includes:**
     - Unlimited contacts
     - Unlimited broadcasts
     - Team inbox
     - API access
     - Basic analytics
     - Live chat support

2. Enter payment details
3. Confirm subscription

### **Step 3: WhatsApp Business Account Setup**

Wati will guide you through:

1. **Connect WhatsApp**
   - Choose: New WhatsApp number OR Migrate existing
   - Enter phone number for WhatsApp Business
   - Verify with OTP

2. **Business Profile**
   - Business name: "InvestoChat Real Estate"
   - Category: "Real Estate"
   - Description: "Luxury property consultants in NCR"
   - Business hours: 9 AM - 8 PM
   - Upload logo (optional)

3. **Verify Business** (Required for production)
   - Upload business documents
   - Wait 1-2 days for Meta approval

**Done!** You now have Wati dashboard access.

---

## 🔗 Step-by-Step: Webhook Integration

This connects Wati to your chatbot.

### **Step 1: Deploy Your Service**

**Option A: Using ngrok (Development/Testing)**

```bash
# Terminal 1: Start your service
cd InvestoChat_Build
uvicorn service:app --host 0.0.0.0 --port 8000

# Terminal 2: Expose with ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option B: Using Render/Railway (Production)**

1. Deploy your code to GitHub
2. Create web service on Render or Railway
3. Copy the public URL (e.g., `https://investochat.onrender.com`)

### **Step 2: Configure Webhook in Wati**

1. **Login to Wati dashboard**
2. **Go to Settings** (gear icon top right)
3. **Click "Integrations"** → **"Webhook"**
4. **Configure webhook:**
   - **Webhook URL**: `https://your-domain.com/whatsapp/webhook`
     - Example: `https://abc123.ngrok.io/whatsapp/webhook`
     - Example: `https://investochat.onrender.com/whatsapp/webhook`

   - **Verify Token**: Copy from your `.env.local`
     - Open `.env.local` file
     - Find: `WHATSAPP_VERIFY_TOKEN=mySuperSecretVerifyToken123`
     - Copy the value: `mySuperSecretVerifyToken123`

   - **Events to subscribe:**
     - ✅ **Message Received** (required)
     - ✅ **Message Status** (optional - for delivery tracking)

5. **Click "Save & Verify"**

**Expected Result:**
```
✅ Webhook verified successfully!
All incoming messages will be forwarded to your webhook.
```

**If verification fails:**
- Check service is running (`curl http://localhost:8000/health`)
- Check ngrok is forwarding correctly
- Check verify token matches exactly
- Check service logs for errors

### **Step 3: Test Webhook**

1. **Send test message from Wati:**
   - Dashboard → **"Messages"** tab
   - Click your test number
   - Type: "Test message"
   - Click send

2. **Reply from your phone:**
   - Open WhatsApp on your phone
   - Reply: "What is the payment plan?"

3. **Check service logs:**
   ```bash
   # You should see:
   [INFO] WhatsApp inbound from +91XXXXXXXXXX | Qualification: 0/4 | Stage: new
   [INFO] ask project=1 mode=docs_expanded latency_ms=2341
   ```

4. **Check WhatsApp:**
   - You should receive bot's response with payment plan details

**If it works:** ✅ Webhook is connected! Proceed to broadcasts.

---

## 📤 How to Send Broadcasts (Wati Dashboard)

### **Prepare Contacts**

#### **Option 1: Manual Entry (Small Lists)**

1. Dashboard → **"Contacts"**
2. Click **"Add Contact"**
3. Enter:
   - Phone: `+919876543210`
   - Name: `Rahul Sharma`
   - Tags: `jan_campaign`, `high_budget`
4. Repeat for each contact

#### **Option 2: CSV Import (Large Lists)**

1. **Create CSV file** (`contacts.csv`):
   ```csv
   name,phone,tags
   Rahul Sharma,+919876543210,jan_campaign;high_budget
   Priya Gupta,+919876543211,jan_campaign;mid_budget
   Amit Kumar,+918888888888,jan_campaign;gurgaon
   ```

2. **Upload to Wati:**
   - Dashboard → **"Contacts"**
   - Click **"Import"** button
   - Upload `contacts.csv`
   - Map columns:
     - Name → Name
     - Phone → Phone
     - Tags → Tags (semicolon separated)
   - Click **"Import"**

3. **Verify import:**
   - Dashboard → **"Contacts"**
   - Filter by tag: `jan_campaign`
   - Should see all imported contacts

---

### **Create & Send Broadcast**

#### **Step 1: Create Broadcast**

1. Dashboard → **"Broadcast"** (megaphone icon)
2. Click **"+ New Broadcast"**
3. **Name your broadcast:**
   - Internal name: "Jan 2025 - Luxury Properties"

#### **Step 2: Write Message**

**Important:** For business-initiated messages, use approved templates OR send during 24-hour window.

**Option A: Using Template (Recommended)**

Wati provides pre-approved templates. Click **"Use Template"**:

```
Hello {{name}}! 👋

We have exclusive luxury properties in Gurgaon:
✨ Premium 3/4 BHK units
🏗️ Ready to move-in
💰 Investment starting ₹3.5Cr

Interested in learning more?
Reply "YES" for detailed brochure!

- Team InvestoChat
```

**Variables:**
- `{{name}}` - Auto-fills from contact name
- `{{custom1}}`, `{{custom2}}` - Custom fields

**Option B: Plain Text (Only works if user messaged you first in last 24h)**

For follow-up messages to engaged users:
```
Hi {{name}},

You showed interest in our Gurgaon properties.

We have 2 new units available this week:
• 3 BHK - ₹3.8Cr (South facing)
• 4 BHK - ₹5.2Cr (Penthouse)

Want to schedule a site visit? Reply YES!
```

#### **Step 3: Select Recipients**

**By Tags:**
- Click **"Select Recipients"**
- Choose **"By Tags"**
- Select: `jan_campaign`
- Preview count: "250 contacts selected"

**By Contact List:**
- Choose **"All Contacts"** OR
- Choose **"Custom List"** → Upload CSV

**Exclude:**
- Contacts who replied in last 7 days (avoid spam)
- Contacts with tag `opted_out`

#### **Step 4: Schedule or Send**

**Send Now:**
- Click **"Send Now"**
- Confirm: "Send to 250 contacts?"
- Click **"Yes, Send"**

**Schedule for Later:**
- Click **"Schedule"**
- Choose date & time (e.g., Tomorrow 10:00 AM)
- Click **"Schedule Broadcast"**

**Best Times:**
- **10:00 AM** - Morning coffee time (high open rate)
- **6:00 PM** - Post-work (high engagement)
- **Avoid:** Before 9 AM, after 9 PM (poor response)

#### **Step 5: Monitor Results**

1. **Dashboard → "Broadcast"** → Select your broadcast
2. **View metrics:**
   - **Sent:** 250
   - **Delivered:** 245 (98%)
   - **Read:** 180 (72%)
   - **Replied:** 25 (10%)

3. **Check responses:**
   - Dashboard → **"Messages"**
   - Filter by broadcast: "Jan 2025 - Luxury Properties"
   - See all replies

**Important:** Responses are automatically forwarded to your webhook!
- Your chatbot handles qualification
- Qualified leads sync to Airtable
- No manual action needed

---

## 📊 After Broadcast: What Happens Automatically

### **User Replies "YES"**

```
User: YES

[Your webhook receives message]

Bot: Great! Before I share property details, let me understand your needs.

💰 What is your investment budget range?

Examples:
• ₹2-3 Crore
• ₹3-5 Crore
• ₹5+ Crore
• ₹10+ Crore
```

**→ Starts 4-question qualification automatically**

### **User Asks Property Question**

```
User: What's the payment plan for The Sanctuaries?

[Your webhook retrieves answer from database]

Bot: The payment plan is structured as:
- EOI: 5%
- Allotment & ATS (within 30 days): 25%
- Prior to Registry (within 60 days): 50%
- Registry and Possession (within 90 days): 20%
Total: 100%

Source: The_Sanctuaries.pdf (p.31)
```

**→ RAG system answers automatically**

### **Qualified Lead Requests Broker**

After completing 4 qualification questions (4/4 score):

```
User: I want to speak with someone

[Your webhook detects broker request + qualified status]

Bot: 🎯 Perfect! I'm connecting you with our investment advisor now.

One of our experts will reach out to you within the next 2 hours (during business hours) to discuss:
• Personalized property recommendations
• Site visit scheduling
• Payment plan customization
• Any specific questions you have

In the meantime, feel free to ask me any questions about the properties!

Your Reference ID: +919876543210
```

**→ Auto-synced to Airtable CRM**
**→ Your team sees new qualified lead**

---

## 🎯 Best Practices for Broadcasts

### **DO's ✅**

1. **Get consent first**
   - Only send to contacts who opted in
   - Track consent source (website form, event, etc.)

2. **Personalize messages**
   - Use `{{name}}` variable
   - Segment by interest (Gurgaon vs Noida)
   - Reference previous interactions

3. **Send at right time**
   - **Best:** 10 AM or 6 PM on weekdays
   - **Avoid:** Weekends, holidays, night time

4. **Clear call-to-action**
   - "Reply YES for brochure"
   - "Reply VISIT for site tour"
   - "Call us at +91-XXXX-XXXX"

5. **Track & optimize**
   - Monitor reply rates
   - A/B test different messages
   - Adjust based on performance

### **DON'Ts ❌**

1. **Don't spam**
   - Max 1 message per week per contact
   - Respect opt-outs immediately

2. **Don't send generic messages**
   - Avoid: "Dear customer, we have offers"
   - Better: "Hi Rahul, your preferred 3 BHK in Sector 89 is now available"

3. **Don't over-promise**
   - Be realistic about prices, timelines
   - No fake urgency ("Last unit! Only today!")

4. **Don't send at bad times**
   - Never before 9 AM or after 9 PM
   - Avoid Monday mornings, Friday evenings

5. **Don't ignore responses**
   - Your chatbot handles this automatically
   - But monitor Airtable for qualified leads
   - Broker should call within 2 hours as promised

---

## 📈 Expected Results

**Typical Campaign (1,000 contacts):**

| Metric | Rate | Count |
|--------|------|-------|
| **Sent** | 100% | 1,000 |
| **Delivered** | 95-98% | 970 |
| **Read** | 60-80% | 700 |
| **Replied** | 5-10% | 70 |
| **Qualified** | 40% of replies | 28 |
| **Deals** | 10% of qualified | 2-3 |

**Revenue:**
- 2.5 deals × ₹2.5L commission = **₹6.25L**

**Cost:**
- Wati: ₹4,999/month
- **ROI: 1,250%**

---

## 🔧 Troubleshooting

### **"Webhook not verified"**

**Symptoms:**
- Wati shows ❌ "Verification failed"
- Can't save webhook URL

**Solutions:**
1. Check service is running:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

2. Check verify token matches:
   - Wati webhook settings
   - `.env.local` file: `WHATSAPP_VERIFY_TOKEN`
   - Must be **exact match** (case-sensitive)

3. Check URL is accessible:
   - If using ngrok: Make sure ngrok is running
   - If using Render: Check deployment status
   - Test: `curl https://your-domain.com/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=YOUR_TOKEN`
   - Should return: `test`

### **"Messages not reaching chatbot"**

**Symptoms:**
- User replies but no response
- Logs show no incoming webhook calls

**Solutions:**
1. Check webhook is enabled in Wati:
   - Settings → Integrations → Webhook
   - Should show ✅ "Active"

2. Check event subscription:
   - Must subscribe to "Message Received" event

3. Check service logs:
   ```bash
   # Should see:
   [INFO] WhatsApp inbound from +91...
   ```

4. Test webhook manually:
   ```bash
   curl -X POST https://your-domain.com/whatsapp/webhook \
     -H "Content-Type: application/json" \
     -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"919876543210","type":"text","text":{"body":"test"}}],"contacts":[{"profile":{"name":"Test"}}]}}]}]}'
   ```

### **"Bot not qualifying leads"**

**Symptoms:**
- User replies but no qualification questions
- Goes straight to Q&A mode

**Solutions:**
1. Check qualification triggers:
   - First-time users should get qualification after 1-2 messages
   - Check `should_start_qualification()` logic

2. Check database:
   ```bash
   docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
     "SELECT phone, qualification_score, conversation_stage FROM lead_qualification WHERE phone = '+919876543210';"
   ```

3. Check lead creation:
   - Every new number should create lead entry
   - If missing, check `get_or_create_lead()` function

### **"No responses from bot"**

**Symptoms:**
- User sends message
- Webhook receives it
- But no reply sent

**Solutions:**
1. Check project routing:
   - File: `workspace/whatsapp_routes.json`
   - User's number should map to project ID
   - OR set `DEFAULT_PROJECT_ID` in `.env`

2. Check data exists:
   ```bash
   docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
     "SELECT COUNT(*) FROM documents WHERE project_id = 1;"
   # Should return > 0
   ```

3. Check Wati credentials:
   - If you configured Wati API tokens, they might be interfering
   - For Wati UI only, you don't need `WATI_API_TOKEN`
   - Only need: `WHATSAPP_VERIFY_TOKEN`

---

## 📞 Support Contacts

**Wati Support:**
- Email: support@wati.io
- WhatsApp: Available in dashboard
- Phone: +91-XXXX-XXXX (check dashboard)
- Response time: <2 hours (business hours)

**Your Service Issues:**
- Check service logs: `docker compose logs -f`
- Check database: Connect via Adminer (localhost:8080)
- Check Airtable: Verify webhook configuration

---

## ✅ Quick Reference: Common Tasks

### **Send a Broadcast**
1. Wati Dashboard → Broadcast
2. New Broadcast → Write message
3. Select recipients by tag
4. Send Now or Schedule

### **View Responses**
1. Wati Dashboard → Messages
2. Filter by broadcast name
3. Click contact to see conversation

### **Check Qualified Leads**
1. Open Airtable (if configured)
2. Go to "Qualified Leads" table
3. Sort by "Created" date (newest first)
4. Assign to broker

### **View Conversation History**
```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT created_at, role, message FROM conversation_history
   WHERE phone = '+919876543210'
   ORDER BY created_at DESC LIMIT 10;"
```

### **Update Webhook URL**
1. Wati Settings → Integrations → Webhook
2. Update URL
3. Save & Verify

---

## 🎉 You're All Set!

**What you do:**
- Upload contacts to Wati
- Write message in dashboard
- Click "Send Broadcast"

**What happens automatically:**
- Wati sends messages
- Users reply
- Your chatbot qualifies leads
- Qualified leads go to Airtable
- Your team closes deals

**No coding. No complexity. Just results.** 🚀
