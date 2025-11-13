#!/usr/bin/env python3
"""
Test script for document_tables retrieval
"""

import os
import psycopg
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _embed_text(text: str):
    """Generate embedding for query text."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return resp.data[0].embedding


def _to_pgvector(vec):
    """Convert embedding list to pgvector format string."""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def test_table_retrieval(query: str, table_type: str = None, project_id: int = None, k: int = 5):
    """
    Test retrieval of labeled tables.

    Args:
        query: Search query
        table_type: Filter by table type (payment_plan, unit_specifications, etc.)
        project_id: Filter by project
        k: Number of results
    """
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    if table_type:
        print(f"Filter: table_type = '{table_type}'")
    if project_id:
        print(f"Filter: project_id = {project_id}")
    print(f"{'='*80}\n")

    # Generate query embedding
    query_vec = _embed_text(query)
    query_vec_str = _to_pgvector(query_vec)

    # Build SQL with filters
    filters = []
    filter_params = []

    if project_id:
        filters.append("project_id = %s")
        filter_params.append(project_id)

    if table_type:
        filters.append("table_type = %s")
        filter_params.append(table_type)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    # Note: WHERE clause placeholders come before vector placeholders in params order
    sql = f"""
        SELECT
            dt.source_path,
            dt.page,
            dt.table_type,
            dt.summary,
            dt.markdown_content,
            1 - (dt.embedding <=> vec.query_embedding) as similarity
        FROM document_tables dt,
        LATERAL (SELECT %s::vector as query_embedding) vec
        {where_clause}
        ORDER BY dt.embedding <=> vec.query_embedding
        LIMIT %s
    """

    # Build params: [query_vec_str, filter_params..., k]
    params = [query_vec_str] + filter_params + [k]

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                results = cur.fetchall()

                if not results:
                    print("❌ No tables found\n")
                    return

                print(f"✅ Found {len(results)} table(s):\n")

                for i, (source, page, ttype, summary, markdown, sim) in enumerate(results, 1):
                    print(f"{i}. {source} p.{page} [{ttype}] (similarity: {sim:.3f})")
                    print(f"   Summary: {summary}")
                    print(f"\n   Content preview:")
                    lines = markdown.split('\n')[:5]
                    for line in lines:
                        print(f"   {line}")
                    all_lines = markdown.split('\n')
                    if len(all_lines) > 5:
                        print(f"   ... ({len(all_lines) - 5} more lines)")
                    print()

    except Exception as e:
        print(f"❌ Error: {e}\n")


def main():
    print("\n" + "="*80)
    print("TABLE RETRIEVAL TEST SUITE")
    print("="*80)

    # Test 1: Find payment plans
    test_table_retrieval(
        query="What is the payment plan?",
        table_type="payment_plan"
    )

    # Test 2: Find unit specifications
    test_table_retrieval(
        query="Show me unit sizes and BHK configurations",
        table_type="unit_specifications",
        k=3
    )

    # Test 3: Find all tables for Trevoc 56 (project_id = 2)
    test_table_retrieval(
        query="property details",
        project_id=2,
        k=5
    )

    # Test 4: Find amenities
    test_table_retrieval(
        query="What amenities are available?",
        table_type="amenities"
    )

    # Test 5: Open search (no filters)
    test_table_retrieval(
        query="payment milestones and construction schedule",
        k=3
    )

    print("\n" + "="*80)
    print("✅ All tests complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
