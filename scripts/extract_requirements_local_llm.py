import re
import pdfplumber
import csv
from transformers import pipeline


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
    Returns the cleaned text.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages_text)
    text = re.sub(r"-\n", "", raw_text)  # Remove hyphenation at line breaks
    text = text.replace("\r", "")  # Remove carriage returns
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # Smooth single line breaks
    text = re.sub(r" +", " ", text).strip()  # Remove excessive whitespace
    return text


# ------------------------------------------------------------------
# Identify requirements based on patterns
# ------------------------------------------------------------------
def find_requirements(text):
    """
    Identifies all requirements in the text using predefined regex patterns.
    Returns a sorted list of tuples containing:
    - Requirement code
    - Start index of the match
    - End index of the match
    """
    patterns = [
        r"Disclosure\s+Requirement\s+([A-Z]\d+[-–]\d+)(?=\s+[–-])",  # Matches patterns like "G1-1 – ..."
        r"Disclosure\s+Requirement\s+([A-Z]\d+-\d+)",  # Matches patterns like "Disclosure Requirement G1-1"
        r"Disclosure\s+(\d+-\d+)",  # Matches GRI patterns like "Disclosure 2-1"
        r"Kriterium\s+(\d+)",  # Matches German "Kriterium 10"
        r"Criterion\s+(\d+)",  # Matches English "Criterion 7"
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)
    matches = []
    for m in regex.finditer(text):
        # Extract the matched code and normalize it
        code = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if m.group(3):
            code = "Kriterium " + code
        elif m.group(4):
            code = "Criterion " + code
        # Store the code along with the start and end positions of the match
        matches.append((code, m.start(), m.end()))
    matches.sort(key=lambda x: x[1])  # Sort matches by their position in the text
    return matches


# ------------------------------------------------------------------
# Extract sections based on identified requirements
# ------------------------------------------------------------------
def extract_requirements(text):
    """
    Splits the full text into segments based on identified requirement anchors.
    Returns a dictionary where:
    - Keys are requirement codes.
    - Values are the corresponding text segments.
    Empty segments are ignored.
    """
    req_matches = find_requirements(text)
    requirements = {}
    for i, (code, start_idx, end_of_match_idx) in enumerate(req_matches):
        # Determine the end of the current segment
        end_of_segment_idx = (
            req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        )

        # Extract the content between the end of the current match and the start of the next
        content = text[end_of_match_idx:end_of_segment_idx]

        # Clean the content and remove excessive whitespace
        cleaned_content = content.strip()

        # Add the content to the dictionary if it's not empty
        if cleaned_content:
            # Append new content to existing content if the code appears multiple times
            if code in requirements:
                requirements[code] += " " + cleaned_content
            else:
                requirements[code] = cleaned_content

    return requirements


# ------------------------------------------------------------------
# Consolidate paragraphs using a local LLM
# ------------------------------------------------------------------
def consolidate_paragraph(text, summarizer=None, min_words_for_consolidation=15):
    """
    Consolidates a given text paragraph.
    - If the text is too short (less than `min_words_for_consolidation`), it is only cleaned.
    - Otherwise, the summarizer is used to rephrase the text.
    Returns the consolidated text.
    """
    text = text.strip()
    word_count = len(text.split())

    # If the text is too short or no summarizer is provided, perform basic cleaning
    if not summarizer or word_count < min_words_for_consolidation:
        paragraph = re.sub(r"\(\w\)", "", text)  # Remove inline references like "(a)"
        paragraph = re.sub(
            r"\bi\.\s*", "", paragraph
        )  # Remove Roman numeral markers like "i."
        paragraph = re.sub(
            r"\s+", " ", paragraph
        ).strip()  # Remove excessive whitespace
        return paragraph

    # Use the summarizer only if the text is long enough
    min_len = max(10, int(word_count * 0.8))  # Minimum length: 80% of the original
    max_len = int(word_count * 1.2) + 20  # Maximum length: 120% + buffer

    try:
        summary = summarizer(
            text, max_length=max_len, min_length=min_len, do_sample=False
        )
        if summary and isinstance(summary, list):
            return summary[0]["summary_text"]
    except Exception as e:
        print(f"Error consolidating text: '{text[:50]}...'. Error: {e}")

    # Fallback: return the original text if summarization fails
    return text


# ------------------------------------------------------------------
# Main function: Process PDF and save consolidated requirements
# ------------------------------------------------------------------
def process_pdf(pdf_path, output_csv):
    """
    Executes the full process:
    - Parses the PDF to extract text.
    - Identifies and extracts requirement segments.
    - Consolidates the text using a local LLM.
    - Saves the consolidated requirements to a CSV file.
    """
    # Step 1: Extract full text from the PDF
    full_text = extract_text_from_pdf(pdf_path)

    # Step 2: Extract requirement segments
    req_dict = extract_requirements(full_text)

    # Step 3: Load the transformer model (check for GPU availability)
    try:
        import torch

        device = 0 if torch.cuda.is_available() else -1
        print(f"Loading transformer model on {'GPU' if device == 0 else 'CPU'}...")
    except ImportError:
        device = -1
        print("PyTorch not found, loading model on CPU.")

    summarizer = pipeline(
        "summarization",
        model="t5-base",  # Use the T5-base model for summarization
        tokenizer="t5-base",
        device=device,
    )

    # Step 4: Consolidate each requirement text
    consolidated = {}
    print(f"Consolidating {len(req_dict)} identified requirements...")
    for code, req_text in req_dict.items():
        consolidated_text = consolidate_paragraph(req_text, summarizer=summarizer)
        consolidated[code] = consolidated_text

    # Step 5: Write the consolidated requirements to a CSV file
    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])  # Write header row
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])  # Write each requirement and its content

    print(f"Process completed. Results saved to '{output_csv}'.")
