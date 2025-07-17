import re
import pdfplumber
import csv
from openai import OpenAI

# ------------------------------------------------------------------
# OpenAI API Configuration (e.g., GPT-4, GPT-3.5 via ChatGPT account)
# ------------------------------------------------------------------
# This section initializes the OpenAI client with the API key and specifies the model to use.
# Replace "XXXXXXXXXXXX" with your actual OpenAI API key.
client = OpenAI(api_key="XXXXXXXXXXXX")
MODEL = "gpt-4"  # Specify the model, e.g., "gpt-4" or "gpt-3.5-turbo"


# ------------------------------------------------------------------
# Extract and clean text from a PDF
# ------------------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and extracts the text from all pages as a single string.
    Performs basic cleaning:
    - Removes hyphenation at line breaks.
    - Removes carriage returns.
    - Smooths single line breaks into spaces.
    - Removes excessive whitespace.
    Saves the extracted text to a file for debugging or reference.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages_text)
    text = re.sub(r"-\n", "", raw_text)  # Remove hyphenation at line breaks
    text = text.replace("\r", "")  # Remove carriage returns
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # Smooth single line breaks
    text = re.sub(r"\s+", " ", text).strip()  # Remove excessive whitespace
    # Save the cleaned text to a file
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    return text


# ------------------------------------------------------------------
# Identify requirements based on patterns
# ------------------------------------------------------------------
def find_requirements(text):
    """
    Identifies requirements in the text using a set of regex patterns.
    Patterns include:
    - Disclosure Requirement codes (e.g., "G1-2", "Disclosure 2-1").
    - German and English keywords for criteria (e.g., "Kriterium 10", "Criterion 7").
    - GRI codes (e.g., "GRI 305-3").
    Returns a list of tuples containing the requirement code and its start index in the text.
    """
    patterns = [
        r"Disclosure\s+Requirement\s+(G\d{1,2}[\-–—−]\d{1,2})",  # e.g., Disclosure Requirement G1-2
        r"Disclosure\s+(G?\d{1,2}[\-–—−]\d{1,2})",  # e.g., Disclosure 2-1 or G1-2
        r"(G\d{1,2}[\-–—−]\d{1,2})",  # e.g., G1-2 standalone
        r"Kriterium\s+(\d{1,2})",  # German: Kriterium 10
        r"Criterion\s+(\d{1,2})",  # English: Criterion 7
        r"\b(\d{1,2})\.\s+(Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten)",  # German section titles
        r"(GRI(?:\s+SRS)?[\- ]?\d{3}[\-–—−]\d{1,2})",  # GRI codes (e.g., GRI 305-3)
        r"\b\d{3}[\-–—−]\d{1,2}\b",  # e.g., 305-5 standalone
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)
    matches = []
    for m in regex.finditer(text):
        # Extract the matched code and normalize it
        code = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5)
        if m.group(4):
            code = "Kriterium " + code
        elif m.group(5):
            code = "Criterion " + code
        matches.append((code, m.start()))
    matches.sort(key=lambda x: x[1])  # Sort matches by their position in the text
    return matches


# ------------------------------------------------------------------
# Extract sections based on identified requirements
# ------------------------------------------------------------------
def extract_requirements(text):
    """
    Extracts text segments corresponding to each identified requirement.
    Uses the start and end positions of each requirement to extract its associated text.
    Returns a dictionary where keys are requirement codes and values are the corresponding text segments.
    """
    req_matches = find_requirements(text)
    requirements = {}
    for i, (code, start_idx) in enumerate(req_matches):
        # Determine the end of the current requirement
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        segment = segment.strip()
        # Append the segment to the requirement code (handles duplicates)
        requirements[code] = requirements.get(code, "") + " " + segment
    return requirements


# ------------------------------------------------------------------
# Consolidate text using OpenAI GPT model
# ------------------------------------------------------------------
def openai_consolidate(code, paragraph):
    """
    Uses the OpenAI GPT model to consolidate a paragraph into a clean, readable text.
    The prompt instructs the model to:
    - Ignore irrelevant content (e.g., footnotes, headers, page numbers).
    - Focus only on content directly related to the requirement.
    Returns the consolidated text or the original paragraph in case of an error.
    """
    prompt = f"""
    Summarize the following paragraph for requirement {code} into a complete, well-readable section.
    Ignore clearly identifiable footnotes, page numbers, headers, or titles unrelated to the requirement.
    Use only content directly relevant to the requirement. No fabrications.

    Text: {paragraph}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise, fact-based consolidator of ESG requirements.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Low temperature for deterministic responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing requirement {code}: {e}")
        return paragraph


# ------------------------------------------------------------------
# Main function: Process PDF and save consolidated requirements
# ------------------------------------------------------------------
def process_pdf(pdf_path, output_csv):
    """
    Processes a PDF file to extract and consolidate requirements.
    - Extracts text from the PDF.
    - Identifies and extracts requirements.
    - Optionally trims irrelevant content (e.g., glossary, appendix).
    - Consolidates requirements using OpenAI GPT.
    - Saves the consolidated requirements to a CSV file.
    """
    full_text = extract_text_from_pdf(pdf_path)
    req_dict = extract_requirements(full_text)

    # Trim irrelevant content from the last requirement (e.g., glossary, appendix)
    if req_dict:
        last_key = list(req_dict.keys())[-1]
        paragraph = req_dict[last_key]

        def trim_end_noise(text):
            """
            Trims irrelevant content from the end of the text based on common markers.
            """
            end_markers = ["Appendix", "Glossar", "Definitions", "Contact", "Imprint"]
            for marker in end_markers:
                idx = text.lower().find(marker.lower())
                if idx != -1:
                    return text[:idx]
            return text

        req_dict[last_key] = trim_end_noise(paragraph)

    # Consolidate requirements using OpenAI GPT
    consolidated = {}
    print(
        f"Consolidating {len(req_dict)} identified requirements with OpenAI {MODEL}..."
    )
    for code, req_text in req_dict.items():
        consolidated[code] = (
            req_text  # Replace with openai_consolidate(code, req_text) if needed
        )

    # Save the consolidated requirements to a CSV file
    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])  # Write header row
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])  # Write each requirement and its content

    print(f"Process completed. Results saved to '{output_csv}'.")
