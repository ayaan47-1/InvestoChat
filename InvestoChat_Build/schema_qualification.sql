-- Lead Qualification & CRM Schema for InvestoChat
-- Run after existing schema.sql

-- =====================================================
-- Lead Qualification Tracking
-- =====================================================

CREATE TABLE IF NOT EXISTS lead_qualification (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),

    -- Qualification answers (the 4 critical questions)
    budget VARCHAR(100),              -- e.g., "₹3-5 Cr", "₹5+ Cr"
    area_preference VARCHAR(255),     -- e.g., "Gurgaon Sector 89, Noida Extension"
    timeline VARCHAR(100),            -- e.g., "Immediate", "1-3 months", "3-6 months"
    unit_preference VARCHAR(100),     -- e.g., "3BHK", "4BHK", "Penthouse"

    -- Qualification status
    is_qualified BOOLEAN DEFAULT FALSE,
    qualification_score INTEGER DEFAULT 0,  -- 0-4 based on questions answered

    -- Conversation state
    last_question_asked VARCHAR(50),   -- Which question was asked last
    conversation_stage VARCHAR(50) DEFAULT 'initial',  -- initial, qualifying, qualified, connected_to_broker

    -- Assignment & tracking
    assigned_broker_id INTEGER REFERENCES projects(id),  -- Reuse projects table for brokers temporarily
    assigned_at TIMESTAMP WITH TIME ZONE,
    broker_connected_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    project_interest INTEGER REFERENCES projects(id),
    source VARCHAR(50) DEFAULT 'whatsapp',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    qualified_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- Conversation History (for context & analytics)
-- =====================================================

CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    message_type VARCHAR(20) NOT NULL,  -- 'user', 'bot', 'system'
    message_text TEXT NOT NULL,

    -- Context
    project_id INTEGER REFERENCES projects(id),
    retrieval_mode VARCHAR(50),         -- facts, tables, docs_expanded, etc.
    retrieval_score FLOAT,

    -- Qualification tracking
    is_qualification_question BOOLEAN DEFAULT FALSE,
    qualification_field VARCHAR(50),    -- budget, area_preference, timeline, unit_preference

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Foreign key to lead
    FOREIGN KEY (phone) REFERENCES lead_qualification(phone) ON DELETE CASCADE
);

-- =====================================================
-- Deals & Commission Tracking
-- =====================================================

CREATE TABLE IF NOT EXISTS deals (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL REFERENCES lead_qualification(phone),

    -- Deal details
    project_id INTEGER NOT NULL REFERENCES projects(id),
    unit_type VARCHAR(100),
    deal_value DECIMAL(15, 2),          -- In ₹

    -- Commission calculation
    broker_commission_percent DECIMAL(5, 2) DEFAULT 2.00,
    broker_commission_amount DECIMAL(15, 2),
    investochat_percent DECIMAL(5, 2) DEFAULT 25.00,
    investochat_commission DECIMAL(15, 2),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'qualified',  -- qualified, site_visit_scheduled, negotiating, closed, lost

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    site_visit_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,

    -- Notes
    notes TEXT
);

-- =====================================================
-- Brokers Table (Separate from projects)
-- =====================================================

CREATE TABLE IF NOT EXISTS brokers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_number VARCHAR(20),

    -- Specialization
    areas_of_expertise TEXT[],          -- Array of areas: ['Gurgaon Sector 89', 'Noida Extension']
    projects_handled INTEGER[],         -- Array of project IDs

    -- Performance
    total_leads_assigned INTEGER DEFAULT 0,
    total_deals_closed INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    max_concurrent_leads INTEGER DEFAULT 10,
    current_leads_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Lead Assignment History
-- =====================================================

CREATE TABLE IF NOT EXISTS lead_assignments (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL REFERENCES lead_qualification(phone),
    broker_id INTEGER NOT NULL REFERENCES brokers(id),

    status VARCHAR(50) DEFAULT 'assigned',  -- assigned, accepted, rejected, completed
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    notes TEXT
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_qualification_phone ON lead_qualification(phone);
CREATE INDEX IF NOT EXISTS idx_qualification_status ON lead_qualification(is_qualified, conversation_stage);
CREATE INDEX IF NOT EXISTS idx_qualification_broker ON lead_qualification(assigned_broker_id);

CREATE INDEX IF NOT EXISTS idx_conversation_phone ON conversation_history(phone);
CREATE INDEX IF NOT EXISTS idx_conversation_time ON conversation_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_deals_phone ON deals(phone);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_project ON deals(project_id);

CREATE INDEX IF NOT EXISTS idx_brokers_phone ON brokers(phone);
CREATE INDEX IF NOT EXISTS idx_brokers_active ON brokers(is_active);

-- =====================================================
-- Functions for Auto-updates
-- =====================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lead_qualification_updated_at
    BEFORE UPDATE ON lead_qualification
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Calculate qualification score automatically
CREATE OR REPLACE FUNCTION calculate_qualification_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.qualification_score =
        (CASE WHEN NEW.budget IS NOT NULL AND NEW.budget != '' THEN 1 ELSE 0 END) +
        (CASE WHEN NEW.area_preference IS NOT NULL AND NEW.area_preference != '' THEN 1 ELSE 0 END) +
        (CASE WHEN NEW.timeline IS NOT NULL AND NEW.timeline != '' THEN 1 ELSE 0 END) +
        (CASE WHEN NEW.unit_preference IS NOT NULL AND NEW.unit_preference != '' THEN 1 ELSE 0 END);

    -- Mark as qualified if all 4 questions answered
    IF NEW.qualification_score = 4 THEN
        NEW.is_qualified = TRUE;
        NEW.qualified_at = NOW();
        NEW.conversation_stage = 'qualified';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_calculate_qualification_score
    BEFORE INSERT OR UPDATE ON lead_qualification
    FOR EACH ROW
    EXECUTE FUNCTION calculate_qualification_score();

-- Calculate deal commissions automatically
CREATE OR REPLACE FUNCTION calculate_deal_commission()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.deal_value IS NOT NULL THEN
        NEW.broker_commission_amount = NEW.deal_value * (NEW.broker_commission_percent / 100);
        NEW.investochat_commission = NEW.broker_commission_amount * (NEW.investochat_percent / 100);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_calculate_commission
    BEFORE INSERT OR UPDATE ON deals
    FOR EACH ROW
    EXECUTE FUNCTION calculate_deal_commission();

-- =====================================================
-- Initial Data: Sample Brokers
-- =====================================================

-- Insert sample brokers (update with real data)
INSERT INTO brokers (name, email, phone, whatsapp_number, areas_of_expertise) VALUES
('Broker 1', 'broker1@example.com', '+919876543210', '+919876543210', ARRAY['Gurgaon Sector 89', 'Sector 95']),
('Broker 2', 'broker2@example.com', '+919876543211', '+919876543211', ARRAY['Noida Extension', 'Greater Noida']),
('Broker 3', 'broker3@example.com', '+919876543212', '+919876543212', ARRAY['Gurgaon Sector 89', 'Noida Extension'])
ON CONFLICT (phone) DO NOTHING;

COMMENT ON TABLE lead_qualification IS 'Stores lead qualification data and conversation state';
COMMENT ON TABLE conversation_history IS 'Complete conversation log for analytics and context';
COMMENT ON TABLE deals IS 'Closed deals with commission tracking';
COMMENT ON TABLE brokers IS 'Broker profiles and performance metrics';
COMMENT ON TABLE lead_assignments IS 'History of lead assignments to brokers';
