#!/usr/bin/env python3
"""
process_pdf.py

Minimal, robust brochure OCR pipeline using per-page rasterization + DeepInfra OLMoCR.

Inputs
------
- Path to a single PDF or a directory containing PDFs.
- Outputs a JSONL per PDF (one line per page) and an optional merged Markdown.

Requirements
------------
- PyMuPDF (fitz)
- requests

Environment
-----------
- DEEPINFRA_API_KEY: 
- OLMOCR_MODEL (optional): defaults to "allenai/olmOCR-2-7B-1025"

Examples
--------
python process_pdf.py ./Investochat_build/brochures ./output_ocr --dpi 300 --merge-md
python process_pdf.py ./Investochat_build/brochures/Godrej_SORA.pdf ./output_ocr

Notes
-----
- Default mode is per-page OCR. This is more reliable than rasterizing the full PDF into a single giant image.
- The prompt biases the model to transcribe text faithfully and to render tables as Markdown where possible.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from typing import Tuple

import fitz  # PyMuPDF
import requests

OPENAI_API = "https://api.deepinfra.com/v1/openai/chat/completions"

DEFAULT_MODEL = os.getenv("OLMOCR_MODEL", "allenai/olmOCR-2-7B-1025")

PROMPT = (
    "You are an OCR engine. Task: transcribe the page image exactly. "
    "Do not add content. Preserve reading order. Use Markdown tables when the page contains tables. "
    "For lists, keep bullets. For headings, keep line breaks. Return only the transcription."
)


@dataclass
class OCRResult:
    pdf_path: Path
    page_index: int
    text: str


class DeepInfraOlmOCR:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: int = 180):
        if not api_key:
            raise RuntimeError("DEEPINFRA_API_KEY is not set")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _encode_image(self, img_path: Path) -> str:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return b64

    def ocr_image(self, img_path: Path, retries: int = 3, backoff: float = 2.0, timeout: Optional[int] = None) -> Tuple[str, Optional[str]]:
        b64 = self._encode_image(img_path)
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "max_tokens": 8192,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]
                }
            ]
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        timeout = timeout or self.timeout

        for attempt in range(1, retries + 1):
            try:
                t0 = time.time()
                resp = requests.post(OPENAI_API, headers=headers, json=payload, timeout=timeout)
                dt = time.time() - t0
                status = resp.status_code
                if status == 429:
                    raise RuntimeError("429 rate limited")
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"].get("content", "")
                if isinstance(content, list):
                    text = "".join(
                        block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") in ("text", "output_text")
                    )
                else:
                    text = content
                text = text.strip()
                print(f"[ocr-page] {img_path.name} attempt={attempt} status={status} dt={dt:.2f}s chars={len(text)}")
                return text, None
            except Exception as e:
                print(f"[warn] {img_path.name} attempt={attempt} error={e}")
                if attempt == retries:
                    return "", f"{e}"
                time.sleep(backoff * attempt)


def render_pdf_pages(pdf_path: Path, out_dir: Path, dpi: int = 220) -> List[Path]:
    """Render each page of PDF to PNG and return list of image file paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    paths: List[Path] = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        max_side = max(pix.width, pix.height)
        if max_side > 2600:
            factor = 2600.0 / max_side
            pix = page.get_pixmap(matrix=fitz.Matrix(scale * factor, scale * factor), alpha=False)
        out_path = out_dir / f"{pdf_path.stem}_p{i+1:04d}.png"
        pix.save(out_path)
        paths.append(out_path)
        print(f"[render-page] {pdf_path.name} -> {out_path.name} ({pix.width}x{pix.height})")
    doc.close()
    return paths


def iter_pdfs(input_path: Path) -> Iterable[Path]:
    if input_path.is_dir():
        for p in sorted(input_path.rglob("*.pdf")):
            yield p
    elif input_path.suffix.lower() == ".pdf":
        yield input_path
    else:
        raise ValueError(f"Unsupported input: {input_path}")


def write_jsonl(jsonl_path: Path, rows: List[dict]) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-page brochure OCR with OLMoCR via DeepInfra")
    parser.add_argument("input", type=Path, help="PDF file or directory of PDFs")
    parser.add_argument("output", type=Path, help="Directory for OCR outputs")
    parser.add_argument("--dpi", type=int, default=220, help="Rasterization DPI, default 220")
    parser.add_argument("--imgdir", type=Path, default=None, help="Optional directory to store page PNGs")
    parser.add_argument("--merge-md", action="store_true", help="Also write a merged Markdown per PDF")
    parser.add_argument("--rate-limit", type=float, default=0.0, help="Seconds to sleep between page OCR calls")
    parser.add_argument("--max-pages", type=int, default=None, help="Process at most N pages per PDF")
    parser.add_argument("--per-page-write", action="store_true", help="Append to JSONL after each page for live progress")
    args = parser.parse_args()

    api_key = os.getenv("DEEPINFRA_API_KEY", "").strip()
    ocr = DeepInfraOlmOCR(api_key=api_key, model=DEFAULT_MODEL)

    input_path: Path = args.input
    out_root: Path = args.output
    img_root: Optional[Path] = args.imgdir

    for pdf in iter_pdfs(input_path):
        pdf_slug = pdf.stem
        pdf_out_dir = out_root / pdf_slug
        img_dir = img_root or (pdf_out_dir / "images")
        img_dir.mkdir(parents=True, exist_ok=True)

        print(f"[render] {pdf}")
        page_imgs_all = render_pdf_pages(pdf, img_dir, dpi=args.dpi)
        page_imgs = page_imgs_all[: args.max_pages] if args.max_pages else page_imgs_all

        rows: List[dict] = []
        merged_text_parts: List[str] = []

        jsonl_path = pdf_out_dir / f"{pdf_slug}.jsonl"
        md_path = pdf_out_dir / f"{pdf_slug}.md"
        per_page_fp = open(jsonl_path, "a", encoding="utf-8") if args.per_page_write else None
        total = len(page_imgs)

        print(f"[ocr] {pdf} -> {total} pages")
        for idx, img in enumerate(page_imgs, start=1):
            try:
                text, err = ocr.ocr_image(img, retries=3, backoff=2.0, timeout=90)
            except Exception as e:
                text, err = "", f"{e}"
            row = {
                "pdf": str(pdf.resolve()),
                "page": idx,
                "image": str(img.resolve()),
                "text": text,
            }
            if err:
                row["error"] = err
            print(f"[page] {pdf_slug}: {idx}/{total} {'OK' if not err else 'ERR'}")
            rows.append(row)
            merged_text_parts.append(f"\n\n# Page {idx}\n\n" + (text or ""))
            if per_page_fp:
                per_page_fp.write(json.dumps(row, ensure_ascii=False) + "\n")
                per_page_fp.flush()
            if args.rate_limit > 0:
                time.sleep(args.rate_limit)

        if per_page_fp:
            per_page_fp.close()

        write_jsonl(jsonl_path, rows)
        print(f"[write] {jsonl_path} ({len(rows)} pages)")

        if args.merge_md:
            md_path.write_text("\n".join(merged_text_parts), encoding="utf-8")
            print(f"[write] {md_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.")
        raise
