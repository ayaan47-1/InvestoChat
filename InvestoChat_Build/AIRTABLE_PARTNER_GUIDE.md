# Airtable CRM Guide for InvestoChat Partner

**For**: Real Estate Partner (Non-Technical)
**Purpose**: Manage qualified leads, assign to brokers, track deals
**Time**: 5-10 minutes/day

---

## What is Airtable?

Think of Airtable as **Excel on steroids** - but easier to use and accessible from your phone.

**You'll use it to**:
- See all qualified leads instantly (name, phone, budget, area preference)
- Assign leads to brokers with one click
- Track deal progress (site visit scheduled → negotiating → closed)
- View monthly commission reports
- Get notified when new leads come in

**No coding required** - everything is point-and-click!

---

## Initial Setup (One-Time, 15 minutes)

### Step 1: Create Account

1. Go to [airtable.com/signup](https://airtable.com/signup)
2. Sign up with your email
3. Choose **Free** plan (sufficient for 100-200 leads/month)
4. Verify email

### Step 2: Create Your Base

1. After signing in, click **"Create a base"**
2. Choose **"Start from scratch"**
3. Name it: `InvestoChat CRM`
4. Choose any color/icon

You'll see an empty table. We'll set this up next.

---

## Setting Up Tables (One-Time, 20 minutes)

You need to create 4 tables. Don't worry - I'll walk you through each one!

### Table 1: Qualified Leads (Main Dashboard)

**This is where you'll spend 90% of your time.**

1. Rename the default table:
   - Click the table name at top left (probably says "Table 1")
   - Change to: `Qualified Leads`

2. Set up columns (click "+" icon to add):

**Column 1**: Rename "Name" to `Phone`
   - Click the column header → Rename
   - Type: Single line text (default)
   - This is your primary identifier

**Column 2**: Add `Name`
   - Click "+" → Single line text
   - For lead's name from WhatsApp

**Column 3**: Add `Budget`
   - Click "+" → Single line text
   - Will show: "₹3-5 Crore", etc.

**Column 4**: Add `Area Preference`
   - Click "+" → Single line text
   - Will show: "Gurgaon Sector 89", etc.

**Column 5**: Add `Timeline`
   - Click "+" → Single line text
   - Will show: "Immediate", "1-3 months", etc.

**Column 6**: Add `Unit Type`
   - Click "+" → Single line text
   - Will show: "3BHK", "4BHK", etc.

**Column 7**: Add `Status`
   - Click "+" → **Single select**
   - Add these options (colors will auto-assign):
     - 🔥 Qualified - Pending Assignment
     - 👤 Assigned to Broker
     - 📞 Broker Contacted
     - 🏢 Site Visit Scheduled
     - 💰 Negotiating
     - ✅ Deal Closed
     - ❌ Lost
   - Set default: "🔥 Qualified - Pending Assignment"

**Column 8**: Add `Qualification Score`
   - Click "+" → Number
   - Format: Integer
   - Will auto-fill with "4" (all qualified leads score 4/4)

**Column 9**: Add `Qualified Date`
   - Click "+" → Date
   - Include time: Yes
   - Auto-fills when lead qualifies

**Column 10**: Add `Assigned Broker`
   - Click "+" → Single line text
   - You'll type broker name here

**Column 11**: Add `Assigned Date`
   - Click "+" → Date

**Column 12**: Add `Source`
   - Click "+" → Single line text
   - Will auto-fill: "WhatsApp Bot"

**Column 13**: Add `Notes`
   - Click "+" → Long text
   - For your internal notes about the lead

Done! Your main dashboard is ready.

---

### Table 2: Deals

**Track closed deals and commission.**

1. Click "+" next to table tabs → Name it: `Deals`

2. Add these columns:

| Column Name | Type | Notes |
|-------------|------|-------|
| Phone | Single line text | Primary field |
| Lead Name | Single line text | |
| Project | Single line text | e.g., "Godrej SORA" |
| Unit Type | Single line text | e.g., "3BHK" |
| Deal Value (₹) | Currency | Choose INR (₹) |
| Broker Commission (₹) | Currency | INR |
| InvestoChat Commission (₹) | Currency | **This is your money!** |
| Closed Date | Date | When deal closed |
| Broker | Single line text | Who closed it |

---

### Table 3: Brokers

**Your broker team directory.**

1. Create table: `Brokers`

2. Add columns:

| Column Name | Type | Notes |
|-------------|------|-------|
| Name | Single line text | Primary field |
| Phone | Phone number | |
| WhatsApp Number | Phone number | |
| Status | Single select | Active / Inactive |
| Areas of Expertise | Long text | "Gurgaon Sector 89, DLF Phase 5" |

3. Add your brokers manually:
   - Click "+ Add record"
   - Fill in: Name, Phone, WhatsApp, Status = Active
   - Repeat for each broker

---

### Table 4: Activity Log

**Automatic log of all activities.**

1. Create table: `Activity Log`

2. Add columns:

| Column Name | Type | Options |
|-------------|------|---------|
| Phone | Phone number | Primary field |
| Activity Type | Single select | Qualified, Broker Request, Assigned, Site Visit, Deal Closed |
| Description | Long text | |
| Timestamp | Date | Include time |

This table auto-fills - you don't need to touch it. Just review for history.

---

## Daily Workflow (5 minutes every morning)

### Your Morning Routine

**Step 1: Open Airtable**
- Go to [airtable.com](https://airtable.com) on laptop
- OR open Airtable app on phone (download from App Store/Play Store)

**Step 2: Check New Qualified Leads**
1. Open `Qualified Leads` table
2. Look for rows with Status: "🔥 Qualified - Pending Assignment"
3. These are NEW leads from last 24 hours

**Step 3: Review Each Lead**

For each 🔥 lead, you'll see:
```
Phone: +919876543210
Name: Rajesh Kumar
Budget: ₹3-5 Crore
Area: Gurgaon Sector 89
Timeline: 1-3 months
Unit Type: 3BHK
Status: 🔥 Qualified - Pending Assignment
```

**Step 4: Assign to Best Broker**

1. Look at "Area Preference"
2. Check your `Brokers` table - who knows that area best?
3. In the lead's row:
   - Click on `Assigned Broker` cell
   - Type broker name: "Rajesh Kumar"
   - Click on `Assigned Date` cell → Select today
   - Click on `Status` dropdown → Select "👤 Assigned to Broker"

**Step 5: Notify Broker** (via WhatsApp/call)

Call or WhatsApp your broker:
```
Hi Rajesh,

New qualified lead for you:

Name: Rajesh Kumar
Phone: +919876543210
Budget: ₹3-5 Crore
Area Interest: Gurgaon Sector 89
Timeline: 1-3 months
Looking for: 3BHK

This lead came through our AI chatbot and answered all qualification questions.
They're serious. Please call within 2 hours.

Thanks!
```

**Step 6: Track Progress**

As broker updates you:
- Broker called lead → Update Status to "📞 Broker Contacted"
- Site visit scheduled → "🏢 Site Visit Scheduled"
- Negotiating price → "💰 Negotiating"
- Deal closed → "✅ Deal Closed" (then log in Deals table)
- Lead went cold → "❌ Lost"

---

## When a Deal Closes (10 minutes)

### Log the Deal

1. Go to `Deals` table
2. Click "+ Add record" at bottom
3. Fill in:
   - **Phone**: +919876543210
   - **Lead Name**: Rajesh Kumar
   - **Project**: Godrej SORA
   - **Unit Type**: 3BHK
   - **Deal Value (₹)**: 50,000,000 (for ₹5 Crore)
   - **Broker Commission (₹)**: 1,000,000 (₹10 Lakh = 2% of deal)
   - **InvestoChat Commission (₹)**: 250,000 (₹2.5 Lakh = 25% of broker commission)
   - **Closed Date**: Select today
   - **Broker**: Rajesh Kumar

4. Update lead status:
   - Go back to `Qualified Leads` table
   - Find the lead's row
   - Update Status to "✅ Deal Closed"

---

## Useful Views (Filters)

Create these views for quick access:

### View 1: New Leads (Needs Assignment)

1. In `Qualified Leads` table, click "Grid view" dropdown → "Create new view"
2. Name: `🔥 New Leads`
3. Click "Filter" → Add filter:
   - Field: Status
   - Condition: is
   - Value: 🔥 Qualified - Pending Assignment
4. Sort by: Qualified Date (newest first)

**Use this view every morning** to see pending work.

---

### View 2: Active Pipeline

1. Create new view: `📊 Active Pipeline`
2. Filter:
   - Status is any of: 👤 Assigned, 📞 Contacted, 🏢 Site Visit, 💰 Negotiating
3. Group by: Status
4. Sort by: Assigned Date

This shows all deals in progress.

---

### View 3: This Month's Closed Deals

1. Go to `Deals` table
2. Create view: `💰 This Month`
3. Filter:
   - Closed Date → is within → this month
4. At bottom, you'll see sum of "InvestoChat Commission (₹)"

**This is your monthly revenue!**

---

## Mobile App Setup (5 minutes)

**Why**: Check leads on-the-go, update status from site visits

1. Download **Airtable** app:
   - [iOS App Store](https://apps.apple.com/app/airtable/id914172636)
   - [Android Play Store](https://play.google.com/store/apps/details?id=com.formagrid.airtable)

2. Sign in with your account

3. Open `InvestoChat CRM` base

4. Pin frequently used views:
   - Click star icon on "🔥 New Leads" view
   - Pin "📊 Active Pipeline"

5. Enable notifications:
   - Settings → Notifications → Allow

Now you'll get push notifications when new leads come in!

---

## Automation Ideas (Advanced)

Once comfortable, set up these automations:

### Auto-Notify on New Lead

1. In Airtable, click "Automations" tab
2. Create automation:
   - **Trigger**: When record enters view "🔥 New Leads"
   - **Action**: Send email to yourself
   - Subject: "New qualified lead: {Name}"
   - Body: Include all lead details

### Weekly Summary Email

1. Create automation:
   - **Trigger**: At scheduled time → Every Monday 9 AM
   - **Action**: Send email
   - Body: "Leads this week: {count}, Deals closed: {count}"

---

## Tips for Success

### Do's ✅
- **Check Airtable every morning** (before 10 AM)
- **Respond to new leads within 1 hour** (HNIs expect speed)
- **Keep Status updated** (so you know pipeline health)
- **Add notes** after broker calls (what lead said, concerns, etc.)
- **Review monthly** (which areas get most leads? which brokers close most?)

### Don'ts ❌
- Don't delete records (even lost leads - keep for analytics)
- Don't forget to log closed deals (that's your revenue tracking!)
- Don't let leads sit unassigned >4 hours (they'll go cold)
- Don't assign all leads to one broker (spread the work)

---

## Common Questions

### Q: How do I know if a new lead came in?
**A**:
- Check "🔥 New Leads" view every morning
- OR set up mobile notifications (see Mobile App section)
- OR create email automation (see Automation section)

### Q: What if broker says lead is not responding?
**A**:
- Update Status to "❌ Lost"
- Add note: "Not responding - tried 3 times"
- Keep record for future analysis

### Q: Can I see history of a lead?
**A**:
- Click on the lead's row in `Qualified Leads`
- Scroll to `Notes` field
- Also check `Activity Log` table - filter by phone number

### Q: How to calculate total commission this month?
**A**:
- Go to `Deals` table
- Use "💰 This Month" view
- Look at bottom of "InvestoChat Commission (₹)" column
- Airtable auto-sums it!

### Q: What if I accidentally delete something?
**A**:
- Don't panic! Airtable has undo
- Press Ctrl+Z (Windows) or Cmd+Z (Mac)
- OR click "Undo" button at top

### Q: Can my accountant access this?
**A**:
- Yes! Click "Share" button (top right)
- Add their email
- Set permission: "Read only" (can view, not edit)

---

## Support

### Need Help?
- **Airtable tutorials**: [airtable.com/guides](https://airtable.com/guides)
- **Video guides**: Search "Airtable basics" on YouTube
- **Support**: support@airtable.com

### Quick Reference Card

**Daily Task** | **How-To** | **Time**
---|---|---
Check new leads | Open "🔥 New Leads" view | 2 min
Assign to broker | Update "Assigned Broker" + "Status" | 1 min
Log closed deal | Add record in "Deals" table | 3 min
Monthly revenue | Check "💰 This Month" view sum | 30 sec

---

## Your First Week Checklist

**Day 1** (Setup):
- [ ] Create Airtable account
- [ ] Set up 4 tables (Qualified Leads, Deals, Brokers, Activity Log)
- [ ] Add your brokers to Brokers table
- [ ] Download mobile app

**Day 2** (Testing):
- [ ] Add a test lead manually (to understand flow)
- [ ] Practice assigning to broker
- [ ] Practice updating status
- [ ] Create "🔥 New Leads" view

**Day 3-7** (Live):
- [ ] Check Airtable every morning
- [ ] Assign new leads within 1 hour
- [ ] Update statuses as brokers report back
- [ ] Review pipeline on Friday (how many in each stage?)

**Week 2**:
- [ ] Log first deal (hopefully!)
- [ ] Set up automations for notifications
- [ ] Teach brokers to update you consistently
- [ ] Review which lead sources work best

---

## Success Stories (What to Expect)

**Month 1**:
- 20-30 qualified leads
- 5-8 site visits scheduled
- 1-2 deals closed
- ₹2.5-5L commission
- ROI: 5-10x (commission vs costs)

**Month 3**:
- 50-70 qualified leads/month
- 15-20 site visits
- 3-5 deals closed
- ₹7.5-12.5L commission/month
- ROI: 15-25x

**Month 6**:
- 100+ leads/month (word spreads in HNI circles)
- 25-30 site visits
- 5-8 deals/month
- ₹12.5-20L commission/month
- Airtable becomes your #1 business tool

---

**Remember**: You don't need to be tech-savvy. If you can use WhatsApp, you can use Airtable!

**Start simple** → Check new leads daily → Assign to brokers → Track status → Log deals

That's it! Everything else is bonus.

Good luck! 🚀
