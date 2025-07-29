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
    """
    # Define patterns to match different types of requirements
    patterns = [
        # ESRS Patterns - require a title starting with '–' to be considered a requirement
        r"Disclosure\s+Requirement\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−]",  # e.g., Disclosure Requirement G1-2 –
        r"Disclosure\s+([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−]",             # e.g., Disclosure G1-2 –
        r"([GES]\d{1,2}[\-–—−]\d{1,2})\s*[\-–—−]",                          # e.g., G1-2 –
        r"(Kriterium\s+\d{1,2})",                                 # German: Kriterium 10
        r"(Criterion\s+\d{1,2})",                                 # English: Criterion 7
        r"(\b\d{1,2}\.\s+(?:Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten))",  # German numbered sections
        
        # GRI Patterns
        r"(GRI(?:\s+SRS)?[\- ]?\d{1,3}[\-–—−]\d{1,2})",           # e.g., GRI 2-1, GRI 305–3
        r"Disclosure\s+(\d{1,3}[\-–—−]\d{1,2})",                  # e.g., Disclosure 2-1
        r"\b(\d{1,3}[\-–—−]\d{1,2})\b",                           # e.g., 2-1, 305-5 standalone
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)

    matches = []
    for m in regex.finditer(text):
        # Determine the standard type and code
        # Groups 1-6 are ESRS, 7-9 are GRI
        if m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5) or m.group(6):
            standard_type = 'esrs'
            code = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5) or m.group(6)
        else:
            standard_type = 'gri'
            code = m.group(7) or m.group(8) or m.group(9)
        
        if code:
            matches.append((code.strip(), m.start(), standard_type))

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
        dict: A dictionary where keys are requirement codes and values are the corresponding text segments.
    """
    req_matches = find_requirements(text)
    requirements = {}

    for i, (code, start_idx, standard_type) in enumerate(req_matches):
        # Determine the end index of the current requirement
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        
        # Process the segment based on its standard type
        processed_segment = _process_segment(segment, standard_type)
        
        # Append the segment to the corresponding requirement code, only if content was found
        if processed_segment:
            requirements[code] = requirements.get(code, "") + " " + processed_segment

    return requirements


def _process_segment(segment, standard_type):
    """
    Processes a text segment based on the standard type (ESRS or GRI).
    
    Args:
        segment (str): The text segment to process.
        standard_type (str): The type of standard ('esrs' or 'gri').
    
    Returns:
        str: Processed segment with sub-points included.
    """
    lines = segment.split('\n')
    result_parts = []
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
    
    # For GRI, we only want the sub-points, so we filter out the main description.
    if standard_type == 'gri':
        # The first part is the main description, which we discard.
        # However, if the first line was already a subpoint, we keep it.
        if result_parts and not gri_subpoint_pattern.match(result_parts[0]):
             result_parts.pop(0)

    return " ".join(result_parts).strip()


# ------------------------------------------------------------------
# Main function: Process a standard PDF and return consolidated requirements
# ------------------------------------------------------------------
def extract_requirements_from_standard_pdf(pdf_path):
    """
    Processes a standard PDF to extract and consolidate requirements.

    Args:
        pdf_path (str): Path to the standard PDF file.

    Returns:
        dict: A dictionary where keys are requirement codes and values are the corresponding text segments.
    """
    full_text = extract_text_from_pdf(pdf_path)  # Extract and clean text from the PDF
    req_dict = extract_requirements(full_text)  # Extract requirements from the text

    # Post-process the last requirement to remove unwanted sections (e.g., glossary, appendix)
    if req_dict:
        last_key = list(req_dict.keys())[-1]  # Get the last requirement code
        paragraph = req_dict[last_key]

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

        req_dict[last_key] = trim_end_noise(paragraph)  # Clean the last requirement

    return req_dict
