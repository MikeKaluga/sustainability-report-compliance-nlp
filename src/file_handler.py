"""
This module handles file selection and processing for the compliance analysis application.
It includes functions for selecting standard and report PDFs, extracting their content,
and updating the application state.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from translations import translate
from extractor import extract_requirements_from_standard_pdf
from parser import extract_paragraphs_from_pdf
from extractor import detect_standard_from_pdf

def select_standard_file(app):
    """
    Opens a dialog to select a standard PDF, extracts requirements, and updates the app's UI and state.
    Args:
        app: The main ComplianceApp instance.
    """
    path = filedialog.askopenfilename(title=translate("select_standard"), filetypes=[("PDF Files", "*.pdf")])
    if not path:
        return

    app.standard_pdf_path = path
    app.status_label.config(text=f"Standard: {os.path.basename(path)}. {translate('extracting_requirements')}")
    app.update_idletasks()

    try:
        app.requirements_data = extract_requirements_from_standard_pdf(app.standard_pdf_path)
        
        app.detected_standard = detect_standard_from_pdf(app.standard_pdf_path)

        app.req_listbox.delete(0, tk.END)
        if app.requirements_data:
            for code in app.requirements_data.keys():
                app.req_listbox.insert(tk.END, code)
        else:
            app.req_listbox.insert(tk.END, translate("no_reqs_found"))

        app.status_label.config(text=f"{len(app.requirements_data)} {translate('reqs_loaded')}")
        app.update_idletasks()
        
        # Prepare texts for embedding: use sub-points if available, otherwise full text
        standard_texts_for_embedding = []
        for req_code, req_data in app.requirements_data.items():
            if req_data['sub_points']:
                standard_texts_for_embedding.extend(req_data['sub_points'])
            else:
                standard_texts_for_embedding.append(req_data['full_text'])
        
        app.standard_emb = app.embedder.encode(standard_texts_for_embedding)
        
        app.status_label.config(
            text=f"{translate('standard_ready')} {translate('standard_detected', standard=app.detected_standard or 'UNKNOWN')}"
        )
        app.select_report_btn.config(state=tk.NORMAL)
        app.export_menu.entryconfig(0, state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror(translate("error_processing_standard"), f"An error occurred:\n{e}")
        app.status_label.config(text=translate("error_try_again"))

def select_report_file(app):
    """
    Opens a dialog to select a report PDF, extracts paragraphs, and updates the app's UI and state.
    Args:
        app: The main ComplianceApp instance.
    """
    path = filedialog.askopenfilename(title=translate("select_report"), filetypes=[("PDF Files", "*.pdf")])
    if not path:
        return

    app.report_pdf_path = path
    app.status_label.config(text=f"Report: {os.path.basename(path)}. Parsing paragraphs...")
    app.update_idletasks()

    try:
        app.report_paras = extract_paragraphs_from_pdf(app.report_pdf_path)
        app.status_label.config(text=f"{len(app.report_paras)} {translate('paras_found')}")
        app.update_idletasks()
        # Update active report label with paragraph count
        if hasattr(app, '_update_current_report_label'):
            app._update_current_report_label()

        app.report_emb = app.embedder.encode(app.report_paras)
        
        app.status_label.config(text=translate("report_ready"))
        app.run_match_btn.config(state=tk.NORMAL)
        app.export_menu.entryconfig(1, state=tk.NORMAL)
        # Update active report label again (state ready)
        if hasattr(app, '_update_current_report_label'):
            app._update_current_report_label()
    except Exception as e:
        messagebox.showerror(translate("error_processing_report"), f"An error occurred:\n{e}")
        app.status_label.config(text=translate("error_try_again"))

def select_reports_multi(app):
    """
    Opens a dialog to select multiple report PDFs for the multi-report UI,
    and updates the app's UI and state.
    Args:
        app: The main MultiReportApp instance.
    """
    if not app._validate_state_for_operation("select_reports"):
        return
    paths = filedialog.askopenfilenames(
        title=translate("select_reports") if translate("select_reports") != "select_reports" else "Select Reports",
        filetypes=[("PDF", "*.pdf")]
    )
    if not paths:
        return
    invalid_files = []
    for p in paths:
        try:
            if not os.path.exists(p) or not os.access(p, os.R_OK):
                invalid_files.append(os.path.basename(p))
        except Exception:
            invalid_files.append(os.path.basename(p))
    if invalid_files:
        messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                               f"Invalid files: {', '.join(invalid_files)}")
        paths = [p for p in paths if os.path.basename(p) not in invalid_files]
        if not paths:
            return
    new_paths = [p for p in paths if p not in app.reports]
    for p in new_paths:
        app.reports[p] = {'paras': [], 'emb': None, 'matches': None}
        app.report_listbox.insert(tk.END, os.path.basename(p))
    if app.reports and not app.current_report_path:
        app.report_listbox.select_set(0)
        app.current_report_path = list(app.reports.keys())[0]
        app.report_pdf_path = app.current_report_path
    app.parse_reports_btn.config(state=tk.NORMAL)
    app.run_match_btn.config(state=tk.DISABLED)
    app.status_label.config(text=translate("reports_ready_multi", count=len(app.reports)) if translate("reports_ready_multi", count=0) != "reports_ready_multi" else f"{len(app.reports)} reports selected.")
    app.export_menu.entryconfig(1, state=tk.DISABLED)
