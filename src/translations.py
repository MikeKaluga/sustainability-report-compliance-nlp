# Dictionary containing translations for different languages
TRANSLATIONS = {
    "en": {
        "app_title": "Sustainability Report Compliance Checker",
        "select_standard": "1. Select Standard PDF",
        "select_report": "2. Select Report PDF",
        "run_matching": "3. Run Matching",
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
        "req_text_label": "REQUIREMENT TEXT:",
        "matches_found_label": "MATCHES FOUND IN REPORT:",
        "no_matches_found": "No matching paragraphs found.",
        "export_as": "Export as",
        "no_reqs_to_export": "There are no requirements to export.",
        "no_paras_to_export": "There are no report paragraphs to export.",
        "no_matches_to_export": "No matches have been generated yet.",
        "export_successful": "Export Successful",
        "export_successful_text": "Data has been successfully saved to\n{path}",
        "export_error": "Export Error",
        "export_error_text": "An error occurred while exporting:\n{e}",
    },
    "de": {
        "app_title": "Sustainability Report Compliance Checker",
        "select_standard": "1. Standard-PDF auswählen",
        "select_report": "2. Bericht-PDF auswählen",
        "run_matching": "3. Matching durchführen",
        "initial_status": "Bitte eine Standard-PDF auswählen.",
        "extracting_requirements": "Anforderungen werden extrahiert...",
        "error_processing_standard": "Fehler bei der Verarbeitung des Standards",
        "error_processing_report": "Fehler bei der Verarbeitung des Berichts",
        "matching_completed": "Matching abgeschlossen. Ergebnisse können jetzt angezeigt werden.",
        "no_data": "Keine Daten verfügbar.",
        "language_switch": "Sprache wechseln",
        "standard_ready": "Standard bereit. Bitte Bericht-PDF auswählen.",
        "report_ready": "Bericht bereit. Matching kann jetzt durchgeführt werden.",
        "performing_matching": "Matching wird durchgeführt...",
        "matching_completed_label": "Matching abgeschlossen. Wähle eine Anforderung zur Ansicht.",
        "requirements_from_standard": "Anforderungen aus Standard",
        "requirement_text_and_matches": "Anforderungstext und gefundene Matches im Bericht",
        "export_reqs": "Anforderungen exportieren",
        "export_paras": "Bericht-Absätze exportieren",
        "export_matches": "Matching-Ergebnisse exportieren",
        "missing_libs": "Fehlende Bibliotheken",
        "missing_libs_text": "Für die Export-Funktionalität werden die Bibliotheken 'pandas', 'openpyxl' und 'reportlab' benötigt.\n\nBitte installieren Sie diese mit:\npip install pandas openpyxl reportlab",
        "no_reqs_found": "Keine Anforderungen gefunden.",
        "reqs_loaded": "Anforderungen geladen. Erstelle Embeddings...",
        "paras_found": "Absätze im Bericht gefunden. Erstelle Embeddings...",
        "error_try_again": "Fehler. Bitte erneut versuchen.",
        "completed": "Abgeschlossen",
        "req_text_label": "ANFORDERUNGSTEXT:",
        "matches_found_label": "GEFUNDENE MATCHES IM BERICHT:",
        "no_matches_found": "Keine passenden Absätze gefunden.",
        "export_as": "Exportieren als",
        "no_reqs_to_export": "Es gibt keine Anforderungen zum Exportieren.",
        "no_paras_to_export": "Es gibt keine Bericht-Absätze zum Exportieren.",
        "no_matches_to_export": "Es wurden noch keine Matches generiert.",
        "export_successful": "Export erfolgreich",
        "export_successful_text": "Daten wurden erfolgreich nach\n{path}\ngespeichert.",
        "export_error": "Exportfehler",
        "export_error_text": "Ein Fehler ist beim Exportieren aufgetreten:\n{e}",
    },
}

# Default language
current_language = "en"


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
