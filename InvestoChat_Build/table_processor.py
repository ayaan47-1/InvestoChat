"""
Table Processor for InvestoChat
Extracts, normalizes, and labels tables from OCR text for better retrieval
"""

import re
from typing import List, Dict, Tuple, Optional
from enum import Enum


class TableType(Enum):
    """Types of tables found in real estate brochures"""
    PAYMENT_PLAN = "payment_plan"
    UNIT_SPECS = "unit_specifications"
    PRICING = "pricing"
    AMENITIES = "amenities"
    LOCATION = "location"
    SPECIFICATIONS = "specifications"
    UNKNOWN = "unknown"


def detect_table_type(table_text: str, header_row: Optional[str] = None) -> TableType:
    """
    Detect what type of table this is based on content and headers.

    Args:
        table_text: Full table text
        header_row: First row of table (headers)

    Returns:
        TableType enum value
    """
    text_lower = table_text.lower()
    header_lower = (header_row or "").lower()

    # Payment plan indicators
    payment_indicators = [
        "payment", "milestone", "installment", "booking", "possession",
        "clp", "plp", "construction linked", "stage", "due", "amount"
    ]
    if any(ind in text_lower for ind in payment_indicators):
        if any(ind in header_lower for ind in ["payment", "milestone", "stage", "installment"]):
            return TableType.PAYMENT_PLAN

    # Pricing indicators
    pricing_indicators = ["price", "rate", "cost", "charge", "fee"]
    if any(ind in text_lower for ind in pricing_indicators):
        if "payment" not in text_lower:  # Not a payment plan
            return TableType.PRICING

    # Unit specifications
    unit_indicators = ["bhk", "carpet", "super area", "saleable", "sqft", "sq.ft", "unit"]
    if any(ind in text_lower for ind in unit_indicators):
        return TableType.UNIT_SPECS

    # Amenities
    amenity_indicators = ["amenity", "amenities", "facility", "club", "gym", "pool"]
    if any(ind in text_lower for ind in amenity_indicators):
        return TableType.AMENITIES

    # Location
    location_indicators = ["distance", "km", "mins", "location", "nearby", "proximity"]
    if any(ind in text_lower for ind in location_indicators):
        return TableType.LOCATION

    # Specifications
    spec_indicators = ["specification", "flooring", "fitting", "finishing", "details"]
    if any(ind in text_lower for ind in spec_indicators):
        return TableType.SPECIFICATIONS

    return TableType.UNKNOWN


def extract_html_table(text: str) -> List[Tuple[str, int, int]]:
    """
    Extract HTML tables from text.

    Returns:
        List of (table_html, start_pos, end_pos) tuples
    """
    pattern = r'<table>.*?</table>'
    tables = []
    for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
        tables.append((match.group(0), match.start(), match.end()))
    return tables


def html_table_to_markdown(html: str) -> str:
    """
    Convert HTML table to markdown table.

    Example:
        <table>
          <tr><th>Name</th><th>Value</th></tr>
          <tr><td>Price</td><td>1 Cr</td></tr>
        </table>

    Becomes:
        | Name | Value |
        |------|-------|
        | Price | 1 Cr |
    """
    # Extract rows
    rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

    if not rows:
        return html

    markdown_rows = []
    is_header = True

    for row in rows:
        # Extract cells (th or td)
        cells = re.findall(r'<t[hd]>(.*?)</t[hd]>', row, re.IGNORECASE)
        cells = [re.sub(r'<.*?>', '', cell).strip() for cell in cells]  # Remove inner tags

        if not cells:
            continue

        # Build markdown row
        markdown_rows.append('| ' + ' | '.join(cells) + ' |')

        # Add separator after first row (header)
        if is_header:
            markdown_rows.append('|' + '|'.join(['---' for _ in cells]) + '|')
            is_header = False

    return '\n'.join(markdown_rows)


def extract_pipe_tables(text: str, min_rows: int = 2) -> List[Tuple[str, int, int]]:
    """
    Extract pipe-delimited tables from text.

    A pipe table has at least min_rows consecutive lines with 2+ pipe characters.

    Returns:
        List of (table_text, start_line, end_line) tuples
    """
    lines = text.split('\n')
    tables = []

    i = 0
    while i < len(lines):
        # Check if this line could start a table (2+ pipes)
        if lines[i].count('|') >= 2:
            start = i
            pipe_count = lines[i].count('|')

            # Scan forward for consecutive lines with similar pipe count
            j = i + 1
            while j < len(lines) and lines[j].count('|') >= max(2, pipe_count - 1):
                j += 1

            # If we found at least min_rows, it's a table
            if j - i >= min_rows:
                table_text = '\n'.join(lines[i:j])
                tables.append((table_text, i, j))
                i = j
            else:
                i += 1
        else:
            i += 1

    return tables


def normalize_pipe_table(table_text: str) -> str:
    """
    Normalize a pipe-delimited table to proper markdown format.

    Fixes:
    - Inconsistent pipe counts
    - Missing header separator
    - Alignment issues
    """
    lines = [ln.strip() for ln in table_text.split('\n') if ln.strip()]

    if not lines:
        return table_text

    # Parse each line into cells
    rows = []
    for line in lines:
        # Remove leading/trailing pipes
        line = line.strip('|').strip()
        cells = [cell.strip() for cell in line.split('|')]
        rows.append(cells)

    if not rows:
        return table_text

    # Determine max column count
    max_cols = max(len(row) for row in rows)

    # Pad rows to same length
    rows = [row + [''] * (max_cols - len(row)) for row in rows]

    # Build normalized markdown table
    markdown_lines = []

    # First row (assume header)
    markdown_lines.append('| ' + ' | '.join(rows[0]) + ' |')

    # Header separator
    markdown_lines.append('|' + '|'.join(['---' for _ in range(max_cols)]) + '|')

    # Data rows
    for row in rows[1:]:
        markdown_lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(markdown_lines)


def process_text_with_tables(text: str) -> Dict:
    """
    Process text to extract and label all tables.

    Returns:
        {
            'original_text': str,
            'tables': [
                {
                    'type': TableType,
                    'markdown': str,
                    'original': str,
                    'position': (start, end),
                    'row_count': int,
                    'col_count': int
                },
                ...
            ],
            'text_without_tables': str,  # Text with tables removed
            'text_with_labeled_tables': str  # Text with tables replaced by labels
        }
    """
    result = {
        'original_text': text,
        'tables': [],
        'text_without_tables': text,
        'text_with_labeled_tables': text
    }

    # Extract HTML tables first
    html_tables = extract_html_table(text)
    for html, start, end in html_tables:
        markdown = html_table_to_markdown(html)

        # Detect table type
        rows = markdown.split('\n')
        header = rows[0] if rows else ""
        table_type = detect_table_type(markdown, header)

        # Count rows and cols
        data_rows = [r for r in rows if r and not r.startswith('|---')]
        row_count = len(data_rows) - 1  # Exclude header
        col_count = data_rows[0].count('|') - 1 if data_rows else 0

        result['tables'].append({
            'type': table_type,
            'markdown': markdown,
            'original': html,
            'position': (start, end),
            'row_count': row_count,
            'col_count': col_count,
            'format': 'html'
        })

    # Extract pipe tables
    pipe_tables = extract_pipe_tables(text)
    for table_text, start_line, end_line in pipe_tables:
        # Skip if already captured as HTML table
        if any(start <= text.find(table_text) < end for _, start, end in html_tables):
            continue

        markdown = normalize_pipe_table(table_text)

        # Detect table type
        rows = markdown.split('\n')
        header = rows[0] if rows else ""
        table_type = detect_table_type(markdown, header)

        # Count rows and cols
        data_rows = [r for r in rows if r and not r.startswith('|---')]
        row_count = len(data_rows) - 1  # Exclude header
        col_count = data_rows[0].count('|') - 1 if data_rows else 0

        result['tables'].append({
            'type': table_type,
            'markdown': markdown,
            'original': table_text,
            'position': (start_line, end_line),
            'row_count': row_count,
            'col_count': col_count,
            'format': 'pipe'
        })

    # Create text without tables
    text_no_tables = text
    for table in sorted(result['tables'], key=lambda t: t['position'][0], reverse=True):
        orig = table['original']
        text_no_tables = text_no_tables.replace(orig, '')
    result['text_without_tables'] = text_no_tables

    # Create text with labeled tables
    text_labeled = text
    for i, table in enumerate(sorted(result['tables'], key=lambda t: t['position'][0], reverse=True)):
        orig = table['original']
        label = f"\n[TABLE_{i+1}: {table['type'].value.upper()}]\n{table['markdown']}\n[/TABLE_{i+1}]\n"
        text_labeled = text_labeled.replace(orig, label)
    result['text_with_labeled_tables'] = text_labeled

    return result


def get_table_summary(table: Dict) -> str:
    """
    Generate a text summary of a table for better embedding/retrieval.

    Example:
        "Payment plan table with 10 rows showing construction milestones and payment percentages"
    """
    table_type = table['type'].value.replace('_', ' ')
    row_count = table['row_count']

    # Extract key info from markdown
    markdown = table['markdown']

    if table['type'] == TableType.PAYMENT_PLAN:
        # Count percentage markers
        percent_count = markdown.count('%')
        milestone_words = ['booking', 'foundation', 'slab', 'possession', 'oc', 'registry']
        milestones = [w for w in milestone_words if w in markdown.lower()]

        summary = f"Payment plan table with {row_count} milestones"
        if milestones:
            summary += f" including {', '.join(milestones[:3])}"
        if percent_count:
            summary += f" with {percent_count} percentage markers"

    elif table['type'] == TableType.UNIT_SPECS:
        bhk_matches = re.findall(r'(\d+)\s*bhk', markdown, re.IGNORECASE)
        area_matches = re.findall(r'(\d+)\s*sq', markdown, re.IGNORECASE)

        summary = f"Unit specifications table with {row_count} configurations"
        if bhk_matches:
            summary += f" ({', '.join(set(bhk_matches))} BHK units)"
        if area_matches:
            summary += f" showing areas"

    elif table['type'] == TableType.PRICING:
        summary = f"Pricing table with {row_count} items"

    else:
        summary = f"{table_type} table with {row_count} rows and {table['col_count']} columns"

    return summary


# Command-line interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python table_processor.py <text_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        text = f.read()

    result = process_text_with_tables(text)

    print(f"Found {len(result['tables'])} tables:\n")

    for i, table in enumerate(result['tables'], 1):
        print(f"Table {i}: {table['type'].value}")
        print(f"Rows: {table['row_count']}, Cols: {table['col_count']}")
        print(f"Summary: {get_table_summary(table)}")
        print(f"\nMarkdown:\n{table['markdown']}\n")
        print("-" * 80)
