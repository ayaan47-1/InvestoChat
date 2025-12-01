# InvestoChat Testing Guide

**Purpose**: Verify the lead qualification system works end-to-end before production launch

**Time Required**: 30-45 minutes

---

## Pre-Testing Checklist

Before you start testing, ensure:

- [ ] Database schema applied (both main and qualification schemas)
- [ ] `.env.local` configured with all credentials
- [ ] API service running (`uvicorn service:app --reload`)
- [ ] Airtable base created with 4 tables
- [ ] At least 1 project ingested with brochure data
- [ ] Test WhatsApp number available

---

## Test Suite 1: Database & Schema Validation

### Test 1.1: Verify Tables Exist

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```

**Expected Output**:
```
 public | brokers               | table | investochat
 public | conversation_history  | table | investochat
 public | deals                 | table | investochat
 public | documents             | table | investochat
 public | facts                 | table | investochat
 public | lead_assignments      | table | investochat
 public | lead_qualification    | table | investochat
 public | ocr_pages             | table | investochat
 public | projects              | table | investochat
```

**Status**: [ ] Pass [ ] Fail

---

### Test 1.2: Verify Triggers Work

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

```sql
-- Insert test lead with only 2 fields
INSERT INTO lead_qualification (phone, name, budget, area_preference)
VALUES ('+919999999990', 'Test User', '₹3-5 Cr', 'Gurgaon Sector 89');

-- Check if qualification_score auto-calculated
SELECT phone, name, budget, area_preference, qualification_score, is_qualified
FROM lead_qualification
WHERE phone = '+919999999990';

-- Expected: qualification_score = 2, is_qualified = FALSE

-- Now add remaining fields
UPDATE lead_qualification
SET timeline = '1-3 months', unit_preference = '3BHK'
WHERE phone = '+919999999990';

-- Check again
SELECT phone, qualification_score, is_qualified, qualified_at
FROM lead_qualification
WHERE phone = '+919999999990';

-- Expected: qualification_score = 4, is_qualified = TRUE, qualified_at = <timestamp>

-- Clean up
DELETE FROM lead_qualification WHERE phone = '+919999999990';
```

**Status**: [ ] Pass [ ] Fail

---

### Test 1.3: Verify Deal Commission Calculation

```sql
-- Insert test deal
INSERT INTO deals (phone, deal_value, broker_commission_percent, investochat_percent)
VALUES ('+919999999990', 50000000, 2.00, 25.00);

-- Check auto-calculated commissions
SELECT
    deal_value,
    broker_commission_amount,  -- Expected: 1000000 (₹10L)
    investochat_commission     -- Expected: 250000 (₹2.5L)
FROM deals
WHERE phone = '+919999999990';

-- Clean up
DELETE FROM deals WHERE phone = '+919999999990';
```

**Status**: [ ] Pass [ ] Fail

---

## Test Suite 2: Airtable Integration

### Test 2.1: Connection Test

```bash
cd InvestoChat_Build
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

print('AIRTABLE_API_KEY:', 'SET' if os.getenv('AIRTABLE_API_KEY') else 'MISSING')
print('AIRTABLE_BASE_ID:', 'SET' if os.getenv('AIRTABLE_BASE_ID') else 'MISSING')

try:
    from pyairtable import Api
    api = Api(os.getenv('AIRTABLE_API_KEY'))
    base = api.base(os.getenv('AIRTABLE_BASE_ID'))
    print('Airtable connection: SUCCESS')
except Exception as e:
    print('Airtable connection: FAILED -', str(e))
"
```

**Expected Output**:
```
AIRTABLE_API_KEY: SET
AIRTABLE_BASE_ID: SET
Airtable connection: SUCCESS
```

**Status**: [ ] Pass [ ] Fail

---

### Test 2.2: Sync Test Lead

```bash
python -c "
from airtable_crm import sync_qualified_lead

test_lead = {
    'phone': '+919999999991',
    'name': 'Airtable Test User',
    'budget': '₹5+ Crore',
    'area_preference': 'Noida Extension',
    'timeline': 'Immediate',
    'unit_preference': '4BHK',
    'qualification_score': 4
}

record_id = sync_qualified_lead(test_lead)
print('Record created in Airtable:', record_id)
"
```

**Manual Verification**:
1. Open your Airtable base
2. Go to "Qualified Leads" table
3. You should see a new row with:
   - Phone: +919999999991
   - Name: Airtable Test User
   - Status: 🔥 Qualified - Pending Assignment

**Status**: [ ] Pass [ ] Fail

---

### Test 2.3: Update Status Test

```bash
python -c "
from airtable_crm import update_lead_status

success = update_lead_status(
    phone='+919999999991',
    status='👤 Assigned to Broker',
    notes='Assigned to Test Broker for verification'
)

print('Status updated:', success)
"
```

**Manual Verification**:
- Refresh Airtable
- Status should now be "👤 Assigned to Broker"
- Notes field should have timestamp + message

**Status**: [ ] Pass [ ] Fail

---

### Test 2.4: Log Activity Test

```bash
python -c "
from airtable_crm import log_activity

log_activity(
    phone='+919999999991',
    activity_type='Qualified',
    description='Test lead completed all 4 qualification questions'
)

print('Activity logged successfully')
"
```

**Manual Verification**:
- Go to "Activity Log" table in Airtable
- You should see new entry with phone, activity type, description, timestamp

**Status**: [ ] Pass [ ] Fail

---

## Test Suite 3: Lead Qualification Module

### Test 3.1: Create Lead

```bash
python -c "
from lead_qualification import get_or_create_lead

lead = get_or_create_lead(phone='+919999999992', name='Module Test User')
print('Lead created:')
print('  Phone:', lead['phone'])
print('  Name:', lead['name'])
print('  Qualification Score:', lead['qualification_score'])
print('  Is Qualified:', lead['is_qualified'])
print('  Stage:', lead['conversation_stage'])
"
```

**Expected Output**:
```
Lead created:
  Phone: +919999999992
  Name: Module Test User
  Qualification Score: 0
  Is Qualified: False
  Stage: initial
```

**Status**: [ ] Pass [ ] Fail

---

### Test 3.2: Get Next Question

```bash
python -c "
from lead_qualification import get_next_question

next_q = get_next_question(phone='+919999999992')
print('Next question field:', next_q[0])
print('Question text:')
print(next_q[1])
"
```

**Expected Output**:
```
Next question field: budget
Question text:
💰 What is your investment budget range?

Examples:
• ₹2-3 Crore
• ₹3-5 Crore
• ₹5+ Crore
```

**Status**: [ ] Pass [ ] Fail

---

### Test 3.3: Process Valid Answer

```bash
python -c "
from lead_qualification import start_qualification_flow, process_qualification_answer

# Start qualification
first_q = start_qualification_flow('+919999999992')
print('Started qualification, first question:', first_q[:50], '...')

# Answer budget question
result = process_qualification_answer(
    phone='+919999999992',
    answer='₹5+ Crore'
)

print('\nResult status:', result['status'])
print('Next field:', result.get('field'))
print('Message preview:', result['message'][:100], '...')
"
```

**Expected Output**:
```
Started qualification, first question: 💰 What is your investment budget range? ...

Result status: continue
Next field: area_preference
Message preview: ✅ Got it!

📍 Which areas are you considering for investment? ...
```

**Status**: [ ] Pass [ ] Fail

---

### Test 3.4: Complete Qualification

```bash
python -c "
from lead_qualification import process_qualification_answer, get_or_create_lead

# Answer remaining questions
questions = [
    ('area_preference', 'Gurgaon Sector 89'),
    ('timeline', 'Immediate'),
    ('unit_preference', '4BHK')
]

for field, answer in questions:
    # Update last_question_asked
    import psycopg, os
    with psycopg.connect(os.getenv('DATABASE_URL')) as conn, conn.cursor() as cur:
        cur.execute(
            'UPDATE lead_qualification SET last_question_asked = %s WHERE phone = %s',
            (field, '+919999999992')
        )
        conn.commit()

    result = process_qualification_answer('+919999999992', answer)
    print(f'{field}: {result[\"status\"]}')

# Check final state
lead = get_or_create_lead('+919999999992')
print('\nFinal state:')
print('  Qualification Score:', lead['qualification_score'])
print('  Is Qualified:', lead['is_qualified'])
print('  Stage:', lead['conversation_stage'])
"
```

**Expected Output**:
```
area_preference: continue
timeline: continue
unit_preference: qualified

Final state:
  Qualification Score: 4
  Is Qualified: True
  Stage: qualified
```

**Status**: [ ] Pass [ ] Fail

---

### Test 3.5: Broker Connect Detection

```bash
python -c "
from lead_qualification import is_broker_connect_request

test_cases = [
    ('yes', True),
    ('YES', True),
    ('Yes please', True),
    ('I want to talk to an advisor', True),
    ('connect me with broker', True),
    ('What is the price?', False),
    ('No thanks', False)
]

for message, expected in test_cases:
    result = is_broker_connect_request(message)
    status = '✓' if result == expected else '✗'
    print(f'{status} \"{message}\" -> {result} (expected {expected})')
"
```

**Expected Output**: All ✓

**Status**: [ ] Pass [ ] Fail

---

## Test Suite 4: API Endpoints

### Test 4.1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Output**:
```json
{"status":"ok"}
```

**Status**: [ ] Pass [ ] Fail

---

### Test 4.2: Ask Endpoint

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the price per sq.ft for Godrej SORA?",
    "project_id": 1,
    "k": 3
  }'
```

**Expected Output**:
```json
{
  "answer": "The price per sq.ft for Godrej SORA is ₹12,500-15,000...",
  "mode": "facts",
  "sources": [...],
  "latency_ms": 1500
}
```

**Status**: [ ] Pass [ ] Fail

---

### Test 4.3: Retrieve Endpoint

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "question": "payment plan",
    "project_id": 1,
    "k": 5
  }'
```

**Expected Output**:
```json
{
  "mode": "tables",
  "chunks": [...],
  "latency_ms": 800
}
```

**Status**: [ ] Pass [ ] Fail

---

## Test Suite 5: WhatsApp Webhook (Simulation)

### Test 5.1: Webhook Verification

```bash
curl "http://localhost:8000/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=YOUR_VERIFY_TOKEN"
```

**Expected Output**:
```
test123
```

(Or 403 if verify token doesn't match)

**Status**: [ ] Pass [ ] Fail

---

### Test 5.2: Message Reception

```bash
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "What is the price for 3BHK?"}
          }],
          "contacts": [{
            "profile": {"name": "Webhook Test User"}
          }]
        }
      }]
    }]
  }'
```

**Expected Output**:
```json
{"status":"sent","mode":"facts"}
```

**Manual Verification**:
- Check database: `SELECT * FROM lead_qualification WHERE phone = '+919999999993';`
- Should have new lead with qualification_score = 0
- Check conversation_history table for logged message

**Status**: [ ] Pass [ ] Fail

---

### Test 5.3: Qualification Trigger

Send second message from same number:

```bash
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "What are the payment plans?"}
          }],
          "contacts": [{
            "profile": {"name": "Webhook Test User"}
          }]
        }
      }]
    }]
  }'
```

**Expected**: Status should be "qualification_started"

**Manual Verification**:
```sql
SELECT conversation_stage, last_question_asked
FROM lead_qualification
WHERE phone = '+919999999993';
```

Should show: `conversation_stage = 'qualifying'`, `last_question_asked = 'budget'`

**Status**: [ ] Pass [ ] Fail

---

### Test 5.4: Full Qualification Flow

Continue with qualification answers:

```bash
# Answer 1: Budget
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "₹3-5 Crore"}
          }],
          "contacts": [{"profile": {"name": "Webhook Test User"}}]
        }
      }]
    }]
  }'

# Answer 2: Area
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "Gurgaon Sector 89"}
          }],
          "contacts": [{"profile": {"name": "Webhook Test User"}}]
        }
      }]
    }]
  }'

# Answer 3: Timeline
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "1-3 months"}
          }],
          "contacts": [{"profile": {"name": "Webhook Test User"}}]
        }
      }]
    }]
  }'

# Answer 4: Unit Type (should qualify!)
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "3BHK"}
          }],
          "contacts": [{"profile": {"name": "Webhook Test User"}}]
        }
      }]
    }]
  }'
```

**Expected**: Last response should return `{"status":"qualified"}`

**Manual Verification**:
1. Database:
```sql
SELECT phone, qualification_score, is_qualified, conversation_stage
FROM lead_qualification
WHERE phone = '+919999999993';
```
Should show: score=4, is_qualified=TRUE, stage='qualified'

2. Airtable:
- Check "Qualified Leads" table
- Should see lead with all 4 fields filled, Status = "🔥 Qualified - Pending Assignment"

**Status**: [ ] Pass [ ] Fail

---

### Test 5.5: Broker Handoff

```bash
curl -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "type": "text",
            "from": "+919999999993",
            "text": {"body": "Yes, connect me"}
          }],
          "contacts": [{"profile": {"name": "Webhook Test User"}}]
        }
      }]
    }]
  }'
```

**Expected**: `{"status":"broker_handoff"}`

**Manual Verification**:
- Airtable "Qualified Leads" table
- Status should update to "📞 Requested Broker Call"
- Activity Log should have entry: "Broker Request"

**Status**: [ ] Pass [ ] Fail

---

## Test Suite 6: End-to-End with Real WhatsApp

**Prerequisites**:
- WhatsApp webhook configured and verified
- Test WhatsApp number available

### Test 6.1: Send Real Message

1. From your test WhatsApp number, send message to your business number:
   ```
   What is the price for 3BHK at Godrej SORA?
   ```

2. **Expected**: Bot responds with price information within 5 seconds

**Status**: [ ] Pass [ ] Fail

---

### Test 6.2: Trigger Qualification

2. Send second message:
   ```
   What are the payment plans?
   ```

3. **Expected**: Bot sends qualification intro + first question (Budget)

**Status**: [ ] Pass [ ] Fail

---

### Test 6.3: Complete Qualification

4. Answer questions in sequence:
   - `₹5+ Crore`
   - `Noida Extension`
   - `Immediate`
   - `4BHK`

5. **Expected**: After 4th answer, bot sends completion message with investment profile summary

**Status**: [ ] Pass [ ] Fail

---

### Test 6.4: Request Broker

6. Reply: `YES`

7. **Expected**: Bot sends broker handoff message

**Status**: [ ] Pass [ ] Fail

---

### Test 6.5: Verify in Airtable

8. Check Airtable:
   - Lead should be in "Qualified Leads" table
   - All 4 qualification fields filled
   - Status = "📞 Requested Broker Call"
   - Activity Log has entries

**Status**: [ ] Pass [ ] Fail

---

## Test Results Summary

### Database Tests
- [ ] 1.1 Tables exist
- [ ] 1.2 Triggers work (auto-calculate qualification_score)
- [ ] 1.3 Commission calculation

### Airtable Tests
- [ ] 2.1 Connection successful
- [ ] 2.2 Sync test lead
- [ ] 2.3 Update status
- [ ] 2.4 Log activity

### Lead Qualification Module Tests
- [ ] 3.1 Create lead
- [ ] 3.2 Get next question
- [ ] 3.3 Process valid answer
- [ ] 3.4 Complete qualification
- [ ] 3.5 Broker connect detection

### API Endpoint Tests
- [ ] 4.1 Health check
- [ ] 4.2 Ask endpoint
- [ ] 4.3 Retrieve endpoint

### WhatsApp Webhook Tests (Simulation)
- [ ] 5.1 Webhook verification
- [ ] 5.2 Message reception
- [ ] 5.3 Qualification trigger
- [ ] 5.4 Full qualification flow
- [ ] 5.5 Broker handoff

### Real WhatsApp Tests
- [ ] 6.1 Send real message
- [ ] 6.2 Trigger qualification
- [ ] 6.3 Complete qualification
- [ ] 6.4 Request broker
- [ ] 6.5 Verify in Airtable

---

## Cleanup After Testing

```bash
# Clean up test leads from database
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB << EOF
DELETE FROM conversation_history WHERE phone LIKE '+9199999999%';
DELETE FROM lead_qualification WHERE phone LIKE '+9199999999%';
DELETE FROM deals WHERE phone LIKE '+9199999999%';
EOF
```

**In Airtable**:
- Delete test records from "Qualified Leads" table
- Delete test records from "Activity Log" table

---

## Troubleshooting

### Tests Failing?

**If Database Tests Fail**:
- Check if schema was applied: `\dt` in psql
- Re-run `schema_qualification.sql`
- Check PostgreSQL logs: `docker compose logs db`

**If Airtable Tests Fail**:
- Verify API key and Base ID in `.env.local`
- Check table names match exactly (case-sensitive!)
- Ensure `pyairtable` installed: `pip list | grep pyairtable`

**If API Tests Fail**:
- Check service is running: `curl http://localhost:8000/health`
- Check logs: `tail -f logs/service.log`
- Verify `.env.local` loaded: `python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); print(os.getenv('DATABASE_URL')[:20])"`

**If WhatsApp Tests Fail**:
- Check webhook URL is accessible (use ngrok for local testing)
- Verify verify token matches in WhatsApp platform and `.env.local`
- Check WhatsApp webhook logs in platform dashboard

---

## Production Readiness Checklist

After all tests pass:

- [ ] All 26 tests passing
- [ ] Database triggers working correctly
- [ ] Airtable syncing reliably
- [ ] WhatsApp messages delivering within 5 seconds
- [ ] Partner can view leads in Airtable
- [ ] Broker handoff flow working
- [ ] Commission calculations accurate
- [ ] No errors in logs during test runs

**When all checkboxes are ticked, you're ready for production launch!** 🚀

---

**Testing Duration**: 30-45 minutes

**Frequency**: Run full test suite before every production deployment

**Regression Testing**: Run Tests 1.2, 2.2, 3.4, 5.4, and 6.3 weekly to catch regressions early.
