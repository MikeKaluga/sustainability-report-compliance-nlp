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
    # Define patterns to match different types of requirements
    patterns = [
        # ESRS Patterns - require a title starting with '–' to be considered a requirement
        r"(Disclosure\s+Requirement\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",  # e.g., Disclosure Requirement G1-2 – title
        r"(Disclosure\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",             # e.g., Disclosure G1-2 – title
        r"(([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−][^\n]*)",                          # e.g., G1-2 – title
        r"(Kriterium\s+\d{1,2})",                                 # German: Kriterium 10
        r"(Criterion\s+\d{1,2})",                                 # English: Criterion 7
        r"(\b\d{1,2}\.\s+(?:Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten))",  # German numbered sections
        
        # GRI Patterns - capture full line including title
        r"((GRI(?:\s+SRS)?[\- ]?\d{1,3}[\-–—−]\d{1,2})[^\n]*)",           # e.g., GRI 2-1 title
        r"(Disclosure\s+(\d{1,3}[\-–—−]\d{1,2})[^\n]*)"                  # e.g., Disclosure 2-1 title
        #r"\b((\d{1,3}[\-–—−]\d{1,2})[^\n]*)",                           # e.g., 2-1 title standalone
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)

    matches = []
    for m in regex.finditer(text):
        # Check for table of contents pattern. This can be single or multi-line.
        # A TOC entry is a line ending with '....' and a page number.
        # For multi-line entries, the '....' might be on a subsequent line.
        
        # We create a small window of text around the match to check for TOC patterns.
        # The window starts at the beginning of the line of the match.
        line_start = text.rfind('\n', 0, m.start()) + 1
        # And ends a bit after the match to catch wrapped lines.
        # Let's look ahead 250 chars, which should cover 2-3 lines.
        context_end = min(len(text), m.end() + 250)
        context = text[line_start:context_end]

        # Now check if any line in this context ends with the TOC pattern.
        if any(re.search(r'\.{2,}\s*\d+\s*$', line) for line in context.split('\n')):
            continue # Skip this match as it's part of a TOC entry.

        # Determine the standard type, code, and full designation
        full_designation = ""
        code = ""
        
        # Groups 1-6 are ESRS patterns
        if m.group(1):  # ESRS with "Disclosure Requirement"
            standard_type = 'esrs'
            full_designation = m.group(1).strip()
            code = m.group(2).strip() if m.group(2) else ""
        elif m.group(3):  # ESRS with "Disclosure"
            standard_type = 'esrs'
            full_designation = m.group(3).strip()
            code = m.group(4).strip() if m.group(4) else ""
        elif m.group(5):  # ESRS standalone code
            standard_type = 'esrs'
            full_designation = m.group(5).strip()
            code = m.group(6).strip() if m.group(6) else ""
        elif m.group(7) or m.group(8) or m.group(9):  # German patterns
            standard_type = 'esrs'
            code = m.group(7) or m.group(8) or m.group(9)
            full_designation = code
        # Groups 10-12 are GRI patterns
        elif m.group(10):  # GRI with full designation
            standard_type = 'gri'
            full_designation = m.group(10).strip()
            code = m.group(11).strip() if m.group(11) else ""
        elif m.group(12):  # GRI Disclosure
            standard_type = 'gri'
            full_designation = m.group(12).strip()
            code = m.group(13).strip() if m.group(13) else ""
        elif m.group(14):  # GRI standalone
            standard_type = 'gri'
            full_designation = m.group(14).strip()
            code = m.group(15).strip() if m.group(15) else ""
        
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
            # If a starting pattern is found, trim the text to start from there.
            cleaned = cleaned[match.start():]
        else:
            # Fallback for cases where the title is repeated without a clear list marker.
            # This removes the "Disclosure Requirement [CODE] – [TITLE]" part.
            disclosure_pattern = rf"Disclosure\s+Requirement\s+{re.escape(code)}\s*[\-–—−][^\n]*"
            # Find all matches and keep only the first one
            matches = list(re.finditer(disclosure_pattern, cleaned, flags=re.IGNORECASE))
            if len(matches) > 1:
                # Remove all occurrences except the first one
                for m in reversed(matches[1:]):  # Reverse to maintain indices
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
    return _process_segment_core(segment, 'esrs')


def _process_gri_segment(segment: str):
    """
    GRI-specific segment processing wrapper.
    Internally calls the core processor with 'gri'.
    """
    # Robustly detect "guidance" (case-insensitive, tolerant to punctuation/whitespace/newlines)
    m = re.search(r'\bguidance\b', segment, flags=re.IGNORECASE)
    if m:
        before_guidance = segment[:m.start()]
        # Keep only up to and including the last period before GUIDANCE
        last_period_index = before_guidance.rfind('.')
        if last_period_index != -1:
            segment = before_guidance[:last_period_index + 1]
        else:
            # If no period before GUIDANCE, keep only the text before GUIDANCE
            segment = before_guidance.strip()

    return _process_segment_core(segment, 'gri')


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
    result_parts = []
    sub_points = []
    current_part = ""
    ignoring_footnote = False

    # Define patterns for sub-points and potential footnotes
    esrs_subpoint_pattern = re.compile(r'^(?:\d{1,2}\.|\([a-z]\))\s+.*')
    gri_subpoint_pattern = re.compile(r'^(?:[a-z]\.|\(?[ivx]+\)?\.)\s+.*')
    # A potential footnote starts with a number, but is not a numbered list item.
    footnote_start_pattern = re.compile(r'^\d+\s+.*')

    # The first line is always the main requirement title/text
    if lines:
        current_part = lines[0].strip()

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        is_esrs_subpoint = standard_type == 'esrs' and esrs_subpoint_pattern.match(line)
        is_gri_subpoint = standard_type == 'gri' and gri_subpoint_pattern.match(line)
        is_subpoint = is_esrs_subpoint or is_gri_subpoint

        # If we find a new sub-point, we stop ignoring footnotes.
        if is_subpoint:
            ignoring_footnote = False
            if current_part:
                result_parts.append(current_part)
                # If the previous part was a subpoint, add it to sub_points list
                if esrs_subpoint_pattern.match(current_part) or gri_subpoint_pattern.match(current_part):
                    sub_points.append(current_part)
            current_part = line
            continue

        # If we are currently ignoring a footnote, skip this line.
        if ignoring_footnote:
            continue

        # Check for a new footnote to start ignoring.
        # This is a line that starts with a number but is not a valid sub-point.
        if footnote_start_pattern.match(line) and not is_subpoint:
            ignoring_footnote = True
            continue
        
        # If none of the above, it's a continuation of the current part.
        if current_part:
            current_part += " " + line

    # Add the last part if it exists
    if current_part and not ignoring_footnote:
        result_parts.append(current_part)
        if esrs_subpoint_pattern.match(current_part) or gri_subpoint_pattern.match(current_part):
            sub_points.append(current_part)
    
    # For GRI, we only want the sub-points, so we filter out the main description.
    if standard_type == 'gri':
        # The first part is the main description, which we discard.
        # However, if the first line was already a subpoint, we keep it.
        if result_parts and not gri_subpoint_pattern.match(result_parts[0]):
            result_parts.pop(0)

        # Neue Anforderung: Eine GRI Anforderung endet nach dem ersten Punkt (Satzende).
        # Punkte in Aufzählungskennzeichnungen (a. b. c. i. ii. iii.) werden ignoriert.
        trimmed_sub_points = []
        new_result_parts = []
        for sp in sub_points:
            enum_match = re.match(r'^((?:[a-z]|(?:\(?[ivx]+\)?))\.)\s+(.*)', sp, flags=re.IGNORECASE)
            if enum_match:
                enum_prefix = enum_match.group(1)  # e.g. 'a.' oder 'ii.'
                rest = enum_match.group(2)
            else:
                enum_prefix = ""
                rest = sp
            period_idx = rest.find('.')
            if period_idx != -1:
                rest = rest[:period_idx + 1]
            truncated = (enum_prefix + ' ' + rest).strip() if enum_prefix else rest.strip()
            trimmed_sub_points.append(truncated)
            new_result_parts.append(truncated)
        sub_points = trimmed_sub_points
        result_parts = new_result_parts

    return " ".join(result_parts).strip(), sub_points


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