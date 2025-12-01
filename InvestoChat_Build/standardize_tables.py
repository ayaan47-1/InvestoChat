#!/usr/bin/env python3
"""
Standardize document_tables across all projects.
Ensures every project has entries for: payment_plan, unit_specifications, pricing, amenities
Missing data is filled with "Not found in documents" placeholders.
"""

import os
import psycopg
from dotenv import load_dotenv
from typing import List

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Standard table types every project should have
STANDARD_TABLE_TYPES = [
    "payment_plan",
    "unit_specifications",
    "pricing",
    "amenities"
]


def _embed_text(text: str) -> List[float]:
    """Generate embedding for placeholder text"""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return resp.data[0].embedding


def _to_pgvector(vec: List[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def get_projects():
    """Get all project IDs and names"""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, slug FROM projects ORDER BY id")
            return cur.fetchall()


def get_existing_table_types(project_id: int):
    """Get table types that already exist for a project"""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT table_type
                FROM document_tables
                WHERE project_id = %s
            """, (project_id,))
            return {row[0] for row in cur.fetchall()}


def create_placeholder_table(project_id: int, project_name: str, table_type: str):
    """Create a placeholder table entry for missing data"""

    # Create placeholder markdown content
    placeholder_markdown = f"""# {table_type.replace('_', ' ').title()}

**Status**: Not found in documents

The {project_name} brochure does not contain structured information about {table_type.replace('_', ' ')}.

Please contact the developer directly for:
- Payment plan details
- Unit specifications
- Pricing information
- Complete amenities list
"""

    # Create summary
    summary = f"{table_type.replace('_', ' ').title()} information is not available in the {project_name} brochure."

    # Generate embedding for the placeholder
    embed_text = f"{summary}\n\n{placeholder_markdown}"
    embedding = _embed_text(embed_text)

    # Insert placeholder
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO document_tables (
                    project_id, source_path, page,
                    table_type, table_format, row_count, col_count,
                    markdown_content, original_content, summary, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
            """, (
                project_id,
                "placeholder",  # No actual source file
                None,           # No page number
                table_type,
                "placeholder",
                0,              # 0 rows
                0,              # 0 cols
                placeholder_markdown,
                "",             # No original content
                summary,
                _to_pgvector(embedding)
            ))
        conn.commit()

    print(f"    ✓ Created placeholder for {table_type}")


def standardize_all_projects():
    """Ensure all projects have all standard table types"""

    print("🔧 Standardizing Tables Across All Projects")
    print("=" * 70)

    projects = get_projects()

    print(f"\n📋 Standard table types: {', '.join(STANDARD_TABLE_TYPES)}")
    print(f"📁 Processing {len(projects)} projects...\n")

    total_created = 0

    for project_id, project_name, project_slug in projects:
        print(f"\n🏗️  {project_name} (ID: {project_id})")

        # Get existing table types
        existing_types = get_existing_table_types(project_id)
        print(f"  Existing: {', '.join(sorted(existing_types)) if existing_types else 'None'}")

        # Find missing types
        missing_types = set(STANDARD_TABLE_TYPES) - existing_types

        if not missing_types:
            print(f"  ✅ All standard tables present")
            continue

        print(f"  📝 Missing: {', '.join(sorted(missing_types))}")
        print(f"  Creating placeholders...")

        # Create placeholders for missing types
        for table_type in sorted(missing_types):
            create_placeholder_table(project_id, project_name, table_type)
            total_created += 1

    print("\n" + "=" * 70)
    print(f"✅ Standardization complete! Created {total_created} placeholder tables")

    # Show final summary
    print("\n📊 Final Summary:")
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    p.name,
                    COUNT(CASE WHEN dt.table_type = 'payment_plan' THEN 1 END) as payment_plan,
                    COUNT(CASE WHEN dt.table_type = 'unit_specifications' THEN 1 END) as unit_specs,
                    COUNT(CASE WHEN dt.table_type = 'pricing' THEN 1 END) as pricing,
                    COUNT(CASE WHEN dt.table_type = 'amenities' THEN 1 END) as amenities,
                    COUNT(*) as total
                FROM projects p
                LEFT JOIN document_tables dt ON p.id = dt.project_id
                GROUP BY p.name
                ORDER BY p.name
            """)

            print(f"\n{'Project':<25} {'Payment':<10} {'Units':<10} {'Pricing':<10} {'Amenities':<10} {'Total':<10}")
            print("-" * 75)

            for row in cur.fetchall():
                name, payment, units, pricing, amenities, total = row
                print(f"{name:<25} {payment:<10} {units:<10} {pricing:<10} {amenities:<10} {total:<10}")


if __name__ == "__main__":
    standardize_all_projects()
