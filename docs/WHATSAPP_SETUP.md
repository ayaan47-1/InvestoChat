# WhatsApp Business API Setup Guide

Complete guide to connect InvestoChat with WhatsApp Business API.

---

## Prerequisites

- Meta Business Manager account
- Verified business
- Phone number for WhatsApp Business (not currently using WhatsApp)
- Public URL for webhook (ngrok, Render, Railway, etc.)

---

## Step 1: Create Meta Business App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** as app type
4. Fill in app details:
   - App name: `InvestoChat`
   - Contact email: your email
   - Business Manager account: select your business
5. Click **"Create App"**

---

## Step 2: Add WhatsApp Product

1. In your app dashboard, find **"WhatsApp"** in the products list
2. Click **"Set Up"**
3. You'll be guided through the setup wizard

### Configure WhatsApp Business Account

1. Select or create a **WhatsApp Business Account**
2. Add a **phone number** (Meta provides a test number for development)
   - For production: Use your own verified business number
   - For testing: Use Meta's test number

---

## Step 3: Get API Credentials

### 3.1 Get Phone Number ID

1. In WhatsApp dashboard, go to **"API Setup"**
2. Copy the **Phone Number ID** (looks like: `123456789012345`)
3. Save this for your `.env` file

### 3.2 Get Access Token

**For Development (Temporary Token):**
1. In WhatsApp dashboard, go to **"API Setup"**
2. Under **"Temporary access token"**, click **"Copy"**
3. Valid for 24 hours - renew daily during development

**For Production (Permanent Token):**
1. Go to **"Settings"** → **"System Users"**
2. Create a system user with **"Admin"** role
3. Generate a token with these permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
4. Save the token securely (shown only once!)

### 3.3 Create Verify Token

1. Generate a random string for webhook verification:
   ```bash
   openssl rand -hex 32
   ```
2. Save this as your `WHATSAPP_VERIFY_TOKEN`

---

## Step 4: Configure Environment Variables

Add these to `InvestoChat_Build/.env.local`:

```bash
# WhatsApp Business API Configuration
WHATSAPP_VERIFY_TOKEN=your_generated_verify_token_here
WHATSAPP_ACCESS_TOKEN=your_meta_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
DEFAULT_PROJECT_ID=1

# Rate Limiting (optional)
API_RATE_LIMIT=30
WHATSAPP_RATE_LIMIT=12
RATE_LIMIT_WINDOW=60
```

---

## Step 5: Deploy Service with Public URL

Your FastAPI service needs a public URL for Meta to send webhooks.

### Option A: Using ngrok (Development)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your FastAPI service
cd InvestoChat_Build
uvicorn service:app --host 0.0.0.0 --port 8000

# In another terminal, expose it
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Option B: Using Render (Production)

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com/)
3. Connect your repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn service:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Add all variables from `.env.local`
5. Deploy and copy the service URL

### Option C: Using Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`
5. Get URL: `railway domain`

---

## Step 6: Configure Webhook in Meta

1. Go to WhatsApp dashboard → **"Configuration"**
2. Under **"Webhook"**, click **"Edit"**
3. Enter:
   - **Callback URL**: `https://your-domain.com/whatsapp/webhook`
   - **Verify Token**: (the token you generated in Step 3.3)
4. Click **"Verify and Save"**

### Subscribe to Webhook Fields

1. After verification, click **"Manage"**
2. Subscribe to these fields:
   - `messages` ✓

---

## Step 7: Configure Phone Number Routing

Edit `InvestoChat_Build/workspace/whatsapp_routes.json`:

```json
{
  "+919876543210": 1,
  "+919876543211": 2,
  "+919876543212": 3
}
```

- Keys: Phone numbers (with country code)
- Values: Project IDs from your database

Users texting from unmapped numbers will get the `DEFAULT_PROJECT_ID` project.

---

## Step 8: Test the Integration

### Test with Meta Test Number

1. In WhatsApp dashboard → **"API Setup"**
2. Find **"Send and receive messages"** section
3. Add your phone number to test recipients
4. You'll receive a WhatsApp code - verify it
5. Send a test message from your phone to the business number

### Test Webhook Locally

```bash
# Send a test webhook payload
curl -X POST https://your-url.com/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "919876543210",
            "type": "text",
            "text": {"body": "What is the payment plan?"}
          }],
          "contacts": [{"profile": {"name": "Test User"}}]
        }
      }]
    }]
  }'
```

### Check Logs

```bash
# In your service logs, you should see:
# [INFO] WhatsApp inbound from +919876543210 project=1
# [INFO] ask project=1 mode=tables latency_ms=1234
```

---

## Step 9: Monitor and Debug

### View Message Status

1. Go to Meta Business Manager → **"WhatsApp Manager"**
2. Check **"Message Insights"** for delivery status
3. View conversation history

### Common Issues

**Webhook verification fails:**
- Check that `WHATSAPP_VERIFY_TOKEN` matches what you entered in Meta
- Ensure your service is running and accessible
- Check ngrok/deployment logs

**Messages not received:**
- Verify webhook subscription includes `messages` field
- Check that user's phone number is in test recipients (development)
- Review service logs for errors

**"Not in the documents" responses:**
- User's phone not in `whatsapp_routes.json` and no `DEFAULT_PROJECT_ID`
- No data ingested for the mapped project
- Query doesn't match any documents

**Rate limiting:**
- Default: 12 messages per minute per user
- Adjust `WHATSAPP_RATE_LIMIT` in `.env` if needed

---

## Step 10: Go Live (Production)

### 1. Verify Your Business

1. Go to **"Settings"** → **"Business Verification"**
2. Submit business documents
3. Wait for approval (1-3 business days)

### 2. Add Your Business Phone Number

1. Go to **"Phone Numbers"** → **"Add Phone Number"**
2. Enter your business phone (cannot be personal WhatsApp)
3. Verify via SMS code
4. Complete registration

### 3. Request Message Template Approval

For sending proactive messages (not just replies), you need approved templates:

1. Go to **"Message Templates"**
2. Create templates for:
   - Welcome messages
   - Property updates
   - Appointment confirmations
3. Submit for approval

### 4. Switch to Production Token

Replace temporary access token with system user permanent token (from Step 3.2).

### 5. Update Rate Limits

For production, request higher limits from Meta:
1. Go to **"App Settings"** → **"WhatsApp"** → **"Request Increase"**
2. Justify based on expected message volume

---

## Testing Checklist

- [ ] Webhook verification successful
- [ ] Inbound messages received and logged
- [ ] Responses sent back to user
- [ ] Rate limiting works (send 13 messages quickly)
- [ ] PII detection blocks sensitive queries
- [ ] Project routing works correctly
- [ ] "Not in documents" fallback works
- [ ] Source citations included in responses
- [ ] Telemetry logs captured

---

## API Endpoints Reference

### GET /whatsapp/webhook
**Purpose**: Webhook verification (called by Meta)

**Query params:**
- `hub.mode=subscribe`
- `hub.challenge=<random_string>`
- `hub.verify_token=<your_verify_token>`

**Response**: Returns `hub.challenge` if token matches

### POST /whatsapp/webhook
**Purpose**: Receive messages from users

**Payload**: See [WhatsApp webhook format](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples)

**Response**: `{"status": "sent", "mode": "tables"}`

---

## Security Best Practices

1. **Never commit credentials**: Use environment variables
2. **Rotate tokens regularly**: Generate new access tokens monthly
3. **Validate webhook signatures**: (Not implemented yet - TODO)
4. **Use HTTPS only**: Webhook must be HTTPS
5. **Implement rate limiting**: Already configured (12/min)
6. **Log suspicious activity**: Review telemetry for abuse

---

## Cost Estimation

WhatsApp Business API pricing (as of 2024):

- **Service conversations** (user-initiated): Free for first 1,000/month
- **Utility conversations** (bot-initiated with templates): Variable by country
- **Marketing conversations**: Higher rate

For real estate use case (mostly service conversations):
- Expected: 100-500 conversations/month
- Cost: $0-50/month

---

## Support Resources

- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)
- [Webhook Setup Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Pricing](https://developers.facebook.com/docs/whatsapp/pricing)

---

## Troubleshooting

### "Invalid access token"
- Token expired (temporary tokens last 24h)
- Token doesn't have correct permissions
- Using wrong token (test vs production)

### "Message failed to send"
- User blocked the business number
- User's phone invalid or not on WhatsApp
- Rate limit exceeded

### "Webhook not receiving messages"
- Check webhook URL is correct and accessible
- Verify subscription to `messages` field
- Check app is not in development mode restricting recipients

---

**Setup complete!** 🎉

Your InvestoChat bot is now live on WhatsApp. Users can ask questions about real estate projects and get instant answers with source citations.
