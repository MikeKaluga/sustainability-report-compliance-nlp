"""
This script provides functionality to extract and process text from sustainability report PDFs.
It includes methods to clean the text, identify specific requirements based on predefined patterns,
and extract relevant sections corresponding to these requirements.

Key Features:
- Removes common footer patterns from PDF pages.
- Cleans and consolidates text extracted from PDFs.
- Identifies and categorizes requirements based on ESRS and GRI standards.
- Extracts and processes text segments corresponding to identified requirements.

Usage:
- Use `extract_requirements_from_standard_pdf(pdf_path)` as the main entry point to process a PDF file.
- The output is a dictionary mapping requirement codes to their corresponding text segments.
"""

import re
import pdfplumber

# --- Standard detection helpers ---
def detect_standard(text, threshold: float = 0.55) -> str:
    """
    Detects which standard (ESRS/GRI) a given text most likely belongs to.
    Returns 'ESRS', 'GRI', or 'UNKNOWN'.
    """
    esrs_patterns = {
        r"\bESRS\b",
        r"\bEFRAG\b",
        r"\bCSRD\b",
        r"\bEuropean Sustainability Reporting Standards\b",
        r"\bDisclosure\s+Requirement\b",
        r"\bESRS\s+[EGST]\d+",
    }
    gri_patterns = {
        r"\bGRI\b",
        r"\bGlobal Reporting Initiative\b",
        r"\bGRI\s*(Standards?)?\b",
        r"\bGRI\s*[1-9]\d{0,2}[-–—−]\d{1,2}\b",
        r"\bUniversal\s+Standards\b|\bTopic[- ]specific\s+Standards\b|\bSector\s+Standards\b",
        # --- German cues ---
        r"\bAngabe\s+\d{1,3}[-–—−]\d{1,2}\b",
        r"\bUniverselle\s+Standards\b|\bThemenspezifische\s+Standards\b|\bSektorstandards\b|\bAllgemeine\s+Standards\b",
    }

    def score(txt: str, patterns: set[str]) -> float:
        hits = sum(1 for p in patterns if re.search(p, txt, flags=re.IGNORECASE))
        return 0.0 if not patterns else hits / len(patterns)

    esrs_score = score(text, esrs_patterns)
    gri_score = score(text, gri_patterns)

    if esrs_score < threshold and gri_score < threshold:
        return "UNKNOWN"
    return "ESRS" if esrs_score >= gri_score else "GRI"


def detect_standard_from_pdf(pdf_path: str) -> str:
    """
    Reads the PDF and returns 'ESRS', 'GRI', or 'UNKNOWN'.
    """
    try:
        full_text = extract_text_from_pdf(pdf_path)
        return detect_standard(full_text)
    except Exception:
        return "UNKNOWN"


# ------------------------------------------------------------------
# Helper function to filter footers from page text
# ------------------------------------------------------------------
def _filter_footers(page_text):
    """
    Removes common footer patterns from the text of a single page.

    Args:
        page_text (str): The text content of a single PDF page.

    Returns:
        str: The page text with footers removed.
    """
    lines = page_text.split('\n')
    
    # Patterns for typical footer content
    footer_patterns = [
        re.compile(r'^\s*page\s*\d+\s*(?:of\s*\d+)?\s*$', re.IGNORECASE),  # "Page 1", "Page 1 of 10"
        re.compile(r'^\s*\d+\s*$'),  # Standalone page numbers
        re.compile(r'^\s*\[\s*draft\s*\]\s*$', re.IGNORECASE),  # "[Draft]"
        re.compile(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}', re.IGNORECASE), # "November 2022"
        # Add other recurring footers if needed, e.g., company name or report title
        # re.compile(r'My Company Name SE', re.IGNORECASE),
    ]
    
    cleaned_lines = []
    for line in lines:
        is_footer = False
        for pattern in footer_patterns:
            if pattern.search(line):
                is_footer = True
                break
        if not is_footer:
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)


# ------------------------------------------------------------------
# Extract and clean text from a PDF
# ------------------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and extracts the full text from all pages as a single string.
    Performs basic cleaning, such as removing hyphenated line breaks and merging lines,
    and filters out common footer patterns from each page.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Cleaned text extracted from the PDF.
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from each page, filter footers, or return an empty string
        pages_text = [_filter_footers(page.extract_text() or "") for page in pdf.pages]
    
    raw_text = "\n".join(pages_text)  # Combine text from all pages
    text = re.sub(r"-\n", "", raw_text)  # Remove hyphenated line breaks
    text = text.replace("\r", "")  # Remove carriage returns
    # Preserve newlines for structure - only clean excessive whitespace within lines
    text = re.sub(r"[ \t]+", " ", text)  # Replace multiple spaces/tabs with single space
    text = re.sub(r"\n[ \t]+", "\n", text)  # Remove leading whitespace after newlines
    text = text.strip()  # Remove leading/trailing whitespace
    return text


# ------------------------------------------------------------------
# Identify requirements based on patterns
# ------------------------------------------------------------------
def find_requirements(text):
    """
    Identifies requirements in the text using predefined patterns.

    Args:
        text (str): The input text to search for requirements.

    Returns:
        list of tuple: A list of tuples where each tuple contains:
                       - The requirement code (str)
                       - The start index of the requirement in the text (int)
                       - The standard type ('esrs' or 'gri')
                       - The full designation/title (str)
    """
    # Define patterns to match different types of requirements.
    # The `^` anchor ensures we only match at the beginning of a line.
    patterns = [
        # ESRS Patterns
        r"^(Disclosure\s+Requirement\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",
        r"^(Disclosure\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",
        r"^(([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",
        r"^(Kriterium\s+\d{1,2})",
        r"^(Criterion\s+\d{1,2})",
        r"^(\b\d{1,2}\.\s+(?:Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten))",
        # GRI Patterns
        r"^((GRI(?:\s+SRS)?[\- ]?\d{1,3}[\-–—−]\d{1,2})[^\n]*)",
        r"^(Disclosure\s+(\d{1,3}[\-–—−]\d{1,2})[^\n]*)",
        r"^((Angabe\s+(\d{1,3}[\-–—−]\d{1,2}))[^\n]*)",
        # NEW: GRI "Requirement N: ..." headers (appear before disclosures)
        r"^(Requirement\s+\d+\s*:\s*[^\n]*)",
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern, re.MULTILINE)

    matches = []
    for m in regex.finditer(text):
        # Check for table of contents pattern. This can be single or multi-line.
        # A TOC entry is a line ending with '....' and a page number.
        # For multi-line entries, the '....' might be on a subsequent line.

        # Create a small window of text around the match to check for TOC patterns.
        # The window starts at the beginning of the line of the match.
        line_start = text.rfind('\n', 0, m.start()) + 1
        # And ends a bit after the match to catch wrapped lines.
        # Let's look ahead 250 chars, which should cover 2-3 lines.
        context_end = min(len(text), m.end() + 250)
        context = text[line_start:context_end]

        # Now check if any line in this context ends with the TOC pattern.
        if any(re.search(r'\.{2,}\s*\d+\s*$', line) for line in context.split('\n')):
            continue # Skip this match as it's part of a TOC entry.

        # Determine the standard type, code, and full designation in a language-agnostic way
        full_designation = m.group(0).strip()
        code = ""
        standard_type = None

        # NEW: Detect GRI "Requirement N: <title>" header
        if re.search(r"^Requirement\s+\d+\s*:", full_designation, flags=re.IGNORECASE):
            standard_type = 'gri'
            m_req = re.search(r"Requirement\s+(\d+)\s*:", full_designation, flags=re.IGNORECASE)
            if m_req:
                code = f"Requirement {m_req.group(1)}"
        # GRI detection (English or German: Disclosure/Angabe)
        elif re.search(r"\bGRI\b", full_designation, flags=re.IGNORECASE) or \
           re.search(r"\b(?:Disclosure|Angabe)\s+\d{1,3}[\-–—−]\d{1,2}\b", full_designation, flags=re.IGNORECASE):
            standard_type = 'gri'
            m_code = re.search(r"(\d{1,3}[\-–—−]\d{1,2})", full_designation)
            code = m_code.group(1) if m_code else ""
        # ESRS detection (code or keywords)
        elif re.search(r"\b[GES]\d{1,2}[\-–—−]\d{1,2}\b", full_designation) or \
             re.search(r"\bDisclosure\s+Requirement\b", full_designation, flags=re.IGNORECASE) or \
             re.search(r"\b(Kriterium|Criterion)\b", full_designation, flags=re.IGNORECASE):
            standard_type = 'esrs'
            m_code = re.search(r"([GES]\d{1,2}[\-–—−]\d{1,2})", full_designation, flags=re.IGNORECASE)
            if m_code:
                code = m_code.group(1)
            else:
                m_krit = re.search(r"(Kriterium\s+\d{1,2}|Criterion\s+\d{1,2})", full_designation, flags=re.IGNORECASE)
                code = m_krit.group(1) if m_krit else ""
        else:
            continue  # Unknown/irrelevant match

        if code:
            matches.append((code.strip(), m.start(), standard_type, full_designation))

    # Sort matches by their position in the text
    matches.sort(key=lambda x: x[1])
    return matches


# ------------------------------------------------------------------
# Extract sections based on identified requirements
# ------------------------------------------------------------------
def extract_requirements(text):
    """
    Extracts sections of text corresponding to identified requirements.

    Args:
        text (str): The input text containing requirements and their descriptions.

    Returns:
        dict: A dictionary where keys are requirement codes and values are dictionaries
              containing the full text ('full_text'), a list of sub-points ('sub_points'),
              and the full designation ('full_designation').
    """
    req_matches = find_requirements(text)
    requirements = {}

    def _clean_full_designation(designation):
        """
        Cleans the full designation by removing trailing dots and page numbers.
        
        Args:
            designation (str): The raw full designation text.
            
        Returns:
            str: The cleaned designation text.
        """
        # Remove trailing dots and page numbers (e.g., ".................................... 7")
        cleaned = re.sub(r'\.{2,}\s*\d*\s*$', '', designation)
        return cleaned.strip()

    def _clean_full_text(text, code):
        """
        Cleans the full text by removing duplicate titles and trailing dots with page numbers.
        
        Args:
            text (str): The raw full text.
            code (str): The requirement code to identify duplicate titles.
            
        Returns:
            str: The cleaned full text.
        """
        # Remove trailing dots and page numbers first
        cleaned = re.sub(r'\.{2,}\s*\d*\s*$', '', text)
        
        # Remove specific unwanted headers
        unwanted_headers = [
            "Metrics and targets",
            "Impact, risk and opportunity management"
        ]
        for header in unwanted_headers:
            # Using re.IGNORECASE to match case-insensitively
            cleaned = re.sub(re.escape(header), '', cleaned, flags=re.IGNORECASE)

        # Trim text at "APPLICATION REQUIREMENTS"
        app_req_marker = "APPLICATION REQUIREMENTS"
        marker_idx = cleaned.upper().find(app_req_marker)
        if marker_idx != -1:
            cleaned = cleaned[:marker_idx]

        # Pattern to find the start of the actual content, which is often a numbered or lettered list.
        # This looks for patterns like "1.", "15.", "(a)", "a.", etc.
        content_start_pattern = re.compile(r'(?:\d{1,2}\.|\([a-z]\)|[a-z]\.)\s+')
        
        match = content_start_pattern.search(cleaned)
        
        if match:
            cleaned = cleaned[match.start():]
        else:
            # Fallback: remove duplicate "Disclosure Requirement {CODE} – ..." occurrences
            disclosure_pattern = rf"Disclosure\s+Requirement\s+{re.escape(code)}\s*[\-–—−][^\n]*"
            matches = list(re.finditer(disclosure_pattern, cleaned, flags=re.IGNORECASE))
            if len(matches) > 1:
                for m in reversed(matches[1:]):
                    cleaned = cleaned[:m.start()] + cleaned[m.end():]

            # NEW: Fallback for "Requirement N: ..." duplicates if code is "Requirement N"
            m_req_code = re.match(r'^Requirement\s+(\d+)$', code, flags=re.IGNORECASE)
            if m_req_code:
                req_num = m_req_code.group(1)
                req_title_pattern = rf"Requirement\s+{re.escape(req_num)}\s*:\s*[^\n]*"
                req_matches = list(re.finditer(req_title_pattern, cleaned, flags=re.IGNORECASE))
                if len(req_matches) > 1:
                    for m in reversed(req_matches[1:]):
                        cleaned = cleaned[:m.start()] + cleaned[m.end():]

        return cleaned.strip()

    for i, (code, start_idx, standard_type, full_designation) in enumerate(req_matches):
        # Determine the end index of the current requirement
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        
        # --- Route to separate handlers for ESRS/GRI ---
        if standard_type == 'esrs':
            full_text, sub_points = _process_esrs_segment(segment)
        else:
            full_text, sub_points = _process_gri_segment(segment)
        
        # Append the segment to the corresponding requirement code, only if content was found
        if full_text:
            if code not in requirements:
                requirements[code] = {'full_text': "", 'sub_points': [], 'full_designation': _clean_full_designation(full_designation)}
            
            requirements[code]['full_text'] += " " + full_text
            requirements[code]['sub_points'].extend(sub_points)

    # Clean up the final dictionary
    for code in requirements:
        requirements[code]['full_text'] = _clean_full_text(requirements[code]['full_text'].strip(), code)

        # Clean unwanted headers from sub-points as well
        unwanted_headers = [
            "Metrics and targets",
            "Impact, risk and opportunity management"
        ]
        app_req_marker = "APPLICATION REQUIREMENTS"
        cleaned_sub_points = []
        for sp in requirements[code]['sub_points']:
            cleaned_sp = sp
            for header in unwanted_headers:
                cleaned_sp = re.sub(re.escape(header), '', cleaned_sp, flags=re.IGNORECASE)
            
            # Trim text at "APPLICATION REQUIREMENTS" for sub-points
            marker_idx = cleaned_sp.upper().find(app_req_marker)
            if marker_idx != -1:
                cleaned_sp = cleaned_sp[:marker_idx]

            # Add the cleaned sub-point only if it's not empty
            if cleaned_sp.strip():
                cleaned_sub_points.append(cleaned_sp.strip())
        
        requirements[code]['sub_points'] = cleaned_sub_points

    return requirements


def _process_esrs_segment(segment: str):
    """
    ESRS-specific segment processing wrapper.
    Internally calls the core processor with 'esrs'.
    """
    # Remove inline amendment notices like "(22 amended)", "(4, 5 amended)", "(30-31 amended)"
    segment = _remove_esrs_amended_notices(segment)
    return _process_segment_core(segment, 'esrs')


def _process_gri_segment(segment: str):
    """
    GRI-specific segment processing wrapper.
    Internally calls the core processor with 'gri'.
    """
    # Trim from the earliest occurrence of any boundary marker:
    # - English: "Compilation requirements" (optional)
    # - German: "Erläuterungen" (explanations)
    # - German: "Hintergrundinformationen" (background information)
    markers = [
        r'Compilation\s+requirements',
        r'\bErläuterungen\b',
        r'\bHintergrundinformationen\b',
    ]
    earliest = None
    for pat in markers:
        m = re.search(pat, segment, flags=re.IGNORECASE)
        if m:
            if earliest is None or m.start() < earliest:
                earliest = m.start()
    if earliest is not None:
        segment = segment[:earliest].rstrip()
    return _process_segment_core(segment, 'gri')


def _remove_esrs_amended_notices(text: str) -> str:
    """
    Removes ESRS inline amendment notices such as:
    - (22 amended)
    - (4, 5 amended)
    - (30-31 amended)
    Case-insensitive, tolerant to various hyphen/dash characters and spacing.
    """
    pattern = re.compile(
        r'\(\s*\d+(?:\s*(?:[-–—−]\s*\d+|\s*,\s*\d+))*\s+amended\s*\)',
        flags=re.IGNORECASE
    )
    cleaned = pattern.sub('', text)
    # Collapse whitespace that may result from removal
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)
    cleaned = re.sub(r'\s+\n', '\n', cleaned)
    return cleaned.strip()


def _process_segment_core(segment, standard_type):
    """
    Core segment processor.
    Processes a text segment based on the standard type (ESRS or GRI).
    
    Args:
        segment (str): The text segment to process.
        standard_type (str): The type of standard ('esrs' or 'gri').
    
    Returns:
        tuple: A tuple containing:
               - str: Processed segment with sub-points included.
               - list: A list of individual sub-points.
    """
    # Discard everything according to "APPLICATION REQUIREMENTS" before any further processing
    _app_marker = "APPLICATION REQUIREMENTS"
    upper_seg = segment.upper()
    marker_idx = upper_seg.find(_app_marker)
    if marker_idx != -1:
        segment = segment[:marker_idx]

    lines = segment.split('\n')
    # Containers for final combination
    result_parts = []
    sub_points = []

    # State
    current_part = ""
    ignoring_footnote = False

    # Patterns
    esrs_subpoint_pattern = re.compile(r'^(?:\d{1,2}\.|\([a-z]\))\s+.*')
    # Accept a., a), i., i) as valid GRI subpoints; case-insensitive
    gri_subpoint_pattern = re.compile(r'^(?:[a-z][\.\)]|\(?[ivx]+\)?[\.\)])\s+.*', flags=re.IGNORECASE)
    footnote_start_pattern = re.compile(r'^\d+\s+.*')

    numeric_prefix = re.compile(r'^\d{1,2}\.\s+')
    letter_prefix = re.compile(r'^\([a-z]\)\s+|^[a-z]\.\s+', flags=re.IGNORECASE)
    roman_prefix = re.compile(r'^\(?[ivx]+\)?\.\s+', flags=re.IGNORECASE)

    def _subtype_for_line(line: str) -> str:
        if numeric_prefix.match(line):
            return 'numeric'
        if letter_prefix.match(line):
            return 'letter'
        if roman_prefix.match(line):
            return 'roman'
        return 'other'

    def _strip_enum_prefix(text: str) -> str:
        text = re.sub(r'^\d{1,2}\.\s+', '', text)
        text = re.sub(r'^\([a-z]\)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^[a-z]\.\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\(?[ivx]+\)?\.\s+', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _first_sentence(text: str) -> str:
        idx = text.find('.')
        if idx != -1:
            return text[:idx+1].strip()
        return text.strip()

    # Smarter first sentence extractor for GRI: ignore common abbreviations and decimals.
    def _first_sentence_smart(text: str) -> str:
        abbreviations = {
            'e.g.', 'i.e.', 'etc.', 'mr.', 'ms.', 'mrs.', 'dr.', 'prof.', 'no.',
            'art.', 'fig.', 'eq.', 'est.', 'approx.', 'vs.', 'cf.', 'al.', 'ed.', 'vol.',
        }
        i = 0
        n = len(text)
        while i < n:
            if text[i] == '.':
                # Check decimal number pattern: digit . digit
                prev_is_digit = i > 0 and text[i-1].isdigit()
                next_is_digit = i+1 < n and text[i+1].isdigit()
                if prev_is_digit and next_is_digit:
                    i += 1
                    continue

                # Check known abbreviations ending at i (case-insensitive)
                start = max(0, i - 6)  # window
                snippet = text[start:i+1].lower()
                if any(snippet.endswith(abbr) for abbr in abbreviations):
                    i += 1
                    continue

                # Consider this a sentence end only if followed by whitespace and an uppercase/opening bracket or end
                j = i + 1
                while j < n and text[j].isspace():
                    j += 1
                if j >= n or (j < n and (text[j].isupper() or text[j] in '([{"\'')):
                    return text[:i+1].strip()
                # Otherwise, keep searching
            i += 1
        return text.strip()

    # Helpers to extract enumeration labels (ESRS)
    def _extract_numeric_label(line):
        m = re.match(r'^\s*(\d{1,2})\.\s+', line)
        return m.group(1) if m else None

    def _extract_child_label(line, subtype):
        if subtype == 'letter':
            m = re.match(r'^\s*\(([a-z])\)\s+', line, flags=re.IGNORECASE)
            if not m:
                m = re.match(r'^\s*([a-z])\.\s+', line, flags=re.IGNORECASE)
            return m.group(1).lower() if m else None
        if subtype == 'roman':
            m = re.match(r'^\s*\(?([ivx]+)\)?\.?\s+', line, flags=re.IGNORECASE)
            return m.group(1).lower() if m else None
        return None

    # Build structured parts with meta to preserve hierarchy
    parts_meta = []
    if lines:
        first_line = lines[0].strip()
        current_part = first_line
        # Determine if the first line is a subpoint (rare) and classify
        if standard_type == 'esrs':
            first_is_sub = bool(esrs_subpoint_pattern.match(first_line))
        else:
            # GRI: do NOT consider numeric prefixes as subpoints
            first_is_sub = bool(gri_subpoint_pattern.match(first_line))
        current_is_sub = first_is_sub
        current_subtype = _subtype_for_line(first_line) if first_is_sub else 'other'

    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue

        is_esrs_subpoint = standard_type == 'esrs' and bool(esrs_subpoint_pattern.match(line))
        # GRI: only letter/roman subpoints, never numeric like "2."
        is_gri_subpoint = standard_type == 'gri' and bool(gri_subpoint_pattern.match(line))
        is_subpoint = is_esrs_subpoint or is_gri_subpoint

        if is_subpoint:
            # Close out current_part
            if current_part:
                parts_meta.append({
                    'text': current_part,
                    'is_subpoint': current_is_sub,
                    'subtype': current_subtype
                })
            # Start a new part
            current_part = line
            current_is_sub = True
            current_subtype = _subtype_for_line(line)
            ignoring_footnote = False
            continue

        # If we are currently ignoring a footnote, skip this line.
        if ignoring_footnote:
            continue

        # Check for a new footnote to start ignoring.
        if footnote_start_pattern.match(line) and not is_subpoint:
            ignoring_footnote = True
            continue

        # Continuation of the current part
        if current_part:
            current_part += " " + line

    # Flush the last part
    if current_part and not ignoring_footnote:
        parts_meta.append({
            'text': current_part,
            'is_subpoint': current_is_sub,
            'subtype': current_subtype
        })

    # Build result parts (for ESRS we keep structure; for GRI we'll rebuild later)
    result_parts = [p['text'] for p in parts_meta]

    # Enrich sub-points with parent context
    # We propagate the parent's first sentence (from the last numeric bullet) to its letter/roman children.
    def build_enriched_subpoints_esrs(parts):
        """
        Rule:
        - If a numeric parent (e.g., '15.') has letter/roman children (e.g., '(a)', '(b)'), do NOT emit the numeric
          as its own sub-point; only emit the children, each prefixed with the parent's first sentence.
        - If a numeric parent has NO children before the next numeric parent (or end), keep the numeric sub-point.
        - Letter/roman lines without a preceding numeric parent are kept as-is.
        """
        enriched = []
        i = 0
        while i < len(parts):
            p = parts[i]
            if not p['is_subpoint']:
                i += 1
                continue

            if p['subtype'] == 'numeric':
                parent_label = _extract_numeric_label(p['text'])
                parent_rest = _strip_enum_prefix(p['text'])
                parent_first_sent = _first_sentence(parent_rest)
                
                # Track seen child labels for this parent to avoid duplicates
                seen_child_labels = set()

                # Look ahead until the next numeric subpoint (or end) and collect letter/roman children.
                j = i + 1
                has_child = False
                while j < len(parts):
                    pj = parts[j]
                    if pj['is_subpoint'] and pj['subtype'] == 'numeric':
                        break  # next numeric parent reached
                    if pj['is_subpoint'] and pj['subtype'] in ('letter', 'roman'):
                        child_label = _extract_child_label(pj['text'], pj['subtype'])
                        
                        # If we have a label and it's already been seen for this parent, skip it.
                        if child_label and child_label in seen_child_labels:
                            j += 1
                            continue
                        
                        if child_label:
                            seen_child_labels.add(child_label)

                        has_child = True
                        child_rest = _strip_enum_prefix(pj['text'])
                        if parent_label and child_label:
                            enum = f"{parent_label}({child_label})."
                            context = f"{parent_first_sent} " if parent_first_sent else ""
                            enriched.append(f"{enum} {context}{child_rest}".strip())
                        else:
                            enriched.append(pj['text'])
                    j += 1

                if not has_child:
                    # No children: keep the numeric parent as a sub-point.
                    if parent_label:
                        enriched.append(f"{parent_label}. {parent_rest}".strip())
                    else:
                        enriched.append(p['text'])

                # Skip over inspected range (children and in-between parts)
                i = j
                continue

            # Letter/Roman without preceding numeric: keep as-is
            if p['subtype'] in ('letter', 'roman'):
                enriched.append(p['text'])
            else:
                enriched.append(p['text'])

            i += 1

        return enriched

    def build_enriched_subpoints_gri(parts):
        """
        GRI specifics:
        - No numeric parent; subpoints start at a., b., c. (or a), i), etc.).
        - Preserve/normalize enumeration prefixes.
        - Keep full subpoint text (do not trim to the first sentence).
        - Do not cut at section-like references (e.g., '2.5'); treat them as part of the text.
        - For roman subpoints, prepend the parent letter's first sentence and show combined enumeration (e.g., a-i.).
        - IMPORTANT: Do not emit a standalone letter (e.g., 'a.') when roman children (i., ii., ...) exist.
        """
        new_result = []
        trimmed = []
        # No reference cutting; keep entire text

        # Pending letter subpoint state; flushed only if it has no roman children
        pending = None  # {'parent_text': str, 'token': str, 'enum_norm': str, 'has_child': bool}

        for p in parts:
            if not p['is_subpoint']:
                continue

            # Capture enumeration prefix and the remainder
            m = re.match(r'^\s*(((?:\(?[ivx]+\)?|[a-z])[.)]))\s+(.*)', p['text'], flags=re.IGNORECASE)
            if m:
                enum_prefix = m.group(1)   # e.g., 'a.', 'a)', 'ii.', '(ii)'
                rest = m.group(3)
                raw_token = enum_prefix[:-1].strip().lower().strip('()')  # token without trailing '.' or ')' and parens
            else:
                enum_prefix = ""
                rest = p['text']
                raw_token = ""

            # Keep rest intact; do not cut at section-like references

            roman_chars = set('ivx')
            is_letter = bool(raw_token) and any(c not in roman_chars for c in raw_token)
            if not is_letter and raw_token in roman_chars:
                # 'i' could be letter only if no parent yet, otherwise roman
                if len(raw_token) >= 2:
                    is_letter = False
                else:
                    is_letter = False  # treat single 'i' as roman when a letter context is possible

            if is_letter:
                # Flush previous pending letter if it had no children
                if pending and not pending['has_child']:
                    combined = f"{pending['enum_norm']} {pending['parent_text']}".strip()
                    new_result.append(combined)
                    trimmed.append(combined)
                # Start new pending letter
                parent_text = rest.strip()
                enum_norm = f"{raw_token}." if raw_token else enum_prefix
                pending = {
                    'parent_text': parent_text,
                    'token': raw_token,
                    'enum_norm': enum_norm,
                    'has_child': False
                }
            else:
                # Roman child: include parent sentence and combined enumeration like 'a-i.'
                child_text = rest.strip()
                if pending:
                    pending['has_child'] = True
                    enum_combined = f"{pending['token']}-{raw_token}." if pending['token'] and raw_token else f"{raw_token}."
                    combined_text = f"{pending['parent_text']} {child_text}".strip()
                else:
                    enum_combined = f"{raw_token}." if raw_token else enum_prefix
                    combined_text = child_text
                combined = f"{enum_combined} {combined_text}".strip()
                new_result.append(combined)
                trimmed.append(combined)

        # After loop: if a letter was pending without children, emit it
        if pending and not pending['has_child']:
            combined = f"{pending['enum_norm']} {pending['parent_text']}".strip()
            new_result.append(combined)
            trimmed.append(combined)

        return new_result, trimmed

    if standard_type == 'esrs':
        sub_points = build_enriched_subpoints_esrs(parts_meta)
        # Keep the original result_parts for ESRS
        full_text_out = " ".join(result_parts).strip()
        return full_text_out, sub_points

    # GRI: Only use sub-points in output; preserve enumeration; smart-trim first sentence
    result_parts_gri, sub_points_gri = build_enriched_subpoints_gri(parts_meta)
    return " ".join(result_parts_gri).strip(), sub_points_gri


# ------------------------------------------------------------------
# Main function: Process a standard PDF and return consolidated requirements
# ------------------------------------------------------------------
def extract_requirements_from_standard_pdf(pdf_path):
    """
    Processes a standard PDF to extract and consolidate requirements.

    Args:
        pdf_path (str): Path to the standard PDF file.

    Returns:
        dict: A dictionary where keys are requirement codes and values are dictionaries
              containing the full text and a list of sub-points.
    """
    full_text = extract_text_from_pdf(pdf_path)  # Extract and clean text from the PDF
    req_dict = extract_requirements(full_text)  # Extract requirements from the text

    # Post-process the last requirement to remove unwanted sections (e.g., glossary, appendix)
    if req_dict:
        last_key = list(req_dict.keys())[-1]  # Get the last requirement code
        paragraph = req_dict[last_key]['full_text']

        def trim_end_noise(text):
            """
            Trims unwanted sections (e.g., glossary, appendix) from the end of the text.

            Args:
                text (str): The input text to clean.

            Returns:
                str: The cleaned text.
            """
            end_markers = ["Appendix", "Glossar", "Definitions", "Contact", "Imprint"]
            for marker in end_markers:
                idx = text.lower().find(marker.lower())
                if idx != -1:
                    return text[:idx]  # Trim the text at the marker
            return text

        req_dict[last_key]['full_text'] = trim_end_noise(paragraph)  # Clean the last requirement

    return req_dict