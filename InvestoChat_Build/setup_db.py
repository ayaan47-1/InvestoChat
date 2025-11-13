import argparse
import json
import os
from pathlib import Path
from typing import List, Optional

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCHEMA_PATH = Path(__file__).parent / "db" / "schema.sql"


def _require_db_url():
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL not set; add it to InvestoChat_Build/.env")


def _require_openai():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY not set; add it to InvestoChat_Build/.env before embedding facts.")


def _split_sql_script(script: str) -> List[str]:
    statements: List[str] = []
    current: List[str] = []
    in_single = False
    in_double = False
    in_line_comment = False
    dollar_tag: Optional[str] = None
    length = len(script)
    i = 0

    def _match_dollar(idx: int) -> Optional[str]:
        if idx + 1 >= length:
            return None
        j = idx + 1
        while j < length and script[j] not in ("$", "\n", "\r"):
            if not script[j].isalnum() and script[j] != "_":
                break
            j += 1
        if j < length and script[j] == "$":
            return script[idx : j + 1]
        return None

    while i < length:
        ch = script[i]
        current.append(ch)

        if ch == "\n" and in_line_comment:
            in_line_comment = False

        if dollar_tag:
            if script.startswith(dollar_tag, i):
                remaining = script[i + 1 : i + len(dollar_tag)]
                if remaining:
                    current.append(remaining)
                i += len(dollar_tag) - 1
                dollar_tag = None
        elif not in_line_comment and ch == "'":
            prev = script[i - 1] if i > 0 else ""
            if prev != "\\":
                in_single = not in_single
        elif not in_line_comment and ch == '"':
            prev = script[i - 1] if i > 0 else ""
            if prev != "\\":
                in_double = not in_double
        elif not in_line_comment and ch == "-" and i + 1 < length and script[i + 1] == "-" and not in_single and not in_double and dollar_tag is None:
            in_line_comment = True
        elif ch == '$' and not in_single and not in_double and not in_line_comment:
            tag = _match_dollar(i)
            if tag:
                remaining = script[i + 1 : i + len(tag)]
                if remaining:
                    current.append(remaining)
                i += len(tag) - 1
                dollar_tag = tag
        elif ch == ';' and not in_single and not in_double and dollar_tag is None and not in_line_comment:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def apply_schema():
    _require_db_url()
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"schema file missing: {SCHEMA_PATH}")
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = _split_sql_script(script)
    with psycopg.connect(DATABASE_URL) as con, con.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)
        con.commit()
    print(f"[schema] applied {len(statements)} statements from {SCHEMA_PATH}")


def list_projects():
    _require_db_url()
    with psycopg.connect(DATABASE_URL) as con, con.cursor() as cur:
        cur.execute("SELECT id, name, slug, COALESCE(whatsapp,'') FROM projects ORDER BY id")
        rows = cur.fetchall()
    if not rows:
        print("no projects yet")
        return
    for row in rows:
        pid, name, slug, whatsapp = row
        slug_part = f" ({slug})" if slug else ""
        wa_part = f" whatsapp={whatsapp}" if whatsapp else ""
        print(f"- #{pid} {name}{slug_part}{wa_part}")


def add_project(name: str, slug: Optional[str], whatsapp: Optional[str], source_root: Optional[str], meta: Optional[str]):
    _require_db_url()
    meta_json = json.loads(meta) if meta else {}
    with psycopg.connect(DATABASE_URL) as con, con.cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (name, slug, whatsapp, source_root, meta)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (name, slug, whatsapp, source_root, json.dumps(meta_json)),
        )
        pid = cur.fetchone()[0]
        con.commit()
    print(f"[projects] inserted #{pid} {name}")


def _embed(value: str) -> List[float]:
    _require_openai()
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=[value])
    return resp.data[0].embedding


def _to_pgvector(vec: Optional[List[float]]) -> Optional[str]:
    if vec is None:
        return None
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def upsert_fact(project_id: int, key: str, value: str, source_page: Optional[str], meta: Optional[str], embed: bool):
    _require_db_url()
    vector = _embed(value) if embed else None
    meta_json = json.loads(meta) if meta else {}
    with psycopg.connect(DATABASE_URL) as con, con.cursor() as cur:
        cur.execute(
            """
            INSERT INTO facts (project_id, key, value, source_page, meta, embedding)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector)
            ON CONFLICT (project_id, key)
            DO UPDATE SET value=EXCLUDED.value,
                          source_page=EXCLUDED.source_page,
                          meta=EXCLUDED.meta,
                          embedding=EXCLUDED.embedding,
                          created_at=NOW()
            """,
            (project_id, key, value, source_page, json.dumps(meta_json), _to_pgvector(vector)),
        )
        con.commit()
    print(f"[facts] upserted ({project_id}, {key})")


def main():
    parser = argparse.ArgumentParser(description="Database utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("schema", help="Apply schema.sql to DATABASE_URL")

    list_parser = sub.add_parser("projects-list", help="List existing projects")

    proj_add = sub.add_parser("projects-add", help="Insert a new project")
    proj_add.add_argument("--name", required=True)
    proj_add.add_argument("--slug")
    proj_add.add_argument("--whatsapp")
    proj_add.add_argument("--source-root")
    proj_add.add_argument("--meta", help='JSON metadata, e.g. \'{"city":"Gurgaon"}\'')

    fact = sub.add_parser("facts-upsert", help="Insert or update a curated fact")
    fact.add_argument("--project-id", type=int, required=True)
    fact.add_argument("--key", required=True)
    fact.add_argument("--value", required=True)
    fact.add_argument("--source-page")
    fact.add_argument("--meta", help="JSON metadata string")
    fact.add_argument("--no-embed", action="store_true", help="Skip embedding (stores NULL)")

    args = parser.parse_args()

    if args.cmd == "schema":
        apply_schema()
    elif args.cmd == "projects-list":
        list_projects()
    elif args.cmd == "projects-add":
        add_project(args.name, args.slug, args.whatsapp, args.source_root, args.meta)
    elif args.cmd == "facts-upsert":
        upsert_fact(args.project_id, args.key, args.value, args.source_page, args.meta, embed=not args.no_embed)
    else:
        parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
