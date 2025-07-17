import re
import pdfplumber
import csv
from openai import OpenAI

# ------------------------------------------------------------------
# OpenAI API-Konfiguration (z. B. GPT-4, GPT-3.5 über ChatGPT-Account)
# ------------------------------------------------------------------
client = OpenAI(api_key="XXXXXXXXXXXX")  # Setze deinen OpenAI API-Schlüssel hier ein
MODEL = "gpt-4"  # oder "gpt-3.5-turbo"


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
    # Speichere den extrahierten Text in einer Datei
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    return text


# ------------------------------------------------------------------
# Anforderungen anhand von Mustern erkennen
# ------------------------------------------------------------------
def find_requirements(text):
    patterns = [
        r"Disclosure\s+Requirement\s+(G\d{1,2}[\-–—−]\d{1,2})",     # z. B. Disclosure Requirement G1-2
        r"Disclosure\s+(G?\d{1,2}[\-–—−]\d{1,2})",                  # z. B. Disclosure 2-1 oder G1-2
        r"(G\d{1,2}[\-–—−]\d{1,2})",                                # z. B. G1-2 alleinstehend
        r"Kriterium\s+(\d{1,2})",                                   # Deutsch: Kriterium 10
        r"Criterion\s+(\d{1,2})"                                    # Englisch: Criterion 7
        r"\b(\d{1,2})\.\s+(Strategie|Wesentlichkeit|Ziele|Tiefe der Wertschöpfungskette|Verantwortung|Regeln und Prozesse|Kontrolle|Anreizsysteme|Beteiligung von Anspruchsgruppen|Innovations- und Produktmanagement|Inanspruchnahme natürlicher Ressourcen|Ressourcenmanagement|Klimarelevante Emissionen|Arbeitnehmerrechte|Chancengleichheit|Qualifizierung|Menschenrechte|Gemeinwesen|Politische Einflussnahme|Gesetzes- und richtlinienkonformes Verhalten)" 
        r"(GRI(?:\s+SRS)?[\- ]?\d{3}[\-–—−]\d{1,2})",               # GRI SRS-205-1, GRI 305–3, etc.
        r"\b\d{3}[\-–—−]\d{1,2}\b"                                  # z. B. 305-5 alleinstehend
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
        end_idx = req_matches[i + 1][1] if i + 1 < len(req_matches) else len(text)
        segment = text[start_idx:end_idx]
        segment = segment.strip()
        requirements[code] = requirements.get(code, "") + " " + segment
    return requirements

# ------------------------------------------------------------------
# Konsolidierung mit OpenAI GPT-Modell
# ------------------------------------------------------------------
def openai_consolidate(code, paragraph):
    prompt = f"""
    Fasse den folgenden Paragraphen zur Anforderung {code} zu einem vollständigen, gut lesbaren Textabschnitt zusammen.
    Ignoriere dabei eindeutig erkennbare Fußnoten, Seitenzahlen, Header oder Titel, die nichts mit dem Inhalt der Anforderung zu tun haben.
    Verwende ausschließlich Inhalte, die direkt zur Anforderung gehören. Keine Erfindungen.

    Text: {paragraph}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein präziser, texttreuer Konsolidierer von ESG-Anforderungen.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Fehler bei Anforderung {code}: {e}")
        return paragraph


# ------------------------------------------------------------------
# Hauptfunktion: PDF verarbeiten und konsolidierte Anforderungen speichern
# ------------------------------------------------------------------
def process_pdf(pdf_path, output_csv):
    full_text = extract_text_from_pdf(pdf_path)
    req_dict = extract_requirements(full_text)

    # Bearbeite nur die letzte Anforderung (z. B. G1-6)
    if req_dict:
        last_key = list(req_dict.keys())[-1]
        paragraph = req_dict[last_key]

        # Trimme alles, was z. B. Glossar, Appendix, Imprint ist
        def trim_end_noise(text):
            end_markers = ["Appendix", "Glossar", "Definitions", "Contact", "Imprint"]
            for marker in end_markers:
                idx = text.lower().find(marker.lower())
                if idx != -1:
                    return text[:idx]
            return text

        req_dict[last_key] = trim_end_noise(paragraph)

    consolidated = {}
    print(f"Konsolidiere {len(req_dict)} gefundene Requirements mit OpenAI {MODEL}...")
    for code, req_text in req_dict.items():
        consolidated[code] = req_text #openai_consolidate(code, req_text)

    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["Requirement", "Paragraph"])
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])

    print(f"Prozess abgeschlossen. Ergebnisse in '{output_csv}' gespeichert.")
