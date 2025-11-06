import re
try:
    import ftfy  # optional; fixes bad unicode artifacts from PDFs (e.g., “Â€”)
    _HAS_FTFY = True
except Exception:
    _HAS_FTFY = False

# -----------------------------------------------------------------------------
# Cleaner for brochure-first OCR pipeline
# -----------------------------------------------------------------------------
# Purpose:
# - Remove brochure chrome (headers/footers like "BROCHURE", "CONTACT", social links)
# - Strip phone numbers, emails, and URLs
# - Normalize bullets and whitespace
#
# Use:
#   text = clean_brochure_text(raw_ocr_text)
#   chunks = drop_too_small_chunks(chunks, min_len=200)
#
# Notes:
# - Keep this narrowly focused on OCR text. Do NOT use on curated DB fields.
# - CSV/structured text normalization has been removed from this file.
# -----------------------------------------------------------------------------

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

def clean_brochure_text(s: str) -> str:
    """
    Clean raw brochure text extracted via OCR before embeddings.
    - Fix broken unicode
    - Normalize bullets
    - Remove boilerplate chrome, contacts, and links
    - Collapse excessive whitespace
    """
    if not s:
        return s
    s = _fix_unicode(s)
    s = s.replace("•", "- ")
    s = NOISE_PHRASES.sub("", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def drop_too_small_chunks(chunks, min_len: int = 200):
    """Filter out tiny chunks that add noise to embeddings."""
    return [c for c in chunks if isinstance(c, str) and len(c.strip()) >= min_len]