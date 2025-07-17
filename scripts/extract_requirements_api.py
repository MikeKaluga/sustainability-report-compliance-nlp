import re
import pdfplumber
import csv
import requests
import json

# ------------------------------------------------------------------
# LLaMA 3.3 API-Konfiguration (Chat-AI Academic Cloud)
# ------------------------------------------------------------------
CHATAI_URL = "https://chat-ai.academiccloud.de/v1/chat/completions"
API_KEY = "<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>"  # Ersetze durch deinen API-Schlüssel
MODEL = "llama-3.3-70b-instruct"

# ------------------------------------------------------------------
# Text aus PDF extrahieren und bereinigen
# ------------------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """
    Öffnet ein PDF und extrahiert den gesamten Text aller Seiten als einzelnes String.
    Führt grundlegende Bereinigung durch (Entfernen von Silbentrennungs-Hyphen und Zusammenfügen von Zeilen).
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages_text)
    text = re.sub(r"-\n", "", raw_text)  # Silbentrennungen entfernen
    text = text.replace("\r", "")  # Carriage-Returns entfernen
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # Einzelne Zeilenumbrüche glätten
    text = re.sub(r"\s+", " ", text).strip()  # Mehrfache Leerzeichen bereinigen
    return text

# ------------------------------------------------------------------
# Anforderungen anhand von Mustern erkennen
# ------------------------------------------------------------------
def find_requirements(text):
    patterns = [
        r"Disclosure\s+Requirement\s+([A-Z]\d+[-–]\d+)",
        r"Disclosure\s+Requirement\s+([A-Z]\d+-\d+)",
        r"Disclosure\s+(\d+-\d+)",
        r"Kriterium\s+(\d+)",
        r"Criterion\s+(\d+)"
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)
    matches = []
    for m in regex.finditer(text):
        code = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5)
        if m.group(4):
            code = "Kriterium " + code
        elif m.group(5):
            code = "Criterion " + code
        matches.append((code, m.start()))
    matches.sort(key=lambda x: x[1])  # nach Fundstelle sortieren
    return matches

# ------------------------------------------------------------------
# Abschnitte nach Requirements extrahieren
# ------------------------------------------------------------------
def extract_requirements(text):
    req_matches = find_requirements(text)
    requirements = {}
    for i, (code, start_idx) in enumerate(req_matches):
        end_idx = req_matches[i+1][1] if i+1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        segment = re.sub(r"^.*?(?=The undertaking shall|The objective|Application requirement|\n)", "", segment, flags=re.IGNORECASE | re.DOTALL).strip()
        requirements[code] = requirements.get(code, "") + " " + segment
    return requirements

# ------------------------------------------------------------------
# Konsolidierung mit LLaMA 3.3 über API
# ------------------------------------------------------------------
def llama_consolidate(code, paragraph):
    prompt = f"Fasse den folgenden Paragraphen zur Anforderung {code} zu einem vollständigen, gut lesbaren Textabschnitt zusammen. Verwende nur vorhandene Inhalte. Keine Erfindungen. Erhalte alle wichtigen Punkte und Aufzählungen vollständig.\n\nText: {paragraph}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Du bist ein präziser, texttreuer Konsolidierer von ESG-Anforderungen."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(CHATAI_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Fehler bei Anforderung {code}: {e}")
        return paragraph

# ------------------------------------------------------------------
# Hauptfunktion: PDF verarbeiten und konsolidierte Anforderungen speichern
# ------------------------------------------------------------------
def process_pdf(pdf_path, output_csv):
    full_text = extract_text_from_pdf(pdf_path)
    req_dict = extract_requirements(full_text)

    consolidated = {}
    print(f"Konsolidiere {len(req_dict)} gefundene Requirements mit LLaMA 3.3...")
    for code, req_text in req_dict.items():
        consolidated[code] = llama_consolidate(code, req_text)

    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Requirement", "Paragraph"])
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])

    print(f"Prozess abgeschlossen. Ergebnisse in '{output_csv}' gespeichert.")
