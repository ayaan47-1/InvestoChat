import re
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from rapidfuzz import fuzz
    HAS_FUZZ = True
except Exception:
    HAS_FUZZ = False

RAW_DIR   = Path("data") 
OUT_DIR   = Path("data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# light normalizers for text fields
BULLETS = {"•": "- ", "–": "-", "—": "-", "·": "- "}
WS_RX   = re.compile(r"[ \t]+")
NL_RX   = re.compile(r"\n{3,}")

def fix_unicode(s: str) -> str:
    if not isinstance(s, str): s = "" if s is None else str(s)
    for k,v in BULLETS.items(): s = s.replace(k, v)
    s = s.replace("\u00a0", " ")
    s = WS_RX.sub(" ", s)
    s = NL_RX.sub("\n\n", s)
    return s.strip()

# canonical column mappings
CANON = {
    "section": {"section","Section","SECTION"},
    "project": {"Project","Project Name","project","PROJECT"},
    "developer": {"Developer","Developer Name"},
    "location": {"Location","City/Location"},
    "pricing": {"Price","Pricing","Base Price","Rate"},
    "unit_types": {"Unit Types","Configuration","BHK","Typology"},
    "sizes": {"Sizes","Area","Carpet Area","Super Area"},
    "payment_plan": {"Payment Plan","Plan","Milestones"},
    "description": {"Description","Overview","Highlights","Features"},
}

def canon_cols(cols: List[str]) -> Dict[str,int]:
    lc = {c.lower(): i for i,c in enumerate(cols)}
    out = {}
    for key, aliases in CANON.items():
        for a in aliases:
            if a in cols: out[key] = cols.index(a); break
            if a.lower() in lc: out[key] = lc[a.lower()]; break
    return out

def read_any_csv(path: Path) -> Tuple[List[str], List[List[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))
    if not reader: return [], []
    header, rows = reader[0], reader[1:]
    return header, rows

def row_to_record(header: List[str], row: List[str], src: str) -> Dict:
    idx = canon_cols(header)
    get = lambda k: fix_unicode(row[idx[k]]).strip() if k in idx and idx[k] < len(row) else ""
    # build a text blob for description if missing
    blob = fix_unicode(" ".join(row))
    return {
        "project":      get("project"),
        "section":      get("section"),
        "developer":    get("developer"),
        "location":     get("location"),
        "pricing":      get("pricing"),
        "unit_types":   get("unit_types"),
        "sizes":        get("sizes"),
        "payment_plan": get("payment_plan"),
        "description":  get("description") or blob,  # fill from all row if empty
        "text":         blob,
        "source":       src,
    }

def load_all(raw_dir: Path) -> List[Dict]:
    recs = []
    for fp in sorted(raw_dir.glob("*.csv")):
        header, rows = read_any_csv(fp)
        if not header: 
            print(f"[skip] empty file: {fp}")
            continue
        for r in rows:
            if not any(cell.strip() for cell in r): 
                continue
            recs.append(row_to_record(header, r, fp.name))
        print(f"[read] {fp.name}: {len(rows)} rows")
    return recs

# exact key for dedupe
def key_exact(rec: Dict) -> Tuple:
    return (
        rec["project"].casefold(),
        rec["section"].casefold(),
        rec["description"].casefold(),
        rec["payment_plan"].casefold(),
    )

def near_dupe(a: Dict, b: Dict) -> bool:
    if (a["project"].casefold(), a["section"].casefold()) != (b["project"].casefold(), b["section"].casefold()):
        return False
    if not HAS_FUZZ:
        return False
    # 85% similarity on description blob
    return fuzz.token_set_ratio(a["description"], b["description"]) >= 85

def dedupe(recs: List[Dict]) -> Tuple[List[Dict], Dict[str,int]]:
    seen = set()
    keep: List[Dict] = []
    removed = {"exact":0, "near":0}
    for r in recs:
        k = key_exact(r)
        if k in seen:
            removed["exact"] += 1
            continue
        # look back a bit for near dupes within same project+section
        if HAS_FUZZ:
            clash = next((x for x in keep if near_dupe(x, r)), None)
            if clash:
                removed["near"] += 1
                continue
        seen.add(k)
        keep.append(r)
    return keep, removed

def write_csv(path: Path, rows: List[Dict]):
    cols = ["project","section","developer","location","pricing","unit_types","sizes","payment_plan","description","source"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in cols})

def main():
    raw = load_all(RAW_DIR)
    print(f"[total raw] {len(raw)} rows")
    cleaned, removed = dedupe(raw)
    print(f"[kept] {len(cleaned)}  [removed exact] {removed['exact']}  [removed near] {removed['near']}  (fuzzy={'on' if HAS_FUZZ else 'off'})")

    master = OUT_DIR / "clean_projects.csv"
    write_csv(master, cleaned)
    print(f"[write] {master}")

    # per-project splits
    by_proj: Dict[str, List[Dict]] = {}
    for r in cleaned:
        by_proj.setdefault(r["project"] or "unknown_project", []).append(r)
    for proj, rows in by_proj.items():
        safe = re.sub(r"[^a-z0-9_]+","_", proj.lower().strip()) or "unknown"
        write_csv(OUT_DIR / f"clean_{safe}.csv", rows)
    print(f"[per-project] wrote {len(by_proj)} files to {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()