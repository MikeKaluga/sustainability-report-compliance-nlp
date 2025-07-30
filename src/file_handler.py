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
        
        app.req_listbox.delete(0, tk.END)
        if app.requirements_data:
            for code in app.requirements_data.keys():
                app.req_listbox.insert(tk.END, code)
        else:
            app.req_listbox.insert(tk.END, translate("no_reqs_found"))

        app.status_label.config(text=f"{len(app.requirements_data)} {translate('reqs_loaded')}")
        app.update_idletasks()
        
        standard_paras = list(app.requirements_data.values())
        app.standard_emb = app.embedder.encode(standard_paras)
        
        app.status_label.config(text=translate("standard_ready"))
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

        app.report_emb = app.embedder.encode(app.report_paras)
        
        app.status_label.config(text=translate("report_ready"))
        app.run_match_btn.config(state=tk.NORMAL)
        app.export_menu.entryconfig(1, state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror(translate("error_processing_report"), f"An error occurred:\n{e}")
        app.status_label.config(text=translate("error_try_again"))
