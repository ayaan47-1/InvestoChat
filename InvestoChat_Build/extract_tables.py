#!/usr/bin/env python3
"""
Extract tables from OCR data and store them in document_tables with labels
"""

import os
import sys
import psycopg
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from table_processor import process_text_with_tables, get_table_summary

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for table summaries"""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]


def _to_pgvector(vec: List[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def create_tables_table():
    """Create the document_tables table if it doesn't exist"""
    with open("create_tables_table.sql", "r") as f:
        sql = f.read()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print("✅ document_tables table created/verified")


def extract_tables_from_ocr():
    """
    Extract tables from ocr_pages and store in document_tables
    """
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL not set")

    print("📊 Extracting tables from OCR data...")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Get all OCR pages
            cur.execute("""
                SELECT source_pdf, page, text, project
                FROM ocr_pages
                WHERE text LIKE '%<table>%' OR text LIKE '%|%|%'
                ORDER BY source_pdf, page
            """)
            ocr_pages = cur.fetchall()

    if not ocr_pages:
        print("⚠️  No pages with tables found")
        return 0

    print(f"Found {len(ocr_pages)} pages with potential tables")

    tables_inserted = 0

    for source_pdf, page, text, project in ocr_pages:
        # Extract source filename
        source_path = Path(source_pdf).name

        # Get project_id from projects table
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Try to match by source_path in documents table first
                cur.execute("""
                    SELECT DISTINCT project_id
                    FROM documents
                    WHERE source_path = %s
                    LIMIT 1
                """, (source_path,))
                result = cur.fetchone()

                if result:
                    project_id = result[0]
                else:
                    # Fallback: use project name if available
                    if project:
                        cur.execute("""
                            SELECT id FROM projects
                            WHERE LOWER(name) = LOWER(%s) OR slug = %s
                            LIMIT 1
                        """, (project, project.lower().replace(' ', '-')))
                        result = cur.fetchone()
                        project_id = result[0] if result else 1
                    else:
                        project_id = 1  # Default

        # Process tables in this page
        result = process_text_with_tables(text)

        if not result['tables']:
            continue

        print(f"  📄 {source_path} p.{page}: Found {len(result['tables'])} table(s)")

        # Generate embeddings for all tables on this page
        summaries = []
        for table in result['tables']:
            summary = get_table_summary(table)
            # Combine summary with markdown for better embedding
            embed_text = f"{summary}\n\n{table['markdown']}"
            summaries.append(embed_text)

        if summaries:
            embeddings = _embed_texts(summaries)
        else:
            embeddings = []

        # Insert tables
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for table, embedding in zip(result['tables'], embeddings):
                    summary = get_table_summary(table)

                    cur.execute("""
                        INSERT INTO document_tables (
                            project_id, source_path, page,
                            table_type, table_format, row_count, col_count,
                            markdown_content, original_content, summary, embedding
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                    """, (
                        project_id,
                        source_path,
                        page,
                        table['type'].value,
                        table['format'],
                        table['row_count'],
                        table['col_count'],
                        table['markdown'],
                        table['original'],
                        summary,
                        _to_pgvector(embedding)
                    ))

                    tables_inserted += 1
                    print(f"    ✓ {table['type'].value} table ({table['row_count']} rows)")

            conn.commit()

    return tables_inserted


def main():
    print("🔧 Table Extraction Pipeline")
    print("=" * 60)

    # Step 1: Create table
    print("\n1️⃣ Creating document_tables table...")
    create_tables_table()

    # Step 2: Extract tables
    print("\n2️⃣ Extracting tables from OCR data...")
    count = extract_tables_from_ocr()

    print("\n" + "=" * 60)
    print(f"✅ Extraction complete! Inserted {count} labeled tables")

    # Step 3: Show summary
    print("\n3️⃣ Summary by type:")
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_type, COUNT(*) as count
                FROM document_tables
                GROUP BY table_type
                ORDER BY count DESC
            """)
            for table_type, count in cur.fetchall():
                print(f"  - {table_type}: {count} tables")


if __name__ == "__main__":
    main()
