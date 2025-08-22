"""
This script provides translation functionality for a multilingual application.
It includes a dictionary of translations for English and German, and utility functions
to retrieve translated text and switch between languages.

Key Features:
- Stores translations for various UI elements and messages in English and German.
- Supports dynamic placeholder replacement in translated strings.
- Allows toggling between English ('en') and German ('de') languages.

Usage:
- Use `translate(key, **kwargs)` to retrieve the translated text for a given key.
- Call `switch_language()` to toggle the current language between English and German.
"""

# Dictionary containing translations for different languages
TRANSLATIONS = {
    "en": {
        "app_title": "Sustainability Report Compliance Checker",
        "select_standard": "Select Standard PDF",
        "select_report": "Select Report PDF",
        "run_matching": "Run Matching",
        "export_llm_analysis": "Export LLM Analysis",
        "initial_status": "Please select a standard PDF.",
        "extracting_requirements": "Extracting requirements...",
        "error_processing_standard": "Error Processing Standard",
        "error_processing_report": "Error Processing Report",
        "matching_completed": "Matching completed. Results are now available for viewing.",
        "no_data": "No data available.",
        "language_switch": "Switch Language",
        "standard_ready": "Standard ready. Please select a report PDF.",
        "report_ready": "Report ready. Matching can now be performed.",
        "performing_matching": "Performing matching...",
        "matching_completed_label": "Matching completed. Select a requirement to view results.",
        "requirements_from_standard": "Requirements from Standard",
        "requirement_text_and_matches": "Requirement Text and Matches in Report",
        "export_reqs": "Export Requirements",
        "export_paras": "Export Report Paragraphs",
        "export_matches": "Export Matching Results",
        "missing_libs": "Missing Libraries",
        "missing_libs_text": "The export functionality requires the libraries 'pandas', 'openpyxl', and 'reportlab'.\n\nPlease install them using:\npip install pandas openpyxl reportlab",
        "no_reqs_found": "No requirements found.",
        "reqs_loaded": "requirements loaded. Generating embeddings...",
        "paras_found": "paragraphs found in the report. Generating embeddings...",
        "error_try_again": "Error. Please try again.",
        "completed": "Completed",
        "disclosure_requirement": "Disclosure Requirement",
        "selected_subpoint": "Selected Sub-point:",
        "datapoint": "Datapoint:",
        "matches_found_label": "Matches found in report:",
        "no_matches_found": "No matching paragraphs found.",
        "export_as": "Export as",
        "no_reqs_to_export": "There are no requirements to export.",
        "no_paras_to_export": "There are no report paragraphs to export.",
        "no_matches_to_export": "No matches have been generated yet.",
        "export_successful": "Export Successful",
        "export_successful_text": "Data has been successfully saved to\n{path}",
        "export_error": "Export Error",
        "export_error_text": "Error exporting file: {e}",
        "sub_points": "Sub-points",
        "run_matching_first": "Please run matching first to see results.",
        "standard_detected": "Detected standard: {standard}",

        # --- FAQ Menu ---
        "help": "Help",
        "about": "About",

        # --- Help/FAQ Window ---
        "help_title": "Instructions & FAQ",
        "help_step1_title": "Step 1: Select Standard",
        "help_step1_text": "Click 'Select Standard' and choose the PDF file of the standard (e.g., GRI or ESRS) you want to check against. The application will automatically extract the requirements contained within.",
        "help_step2_title": "Step 2: Select Report",
        "help_step2_text": "After the standard is loaded, click 'Select Report' and choose the sustainability report (PDF) you want to analyze. The application will parse the report into individual paragraphs.",
        "help_step3_title": "Step 3: Run Matching",
        "help_step3_text": "Click 'Run Matching' to start the semantic analysis. The application compares each requirement from the standard with all paragraphs from the report to find the most relevant matches.",   
        "help_step4_title": "Step 4: View Results",
        "help_step4_text": "Click on a requirement in the list on the left. The full text of the requirement and the top five matching paragraphs from the report, along with their similarity scores, will be displayed on the right.",
        "help_step5_title": "Step 5: Export Results",
        "help_step5_text": "Use the 'Export' menu to save the extracted requirements, the report paragraphs, or the complete matching results as a CSV, Excel, or PDF file.",
        "help_step6_title": "Step 6: Export LLM Analysis Results",
        "help_step6_text": "Click 'Export LLM Analysis' to save the results for all requirements and their matches to a CSV file.",

        # --- About Window ---
        "about_title": "About the app for investigating the compliance of sustainability reports with reporting standards using NLP methods",
        "about_text": "This application was developed as part of a bachelor's thesis to analyze the compliance of sustainability reports with established standards (such as GRI and ESRS) using NLP methods.",
        "about_version": "Version: 1.4",
        "about_author": "Author: Mihail Savvateev",

        # --- For The Multiple Report UI ---
        "multi_report_app_title": "Multi-Report Compliance Analyzer",
        "select_reports": "Select Reports",
        "reports": "Reports",
        "reports_ready_multi": "{count} reports selected. Ready.",
        "parse_reports": "Parse Reports",
        "parsing_report": "Parsing report {current}/{total}: {name}...",
        "reports_parsed_status": '{count} reports parsed.',
    },
    "de": {
        "app_title": "Untersuchung der Übereinstimmung von Nachhaltigkeitsberichten",
        "select_standard": "Standard-PDF auswählen",
        "select_report": "Bericht-PDF auswählen",
        "run_matching": "Übereinstimmung prüfen",
        "export_llm_analysis": "LLM-Analyse exportieren",
        "initial_status": "Bitte eine Standard-PDF auswählen.",
        "extracting_requirements": "Anforderungen werden extrahiert...",
        "error_processing_standard": "Fehler bei der Verarbeitung des Standards",
        "error_processing_report": "Fehler bei der Verarbeitung des Berichts",
        "matching_completed": "Prüfung der Übereinstimmung abgeschlossen. Ergebnisse können jetzt angezeigt werden.",
        "no_data": "Keine Daten verfügbar.",
        "language_switch": "Sprache wechseln",
        "standard_ready": "Standard bereit. Bitte Bericht-PDF auswählen.",
        "report_ready": "Bericht bereit. Prüfung der Übereinstimmung kann jetzt durchgeführt werden.",
        "performing_matching": "Prüfung der Übereinstimmung wird durchgeführt...",
        "matching_completed_label": "Prüfung abgeschlossen. Wähle eine Anforderung zur Ansicht.",
        "requirements_from_standard": "Anforderungen aus Standard",
        "requirement_text_and_matches": "Anforderungstext und gefundene Übereinstimmungen im Bericht",
        "export_reqs": "Anforderungen exportieren",
        "export_paras": "Bericht-Absätze exportieren",
        "export_matches": "Übereinstimmungs-Ergebnisse exportieren",
        "missing_libs": "Fehlende Bibliotheken",
        "missing_libs_text": "Für die Export-Funktionalität werden die Bibliotheken 'pandas', 'openpyxl' und 'reportlab' benötigt.\n\nBitte installieren Sie diese mit:\npip install pandas openpyxl reportlab",
        "no_reqs_found": "Keine Anforderungen gefunden.",
        "reqs_loaded": "Anforderungen geladen. Erstelle Embeddings...",
        "paras_found": "Absätze im Bericht gefunden. Erstelle Embeddings...",
        "error_try_again": "Fehler. Bitte erneut versuchen.",
        "completed": "Abgeschlossen",
        "disclosure_requirement": "Angabepflicht",
        "selected_subpoint": "Ausgewählter Unterpunkt:",
        "datapoint": "Angabe:",
        "matches_found_label": "Gefundene Übereinstimmungen im Bericht:",
        "no_matches_found": "Keine Übereinstimmungen gefunden.",
        "export_as": "Exportieren als",
        "no_reqs_to_export": "Es gibt keine Anforderungen zum Exportieren.",
        "no_paras_to_export": "Es gibt keine Bericht-Absätze zum Exportieren.",
        "no_matches_to_export": "Es wurden noch keine Übereinstimmungen generiert.",
        "export_successful": "Export erfolgreich",
        "export_successful_text": "Daten wurden erfolgreich nach\n{path}\ngespeichert.",
        "export_error": "Exportfehler",
        "export_error_text": "Fehler beim Exportieren der Datei: {e}",
        "sub_points": "Unterpunkte",
        "run_matching_first": "Bitte führen Sie zuerst das Matching aus, um Ergebnisse zu sehen.",
        "standard_detected": "Erkannter Standard: {standard}",

        # --- FAQ Menu ---
        "help": "Hilfe",
        "about": "Über",

        # --- Help/FAQ Window ---
        "help_title": "Anleitung & FAQ",
        "help_step1_title": "Schritt 1: Standard auswählen",
        "help_step1_text": "Klicken Sie auf 'Standard auswählen' und wählen Sie die PDF-Datei des Standards (z.B. GRI oder ESRS), gegen den Sie prüfen möchten. Die Anwendung extrahiert automatisch die darin enthaltenen Anforderungen.",
        "help_step2_title": "Schritt 2: Bericht auswählen",
        "help_step2_text": "Nachdem der Standard geladen wurde, klicken Sie auf 'Bericht auswählen' und wählen Sie den Nachhaltigkeitsbericht (PDF), den Sie analysieren möchten. Die Anwendung zerlegt den Bericht in einzelne Absätze.",
        "help_step3_title": "Schritt 3: Abgleich durchführen",
        "help_step3_text": "Klicken Sie auf 'Abgleich durchführen', um die semantische Analyse zu starten. Die Anwendung vergleicht jede Anforderung aus dem Standard mit allen Absätzen aus dem Bericht und findet die relevantesten Übereinstimmungen.",
        "help_step4_title": "Schritt 4: Ergebnisse ansehen",
        "help_step4_text": "Klicken Sie auf eine Anforderung in der linken Liste. Rechts werden der vollständige Text der Anforderung sowie die fünf am besten passenden Absätze aus dem Bericht samt Ähnlichkeits-Score angezeigt.",
        "help_step5_title": "Schritt 5: Ergebnisse exportieren",
        "help_step5_text": "Nutzen Sie das 'Export'-Menü, um die extrahierten Anforderungen, die Berichtsabsätze oder die vollständigen Übereinstimmungs-Ergebnisse als CSV, Excel oder PDF zu speichern.",
        "help_step6_title": "Schritt 6: LLM-Analyseergebnisse exportieren",
        "help_step6_text": "Klicken Sie auf 'LLM-Analyse exportieren', um die Ergebnisse für alle Anforderungen und deren Übereinstimmungen in einer CSV-Datei zu speichern.",

        # --- About Window ---
        "about_title": "Über die App zur Untersuchung der Übereinstimmung von Nachhaltigkeitsberichten mit Berichtsstandards unter Verwendung von NLP-Methoden",
        "about_text": "Diese Anwendung wurde im Rahmen einer Bachelorarbeit entwickelt, um die Einhaltung von Nachhaltigkeitsberichten mit etablierten Standards (wie GRI und ESRS) mithilfe von NLP-Methoden zu analysieren.",
        "about_version": "Version: 1.4",
        "about_author": "Autor: Mihail Savvateev",

        # --- Für das Multi Report UI ---
        "multi_report_app_title": "Multi-Bericht Compliance-Analysator",
        "select_reports": "Berichte auswählen",
        "reports": "Berichte",
        "reports_ready_multi": "{count} Berichte ausgewählt. Bereit.",
        "parse_reports": "Berichte parsen",
        "parsing_report": "Bericht wird verarbeitet {current}/{total}: {name}...",
        "reports_parsed_status": "{count} Berichte geparst.",
    },
}

# Default language
current_language = "de"


def translate(key, **kwargs):
    """
    Returns the translated text for the given key based on the current language.
    Supports placeholder replacement.

    Args:
        key (str): The key for the text to be translated.
        **kwargs: Placeholder values to format the string.

    Returns:
        str: The translated and formatted text.
    """
    text = TRANSLATIONS.get(current_language, {}).get(key, key)
    return text.format(**kwargs)


def switch_language():
    """
    Toggles the current language between English ('en') and German ('de').
    """
    global current_language
    current_language = "de" if current_language == "en" else "en"
