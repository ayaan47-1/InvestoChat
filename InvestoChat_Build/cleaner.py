import re
try:
    import ftfy  # optional; fixes bad unicode artifacts from PDFs (e.g., “Â€”)
    _HAS_FTFY = True
except Exception:
    _HAS_FTFY = False

# -----------------------------------------------------------------------------
# Cleaner for brochure-first OCR pipeline (storage + search safe)
# -----------------------------------------------------------------------------
# Purpose:
# - Remove brochure chrome that appears as standalone lines (headers/footers).
# - Redact inline PII (phones, emails) and URLs.
# - Normalize bullets and whitespace.
# - Preserve finance/legal terms (GST, PLC, IDC, EDC, Stamp duty, Registration, TDS).
# - Preserve RERA references; normalize label spelling.
#
# Use:
#   text = clean_brochure_text(raw_ocr_text)
#   chunks = drop_too_small_chunks(chunks, min_len=200)
#
# Notes:
# - Keep this narrowly focused on OCR text. Do NOT use on curated DB fields.
# - CSV/structured text normalization is out of scope here.
# -----------------------------------------------------------------------------

# Lines that are safe to drop when they appear as their own line
NOISE_LINES = re.compile(
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
        PRIVACY\s*POLICY|COOKIE\s*POLICY|
        COPYRIGHT|ALL\s*RIGHTS\s*RESERVED|
        FOLLOW\s*US|CONNECT\s*WITH\s*US|
        QR\s*CODE|SCAN\s*TO\s*(?:VIEW|DOWNLOAD|CALL|WHATSAPP)?|
        CALL|EMAIL|PHONE|MOBILE|WHATSAPP|WEBSITE|
        FACEBOOK|INSTAGRAM|YOUTUBE|LINKEDIN|TWITTER|X
    )\s*:?\s*$
    """,
    flags=0,
)

# Inline redactions that should not be indexed or stored verbatim
REDACT_INLINE = re.compile(
    r"""(?ix)
    (https?://\S+|www\.[^\s]+)                         # URLs
    |(\b[\w.+-]+@[\w-]+\.[\w.-]+\b)                    # Emails
    |(\+?\d[\d\s().-]{6,}\d)                           # Phone-like long numbers
    """
)

# RERA label normalizer (keep content, tidy label)
RERA_NORMALIZE = re.compile(r'(?i)\bRERA\s*(?:No\.?|Number)?\s*:\s*')

def _fix_unicode(s: str) -> str:
    if _HAS_FTFY:
        try:
            return ftfy.fix_text(s)
        except Exception:
            return s
    return s

def clean_brochure_text(s: str) -> str:
    """
    Clean raw brochure text extracted via OCR before storing/searching.
    - Fix unicode artifacts
    - Normalize bullets to "- "
    - Drop line-only brochure chrome
    - Redact URLs/emails/phones
    - Keep finance/legal tokens (GST, PLC, IDC, EDC, Stamp duty, Registration, TDS)
    - Normalize 'RERA No: ' label while preserving the number/text
    - Collapse whitespace
    """
    if not s:
        return s
    s = _fix_unicode(s)

    # Standardize bullets
    s = s.replace("•", "- ")

    # Drop line-only brochure chrome
    s = "\n".join([ln for ln in s.splitlines() if not NOISE_LINES.match(ln)])

    # Redact inline PII/links
    s = REDACT_INLINE.sub("[REDACTED]", s)

    # Normalize RERA label (content preserved)
    s = RERA_NORMALIZE.sub("RERA No: ", s)

    # Whitespace normalization
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def drop_too_small_chunks(chunks, min_len: int = 200):
    """Filter out tiny text chunks before storing or searching."""
    return [c for c in chunks if isinstance(c, str) and len(c.strip()) >= min_len]

# Optional helper alias for clarity without breaking imports elsewhere
def drop_tiny_chunks(chunks, min_len: int = 200):
    """Alias of drop_too_small_chunks."""
    return drop_too_small_chunks(chunks, min_len)