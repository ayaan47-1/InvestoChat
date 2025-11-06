import re
try:
    import ftfy  # optional; fixes bad unicode artifacts from PDFs (e.g., “Â€”)
    _HAS_FTFY = True
except Exception:
    _HAS_FTFY = False

# Regex for stripping brochure/page chrome from RAW PDF text only.
NOISE_PHRASES = re.compile(
    r"""(?imx)
    ^\s*(
        E-?BROCHURE|BROCHURE|
        SITE\s*PLAN|MASTER\s*PLAN|
        LOCATION(?:\s*MAP)?|APPLICATION\s*FORM|
        UNIT\s*PLAN|FLOOR\s*PLAN|WALK\s*THROUGH|
        IMAGES?|GALLERY|
        CONTACT|ENQUIRE\s*NOW|
        TERMS\s*&\s*CONDITIONS?|DISCLAIMER|LEGAL\s*DISCLAIMER|
        NOTES?|T&C|E&OE|
        RERA(?:\s*(?:NO\.?|NUMBER))?|UP\s*RERA|HARYANA\s*RERA|
        PRIVACY\s*POLICY|COOKIE\s*POLICY|
        COPYRIGHT|ALL\s*RIGHTS\s*RESERVED|
        FOLLOW\s*US|CONNECT\s*WITH\s*US|
        QR\s*CODE|SCAN\s*TO\s*(?:VIEW|DOWNLOAD|CALL|WHATSAPP)?|
        CALL|EMAIL|PHONE|MOBILE|WHATSAPP|WEBSITE|
        FACEBOOK|INSTAGRAM|YOUTUBE|LINKEDIN|TWITTER|X
    )\s*:?
    \s*$
    |
    (Artist'?s\s*impression|Not\s*to\s*scale|For\s*representation\s*only|E&OE|
     GST\s*extra|GST\s*as\s*applicable|PLC|IDC|EDC|Stamp\s*duty|Registration|TDS|
     Cheque\s*in\s*favour\s*of|Bank\s*details)
    |
    (https?://\S+|www\.[^\s]+)
    |
    (\b[\w.+-]+@[\w-]+\.[\w.-]+\b|\+?\d[\d\s().-]{6,}\d)
    """,
    flags=0,
)

def _fix_unicode(s: str) -> str:
    if _HAS_FTFY:
        try:
            return ftfy.fix_text(s)
        except Exception:
            return s
    return s

# -----------------------------
# Public API (two normalizers)
# -----------------------------

def normalize_pdf_text(s: str) -> str:
    """Aggressive cleaner for RAW PDF text. Removes brochure chrome and artifacts.
    Use this ONLY for text extracted from PDFs.
    """
    if not s:
        return s
    s = _fix_unicode(s)
    s = s.replace("•", "- ")
    s = NOISE_PHRASES.sub("", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def normalize_structured_text(s: str) -> str:
    """Light normalizer for CSV/XLSX cells and other curated text.
    Keeps content, only fixes spacing and bullets. Safe for all projects.
    """
    if not isinstance(s, str):
        return ""
    s = s.replace("\n", " ").replace("•", "- ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Backward-compat shim: legacy imports will still work
# (main.py may import `normalize_text`; map it to structured version by default.)
normalize_text = normalize_structured_text

# Optional: keep if you still chunk long fields elsewhere
def drop_too_small_chunks(chunks, min_len: int = 200):
    """Filter out tiny chunks that add noise to embeddings.
    Safe no-op for CSV rows treated as single docs.
    """
    return [c for c in chunks if isinstance(c, str) and len(c.strip()) >= min_len]