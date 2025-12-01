import os
from dotenv import load_dotenv
from lead_qualification import get_or_create_lead, get_next_question

# Load environment variables
load_dotenv('.env.local')

# Create a lead
lead = get_or_create_lead(phone='+919999999991', name='Python Test')
print('✅ Lead created:', lead['phone'])
print('   Qualification score:', lead['qualification_score'])
print('   Stage:', lead['conversation_stage'])

# Get first question
field, question = get_next_question('+919999999991')
print('\n✅ First question field:', field)
print('   Question preview:', question[:80], '...')
