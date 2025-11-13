# Adding Image Support to WhatsApp Bot

## Current State
✅ **Images are stored**: `ocr_pages.image_path` has PNG paths for all 268 pages
❌ **Images not sent**: WhatsApp webhook only sends text responses

## How to Add Image Support

### Step 1: Create Image Sending Function

Add this to `service.py`:

```python
def send_whatsapp_image(to: str, image_url: str, caption: Optional[str] = None) -> dict:
    """
    Send an image via WhatsApp Business API.

    Args:
        to: Recipient phone number
        image_url: Public URL to the image (must be HTTPS)
        caption: Optional caption text
    """
    if not (WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID):
        LOG.warning("missing WhatsApp creds; simulated image to %s: %s", to, image_url)
        return {"status": "simulated"}

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
        }
    }

    if caption:
        payload["image"]["caption"] = caption

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        LOG.error("WhatsApp image send failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(resp.status_code, "WhatsApp image send failed")

    return resp.json()
```

### Step 2: Detect Image Requests

Add intent detection function:

```python
def detect_image_intent(question: str) -> Optional[str]:
    """
    Detect if user is asking for images/maps/photos.
    Returns intent type: 'image', 'map', 'floorplan', 'location', or None
    """
    lower = question.lower()

    image_keywords = {
        'image': ['image', 'photo', 'picture', 'pic'],
        'map': ['map', 'location map', 'site map'],
        'floorplan': ['floor plan', 'unit plan', 'layout', 'blueprint'],
        'location': ['location', 'where is', 'address'],
    }

    for intent, keywords in image_keywords.items():
        if any(kw in lower for kw in keywords):
            return intent

    return None
```

### Step 3: Retrieve Image from Database

Add this query function:

```python
def get_relevant_images(question: str, project_id: Optional[int] = None, limit: int = 3) -> List[dict]:
    """
    Find relevant page images based on question.
    Returns list of dicts with 'page', 'image_path', 'text', 'source_pdf'
    """
    with _pg() as con, con.cursor() as cur:
        # Use semantic matching via text content
        terms = keyword_terms(question)  # Reuse from main.py

        where_parts = []
        params = []

        if terms:
            where_parts.append("(" + " OR ".join(["text ILIKE %s"] * len(terms)) + ")")
            params.extend([f"%{t}%" for t in terms])

        if project_id:
            # Query projects table to get source_path
            cur.execute("SELECT source_root FROM projects WHERE id = %s", (project_id,))
            result = cur.fetchone()
            if result and result[0]:
                where_parts.append("source_pdf LIKE %s")
                params.append(f"%{result[0]}%")

        where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

        cur.execute(f"""
            SELECT page, image_path, text, source_pdf
            FROM ocr_pages
            {where_clause}
            ORDER BY page ASC
            LIMIT %s
        """, tuple(params + [limit]))

        rows = cur.fetchall()

    return [
        {
            "page": row[0],
            "image_path": row[1],
            "text": row[2],
            "source_pdf": row[3]
        }
        for row in rows
    ]
```

### Step 4: Serve Images via HTTP

**Problem**: WhatsApp requires public HTTPS URLs, but your images are in `/app/outputs/`

**Solution A**: Add static file serving to FastAPI:

```python
from fastapi.staticfiles import StaticFiles

# Add to service.py after app creation
app.mount("/images", StaticFiles(directory="/app/outputs"), name="images")
```

**Usage**: Images become accessible at `http://yourserver.com/images/The_Sanctuaries/images/The_Sanctuaries_p0001.png`

**Solution B**: Upload images to cloud storage (S3, Cloudinary, etc.) and store public URLs

### Step 5: Update WhatsApp Webhook Handler

Modify the webhook to handle image requests:

```python
@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    message = extract_whatsapp_payload(payload)
    if not message:
        LOG.info("webhook received non-text payload")
        return {"status": "ignored"}

    allowed, reason = guard_question(message["text"])
    if not allowed:
        LOG.warning("guard blocked message from %s: %s", message.get("from"), reason)
        if message.get("from"):
            send_whatsapp_message(message["from"], reason)
        return {"status": "blocked"}

    retry_after = whatsapp_rate_limiter.check(message.get("from") or "anon")
    if retry_after:
        if message.get("from"):
            send_whatsapp_message(message["from"], f"Too many questions. Try again in {retry_after}s.")
        return {"status": "rate-limited"}

    project_id = resolve_project(message.get("from"))
    if not project_id:
        LOG.warning("no project mapping for %s", message.get("from"))
        if message.get("from"):
            send_whatsapp_message(message["from"], "Thanks for reaching out. An advisor will contact you shortly.")
        return {"status": "routed-to-human"}

    # NEW: Check for image intent
    image_intent = detect_image_intent(message["text"])
    if image_intent:
        LOG.info("Image request detected: %s", image_intent)
        images = get_relevant_images(message["text"], project_id=project_id, limit=1)

        if images:
            image = images[0]
            # Construct public URL (adjust based on your deployment)
            image_url = f"https://yourserver.com/images/{image['image_path'].replace('/app/outputs/', '')}"
            caption = f"Page {image['page']}: {image['text'][:200]}"

            send_whatsapp_image(message["from"], image_url, caption)
            log_interaction(
                channel="whatsapp",
                user_id=message["from"],
                project_id=project_id,
                question=message["text"],
                answer=f"[IMAGE_SENT] {image_url}",
                mode="image",
                latency_ms=0,
            )
            return {"status": "image_sent", "image": image_url}
        else:
            send_whatsapp_message(message["from"], "I couldn't find a relevant image. Please rephrase your question.")
            return {"status": "no_image_found"}

    # EXISTING: Text-based RAG flow
    LOG.info("WhatsApp inbound from %s project=%s", message["from"], project_id)
    retrieval = retrieve(message["text"], project_id=project_id)
    answer = answer_from_retrieval(message["text"], retrieval, model=DEFAULT_MODEL)
    reply = format_whatsapp_reply(answer)
    send_whatsapp_message(message["from"], reply)
    log_interaction(
        channel="whatsapp",
        user_id=message["from"],
        project_id=project_id,
        question=message["text"],
        answer=answer["answer"],
        mode=answer["mode"],
        latency_ms=0,
    )
    return {"status": "sent", "mode": answer["mode"]}
```

### Step 6: Example Queries That Would Trigger Images

User asks:
- "Show me the floor plan"
- "Send me a picture of the property"
- "Where is The Sanctuaries located? Show map"
- "Can I see the unit layout?"

Bot response:
1. Detects image intent
2. Searches `ocr_pages` for relevant pages
3. Sends image with caption via WhatsApp

## Deployment Considerations

### 1. Image Hosting
**Option A**: Use FastAPI StaticFiles (simple, but requires public server)
```python
app.mount("/images", StaticFiles(directory="/app/outputs"), name="images")
```

**Option B**: Upload to S3/Cloudinary (recommended for production)
```python
import boto3

def upload_to_s3(local_path: str, bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket, key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"
```

### 2. WhatsApp Media Limits
- Max image size: 5MB
- Supported formats: JPG, PNG
- Images must be publicly accessible via HTTPS
- Image URL must be valid for at least 5 minutes

### 3. Security
- Add authentication to `/images` endpoint if using StaticFiles
- Rate limit image requests (already handled by `whatsapp_rate_limiter`)
- Validate image paths to prevent directory traversal

## Testing

### Test Image Endpoint Locally
```bash
# Start service with static files
uvicorn service:app --host 0.0.0.0 --port 8000

# Access image via browser
http://localhost:8000/images/The_Sanctuaries/images/The_Sanctuaries_p0001.png
```

### Test WhatsApp Image Sending
```python
# In Python shell or test script
from service import send_whatsapp_image

send_whatsapp_image(
    to="+1234567890",
    image_url="https://yourserver.com/images/The_Sanctuaries/images/The_Sanctuaries_p0001.png",
    caption="The Sanctuaries - Main Entrance"
)
```

## Alternative: Smart Text Response

If you don't want to implement full image sending, you can mention image availability:

```python
def format_whatsapp_reply_with_image_info(answer: dict, image_intent: Optional[str] = None) -> str:
    lines = [answer["answer"]]

    source_text = format_sources(answer.get("sources") or [])
    if source_text and answer["answer"].strip().lower() != "not in the documents.":
        lines.append(f"Source: {source_text}")

    if image_intent:
        lines.append("📷 Visual content is available. Please contact our sales team for detailed images and floor plans.")

    if answer["answer"].strip().lower() == "not in the documents.":
        lines.append("I'll connect you with an advisor for more details.")

    return "\n\n".join(lines)
```

## Summary

**Current**: ❌ Text responses only
**After implementation**: ✅ Can send images/maps/floor plans

**Required changes**:
1. Add `send_whatsapp_image()` function
2. Add `detect_image_intent()` for intent detection
3. Add `get_relevant_images()` to query database
4. Mount static files or use cloud storage
5. Update webhook to handle image requests

**Estimated effort**: 2-4 hours for basic implementation
