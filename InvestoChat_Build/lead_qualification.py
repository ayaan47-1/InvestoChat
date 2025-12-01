"""
Lead Qualification Module for InvestoChat

Handles the 4-question qualification flow:
1. Budget
2. Area Preference
3. Timeline
4. Unit Preference
"""

import os
import re
from typing import Optional, Dict, Tuple
from datetime import datetime

import psycopg
from dotenv import load_dotenv

# Load .env.local first, fallback to .env
load_dotenv('.env.local')
load_dotenv()  # Fallback to .env if .env.local doesn't exist
DATABASE_URL = os.getenv("DATABASE_URL")

# =====================================================
# Qualification Questions Configuration
# =====================================================

QUALIFICATION_QUESTIONS = {
    "budget": {
        "order": 1,
        "question": "💰 What is your investment budget range?\n\nExamples:\n• ₹2-3 Crore\n• ₹3-5 Crore\n• ₹5+ Crore\n• ₹10+ Crore",
        "validation": lambda x: any(char.isdigit() for char in x) or "crore" in x.lower() or "cr" in x.lower() or "lakh" in x.lower(),
        "error_message": "Please specify your budget range (e.g., ₹3-5 Crore)"
    },
    "area_preference": {
        "order": 2,
        "question": "📍 Which areas are you considering for investment?\n\nExamples:\n• Gurgaon Sector 89\n• Noida Extension\n• Greater Noida\n• DLF Phase 5\n• Multiple areas",
        "validation": lambda x: len(x.strip()) > 3,
        "error_message": "Please tell us your preferred location(s)"
    },
    "timeline": {
        "order": 3,
        "question": "📅 When are you planning to invest?\n\nOptions:\n• Immediate (within 2 weeks)\n• 1-3 months\n• 3-6 months\n• Just exploring",
        "validation": lambda x: len(x.strip()) > 2,
        "error_message": "Please share your investment timeline"
    },
    "unit_preference": {
        "order": 4,
        "question": "🏠 What unit configuration are you looking for?\n\nOptions:\n• 2 BHK\n• 3 BHK\n• 4 BHK\n• Penthouse\n• Open to options",
        "validation": lambda x: "bhk" in x.lower() or "penthouse" in x.lower() or "open" in x.lower() or any(d in x for d in ["2", "3", "4"]),
        "error_message": "Please specify unit type (e.g., 3 BHK, Penthouse)"
    }
}

# =====================================================
# Database Helper Functions
# =====================================================

def _get_connection():
    """Get database connection"""
    return psycopg.connect(DATABASE_URL)

def get_or_create_lead(phone: str, name: Optional[str] = None) -> Dict:
    """Get existing lead or create new one"""
    with _get_connection() as conn, conn.cursor() as cur:
        # Try to get existing lead
        cur.execute("""
            SELECT phone, name, budget, area_preference, timeline, unit_preference,
                   is_qualified, qualification_score, conversation_stage, last_question_asked
            FROM lead_qualification
            WHERE phone = %s
        """, (phone,))

        row = cur.fetchone()

        if row:
            return {
                "phone": row[0],
                "name": row[1],
                "budget": row[2],
                "area_preference": row[3],
                "timeline": row[4],
                "unit_preference": row[5],
                "is_qualified": row[6],
                "qualification_score": row[7],
                "conversation_stage": row[8],
                "last_question_asked": row[9]
            }
        else:
            # Create new lead
            cur.execute("""
                INSERT INTO lead_qualification (phone, name)
                VALUES (%s, %s)
                RETURNING phone, name, budget, area_preference, timeline, unit_preference,
                          is_qualified, qualification_score, conversation_stage, last_question_asked
            """, (phone, name))

            row = cur.fetchone()
            conn.commit()

            return {
                "phone": row[0],
                "name": row[1],
                "budget": row[2],
                "area_preference": row[3],
                "timeline": row[4],
                "unit_preference": row[5],
                "is_qualified": row[6],
                "qualification_score": row[7],
                "conversation_stage": row[8],
                "last_question_asked": row[9]
            }

def update_qualification_answer(phone: str, field: str, answer: str) -> bool:
    """Update a qualification field and return success status"""
    with _get_connection() as conn, conn.cursor() as cur:
        # Update the specific field
        cur.execute(f"""
            UPDATE lead_qualification
            SET {field} = %s,
                last_question_asked = %s,
                updated_at = NOW()
            WHERE phone = %s
        """, (answer.strip(), field, phone))

        conn.commit()
        return cur.rowcount > 0

def log_conversation(phone: str, message_type: str, message_text: str,
                     is_qualification: bool = False, qualification_field: Optional[str] = None):
    """Log conversation to history"""
    with _get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO conversation_history
            (phone, message_type, message_text, is_qualification_question, qualification_field)
            VALUES (%s, %s, %s, %s, %s)
        """, (phone, message_type, message_text, is_qualification, qualification_field))
        conn.commit()

# =====================================================
# Qualification Logic
# =====================================================

def get_next_question(phone: str) -> Optional[Tuple[str, str]]:
    """
    Get the next unanswered qualification question.

    Returns:
        Tuple of (field_name, question_text) or None if all questions answered
    """
    lead = get_or_create_lead(phone)

    # Check each question in order
    for field, config in sorted(QUALIFICATION_QUESTIONS.items(), key=lambda x: x[1]["order"]):
        if not lead.get(field):
            return (field, config["question"])

    return None  # All questions answered

def process_qualification_answer(phone: str, answer: str) -> Dict:
    """
    Process user's answer to qualification question.

    Returns:
        Dict with status, next_question, and message
    """
    lead = get_or_create_lead(phone)
    last_question = lead.get("last_question_asked")

    # If this is response to a qualification question
    if last_question and last_question in QUALIFICATION_QUESTIONS:
        config = QUALIFICATION_QUESTIONS[last_question]

        # Validate answer
        if not config["validation"](answer):
            # Log invalid attempt
            log_conversation(phone, "user", answer, is_qualification=True, qualification_field=last_question)

            return {
                "status": "invalid",
                "field": last_question,
                "message": config["error_message"],
                "next_question": None
            }

        # Valid answer - save it
        update_qualification_answer(phone, last_question, answer)
        log_conversation(phone, "user", answer, is_qualification=True, qualification_field=last_question)

        # Get next question
        next_q = get_next_question(phone)

        if next_q:
            field, question = next_q
            # Mark this question as asked
            with _get_connection() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE lead_qualification
                    SET last_question_asked = %s
                    WHERE phone = %s
                """, (field, phone))
                conn.commit()

            log_conversation(phone, "bot", question, is_qualification=True, qualification_field=field)

            return {
                "status": "continue",
                "field": field,
                "message": f"✅ Got it!\n\n{question}",
                "next_question": question
            }
        else:
            # All questions answered - lead is now qualified!
            return {
                "status": "qualified",
                "field": None,
                "message": get_qualification_complete_message(phone),
                "next_question": None
            }

    return {
        "status": "error",
        "field": None,
        "message": "I didn't understand. Could you please rephrase?",
        "next_question": None
    }

def should_start_qualification(phone: str) -> bool:
    """
    Check if we should start qualification flow.

    Start qualification after:
    - User has asked 2+ questions about properties
    - User hasn't been qualified yet
    """
    lead = get_or_create_lead(phone)

    if lead["is_qualified"]:
        return False

    # Check conversation count
    with _get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM conversation_history
            WHERE phone = %s AND message_type = 'user'
        """, (phone,))

        count = cur.fetchone()[0]

        # Start qualification after 2 user messages
        return count >= 2 and lead["qualification_score"] == 0

def get_qualification_start_message() -> str:
    """Get message to start qualification flow"""
    return """
Great! I can see you're interested in these properties.

To connect you with the best investment advisor and get personalized recommendations, I'd like to ask you a few quick questions (takes just 1 minute).

Ready to start? 🚀
"""

def start_qualification_flow(phone: str) -> str:
    """
    Start the qualification flow.

    Returns:
        First question to ask
    """
    next_q = get_next_question(phone)

    if next_q:
        field, question = next_q

        # Mark this question as asked
        with _get_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                UPDATE lead_qualification
                SET last_question_asked = %s,
                    conversation_stage = 'qualifying'
                WHERE phone = %s
            """, (field, phone))
            conn.commit()

        log_conversation(phone, "bot", question, is_qualification=True, qualification_field=field)

        return question

    return "It looks like you've already answered all questions!"

def get_qualification_complete_message(phone: str) -> str:
    """Get message when qualification is complete"""
    lead = get_or_create_lead(phone)

    summary = f"""
🎉 Perfect! I have all the information I need.

📊 **Your Investment Profile:**
💰 Budget: {lead.get('budget', 'Not specified')}
📍 Location: {lead.get('area_preference', 'Not specified')}
📅 Timeline: {lead.get('timeline', 'Not specified')}
🏠 Unit Type: {lead.get('unit_preference', 'Not specified')}

I can now connect you with one of our expert investment advisors who will provide personalized recommendations based on your requirements.

🔥 **Would you like to speak with an advisor now?**

Reply "YES" to connect, or continue asking me questions about specific properties.
"""

    return summary

def is_broker_connect_request(message: str) -> bool:
    """Check if user wants to connect with broker"""
    triggers = ["yes", "connect", "talk", "call", "speak", "advisor", "broker", "agent"]
    return any(trigger in message.lower() for trigger in triggers)

# =====================================================
# Analytics & Status
# =====================================================

def get_qualification_stats() -> Dict:
    """Get qualification statistics"""
    with _get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total_leads,
                COUNT(CASE WHEN is_qualified = TRUE THEN 1 END) as qualified_leads,
                COUNT(CASE WHEN qualification_score >= 3 THEN 1 END) as nearly_qualified,
                AVG(qualification_score) as avg_score,
                COUNT(CASE WHEN assigned_broker_id IS NOT NULL THEN 1 END) as assigned_leads
            FROM lead_qualification
        """)

        row = cur.fetchone()

        return {
            "total_leads": row[0],
            "qualified_leads": row[1],
            "nearly_qualified": row[2],
            "avg_qualification_score": float(row[3]) if row[3] else 0,
            "assigned_to_brokers": row[4],
            "qualification_rate": (row[1] / row[0] * 100) if row[0] > 0 else 0
        }

def get_lead_summary(phone: str) -> str:
    """Get human-readable lead summary"""
    lead = get_or_create_lead(phone)

    if lead["is_qualified"]:
        status = "✅ Qualified"
    elif lead["qualification_score"] >= 3:
        status = "⏳ Nearly Qualified"
    elif lead["qualification_score"] > 0:
        status = "📝 In Progress"
    else:
        status = "🆕 New Lead"

    return f"{status} ({lead['qualification_score']}/4 questions answered)"
