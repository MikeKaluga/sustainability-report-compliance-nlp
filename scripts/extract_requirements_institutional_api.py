import re
import pdfplumber
import csv
import requests
import json

# ------------------------------------------------------------------
# LLaMA 3.3 API Configuration (Chat-AI Academic Cloud)
# ------------------------------------------------------------------
# This section configures the API endpoint and credentials for the LLaMA 3.3 model.
# Replace "<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>" with your actual API key.
CHATAI_URL = "https://chat-ai.academiccloud.de/v1/chat/completions"
API_KEY = "<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>"
MODEL = "llama-3.3-70b-instruct"  # Specify the model to use


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
    text = re.sub(r"\s+", " ", text).strip()  # Remove excessive whitespace
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
    """
    patterns = [
        r"Disclosure\s+Requirement\s+([A-Z]\d+[-–]\d+)",  # Matches patterns like "Disclosure Requirement G1-1"
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
    Splits the full text into segments based on identified requirement anchors.
    Returns a dictionary where:
    - Keys are requirement codes.
    - Values are the corresponding text segments.
    """
    req_matches = find_requirements(text)
    requirements = {}
    for i, (code, start_idx) in enumerate(req_matches):
        # Determine the end of the current segment
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        # Remove irrelevant prefixes and clean the segment
        segment = re.sub(
            r"^.*?(?=The undertaking shall|The objective|Application requirement|\n)",
            "",
            segment,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
        # Append the segment to the requirement code (handles duplicates)
        requirements[code] = requirements.get(code, "") + " " + segment
    return requirements


# ------------------------------------------------------------------
# Consolidate text using LLaMA 3.3 via API
# ------------------------------------------------------------------
def llama_consolidate(code, paragraph):
    """
    Uses the LLaMA 3.3 API to consolidate a paragraph into a clean, readable text.
    The prompt instructs the model to:
    - Retain all important points and lists.
    - Avoid fabrications and use only existing content.
    Returns the consolidated text or the original paragraph in case of an error.
    """
    prompt = f"Fasse den folgenden Paragraphen zur Anforderung {code} zu einem vollständigen, gut lesbaren Textabschnitt zusammen. Verwende nur vorhandene Inhalte. Keine Erfindungen. Erhalte alle wichtigen Punkte und Aufzählungen vollständig.\n\nText: {paragraph}"

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Du bist ein präziser, texttreuer Konsolidierer von ESG-Anforderungen.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,  # Low temperature for deterministic responses
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(CHATAI_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error processing requirement {code}: {e}")
        return paragraph


# ------------------------------------------------------------------
# Main function: Process PDF and save consolidated requirements
# ------------------------------------------------------------------
def process_pdf(pdf_path, output_csv):
    """
    Executes the full process:
    - Parses the PDF to extract text.
    - Identifies and extracts requirement segments.
    - Consolidates the text using the LLaMA 3.3 API.
    - Saves the consolidated requirements to a CSV file.
    """
    # Step 1: Extract full text from the PDF
    full_text = extract_text_from_pdf(pdf_path)

    # Step 2: Extract requirement segments
    req_dict = extract_requirements(full_text)

    # Step 3: Consolidate each requirement text using the LLaMA 3.3 API
    consolidated = {}
    print(f"Consolidating {len(req_dict)} identified requirements with LLaMA 3.3...")
    for code, req_text in req_dict.items():
        consolidated[code] = llama_consolidate(code, req_text)

    # Step 4: Write the consolidated requirements to a CSV file
    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])  # Write header row
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])  # Write each requirement and its content

    print(f"Process completed. Results saved to '{output_csv}'.")
