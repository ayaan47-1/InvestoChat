"""
Airtable CRM Integration for InvestoChat

Syncs qualified leads to Airtable for partner management.
Partner can view leads, assign to brokers, track deals - all without coding.
"""

import os
from typing import Dict, Optional, List
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# Check if Airtable is configured
AIRTABLE_ENABLED = os.getenv("AIRTABLE_API_KEY") is not None
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

if AIRTABLE_ENABLED:
    try:
        from pyairtable import Api
        airtable_api = Api(AIRTABLE_API_KEY)
    except ImportError:
        print("[WARNING] pyairtable not installed. Run: pip install pyairtable")
        AIRTABLE_ENABLED = False

# =====================================================
# Table Names (must match Airtable base)
# =====================================================

LEADS_TABLE = "Qualified Leads"
DEALS_TABLE = "Deals"
BROKERS_TABLE = "Brokers"
ACTIVITIES_TABLE = "Activity Log"

# =====================================================
# Airtable Sync Functions
# =====================================================

def sync_qualified_lead(lead_data: Dict) -> Optional[str]:
    """
    Sync qualified lead to Airtable.

    Args:
        lead_data: Dict with phone, name, budget, area_preference, timeline, unit_preference

    Returns:
        Airtable record ID or None if disabled/error
    """
    if not AIRTABLE_ENABLED:
        print("[Airtable] Not configured - skipping sync")
        return None

    try:
        leads_table = airtable_api.table(AIRTABLE_BASE_ID, LEADS_TABLE)

        # Check if lead already exists
        existing = leads_table.all(formula=f"{{Phone}} = '{lead_data['phone']}'")

        record_data = {
            "Phone": lead_data["phone"],
            "Name": lead_data.get("name", "Unknown"),
            "Budget": lead_data.get("budget", ""),
            "Area Preference": lead_data.get("area_preference", ""),
            "Timeline": lead_data.get("timeline", ""),
            "Unit Type": lead_data.get("unit_preference", ""),
            "Status": "🔥 Qualified - Pending Assignment",
            "Qualification Score": lead_data.get("qualification_score", 4),
            "Qualified Date": datetime.now().isoformat(),
            "Source": "WhatsApp Bot"
        }

        if existing:
            # Update existing record
            record_id = existing[0]["id"]
            leads_table.update(record_id, record_data)
            print(f"[Airtable] Updated lead: {lead_data['phone']}")
            return record_id
        else:
            # Create new record
            record = leads_table.create(record_data)
            print(f"[Airtable] Created lead: {lead_data['phone']}")
            return record["id"]

    except Exception as e:
        print(f"[Airtable] Error syncing lead: {e}")
        return None

def update_lead_status(phone: str, status: str, notes: Optional[str] = None) -> bool:
    """
    Update lead status in Airtable.

    Statuses:
    - 🔥 Qualified - Pending Assignment
    - 👤 Assigned to Broker
    - 📞 Broker Contacted
    - 🏢 Site Visit Scheduled
    - 💰 Negotiating
    - ✅ Deal Closed
    - ❌ Lost
    """
    if not AIRTABLE_ENABLED:
        return False

    try:
        leads_table = airtable_api.table(AIRTABLE_BASE_ID, LEADS_TABLE)
        existing = leads_table.all(formula=f"{{Phone}} = '{phone}'")

        if not existing:
            print(f"[Airtable] Lead not found: {phone}")
            return False

        record_id = existing[0]["id"]
        update_data = {"Status": status}

        if notes:
            # Append to existing notes
            current_notes = existing[0]["fields"].get("Notes", "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            update_data["Notes"] = f"{current_notes}\n\n[{timestamp}] {notes}" if current_notes else f"[{timestamp}] {notes}"

        leads_table.update(record_id, update_data)
        print(f"[Airtable] Updated status for {phone}: {status}")
        return True

    except Exception as e:
        print(f"[Airtable] Error updating status: {e}")
        return False

def assign_to_broker(phone: str, broker_name: str) -> bool:
    """Assign lead to broker in Airtable"""
    if not AIRTABLE_ENABLED:
        return False

    try:
        leads_table = airtable_api.table(AIRTABLE_BASE_ID, LEADS_TABLE)
        existing = leads_table.all(formula=f"{{Phone}} = '{phone}'")

        if not existing:
            return False

        record_id = existing[0]["id"]
        leads_table.update(record_id, {
            "Assigned Broker": broker_name,
            "Status": "👤 Assigned to Broker",
            "Assigned Date": datetime.now().isoformat()
        })

        print(f"[Airtable] Assigned {phone} to {broker_name}")
        return True

    except Exception as e:
        print(f"[Airtable] Error assigning broker: {e}")
        return False

def log_deal(deal_data: Dict) -> Optional[str]:
    """
    Log closed deal to Airtable.

    Args:
        deal_data: Dict with phone, project, deal_value, commission, etc.

    Returns:
        Airtable record ID or None
    """
    if not AIRTABLE_ENABLED:
        return None

    try:
        deals_table = airtable_api.table(AIRTABLE_BASE_ID, DEALS_TABLE)

        record = deals_table.create({
            "Phone": deal_data["phone"],
            "Lead Name": deal_data.get("name", ""),
            "Project": deal_data.get("project", ""),
            "Unit Type": deal_data.get("unit_type", ""),
            "Deal Value (₹)": deal_data.get("deal_value", 0),
            "Broker Commission (₹)": deal_data.get("broker_commission", 0),
            "InvestoChat Commission (₹)": deal_data.get("investochat_commission", 0),
            "Closed Date": datetime.now().isoformat(),
            "Broker": deal_data.get("broker_name", "")
        })

        # Update lead status
        update_lead_status(deal_data["phone"], "✅ Deal Closed",
                          f"Deal closed: {deal_data.get('project')} - ₹{deal_data.get('deal_value', 0)/10000000:.2f} Cr")

        print(f"[Airtable] Logged deal: {deal_data['phone']} - ₹{deal_data.get('deal_value', 0)}")
        return record["id"]

    except Exception as e:
        print(f"[Airtable] Error logging deal: {e}")
        return None

def log_activity(phone: str, activity_type: str, description: str) -> bool:
    """Log activity for analytics"""
    if not AIRTABLE_ENABLED:
        return False

    try:
        activities_table = airtable_api.table(AIRTABLE_BASE_ID, ACTIVITIES_TABLE)

        activities_table.create({
            "Phone": phone,
            "Activity Type": activity_type,
            "Description": description,
            "Timestamp": datetime.now().isoformat()
        })

        return True

    except Exception as e:
        print(f"[Airtable] Error logging activity: {e}")
        return False

# =====================================================
# Broker Management
# =====================================================

def get_available_broker(area_preference: str) -> Optional[Dict]:
    """
    Get available broker based on area expertise.

    Returns:
        Dict with broker info or None
    """
    if not AIRTABLE_ENABLED:
        return None

    try:
        brokers_table = airtable_api.table(AIRTABLE_BASE_ID, BROKERS_TABLE)

        # Get active brokers
        brokers = brokers_table.all(formula="{Status} = 'Active'")

        # Simple round-robin for now
        # TODO: Implement smart assignment based on area expertise and workload

        if brokers:
            return {
                "name": brokers[0]["fields"].get("Name"),
                "phone": brokers[0]["fields"].get("Phone"),
                "whatsapp": brokers[0]["fields"].get("WhatsApp Number")
            }

        return None

    except Exception as e:
        print(f"[Airtable] Error getting broker: {e}")
        return None

# =====================================================
# Dashboard Data
# =====================================================

def get_dashboard_stats() -> Dict:
    """Get stats for partner dashboard"""
    if not AIRTABLE_ENABLED:
        return {
            "error": "Airtable not configured",
            "total_leads": 0,
            "qualified_today": 0,
            "pending_assignment": 0,
            "deals_closed": 0,
            "total_revenue": 0
        }

    try:
        leads_table = airtable_api.table(AIRTABLE_BASE_ID, LEADS_TABLE)
        deals_table = airtable_api.table(AIRTABLE_BASE_ID, DEALS_TABLE)

        # Get all leads
        all_leads = leads_table.all()

        # Count by status
        pending = [l for l in all_leads if "Pending Assignment" in l["fields"].get("Status", "")]
        assigned = [l for l in all_leads if "Assigned" in l["fields"].get("Status", "")]

        # Get deals
        all_deals = deals_table.all()
        total_revenue = sum(d["fields"].get("InvestoChat Commission (₹)", 0) for d in all_deals)

        # Today's qualified leads
        today = datetime.now().date().isoformat()
        today_qualified = [l for l in all_leads
                          if l["fields"].get("Qualified Date", "").startswith(today)]

        return {
            "total_leads": len(all_leads),
            "qualified_today": len(today_qualified),
            "pending_assignment": len(pending),
            "assigned_to_brokers": len(assigned),
            "deals_closed": len(all_deals),
            "total_revenue": total_revenue,
            "avg_deal_value": total_revenue / len(all_deals) if all_deals else 0
        }

    except Exception as e:
        print(f"[Airtable] Error getting stats: {e}")
        return {"error": str(e)}

# =====================================================
# Helper: Get lead details
# =====================================================

def get_lead_from_airtable(phone: str) -> Optional[Dict]:
    """Get lead details from Airtable"""
    if not AIRTABLE_ENABLED:
        return None

    try:
        leads_table = airtable_api.table(AIRTABLE_BASE_ID, LEADS_TABLE)
        results = leads_table.all(formula=f"{{Phone}} = '{phone}'")

        if results:
            return results[0]["fields"]

        return None

    except Exception as e:
        print(f"[Airtable] Error getting lead: {e}")
        return None
