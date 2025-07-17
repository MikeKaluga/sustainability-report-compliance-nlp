import re
import csv
import pdfplumber

# ---------------------- GRI Extraction (Deutsch & Englisch) ----------------------
# The following functions handle the extraction of requirements from GRI standards.
# The text can be in either German or English, and the appropriate extraction logic is applied.


def extract_gri(text):
    """
    Determines whether the text is in English or German and calls the appropriate extraction function.
    """
    if "Disclosure 205-1" in text:  # Check for an English-specific keyword
        return extract_gri_en(text)
    else:  # Default to German extraction
        return extract_gri_de(text)


def extract_gri_de(text):
    """
    Extracts GRI requirements from German text.
    - Matches patterns like "Angabe 205-1" and extracts the associated content.
    - Uses regex to identify sections and sub-requirements.
    """
    results = {}
    # Regex pattern to match GRI codes and their titles in German
    pattern = re.compile(
        r"Angabe\s+(\d{3}[-\u2013\u2014\u2212]\d{1,2})\s+([^\n\r]+)", re.IGNORECASE
    )
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        code = f"GRI {match.group(1)}"  # Format the GRI code
        start_idx = match.end()  # Start of the content for this GRI code

        # Determine the end of the current section
        if i + 1 < len(matches):
            end_idx = matches[i + 1].start()  # End at the start of the next match
        else:
            # Look for keywords indicating the end of the section
            end_block = re.search(
                r"(Erl\u00e4uterungen|EMPFEHLUNGEN|Hintergrundinformationen)",
                text[start_idx:],
                re.IGNORECASE,
            )
            end_idx = start_idx + end_block.start() if end_block else len(text)

        # Extract the section text and clean it
        section = text[start_idx:end_idx].strip()
        requirement_matches = re.findall(
            r"(?m)^[a-z]\.\s.*?(?=(?:\\n[a-z]\.\s)|$)", section, re.DOTALL
        )
        clean_text = "\n".join([r.strip() for r in requirement_matches])

        results[code] = clean_text.strip()  # Store the cleaned requirements

    return results


def extract_gri_en(text):
    """
    Extracts GRI requirements from English text.
    - Matches patterns like "Disclosure 205-1" and extracts the associated content.
    - Uses regex to identify sections and sub-requirements.
    """
    results = {}
    # Regex pattern to match GRI codes and their titles in English
    pattern = re.compile(
        r"Disclosure\s+(205[-\u2013\u2014\u2212]\d)\s+(.+?)\n", re.IGNORECASE
    )
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        code = f"GRI {match.group(1)}"  # Format the GRI code
        start_idx = match.end()  # Start of the content for this GRI code

        # Look for the "REQUIREMENTS" keyword to find the real start of the content
        start_block = re.search(r"(?i)REQUIREMENTS", text[start_idx:])
        if not start_block:
            continue  # Skip if no valid content is found

        real_start = start_idx + start_block.end()

        # Determine the end of the current section
        if i + 1 < len(matches):
            end_idx = matches[i + 1].start()  # End at the start of the next match
        else:
            # Look for keywords indicating the end of the section
            end_block = re.search(
                r"(Guidance for Disclosure|Glossary|Background|Bibliography)",
                text[real_start:],
                re.IGNORECASE,
            )
            end_idx = real_start + end_block.start() if end_block else len(text)

        # Extract the section text and clean it
        section = text[real_start:end_idx].strip()
        requirement_matches = re.findall(
            r"(?m)^[a-z]\.\s.*?(?=(?:\\n[a-z]\.\s)|$)", section, re.DOTALL
        )
        clean_text = "\n".join([r.strip() for r in requirement_matches])
        results[code] = clean_text.strip()  # Store the cleaned requirements

    return results


# ---------------------- Placeholder Functions ----------------------
# These functions are placeholders for extracting requirements from other standards (e.g., ESRS, DNK).
# They currently return empty results but can be implemented as needed.


def extract_esrs(text):
    """
    Placeholder for extracting ESRS requirements.
    """
    return {}


def extract_dnk(text):
    """
    Placeholder for extracting DNK requirements.
    """
    return {}


# ---------------------- Dispatcher ----------------------
# This function acts as a dispatcher to call the appropriate extraction function based on the standard.


def extract_requirements(text, standard="auto"):
    """
    Extracts requirements based on the specified standard.
    - If 'auto', attempts to detect the standard from the text.
    """
    if standard == "GRI":
        return extract_gri(text)
    elif standard == "ESRS":
        return extract_esrs(text)
    elif standard == "DNK":
        return extract_dnk(text)
    elif standard == "auto":
        # Auto-detection logic for the standard
        if "Disclosure 205-1" in text or "Angabe 205-" in text:
            return extract_gri(text)
        elif re.search(r"\bG\d{1,2}[-\u2013\u2014\u2212]\d{1,2}\b", text):
            return extract_esrs(text)
        elif re.search(r"\d{1,2}\.\s+(Strategie|Wesentlichkeit|Ziele)", text):
            return extract_dnk(text)
        else:
            return {}
    else:
        raise ValueError(f"Unknown standard: {standard}")


# ---------------------- PDF Processing & CSV Export ----------------------
# This section handles reading a PDF file, extracting requirements, and exporting them to a CSV file.


def process_pdf(pdf_path, output_csv, standard="auto"):
    """
    Processes a PDF file to extract requirements and saves them to a CSV file.
    - pdf_path: Path to the input PDF file.
    - output_csv: Path to the output CSV file.
    - standard: The standard to use for extraction ('GRI', 'ESRS', 'DNK', or 'auto').
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from all pages of the PDF
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Extract requirements based on the specified standard
    requirements = extract_requirements(full_text, standard=standard)

    # Write the extracted requirements to a CSV file
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])  # Header row
        for code, text in requirements.items():
            writer.writerow([code, text])  # Write each requirement and its content

    print(
        f"{len(requirements)} requirements were extracted for {standard} and saved to '{output_csv}'."
    )


# ---------------------- Example Usage ----------------------
# This section demonstrates how to use the script to process a PDF file.

if __name__ == "__main__":
    process_pdf("data/standard.pdf", "data/gri_requirements.csv", standard="GRI")
