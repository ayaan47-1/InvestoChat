"""
Automated ingestion helper.

Scans a brochure root (default: ./brochures) for supported files (pdf/jpg/png),
detects new or modified files via a manifest stored under workspace/,
and pipes each file through the existing OCR → ingest pipeline.

Usage examples:
  python auto_ingest.py --project-id 42
  python auto_ingest.py --project-id 42 --root brochures/tarc --min-len 300
  python auto_ingest.py --project-map workspace/projects.json --loop 60
"""
from __future__ import annotations

import argparse
import json
import time
import logging
from pathlib import Path
from typing import Dict, Iterable, Optional

from process_pdf import SUPPORTED_EXTS, run_one

HERE = Path(__file__).parent
WORKSPACE = HERE / "workspace"
STATE_PATH = WORKSPACE / "ingest_state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
LOG = logging.getLogger("auto_ingest")


def load_state() -> Dict[str, dict]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        LOG.warning("could not read %s (%s); starting fresh", STATE_PATH, exc)
        return {}


def save_state(state: Dict[str, dict]) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def needs_ingest(state: Dict[str, dict], path: Path) -> bool:
    entry = state.get(str(path))
    mtime = path.stat().st_mtime
    return not entry or entry.get("mtime", 0) < mtime


def resolve_project_and_source(path: Path, project_id: Optional[int], source: Optional[str], root: Path) -> tuple[int, str]:
    if project_id is None:
        raise SystemExit("project id missing; pass --project-id or provide a project map entry.")
    label = source or str(path.parent.relative_to(root))
    return project_id, label


def load_project_map(map_path: Optional[Path]) -> Dict[str, int]:
    if not map_path:
        return {}
    if not map_path.exists():
        raise SystemExit(f"project map not found: {map_path}")
    raw = json.loads(map_path.read_text(encoding="utf-8"))
    out = {}
    for key, value in raw.items():
        out[str(Path(key))] = int(value)
    return out


def pick_project_id(path: Path, root: Path, project_id: Optional[int], project_map: Dict[str, int]) -> Optional[int]:
    if project_id is not None:
        return project_id
    for prefix, pid in project_map.items():
        prefix_path = Path(prefix)
        try:
            path.relative_to(prefix_path)
            return pid
        except ValueError:
            continue
    try:
        rel = path.relative_to(root)
        parts = rel.parts
    except ValueError:
        return None
    if parts:
        key = str(root / parts[0])
        if key in project_map:
            return project_map[key]
    return None


def ingest_once(
    root: Path,
    project_id: Optional[int],
    source: Optional[str],
    state: Dict[str, dict],
    min_len: int,
    project_map: Dict[str, int],
) -> int:
    processed = 0
    for file_path in iter_supported_files(root):
        if not needs_ingest(state, file_path):
            continue
        pid = pick_project_id(file_path, root, project_id, project_map)
        if pid is None:
            LOG.warning("skip %s (no project id mapping)", file_path)
            continue
        source_label = source or str(file_path.parent.relative_to(root))
        LOG.info("ingesting %s (project=%s, source=%s)", file_path, pid, source_label)
        try:
            run_one(str(file_path), pid, source_label, min_len=min_len)
        except SystemExit as exc:
            LOG.error("ingest failed for %s: %s", file_path, exc)
            continue
        state[str(file_path)] = {"mtime": file_path.stat().st_mtime, "project_id": pid, "source": source_label}
        processed += 1
    if processed:
        save_state(state)
    return processed


def main():
    parser = argparse.ArgumentParser(description="Automatic brochure ingestion orchestrator")
    parser.add_argument("--root", type=Path, default=HERE / "brochures", help="Directory containing brochures (default: ./brochures)")
    parser.add_argument("--project-id", type=int, help="Project id for all files (unless overridden by --project-map)")
    parser.add_argument("--source", type=str, help="Optional static source label (defaults to relative folder)")
    parser.add_argument("--project-map", type=Path, help="JSON mapping of folder prefixes to project ids")
    parser.add_argument("--min-len", type=int, default=200, help="Minimum characters per chunk (default: 200)")
    parser.add_argument("--loop", type=int, help="If set, keep scanning every N seconds")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"root path not found: {root}")

    project_map = load_project_map(args.project_map)
    state = load_state()

    def run_cycle():
        count = ingest_once(root, args.project_id, args.source, state, args.min_len, project_map)
        LOG.info("cycle complete: %s new/updated files ingested", count)

    run_cycle()
    if not args.loop:
        return
    LOG.info("watching %s every %s seconds", root, args.loop)
    try:
        while True:
            time.sleep(args.loop)
            run_cycle()
    except KeyboardInterrupt:
        LOG.info("stopping on Ctrl+C")


if __name__ == "__main__":
    main()
