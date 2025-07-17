import re
import csv
import pdfplumber

# ---------------------- GRI Extraction (Deutsch & Englisch) ----------------------
def extract_gri(text):
    if "Disclosure 205-1" in text:
        return extract_gri_en(text)
    else:
        return extract_gri_de(text)

def extract_gri_de(text):
    results = {}
    pattern = re.compile(r"Angabe\s+(\d{3}[-\u2013\u2014\u2212]\d{1,2})\s+([^\n\r]+)", re.IGNORECASE)
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        code = f"GRI {match.group(1)}"
        start_idx = match.end()

        if i + 1 < len(matches):
            end_idx = matches[i + 1].start()
        else:
            end_block = re.search(r"(Erl\u00e4uterungen|EMPFEHLUNGEN|Hintergrundinformationen)", text[start_idx:], re.IGNORECASE)
            end_idx = start_idx + end_block.start() if end_block else len(text)

        section = text[start_idx:end_idx].strip()
        requirement_matches = re.findall(r"(?m)^[a-z]\.\s.*?(?=(?:\\n[a-z]\.\s)|$)", section, re.DOTALL)
        clean_text = "\n".join([r.strip() for r in requirement_matches])

        results[code] = clean_text.strip()

    return results

def extract_gri_en(text):
    results = {}
    pattern = re.compile(r"Disclosure\s+(205[-\u2013\u2014\u2212]\d)\s+(.+?)\n", re.IGNORECASE)
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        code = f"GRI {match.group(1)}"
        start_idx = match.end()

        # Suche nach echter Startstelle: REQUIREMENTS
        start_block = re.search(r"(?i)REQUIREMENTS", text[start_idx:])
        if not start_block:
            continue  # Kein echter Inhalt -> skip

        real_start = start_idx + start_block.end()

        # Bestimme Ende
        if i + 1 < len(matches):
            end_idx = matches[i + 1].start()
        else:
            end_block = re.search(r"(Guidance for Disclosure|Glossary|Background|Bibliography)", text[real_start:], re.IGNORECASE)
            end_idx = real_start + end_block.start() if end_block else len(text)

        section = text[real_start:end_idx].strip()
        requirement_matches = re.findall(r"(?m)^[a-z]\.\s.*?(?=(?:\\n[a-z]\.\s)|$)", section, re.DOTALL)
        clean_text = "\n".join([r.strip() for r in requirement_matches])
        results[code] = clean_text.strip()

    return results

# ---------------------- Placeholder Functions ----------------------
def extract_esrs(text):
    return {}

def extract_dnk(text):
    return {}

# ---------------------- Dispatcher ----------------------
def extract_requirements(text, standard='auto'):
    if standard == 'GRI':
        return extract_gri(text)
    elif standard == 'ESRS':
        return extract_esrs(text)
    elif standard == 'DNK':
        return extract_dnk(text)
    elif standard == 'auto':
        if "Disclosure 205-1" in text or "Angabe 205-" in text:
            return extract_gri(text)
        elif re.search(r"\bG\d{1,2}[-\u2013\u2014\u2212]\d{1,2}\b", text):
            return extract_esrs(text)
        elif re.search(r"\d{1,2}\.\s+(Strategie|Wesentlichkeit|Ziele)", text):
            return extract_dnk(text)
        else:
            return {}
    else:
        raise ValueError(f"Unbekannter Standard: {standard}")

# ---------------------- PDF Verarbeitung & CSV Export ----------------------
def process_pdf(pdf_path, output_csv, standard='auto'):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    requirements = extract_requirements(full_text, standard=standard)

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])
        for code, text in requirements.items():
            writer.writerow([code, text])

    print(f"{len(requirements)} Anforderungen wurden nach {standard} extrahiert und gespeichert in '{output_csv}'.")

# ---------------------- Beispielnutzung ----------------------
if __name__ == "__main__":
    process_pdf("data/standard.pdf", "data/gri_requirements.csv", standard="GRI")
