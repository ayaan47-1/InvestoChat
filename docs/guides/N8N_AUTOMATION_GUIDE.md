# n8n Automation Guide for InvestoChat Table Extraction

## Overview

This guide shows how to automate the complete InvestoChat pipeline using n8n, from PDF upload to table extraction and RAG-ready ingestion.

## Automation Workflows

### Workflow 1: Complete PDF Ingestion Pipeline

**Trigger**: New PDF uploaded to `brochures/` folder

**Steps**:
1. Detect new PDF file
2. Run OCR processing (`process_pdf.py`)
3. Run text ingestion (`ingest.py`)
4. Run table extraction (`extract_tables.py`)
5. Send notification with results

**n8n Nodes Required**:
- **File Trigger** or **Webhook** or **Schedule Trigger**
- **Execute Command** (for Docker/Python scripts)
- **Postgres** (for database operations)
- **HTTP Request** (optional - for notifications)

---

## Workflow Designs

### Option A: Scheduled Batch Processing

**Use Case**: Process all new PDFs every hour/day

```
┌─────────────────┐
│ Schedule Trigger│ (Every 1 hour)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  List New PDFs  │ (Check brochures/ for unprocessed files)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  For Each PDF   │ (Loop through new files)
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│  OCR Processing │              │  Create Project │
│  (process_pdf)  │              │  (if needed)    │
└────────┬────────┘              └────────┬────────┘
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│   Ingest to DB  │◄─────────────┤  Get Project ID │
│   (ingest.py)   │              └─────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Tables  │
│(extract_tables) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Send Notification│ (Email/Slack/Webhook)
└─────────────────┘
```

### Option B: Real-Time Processing via Webhook

**Use Case**: Process PDF immediately when uploaded via API

```
┌─────────────────┐
│  Webhook Trigger│ (POST /process-pdf)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate Input │ (Check file_path, project_name)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OCR Processing │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ingest to DB   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Tables  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Response │ (JSON with table count, status)
└─────────────────┘
```

### Option C: Watch Folder for New Files

**Use Case**: Monitor folder and auto-process on upload

```
┌─────────────────┐
│  File Watcher   │ (Monitor brochures/ directory)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Detect New File │ (Trigger on .pdf creation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract Metadata│ (filename → project name)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Run Pipeline   │ (OCR → Ingest → Tables)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Update Status  │ (Mark as processed)
└─────────────────┘
```

---

## n8n Node Configurations

### 1. Schedule Trigger Node

**Configuration**:
```json
{
  "mode": "everyX",
  "value": 1,
  "unit": "hours",
  "triggerAtTime": "00:00"
}
```

**Use**: Run pipeline every hour to check for new PDFs

---

### 2. Execute Command Node - OCR Processing

**Node Name**: `Run OCR Processing`

**Configuration**:
```json
{
  "command": "docker compose exec -T ingest python process_pdf.py brochures/{{ $json.filename }} outputs --dpi 220",
  "cwd": "/Users/ayaan/Documents/GitHub/InvestoChat"
}
```

**Input**: `{ "filename": "Godrej_SORA.pdf" }`

**Output**: OCR JSONL files in `outputs/` directory

---

### 3. Execute Command Node - Database Ingestion

**Node Name**: `Ingest to Database`

**Configuration**:
```json
{
  "command": "docker compose exec -T ingest python ingest.py --project-id {{ $json.project_id }} --source \"{{ $json.filename }}\" --ocr-json outputs/{{ $json.base_name }}/{{ $json.base_name }}.jsonl --min-len 200",
  "cwd": "/Users/ayaan/Documents/GitHub/InvestoChat"
}
```

**Input**:
```json
{
  "project_id": 4,
  "filename": "Godrej_SORA.pdf",
  "base_name": "Godrej_SORA"
}
```

**Output**: Documents inserted into PostgreSQL

---

### 4. Execute Command Node - Table Extraction

**Node Name**: `Extract Tables`

**Configuration**:
```json
{
  "command": "docker compose exec -T ingest python extract_tables.py",
  "cwd": "/Users/ayaan/Documents/GitHub/InvestoChat"
}
```

**Output**: Tables extracted and stored in `document_tables`

---

### 5. Postgres Node - Check for Unprocessed Files

**Node Name**: `Get Unprocessed PDFs`

**Query**:
```sql
SELECT DISTINCT file_name
FROM (
    SELECT UNNEST(ARRAY[
        'Godrej_SORA.pdf',
        'Trevoc_56.pdf',
        'TARC_Ishva.pdf',
        'The_Sanctuaries.pdf',
        'Estate_360.pdf',
        'Project_1.pdf'
    ]) AS file_name
) all_files
WHERE file_name NOT IN (
    SELECT DISTINCT source_path FROM documents
)
```

**Output**: List of PDF files not yet in database

---

### 6. Postgres Node - Create Project

**Node Name**: `Create Project If Not Exists`

**Query**:
```sql
INSERT INTO projects (name, slug, description)
VALUES (
    '{{ $json.project_name }}',
    '{{ $json.project_slug }}',
    'Auto-created via n8n'
)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
RETURNING id;
```

**Input**:
```json
{
  "project_name": "Godrej SORA",
  "project_slug": "godrej-sora"
}
```

**Output**: `{ "id": 4 }`

---

### 7. HTTP Request Node - Send Notification

**Node Name**: `Send Slack Notification`

**Configuration**:
```json
{
  "method": "POST",
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "jsonParameters": true,
  "bodyParameters": {
    "text": "✅ PDF processed: {{ $json.filename }}\n- OCR pages: {{ $json.page_count }}\n- Documents: {{ $json.doc_count }}\n- Tables: {{ $json.table_count }}"
  }
}
```

---

## Complete n8n Workflow Example

### Scheduled PDF Processing Workflow

**Filename**: `InvestoChat_Auto_Ingest.json`

```json
{
  "name": "InvestoChat Auto Ingest",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 1
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "command": "ls -1 brochures/*.pdf | xargs -n1 basename"
      },
      "name": "List PDF Files",
      "type": "n8n-nodes-base.executeCommand",
      "position": [450, 300]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT DISTINCT source_path FROM documents"
      },
      "name": "Get Processed Files",
      "type": "n8n-nodes-base.postgres",
      "position": [650, 300],
      "credentials": {
        "postgres": {
          "name": "InvestoChat DB"
        }
      }
    },
    {
      "parameters": {
        "functionCode": "const allFiles = $input.first().json.stdout.split('\\n').filter(f => f.endsWith('.pdf'));\nconst processed = $input.last().json.map(row => row.source_path);\nconst newFiles = allFiles.filter(f => !processed.includes(f));\n\nreturn newFiles.map(file => ({ filename: file, base_name: file.replace('.pdf', '') }));"
      },
      "name": "Filter Unprocessed",
      "type": "n8n-nodes-base.function",
      "position": [850, 300]
    },
    {
      "parameters": {
        "command": "docker compose exec -T ingest python process_pdf.py brochures/{{ $json.filename }} outputs --dpi 220"
      },
      "name": "Run OCR",
      "type": "n8n-nodes-base.executeCommand",
      "position": [1050, 300]
    },
    {
      "parameters": {
        "functionCode": "const filename = $json.filename;\nconst baseName = filename.replace('.pdf', '').replace(/_/g, ' ');\nconst slug = baseName.toLowerCase().replace(/\\s+/g, '-');\n\nreturn { ...$ json, project_name: baseName, project_slug: slug };"
      },
      "name": "Extract Project Name",
      "type": "n8n-nodes-base.function",
      "position": [1250, 300]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "INSERT INTO projects (name, slug) VALUES ('{{ $json.project_name }}', '{{ $json.project_slug }}') ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id"
      },
      "name": "Create Project",
      "type": "n8n-nodes-base.postgres",
      "position": [1450, 300]
    },
    {
      "parameters": {
        "command": "docker compose exec -T ingest python ingest.py --project-id {{ $json.id }} --source \"{{ $json.filename }}\" --ocr-json outputs/{{ $json.base_name }}/{{ $json.base_name }}.jsonl"
      },
      "name": "Ingest to DB",
      "type": "n8n-nodes-base.executeCommand",
      "position": [1650, 300]
    },
    {
      "parameters": {
        "command": "docker compose exec -T ingest python extract_tables.py"
      },
      "name": "Extract Tables",
      "type": "n8n-nodes-base.executeCommand",
      "position": [1850, 300]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT COUNT(*) as table_count FROM document_tables WHERE source_path = '{{ $json.filename }}'"
      },
      "name": "Count Tables",
      "type": "n8n-nodes-base.postgres",
      "position": [2050, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK",
        "jsonParameters": true,
        "bodyParameters": {
          "text": "✅ Processed {{ $json.filename }}\\n- Tables extracted: {{ $json.table_count }}"
        }
      },
      "name": "Send Notification",
      "type": "n8n-nodes-base.httpRequest",
      "position": [2250, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": { "main": [[{ "node": "List PDF Files" }]] },
    "List PDF Files": { "main": [[{ "node": "Get Processed Files" }]] },
    "Get Processed Files": { "main": [[{ "node": "Filter Unprocessed" }]] },
    "Filter Unprocessed": { "main": [[{ "node": "Run OCR" }]] },
    "Run OCR": { "main": [[{ "node": "Extract Project Name" }]] },
    "Extract Project Name": { "main": [[{ "node": "Create Project" }]] },
    "Create Project": { "main": [[{ "node": "Ingest to DB" }]] },
    "Ingest to DB": { "main": [[{ "node": "Extract Tables" }]] },
    "Extract Tables": { "main": [[{ "node": "Count Tables" }]] },
    "Count Tables": { "main": [[{ "node": "Send Notification" }]] }
  }
}
```

---

## Webhook-Based Workflow

### API Endpoint for Manual Triggers

**Webhook URL**: `http://your-n8n-instance.com/webhook/investochat-ingest`

**Request**:
```bash
curl -X POST http://your-n8n-instance.com/webhook/investochat-ingest \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "brochures/New_Project.pdf",
    "project_name": "New Project",
    "project_slug": "new-project"
  }'
```

**Webhook Node Configuration**:
```json
{
  "parameters": {
    "path": "investochat-ingest",
    "responseMode": "responseNode",
    "options": {}
  },
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook"
}
```

**Response Node Configuration**:
```json
{
  "parameters": {
    "respondWith": "json",
    "responseBody": {
      "status": "success",
      "file": "{{ $json.filename }}",
      "project_id": "{{ $json.project_id }}",
      "documents": "{{ $json.doc_count }}",
      "tables": "{{ $json.table_count }}"
    }
  },
  "name": "Respond to Webhook",
  "type": "n8n-nodes-base.respondToWebhook"
}
```

---

## Advanced Workflows

### Workflow 2: Re-process Failed Ingestions

**Trigger**: Manual or scheduled

**Steps**:
1. Query database for PDFs with < 10 documents (likely failed)
2. Re-run OCR and ingestion
3. Log results

**Query**:
```sql
SELECT source_path, COUNT(*) as doc_count
FROM documents
GROUP BY source_path
HAVING COUNT(*) < 10
```

---

### Workflow 3: Detect and Label Unknown Tables

**Trigger**: After table extraction

**Steps**:
1. Query `document_tables` for `table_type = 'unknown'`
2. For each unknown table:
   - Extract context from surrounding text
   - Use OpenAI API to classify table type
   - Update `table_type` in database

**OpenAI Classification Prompt**:
```
Given this table and context, classify it as one of:
- payment_plan
- unit_specifications
- pricing
- amenities
- location
- specifications

Table:
{{ $json.markdown_content }}

Context:
{{ $json.context }}

Return only the classification.
```

---

### Workflow 4: Monitor and Alert

**Trigger**: Schedule (every 6 hours)

**Steps**:
1. Check database health (row counts, last update time)
2. Check for errors in logs
3. Send summary report

**Health Check Query**:
```sql
SELECT
    'projects' as table_name,
    COUNT(*) as count,
    MAX(created_at) as last_update
FROM projects
UNION ALL
SELECT
    'documents',
    COUNT(*),
    MAX(created_at)
FROM documents
UNION ALL
SELECT
    'document_tables',
    COUNT(*),
    MAX(created_at)
FROM document_tables
```

---

## Setup Instructions

### 1. Install n8n

**Option A: Docker**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Option B: npm**
```bash
npm install -g n8n
n8n start
```

Access at: `http://localhost:5678`

---

### 2. Configure Database Connection

1. Go to **Credentials** → **New**
2. Select **Postgres**
3. Enter connection details:
   - **Host**: `localhost` (or your PostgreSQL host)
   - **Database**: `investochat`
   - **User**: `investo_user`
   - **Password**: (from `.env`)
   - **Port**: `5432`
   - **SSL**: `disable` (or configure as needed)

4. Test connection and save

---

### 3. Configure Execute Command Permissions

**Important**: n8n needs access to run Docker commands

**Option 1**: Run n8n with Docker socket access
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /Users/ayaan/Documents/GitHub/InvestoChat:/workspace \
  n8nio/n8n
```

**Option 2**: Use SSH node to connect to host
```json
{
  "parameters": {
    "command": "cd /Users/ayaan/Documents/GitHub/InvestoChat && docker compose exec -T ingest python extract_tables.py",
    "authentication": "password"
  },
  "name": "Execute via SSH",
  "type": "n8n-nodes-base.ssh"
}
```

---

### 4. Import Workflow

1. Copy the workflow JSON above
2. In n8n, click **Import from File** or **Import from URL**
3. Paste JSON
4. Update credentials for Postgres nodes
5. Test each node individually
6. Activate workflow

---

## Error Handling

### Add Error Handling Nodes

**Catch Errors**:
```json
{
  "parameters": {
    "mode": "catchErrors",
    "errorWorkflow": "error-notification-workflow"
  },
  "name": "Error Trigger",
  "type": "n8n-nodes-base.errorTrigger"
}
```

**Log to Database**:
```sql
INSERT INTO ingestion_logs (filename, step, status, error_message, created_at)
VALUES (
    '{{ $json.filename }}',
    '{{ $json.node_name }}',
    'error',
    '{{ $json.error_message }}',
    NOW()
)
```

---

## Monitoring and Logging

### Create Logging Table

```sql
CREATE TABLE ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    filename TEXT,
    step VARCHAR(50),
    status VARCHAR(20),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ingestion_logs_filename ON ingestion_logs(filename);
CREATE INDEX idx_ingestion_logs_status ON ingestion_logs(status);
```

### Log Each Step

**Postgres Insert Node**:
```sql
INSERT INTO ingestion_logs (filename, step, status, metadata)
VALUES (
    '{{ $json.filename }}',
    'ocr_processing',
    'success',
    '{"page_count": {{ $json.page_count }}, "duration_ms": {{ $json.duration }}}'::jsonb
)
```

---

## Integration with External Services

### 1. Google Drive Upload Trigger

When new PDF uploaded to Google Drive folder → Auto-process

**Google Drive Trigger Node**:
```json
{
  "parameters": {
    "folderId": "YOUR_FOLDER_ID",
    "event": "file.created",
    "options": {
      "fileType": "pdf"
    }
  },
  "name": "Google Drive Trigger",
  "type": "n8n-nodes-base.googleDriveTrigger"
}
```

---

### 2. Slack Command

Trigger processing via Slack command: `/process-pdf Godrej_SORA.pdf`

**Slack Trigger Node**:
```json
{
  "parameters": {
    "appId": "YOUR_APP_ID",
    "event": "slash_command"
  },
  "name": "Slack Command",
  "type": "n8n-nodes-base.slack"
}
```

---

### 3. Email Upload

Send PDF via email → Auto-process

**Email Trigger (IMAP)**:
```json
{
  "parameters": {
    "mailbox": "INBOX",
    "options": {
      "attachmentsPrefix": "attachment_",
      "downloadAttachments": true
    }
  },
  "name": "Email Trigger",
  "type": "n8n-nodes-base.emailReadImap"
}
```

---

## Best Practices

### 1. Idempotency

Ensure workflows can be re-run safely:

```sql
-- Check if already processed
SELECT COUNT(*) FROM documents WHERE source_path = '{{ $json.filename }}'
```

Use `ON CONFLICT` for projects:
```sql
INSERT INTO projects (name, slug)
VALUES ('{{ $json.name }}', '{{ $json.slug }}')
ON CONFLICT (slug) DO NOTHING
RETURNING id
```

### 2. Rate Limiting

Add delays between heavy operations:

**Wait Node**:
```json
{
  "parameters": {
    "amount": 5,
    "unit": "seconds"
  },
  "name": "Wait",
  "type": "n8n-nodes-base.wait"
}
```

### 3. Parallel Processing

Process multiple PDFs in parallel using **Split In Batches**:

```json
{
  "parameters": {
    "batchSize": 3,
    "options": {}
  },
  "name": "Split In Batches",
  "type": "n8n-nodes-base.splitInBatches"
}
```

---

## Cost Considerations

### OpenAI API Costs

**Per PDF**:
- OCR (OLMoCR via DeepInfra): ~$0.01-0.05 per page
- Embeddings (text-embedding-3-small): ~$0.0001 per page
- **Total**: ~$0.01-0.06 per page

**Monthly** (assuming 100 PDFs/month, 20 pages each):
- OCR: $20-100
- Embeddings: $2
- **Total**: ~$22-102/month

### n8n Costs

- **Self-hosted**: Free (only infrastructure costs)
- **n8n Cloud**: Starts at $20/month (includes 2,500 executions)

---

## Summary

### What You Can Automate

✅ **PDF Upload & OCR**: Auto-process new PDFs when uploaded
✅ **Database Ingestion**: Auto-ingest OCR results to PostgreSQL
✅ **Table Extraction**: Auto-extract and label tables
✅ **Project Creation**: Auto-create projects from filename
✅ **Notifications**: Email/Slack alerts on completion
✅ **Error Handling**: Log and retry failed operations
✅ **Monitoring**: Health checks and status reports

### Recommended Workflows

1. **Production**: Webhook-based real-time processing
2. **Batch**: Scheduled processing every 1-6 hours
3. **Monitoring**: Health checks every 6 hours
4. **Cleanup**: Weekly cleanup of failed/orphaned records

### Next Steps

1. Install n8n (Docker or npm)
2. Import the workflow JSON
3. Configure Postgres credentials
4. Test with a single PDF
5. Deploy and activate

The automation will save significant time and ensure consistent processing of all new brochures.
