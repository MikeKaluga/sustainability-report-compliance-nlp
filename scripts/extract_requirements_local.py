import re
import pdfplumber
import csv
from transformers import pipeline


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
    text = re.sub(r" +", " ", text).strip()  # Mehrfache Leerzeichen bereinigen
    return text


def find_requirements(text):
    """
    Identifiziert alle Requirements anhand vordefinierter Regex-Muster.
    Gibt eine geordnete Liste von Tupeln (Requirement-Code, Start-Index, Ende-Index des Matches) zurück.
    """
    patterns = [
        r"Disclosure\s+Requirement\s+([A-Z]\d+[-–]\d+)(?=\s+[–-])",  # G1-1 – ... (mit en dash oder normalem Bindestrich)
        r"Disclosure\s+Requirement\s+([A-Z]\d+-\d+)",                # Fallback-Muster
        r"Disclosure\s+(\d+-\d+)",                                    # GRI
        r"Kriterium\s+(\d+)",
        r"Criterion\s+(\d+)"
    ]
    combined_pattern = "|".join(patterns)
    regex = re.compile(combined_pattern)
    matches = []
    for m in regex.finditer(text):
        code = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if m.group(3):
            code = "Kriterium " + code
        elif m.group(4):
            code = "Criterion " + code
        # Speichere Code, Start- und Endposition des gesamten Matches
        matches.append((code, m.start(), m.end()))
    matches.sort(key=lambda x: x[1])  # nach Fundstelle sortieren
    return matches


def extract_requirements(text):
    """
    Schneidet den Volltext anhand der gefundenen Requirement-Anker in Segmente.
    Gibt ein Wörterbuch zurück: {Requirement-Code: zusammengesetzter Textabsatz}.
    Leere Segmente werden ignoriert.
    """
    req_matches = find_requirements(text)
    requirements = {}
    for i, (code, start_idx, end_of_match_idx) in enumerate(req_matches):
        # Das Ende des Segments ist der Anfang des nächsten Requirements oder das Ende des Textes
        end_of_segment_idx = req_matches[i+1][1] if i+1 < len(req_matches) else len(text)
        
        # Der eigentliche Inhalt beginnt NACH dem Requirement-Code und geht bis zum Anfang des nächsten.
        content = text[end_of_match_idx:end_of_segment_idx]
        
        # Bereinige den Inhalt und entferne überflüssige Leerzeichen
        cleaned_content = content.strip()

        # Füge den Inhalt nur hinzu, wenn er nicht leer ist
        if cleaned_content:
            # Hänge neuen Inhalt an bestehenden an (falls der Code mehrfach vorkommt)
            if code in requirements:
                requirements[code] += " " + cleaned_content
            else:
                requirements[code] = cleaned_content
                
    return requirements


def consolidate_paragraph(text, summarizer=None, min_words_for_consolidation=15):
    """
    Konsolidiert einen gegebenen Text. Wenn der Text zu kurz ist
    (weniger als `min_words_for_consolidation`), wird er nur bereinigt.
    Ansonsten wird der Summarizer zur Umformulierung genutzt.
    """
    text = text.strip()
    word_count = len(text.split())

    # Wenn der Text zu kurz ist oder kein Summarizer da ist, nur einfache Bereinigung
    if not summarizer or word_count < min_words_for_consolidation:
        paragraph = re.sub(r"\(\w\)", "", text)
        paragraph = re.sub(r"\bi\.\s*", "", paragraph)
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        return paragraph

    # Nur wenn der Text lang genug ist, das Transformer-Modell verwenden
    min_len = max(10, int(word_count * 0.8))  # Mindestens 80% der Originallänge
    max_len = int(word_count * 1.2) + 20      # Maximal 120% + Puffer

    try:
        summary = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False)
        if summary and isinstance(summary, list):
            return summary[0]['summary_text']
    except Exception as e:
        print(f"Fehler bei der Konsolidierung für Text: '{text[:50]}...'. Fehler: {e}")

    # Fallback, falls die Zusammenfassung fehlschlägt
    return text


def process_pdf(pdf_path, output_csv):
    """
    Führt den gesamten Prozess durch: PDF parsen, Requirements extrahieren, konsolidieren und in CSV speichern.
    """
    # Schritt 1: Volltext aus PDF extrahieren
    full_text = extract_text_from_pdf(pdf_path)

    # Schritt 2: Requirements-Segmente heraustrennen
    req_dict = extract_requirements(full_text)

    # Schritt 3: Transformer-Modell laden (mit GPU-Prüfung)
    try:
        import torch
        device = 0 if torch.cuda.is_available() else -1
        print(f"Transformer-Modell wird auf {'GPU' if device == 0 else 'CPU'} geladen...")
    except ImportError:
        device = -1
        print("PyTorch nicht gefunden, lade Modell auf CPU.")

    summarizer = pipeline(
        "summarization",
        model="t5-base",
        tokenizer="t5-base",
        device=device
    )

    # Schritt 4: Jeden Requirement-Text konsolidieren
    consolidated = {}
    print(f"Konsolidiere {len(req_dict)} gefundene Requirements...")
    for code, req_text in req_dict.items():
        consolidated_text = consolidate_paragraph(req_text, summarizer=summarizer)
        consolidated[code] = consolidated_text

    # Schritt 5: In CSV schreiben
    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Requirement", "Paragraph"])
        for code, paragraph in consolidated.items():
            writer.writerow([code, paragraph])

    print(f"Prozess abgeschlossen. Ergebnisse in '{output_csv}' gespeichert.")
