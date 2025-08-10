"""
This script provides functionality for extracting and cleaning text from PDF documents.
It is designed to process sustainability reports by segmenting the text into meaningful paragraphs
while filtering out noise such as metadata, headers, and irrelevant content.

Key Features:
- Cleans raw text by normalizing line breaks and removing unnecessary spaces.
- Extracts paragraphs based on double line breaks or sentence-based segmentation as a fallback.
- Filters paragraphs based on minimum word/character count and optional noise patterns.
- Provides debug mode for detailed statistics during text extraction.

Usage:
- Use `extract_paragraphs_from_pdf(pdf_path, ...)` to extract cleaned paragraphs from a PDF file.
- Customize parameters like `min_words`, `min_chars`, and `noise_filter` to suit specific requirements.
"""

import pdfplumber
import re

def clean_text(text):
    """
    Cleans the input text by removing unnecessary line breaks and spaces.

    Args:
        text (str): The raw text to be cleaned.

    Returns:
        str: The cleaned text with normalized line breaks and spaces.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")  # Normalize line breaks
    text = re.sub(r"\n{2,}", "\n\n", text)  # Normalize multiple line breaks
    text = re.sub(r" +", " ", text)  # Remove extra spaces
    return text.strip()


def extract_paragraphs_from_pdf(
    pdf_path, min_words=20, min_chars=100, noise_filter=True, debug=False
):
    """
    Extracts paragraphs from a PDF by smoothing line breaks and segmenting text based on double line breaks.
    Falls back to sentence-based segmentation if too few paragraphs are found.
    Filters out paragraphs with fewer than `min_words` words or `min_chars` characters.
    Optionally removes typical metadata patterns using `noise_filter`.
    Outputs debug statistics if `debug=True`.

    Args:
        pdf_path (str): Path to the PDF file.
        min_words (int): Minimum number of words required for a paragraph to be included.
        min_chars (int): Minimum number of characters required for a paragraph to be included.
        noise_filter (bool): Whether to filter out paragraphs matching typical metadata patterns.
        debug (bool): Whether to output debug statistics.

    Returns:
        list of str: A list of cleaned and filtered paragraphs extracted from the PDF.
    """
    # Define regex patterns for filtering out noise (e.g., metadata, headers, URLs)
    noise_patterns = [
        # Table of contents and chapter headings
        r"^(Table of Contents|List of Figures|List of Tables|Appendix|Inhaltsverzeichnis|Abbildungsverzeichnis|Tabellenverzeichnis|Anhang)$",
        r"^Page\s*\d+|^Seite\s*\d+",
        # Management texts and salutations
        r"^Dear (Shareholders|Readers|Stakeholders|Customers)",
        r"^(Sehr geehrte|Liebe) (Damen und Herren|Aktionär.*|Leser.*)",
        # URLs and email addresses
        r"\bhttps?://\S+",
        r"\S+@\S+\.\S+",
        # Standard references (multilingual)
        r"\bGRI\s*\d{1,3}(-\d{1,3})?",  # GRI 1–999
        r"\bGlobal Reporting Initiative\b",
        r"\bGRI[- ]?(Standards|SRS|Index|Bericht)?\b",
        r"\bDNK\b|\bDeutscher Nachhaltigkeitskodex\b",
        r"\bCSRD\b|\bCorporate Sustainability Reporting Directive\b",
        r"\bESRS\s*[A-Z]?\d{0,3}(-\d+)?",
        r"\bEFRAG\b",
        r"\bUN\b.*?(Compact|Principles|SDG|Agenda)",
        r"\bUnited Nations\b.*?(Treaty|Guideline|Charter)?",
        r"\bOECD\b.*?(Guidelines|Principles)?",
        r"\bIFRS\s*\d{0,3}",
        r"\bISO\s*\d{4,6}",
        r"\bEU[- ]?(Directive|Regulation|Verordnung|Richtlinie)?\s*\d{4}\/\d{1,5}",
        r"\b(Artikel|Art\.?)\s*\d+(\s*[a-z]*)?\s*(Abs\.?|Paragraph)?\s*\d*",
        r"\bCSR[- ]?(Richtlinie|Directive|RUG|Umsetzungsgesetz)\b",
        # Topic and disclosure labels
        r"\bAngabe\s*\d{3}-\d{1,3}",
        r"\bDisclosure\s+(Requirement|DR)\s+[A-Z]?\d{1,2}(-\d{1,2})?",
        r"\bKriterium\s*\d+",
        r"\bIndikator\s*\d+",
        r"\bKey (figures|metrics|indicators)\b",
        r"\bThemenstandard\b|\bTopic standard\b",
        # Glossary, appendix, bibliography, footnotes
        r"^(Glossary|Annex|Attachment|Appendix|Bibliography|Footnote|Quellen|Anhang|Glossar|Literaturverzeichnis)\b",
        r"\[\d+\]",  # e.g., [1], [24]
        # Legal notices and copyrights
        r"\b(All rights reserved|Haftungsausschluss|Rechtsgrundlage|Impressum|Datenschutz|Copyright|Markenzeichen|Disclaimer)\b",
        # Metadata and mandatory information
        r"\bReporting period\b|\bBerichtszeitraum\b",
        r"\bBerichtspflicht(ig)?\b",
        r"\bComply or Explain\b",
        r"\b(Stand|Version):?\s*\d{4}",
    ]
    # Compile noise regex patterns
    noise_regex = [re.compile(p, re.IGNORECASE) for p in noise_patterns]

    # Read the PDF and combine text from all pages
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages)

    # Optionally clean the raw text
    try:
        raw_text = clean_text(raw_text)
    except NameError:
        raw_text = raw_text

    # Smooth line breaks
    text = re.sub(r"-\n", "", raw_text)
    text = text.replace("\r\n", "\n")

    # Primary paragraph segmentation: split by double line breaks
    raw_paragraphs = re.split(r"\n{2,}", text)
    if debug:
        print(f"Primary raw paragraphs: {len(raw_paragraphs)}")

    paragraphs = []

    # Function to check if a paragraph matches noise patterns
    def is_noise(p):
        return any(rx.search(p) for rx in noise_regex)

    # Function to filter paragraphs by length and noise
    def filter_paras(candidates):
        filtered = []
        for p in candidates:
            p = p.strip()
            if len(p.split()) < min_words or len(p) < min_chars:
                continue
            if noise_filter and is_noise(p):
                continue
            filtered.append(p)
        return filtered

    paragraphs = filter_paras(raw_paragraphs)
    # Fallback: sentence-based segmentation if too few paragraphs are found
    if len(paragraphs) < 2:
        if debug:
            print(
                "Too few paragraphs after primary segmentation, attempting sentence-based segmentation."
            )
        # Sentence splitting: split by punctuation followed by a capital letter
        sentences = re.split(
            r"(?<=[\.!?])\s+(?=[A-ZÄÖÜ])", re.sub(r"\s+", " ", raw_text)
        )
        if debug:
            print(f"Found sentences: {len(sentences)}")

        # Combine sentences into potential paragraphs
        all_paragraphs_from_sentences = []
        current = ""
        for sent in sentences:
            if not current:
                current = sent.strip()
            else:
                current += " " + sent.strip()
            
            if len(current.split()) >= min_words and len(current) >= min_chars:
                all_paragraphs_from_sentences.append(current)
                current = ""
        if current:  # Add any remaining text
            all_paragraphs_from_sentences.append(current)

        # Replace raw paragraphs with those generated from sentences
        raw_paragraphs = all_paragraphs_from_sentences
        # Filter the new list to get the final relevant paragraphs
        paragraphs = filter_paras(raw_paragraphs)

    if debug:
        print(f"Final paragraphs: {len(paragraphs)}")

    return paragraphs
