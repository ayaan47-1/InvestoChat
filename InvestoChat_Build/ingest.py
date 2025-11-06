import os
import argparse
import hashlib
from pathlib import Path
from typing import Tuple

import pandas as pd
from chromadb import CloudClient, PersistentClient
from cleaner import normalize_structured_text as normalize_text
from dotenv import load_dotenv

# Config 

load_dotenv()
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
DATA_DIR = Path("data/clean")
COLLECTION_NAME = "investochat_projects"

missing_chroma_creds = (not CHROMA_API_KEY) or (not CHROMA_TENANT)
client = (
    PersistentClient(path=".chroma")
    if missing_chroma_creds
    else CloudClient(api_key=CHROMA_API_KEY, tenant=CHROMA_TENANT, database="InvestoChat")
)
if missing_chroma_creds:
    print("[warning] Missing Chroma Cloud credentials → using local PersistentClient at ./.chroma")


# Helpers

def get_collection(reset: bool = False):
    """Create or reset the target collection."""
    if reset:
        try:
            names = [c.name for c in client.list_collections()]
            if COLLECTION_NAME in names:
                client.delete_collection(COLLECTION_NAME)
                print(f"[deleted] old '{COLLECTION_NAME}' collection.")
        except Exception as e:
            print(f"[warn] could not list/delete collections: {e}")
    return client.get_or_create_collection(COLLECTION_NAME)


def _read_file(fp: Path) -> pd.DataFrame:
    """Load CSV/XLSX into a dataframe with empty strings instead of NaN."""
    if fp.suffix.lower() == ".csv":
        df = pd.read_csv(fp, encoding="utf-8-sig")
    elif fp.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(fp)
    else:
        raise ValueError(f"Unsupported file type: {fp.suffix}")
    return df.fillna("")


def _row_to_doc(row: pd.Series) -> Tuple[str, dict]:
    """Flatten a row to a normalized document string and its metadata."""
    # Concatenate all cell values into one text blob
    text = " ".join(map(str, row.values))
    text = normalize_text(text)
    meta = {}
    return text, meta


def _stable_id(prefix: str, row: pd.Series, idx: int) -> str:
    """Stable ID using sha1 of the raw row values plus index."""
    raw = "|".join(map(str, row.values))
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{idx}_{h}"


# Ingest function

def ingest_file(collection, file_path: Path):
    df = _read_file(file_path)
    if df.empty:
        print(f"[skip] {file_path} has no rows")
        return 0

    prefix = file_path.stem.lower().replace(" ", "_")

    docs = []
    metas = []
    ids   = []

    for i, (_, row) in enumerate(df.iterrows()):
        doc, extra_meta = _row_to_doc(row)
        if not doc.strip():
            continue

        _id = _stable_id(prefix, row, i)
        section = str(row.get("Section", "")).strip()

        docs.append(doc)
        metas.append({
            "doc_id":  _id,
            "project": prefix,
            "section": section,
            "source":  file_path.name,
            **extra_meta,
        })
        ids.append(_id)

    if not docs:
        print(f"[skip] {file_path} produced no documents after cleaning")
        return 0

    collection.add(documents=docs, metadatas=metas, ids=ids)
    print(f"[ingested] {len(docs):4d} rows from {file_path}")   
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Ingest CSV/XLSX project data into Chroma")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the collection before ingesting")
    parser.add_argument("--data", type=str, default=str(DATA_DIR), help="Folder containing CSV/XLSX files")
    args = parser.parse_args()

    data_dir = Path(args.data)
    if not data_dir.exists():
        raise SystemExit(f"[error] Data folder not found: {data_dir}")

    collection = get_collection(reset=args.reset)

    added_total = 0
    for fp in sorted(data_dir.glob("*")):
        if fp.suffix.lower() in {".csv", ".xlsx", ".xls"}:
            added_total += ingest_file(collection, fp)

    print(
        f"\n[done] Ingested {added_total} documents. Collection '{collection.name}' now has {collection.count()} documents."
    )


if __name__ == "__main__":
    main()