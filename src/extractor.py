import re
import pdfplumber


# ------------------------------------------------------------------
# Extract and clean text from a PDF
# ------------------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and extracts the full text from all pages as a single string.
    Performs basic cleaning, such as removing hyphenated line breaks and merging lines.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Cleaned text extracted from the PDF.
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from each page, or return an empty string if no text is found
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages_text)  # Combine text from all pages
    text = re.sub(r"-\n", "", raw_text)  # Remove hyphenated line breaks
    text = text.replace("\r", "")  # Remove carriage returns
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # Merge single line breaks
    text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces and trim
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
    """
    # Define patterns to match different types of requirements
    patterns = [
        r"Disclosure\s+Requirement\s+(G\d{1,2}[\-–—−]\d{1,2})",  # e.g., Disclosure Requirement G1-2
        r"Disclosure\s+(G?\d{1,2}[\-–—−]\d{1,2})",  # e.g., Disclosure 2-1 or G1-2
        r"(G\d{1,2}[\-–—−]\d{1,2})",  # e.g., G1-2 standalone
        r"Kriterium\s+(\d{1,2})",  # German: Kriterium 10
        r"Criterion\s+(\d{1,2})",  # English: Criterion 7
        r"\b(\d{1,2})\.\s+(Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten)",  # German numbered sections
        r"(GRI(?:\s+SRS)?[\- ]?\d{3}[\-–—−]\d{1,2})",  # e.g., GRI SRS-205-1, GRI 305–3
        r"\b\d{3}[\-–—−]\d{1,2}\b",  # e.g., 305-5 standalone
    ]
    combined_pattern = "|".join(patterns)  # Combine all patterns into a single regex
    regex = re.compile(combined_pattern)

    matches = []
    for m in regex.finditer(text):
        # Extract the matched requirement code
        code = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5)
        if m.group(4):  # German "Kriterium"
            code = "Kriterium " + code
        elif m.group(5):  # English "Criterion"
            code = "Criterion " + code
        matches.append((code, m.start()))  # Append the code and its start index

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
    req_matches = find_requirements(text)  # Find all requirements in the text
    requirements = {}

    for i, (code, start_idx) in enumerate(req_matches):
        # Determine the end index of the current requirement
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx].strip()  # Extract and clean the segment
        # Append the segment to the corresponding requirement code
        requirements[code] = requirements.get(code, "") + " " + segment

    return requirements


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
