-- Create a dedicated table for storing extracted and labeled tables
-- This allows better retrieval of structured data like payment plans

CREATE TABLE IF NOT EXISTS document_tables (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    page INTEGER,

    -- Table metadata
    table_type VARCHAR(50) NOT NULL,  -- payment_plan, unit_specifications, pricing, etc.
    table_format VARCHAR(20),          -- html, pipe, markdown
    row_count INTEGER,
    col_count INTEGER,

    -- Table content
    markdown_content TEXT NOT NULL,    -- Normalized markdown table
    original_content TEXT,              -- Original extracted content
    summary TEXT,                       -- Text summary for embedding

    -- For retrieval
    embedding vector(1536),            -- Embedding of summary + markdown

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_document_tables_project ON document_tables(project_id);
CREATE INDEX IF NOT EXISTS idx_document_tables_type ON document_tables(table_type);
CREATE INDEX IF NOT EXISTS idx_document_tables_source ON document_tables(source_path);
CREATE INDEX IF NOT EXISTS idx_document_tables_embedding ON document_tables
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Composite index for project + type queries
CREATE INDEX IF NOT EXISTS idx_document_tables_project_type ON document_tables(project_id, table_type);

COMMENT ON TABLE document_tables IS 'Extracted and labeled tables from real estate brochures for enhanced retrieval';
COMMENT ON COLUMN document_tables.table_type IS 'payment_plan, unit_specifications, pricing, amenities, location, specifications, unknown';
COMMENT ON COLUMN document_tables.summary IS 'Human-readable summary used for embedding generation';
