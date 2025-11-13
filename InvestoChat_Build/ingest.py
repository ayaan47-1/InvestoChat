import os
import re
import json
import argparse
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

import psycopg
from dotenv import load_dotenv

from cleaner import clean_brochure_text, drop_too_small_chunks
from collections import Counter

# -----------------------------------------------------------------------------
# Brochure-first ingestion: OlmOCR JSON → clean → chunk → embed → Postgres
# -----------------------------------------------------------------------------

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL   = os.getenv("DATABASE_URL")

# Lazy import to avoid hard dependency if not running ingest
def _embed_texts(texts: List[str]) -> List[List[float]]:
    import openai
    openai.api_key = OPENAI_API_KEY
    resp = openai.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

def _to_pgvector(vec: List[float]) -> str:
    # psycopg3 does not natively adapt pgvector without extra adapter; cast via text
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"

def _detect_repeated_lines(page_texts: List[str], min_pages: int = 3, min_len: int = 15) -> List[str]:
    """
    Detect lines that appear repeatedly across multiple pages (headers/footers).

    Args:
        page_texts: List of page text strings
        min_pages: Minimum number of pages a line must appear in to be considered repeated
        min_len: Minimum character length for a line to be considered

    Returns:
        List of repeated line strings to remove
    """
    if len(page_texts) < min_pages: 
        return []

    # Extract lines from all pages
    all_lines = []
    for page_text in page_texts:
        lines = [ln.strip() for ln in page_text.split('\n') if len(ln.strip()) >= min_len]
        all_lines.extend(lines)

    if not all_lines:
        return []

    # Count occurrences
    line_counts = Counter(all_lines)

    # Find lines appearing in at least min_pages
    repeated = [line for line, count in line_counts.items() if count >= min_pages]

    return repeated


def _remove_repeated_lines(text: str, repeated_patterns: List[str]) -> str:
    """
    Remove repeated header/footer lines from text.

    Args:
        text: Input text
        repeated_patterns: List of line patterns to remove

    Returns:
        Text with repeated lines removed
    """
    if not repeated_patterns:
        return text

    lines = text.split('\n')
    filtered_lines = []

    for line in lines:
        line_stripped = line.strip()
        # Keep line if it's not in the repeated patterns
        if line_stripped not in repeated_patterns:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def _read_olmocr_json(fp: Path) -> dict:
    """
    Read OCR JSON file. Handles two formats:
    1. JSONL (one JSON object per line) - from process_pdf.py
    2. Single JSON with pages array - from OlmOCR API
    """
    with open(fp, "r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)

        # Check if it's JSONL format (one object per line)
        try:
            first_obj = json.loads(first_line)
            if "pdf" in first_obj and "page" in first_obj and "text" in first_obj:
                # This is JSONL format from process_pdf.py
                pages = []
                for line in f:
                    if line.strip():
                        pages.append(json.loads(line))
                return {"pages": pages}
        except:
            pass

        # Otherwise, treat as single JSON object
        f.seek(0)
        return json.load(f)

def _yield_page_chunks(ocr: dict, deduplicate: bool = True) -> Iterable[Tuple[int, str, str]]:
    """
    Yields (page, section, text). Handles multiple formats:
    1. {"pages": [{"page": 1, "text": "..."}, ...]} - OlmOCR or converted JSONL
    2. {"text": "..."} - single document

    Args:
        ocr: OCR result dictionary
        deduplicate: If True, removes repeated headers/footers across pages
    """
    pages = ocr.get("pages") or []
    if isinstance(pages, list) and pages:
        # First pass: collect all raw page texts for deduplication
        page_data = []
        for p in pages:
            page_no = int(p.get("page") or p.get("page_number") or 0)
            txt = str(p.get("text") or p.get("content") or "")
            page_data.append((page_no, txt))

        # Detect repeated lines across pages
        repeated_patterns = []
        if deduplicate and len(page_data) >= 3:
            raw_texts = [txt for _, txt in page_data]
            repeated_patterns = _detect_repeated_lines(raw_texts, min_pages=3, min_len=15)
            if repeated_patterns:
                print(f"[dedup] Found {len(repeated_patterns)} repeated lines to remove")
                if os.getenv("DEBUG_RAG") == "1":
                    for pattern in repeated_patterns[:5]:  # Show first 5
                        print(f"  - {pattern[:80]}")

        # Second pass: clean and yield chunks with deduplication
        for page_no, txt in page_data:
            # Remove repeated lines first
            if repeated_patterns:
                txt = _remove_repeated_lines(txt, repeated_patterns)

            # Then apply standard cleaning
            cleaned = clean_brochure_text(txt)
            if cleaned:
                yield page_no or 0, "page", cleaned
        return

    # Fallback: whole-document text
    whole = ocr.get("text") or ocr.get("content") or ""
    cleaned = clean_brochure_text(str(whole))
    if cleaned:
        yield 0, "document", cleaned

def _preview_chunks(chunks: List[Tuple[int, str, str]], max_show: int = 2):
    print(f"[debug] cleaned chunks: {len(chunks)} total")
    for idx, (_, section, text) in enumerate(chunks[:max_show], 1):
        snippet = text[:400].replace("\n", " ") + ("..." if len(text) > 400 else "")
        print(f"  #{idx} section={section} chars={len(text)} :: {snippet}")

def ingest_ocr_json(
    project_id: int,
    source_path: str,
    ocr_json_path: Path,
    min_len: int = 200,
    debug: bool = False,
    dry_run: bool = False,
    deduplicate: bool = True,
) -> int:
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL not set in InvestoChat_Build/.env")

    ocr = _read_olmocr_json(ocr_json_path)

    # Chunk by page, clean, filter small, then embed
    chunks = list(_yield_page_chunks(ocr, deduplicate=deduplicate))
    if not chunks:
        print(f"[skip] {ocr_json_path.name}: no text after cleaning")
        return 0

    texts = [c[2] for c in chunks]
    texts = drop_too_small_chunks(texts, min_len=min_len)
    if not texts:
        print(f"[skip] {ocr_json_path.name}: all chunks below min_len={min_len}")
        return 0

    if debug:
        kept = [(pg, sec, txt) for (pg, sec, txt) in chunks if txt in texts]
        _preview_chunks(kept)

    if dry_run:
        print(f"[dry-run] would insert {len(texts)} chunks for {ocr_json_path.name}")
        return len(texts)

    embeddings = _embed_texts(texts)

    # Insert into Postgres
    inserted = 0
    with psycopg.connect(DATABASE_URL) as con, con.cursor() as cur:
        for (page, section, txt), emb in zip(chunks, embeddings):
            # Skip if this text was filtered out by min_len
            if txt not in texts:
                continue
            cur.execute(
                """
                INSERT INTO documents (project_id, source_path, page, section, text, meta, embedding)
                VALUES (%s, %s, %s, %s, %s, '{}', %s::vector)
                """,
                (project_id, source_path, page, section, txt, _to_pgvector(emb)),
            )
            inserted += 1
    print(f"[ingested] {inserted} chunks from {ocr_json_path.name}")
    return inserted

def main():
    parser = argparse.ArgumentParser(description="Ingest OlmOCR JSON into Postgres (pgvector)")
    parser.add_argument("--project-id", type=int, required=True, help="Internal project id")
    parser.add_argument("--source", type=str, required=True, help="Original brochure path or label")
    parser.add_argument("--ocr-json", type=str, required=True, help="Path to OlmOCR JSON file")
    parser.add_argument("--min-len", type=int, default=200, help="Minimum characters per chunk")
    parser.add_argument("--debug", action="store_true", help="Print cleaned chunk previews before inserting")
    parser.add_argument("--dry-run", action="store_true", help="Stop after cleaning (no embeddings/DB insert)")
    parser.add_argument("--no-dedup", action="store_true", help="Disable header/footer deduplication across pages")
    args = parser.parse_args()

    count = ingest_ocr_json(
        project_id=args.project_id,
        source_path=args.source,
        ocr_json_path=Path(args.ocr_json),
        min_len=args.min_len,
        debug=args.debug,
        dry_run=args.dry_run,
        deduplicate=not args.no_dedup,
    )
    print(f"[done] total inserted: {count}")

if __name__ == "__main__":
    main()
