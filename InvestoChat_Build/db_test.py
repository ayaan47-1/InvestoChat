import os, sys
import psycopg

# Load variables from InvestoChat_Build/.env if present
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

dsn = os.getenv("DATABASE_URL")
if not dsn:
    sys.stderr.write(
        "ERROR: DATABASE_URL not set.\n"
        "Add this line to InvestoChat_Build/.env:\n"
        "  DATABASE_URL=postgresql://investo:change_me@localhost:5432/investochat\n"
    )
    sys.exit(1)

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("select 'ok', current_database(), version();")
        print(cur.fetchone())