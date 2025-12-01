# HNI Investment Platform - Deployment Guide

**Target Audience**: High Net Worth Individuals (HNI) in NCR region (Delhi, Gurgaon, Noida)
**Use Case**: Real estate investment opportunities, not end-user home purchases
**Last Updated**: 2025-01-17

---

## 🎯 HNI Investor Profile

### What Makes HNI Queries Different

**HNI Investors Ask About:**
- ✅ Price per sq.ft., ROI, rental yields
- ✅ CLP/PLP payment structures
- ✅ RERA compliance, builder track record
- ✅ Possession timelines, carpet vs super area
- ✅ Investment comparison across projects
- ❌ NOT: Vastu, interior design, clubhouse details

**Expected Response Quality:**
- **Data-driven**: Exact numbers, percentages, dates
- **Professional**: No marketing fluff, concise answers
- **Sourced**: Page references for all claims
- **Fast**: < 3 seconds response time
- **Accurate**: "Not in brochure" > wrong information

---

## 📊 Critical Data Requirements

### 1. **Investment-Focused Facts** (Priority 1)

Add these to `facts` table for **every project**:

```sql
-- Run for each project (replace project_id and values)
INSERT INTO facts (project_id, key, value, source_page, embedding) VALUES

-- Pricing (CRITICAL for HNIs)
(1, 'price_per_sqft', '₹12,500-15,000 per sq.ft. (varies by floor/unit)', 'p.8', <embedding>),
(1, 'total_price_range', '₹1.85 Cr - ₹3.50 Cr', 'p.8', <embedding>),

-- Possession (CRITICAL - affects financial planning)
(1, 'possession_date', 'December 2026 (36 months from booking)', 'p.3', <embedding>),
(1, 'construction_status', 'Under construction - 40% complete as of Jan 2025', 'site visit', <embedding>),

-- Compliance (CRITICAL - HNI due diligence)
(1, 'rera_number', 'RC/REP/HARERA/GGM/767/499/2023/48', 'p.2', <embedding>),
(1, 'rera_status', 'RERA registered and approved', 'p.2', <embedding>),

-- Developer (trust factor)
(1, 'builder_name', 'Godrej Properties', 'p.1', <embedding>),
(1, 'builder_experience', '25+ years, 80+ projects delivered across India', 'p.1', <embedding>),

-- Payment (financial planning)
(1, 'payment_plan_summary', 'CLP: 20-80 (20% booking, 80% on possession) | PLP: 10-10-80', 'p.12', <embedding>),
(1, 'booking_amount', '₹5 lakhs (refundable within 15 days)', 'p.12', <embedding>),

-- Investment metrics (if available)
(1, 'expected_rental_yield', '3.5-4.2% annually based on Sector 89 market rates', 'market analysis', <embedding>),
(1, 'appreciation_potential', '8-12% CAGR based on Gurgaon Sector 89 historical data', 'market analysis', <embedding>),
(1, 'occupancy_certificate_eta', 'Expected Q2 2027 (6 months post possession)', 'developer timeline', <embedding>);
```

**How to Add:**
```bash
# Use setup_db.py to add facts
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 \
  --key "price_per_sqft" \
  --value "₹12,500-15,000 per sq.ft." \
  --source-page "p.8"
```

---

### 2. **Tables Must Include** (Priority 1)

Ensure these table types exist for each project:

#### Payment Plan Table
```markdown
| Milestone | Percentage | Amount (for ₹2.5Cr unit) | Timeline |
|-----------|------------|--------------------------|----------|
| Booking   | 20%        | ₹50 lakhs                | At booking |
| On Possession | 80%    | ₹2 crores                | Dec 2026 |
```

**Required fields**: milestone, percentage, timing, amount calculation

#### Unit Specifications Table
```markdown
| Unit Type | Carpet Area | Super Area | Balcony | Price Range |
|-----------|-------------|------------|---------|-------------|
| 2 BHK     | 1,250 sq.ft | 1,650 sq.ft | 150 sq.ft | ₹2.06-2.48 Cr |
| 3 BHK     | 1,850 sq.ft | 2,350 sq.ft | 200 sq.ft | ₹2.94-3.53 Cr |
```

**Required fields**: unit type, carpet area, super area, price

#### Pricing Table (if available)
```markdown
| Floor Range | 2 BHK Price | 3 BHK Price | Premium % |
|-------------|-------------|-------------|-----------|
| 1-5         | ₹2.06 Cr    | ₹2.94 Cr    | Base      |
| 6-10        | ₹2.18 Cr    | ₹3.12 Cr    | +6%       |
| 11-15       | ₹2.31 Cr    | ₹3.30 Cr    | +12%      |
```

---

### 3. **Query Examples - HNI Focus**

Test your system with these actual HNI queries:

```python
# Investment-focused
"What is the price per square foot?"
"What is the expected rental yield for 3BHK?"
"What is the ROI if I invest now?"

# Due diligence
"Is this RERA approved? What's the number?"
"When is the possession date?"
"Who is the builder and what's their track record?"

# Financial planning
"What are the CLP payment milestones?"
"How much is the booking amount?"
"Can I get flexi payment or subvention?"

# Unit comparison
"What's the carpet area vs super area for 2BHK?"
"Compare 2BHK and 3BHK pricing"
"What's the price difference between floor 5 and floor 12?"

# Timing
"When will I get possession?"
"How much time to complete payment under CLP?"
"When can I start getting rental income?"
```

---

## 🚀 System Optimizations for HNI

### Already Implemented ✅

1. **Query Expansion** - Investment vocabulary (ROI, yield, appreciation)
2. **Professional LLM Prompt** - Data-driven, concise, cited responses
3. **Tables Retrieval** - Prioritizes structured data (payment, pricing)
4. **HNI Test Queries** - 7 new investment-focused test cases

### Still Need To Do 📋

1. **Populate Facts Table** - Add investment data for all 6 projects
2. **Verify Tables** - Ensure payment/pricing/specs tables exist
3. **Test HNI Queries** - Run `python evaluate.py --category hni_investment`
4. **WhatsApp Setup** - Choose Wati vs Direct API

---

## 💬 WhatsApp Strategy for HNIs

### Recommended: **Wati Growth Plan** (₹4,999/month)

**Why Wati for HNI Platform:**

1. **Professional Image**
   - HNIs judge you by every interaction
   - Reliable delivery, read receipts, typing indicators
   - No "bot is down" excuses

2. **Relationship Management**
   - Tag: "Portfolio >5Cr", "Hot lead", "Repeat investor"
   - Assign to senior investment advisor
   - Track conversation history across months

3. **Multi-Project Comparison**
   - HNI: "Compare payment plans for 3 projects"
   - Bot provides data, human sends Excel comparison
   - Seamless handoff bot → human

4. **Follow-up Campaigns**
   - New launch → Targeted broadcast to HNIs
   - Price revision → Notify interested investors
   - RERA approval → Update all pending queries

5. **Analytics**
   - Which projects get most HNI queries?
   - Average time to conversion
   - Response time tracking (critical for HNIs)

**Setup:**
```
HNI WhatsApp Query
    ↓
Wati (₹4,999/month)
    ├─ AI Bot (instant data) → Your InvestoChat RAG
    └─ Senior Advisor (complex queries) → Human
```

---

## 📈 HNI Conversion Funnel

### Stage 1: Initial Query (Bot)
```
HNI: "What's the price for 3BHK at Godrej Sora?"
Bot: "Godrej Sora 3BHK (1,850 sq.ft):
      - Price: ₹2.94-3.30 Cr (₹12,500-14,000/sq.ft)
      - Varies by floor (6-12% premium for higher floors)
      - As per brochure p.8

      Would you like payment plan details?"
```

### Stage 2: Detailed Info (Bot)
```
HNI: "Yes, show payment plan"
Bot: "Godrej Sora CLP Structure (p.12):
      - Booking: 20% (₹59 lakhs)
      - On possession: 80% (₹2.35 Cr)
      - Possession: Dec 2026
      - RERA: RC/REP/HARERA/GGM/767/499/2023/48

      Connect with investment advisor for site visit?"
```

### Stage 3: Human Takeover
```
HNI: "Yes, schedule site visit"
→ Wati routes to Senior Advisor
→ Advisor sees full chat history
→ Sends calendar invite, comparison sheet, floor plans
→ Marks as "Site Visit Scheduled - High Priority"
```

---

## 🎯 Success Metrics for HNI Platform

### Week 1 (Testing)
- [ ] Facts table populated for all 6 projects
- [ ] HNI test queries passing (>80%)
- [ ] Response time < 3 seconds
- [ ] Wati trial started

### Month 1 (Soft Launch)
- [ ] 50-100 HNI conversations
- [ ] <5% "Not in documents" rate
- [ ] Avg response time < 2 seconds
- [ ] 3-5 site visits booked

### Month 3 (Optimization)
- [ ] 200-300 HNI conversations/month
- [ ] 10-15% lead-to-site-visit conversion
- [ ] 2-3% site-visit-to-booking conversion
- [ ] ROI: 1-2 bookings = ₹2-10L commission

**Target**: If platform enables **1 extra HNI booking per quarter**, it pays for itself 100x over.

---

## 🔧 Quick Start Checklist

### Data Setup (Day 1-2)
```bash
# 1. Add HNI-focused facts for each project
cd InvestoChat_Build
docker compose exec ingest python setup_db.py facts-upsert \
  --project-id 1 --key "price_per_sqft" --value "₹12,500/sq.ft" --source-page "p.8"

# Repeat for: RERA number, possession date, builder name, payment summary

# 2. Verify tables exist
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT project_id, table_type, COUNT(*) FROM document_tables GROUP BY project_id, table_type;"

# Should see: payment_plan, unit_specifications, pricing for each project
```

### Testing (Day 2-3)
```bash
# 3. Test HNI queries
python evaluate.py --category hni_investment --verbose

# 4. Manual testing
python main.py --rag "What is the price per sq.ft for Godrej Sora?" --project-id 4

# Expected: Professional tone, exact numbers, page citations
```

### WhatsApp Setup (Day 3-5)
```bash
# 5. Start Wati trial
Visit: wati.io
Sign up with business number
Choose Growth plan (₹4,999/month)

# 6. Test integration
# Follow docs/WHATSAPP_SETUP.md for Wati-specific setup
```

---

## 💡 HNI Communication Best Practices

### DO:
- ✅ Cite exact page numbers: "As per brochure p.8, ..."
- ✅ Provide ranges when uncertain: "₹12,500-15,000/sq.ft (varies by floor)"
- ✅ State limitations: "Rental yield data not in brochure. Based on market analysis: 3.5-4.2%"
- ✅ Offer human handoff: "Connect with investment advisor for detailed ROI analysis"

### DON'T:
- ❌ Use marketing language: "Luxurious", "Premium lifestyle"
- ❌ Speculate: "Around 3Cr" → Use exact: "₹2.94-3.30 Cr (p.8)"
- ❌ Hide missing data: If not in brochure, say so
- ❌ Over-promise: Stick to documented facts

---

## 📞 Support & Escalation

### Bot Handles (80% of queries):
- Pricing, payment plans, unit specs
- Possession dates, RERA numbers
- Builder info, location details
- Simple comparisons

### Human Handles (20% of queries):
- Multi-project comparisons (complex)
- Negotiation, discounts, offers
- Site visit scheduling
- Loan assistance, legal queries
- Post-booking support

**Escalation Trigger**: If bot says "Connect with investment advisor" → Wati routes to human immediately.

---

## 🎓 Next Steps

1. **Populate facts table** - Use template above
2. **Test HNI queries** - Run `python evaluate.py`
3. **Start Wati trial** - wati.io
4. **Get professor feedback** - Show test results
5. **Go live** - Soft launch with 10-20 HNI contacts

**Goal**: Demonstrate that AI can handle 80% of HNI queries instantly, freeing advisors to focus on high-value relationship building and closures.

---

**Ready to deploy?** Start with facts population - that's your highest-impact activity for HNI accuracy.
