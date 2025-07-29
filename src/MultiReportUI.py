"""
This script provides a graphical user interface (GUI) for analyzing compliance of sustainability reports
against a given standard. It allows users to select a standard PDF and multiple report PDFs, and then
performs an analysis to match requirements from the standard to the content of the reports.

Key Features:
- Extracts requirements from a standard PDF.
- Processes multiple sustainability reports to extract paragraphs.
- Embeds text using Sentence-BERT (SBERT) and matches requirements to report content using cosine similarity.
- Displays summary statistics of the analysis in a user-friendly interface.

Usage:
- Run the script to launch the GUI.
- Use the interface to select a standard PDF and multiple report PDFs.
- Click "Run Analysis" to perform the compliance analysis and view the results.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import pandas as pd

# Import functionalities from your existing modules
from extractor import extract_requirements_from_standard_pdf
from parser import extract_paragraphs_from_pdf
from embedder import SBERTEmbedder
from matcher import match_requirements_to_report
from translations import translate, switch_language

class MultiReportApp(tk.Tk):
    """
    An application for compliance analysis of one standard against multiple sustainability reports.
    """
    def __init__(self):
        super().__init__()
        self.title(translate("multi_report_app_title"))
        self.geometry("900x700")

        # --- Data storage ---
        self.standard_pdf_path = None
        self.report_pdf_paths = []
        self.requirements_data = {}
        self.standard_emb = None
        self.embedder = SBERTEmbedder()
        self.results = {} # {report_path: matches}

        self._create_widgets()

    def _create_widgets(self):
        """Creates the GUI layout."""
        # --- Main container ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Top frame for controls ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.select_standard_btn = ttk.Button(control_frame, text=translate("select_standard"), command=self._select_standard_file)
        self.select_standard_btn.pack(side=tk.LEFT, padx=5)

        self.select_reports_btn = ttk.Button(control_frame, text=translate("select_multiple_reports"), command=self._select_report_files, state=tk.DISABLED)
        self.select_reports_btn.pack(side=tk.LEFT, padx=5)

        self.run_analysis_btn = ttk.Button(control_frame, text=translate("run_analysis"), command=self._run_analysis, state=tk.DISABLED)
        self.run_analysis_btn.pack(side=tk.LEFT, padx=5)

        # --- Frame for selected files list ---
        files_frame = ttk.LabelFrame(main_frame, text=translate("selected_files"), padding="10")
        files_frame.pack(fill=tk.X, pady=10)
        self.selected_files_list = tk.Listbox(files_frame, height=5)
        self.selected_files_list.pack(fill=tk.X, expand=True)

        # --- Frame for results ---
        results_frame = ttk.LabelFrame(main_frame, text=translate("summary_statistics"), padding="10")
        results_frame.pack(expand=True, fill=tk.BOTH)

        # --- Treeview for statistics ---
        self.stats_tree = ttk.Treeview(results_frame, columns=("req_code", "req_text", "avg_max_score", "reports_covered"), show="headings")
        self.stats_tree.heading("req_code", text=translate("req_code"))
        self.stats_tree.heading("req_text", text=translate("req_text"))
        self.stats_tree.heading("avg_max_score", text=translate("avg_max_score"))
        self.stats_tree.heading("reports_covered", text=translate("reports_covered"))

        self.stats_tree.column("req_code", width=100)
        self.stats_tree.column("req_text", width=400)
        self.stats_tree.column("avg_max_score", width=120, anchor=tk.CENTER)
        self.stats_tree.column("reports_covered", width=120, anchor=tk.CENTER)
        
        self.stats_tree.pack(expand=True, fill=tk.BOTH)

        # --- Status Bar ---
        self.status_label = ttk.Label(self, text=translate("initial_status"), relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _select_standard_file(self):
        """Opens a dialog to select a single standard PDF file."""
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return

        self.standard_pdf_path = path
        self.status_label.config(text=translate("extracting_requirements"))
        self.update_idletasks()

        try:
            self.requirements_data = extract_requirements_from_standard_pdf(self.standard_pdf_path)
            if not self.requirements_data:
                messagebox.showerror(translate("error_processing_standard"), translate("no_reqs_found"))
                return

            req_texts = list(self.requirements_data.values())
            self.standard_emb = self.embedder.encode(req_texts)
            
            self.selected_files_list.insert(tk.END, f"Standard: {os.path.basename(self.standard_pdf_path)}")
            self.select_reports_btn.config(state=tk.NORMAL)
            self.status_label.config(text=translate("standard_ready_multi"))
        except Exception as e:
            messagebox.showerror(translate("error_processing_standard"), str(e))
            self.status_label.config(text=translate("error_try_again"))

    def _select_report_files(self):
        """Opens a dialog to select multiple report PDF files."""
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not paths:
            return
        
        self.report_pdf_paths = paths
        self.selected_files_list.insert(tk.END, "--- Reports ---")
        for path in paths:
            self.selected_files_list.insert(tk.END, os.path.basename(path))
        
        self.run_analysis_btn.config(state=tk.NORMAL)
        self.status_label.config(text=translate("reports_ready_multi", count=len(paths)))

    def _run_analysis(self):
        """Runs the analysis in a separate thread to keep the UI responsive."""
        self.run_analysis_btn.config(state=tk.DISABLED)
        self.select_standard_btn.config(state=tk.DISABLED)
        self.select_reports_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._analysis_thread)
        thread.start()

    def _analysis_thread(self):
        """The actual analysis logic that runs in a background thread."""
        self.results = {}
        total_reports = len(self.report_pdf_paths)

        for i, report_path in enumerate(self.report_pdf_paths):
            self.status_label.config(text=translate("processing_report", current=i+1, total=total_reports, name=os.path.basename(report_path)))
            try:
                report_paras = extract_paragraphs_from_pdf(report_path)
                if not report_paras:
                    continue
                
                report_emb = self.embedder.encode(report_paras)
                matches = match_requirements_to_report(self.standard_emb, report_emb, top_k=1) # We only need the top match for stats
                self.results[report_path] = matches
            except Exception as e:
                print(f"Could not process {report_path}: {e}") # Log error to console
        
        self._calculate_and_display_stats()
        self.status_label.config(text=translate("analysis_complete"))
        self.run_analysis_btn.config(state=tk.NORMAL)
        self.select_standard_btn.config(state=tk.NORMAL)
        self.select_reports_btn.config(state=tk.NORMAL)

    def _calculate_and_display_stats(self):
        """Calculates summary statistics and displays them in the treeview."""
        # Clear previous results
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        req_codes = list(self.requirements_data.keys())
        req_texts = list(self.requirements_data.values())

        for i, code in enumerate(req_codes):
            max_scores = []
            for report_path in self.report_pdf_paths:
                if report_path in self.results and self.results[report_path][i]:
                    # Get the score of the best match for this requirement in this report
                    top_match_score = self.results[report_path][i][0][1]
                    max_scores.append(top_match_score)
            
            if not max_scores:
                avg_max_score = 0.0
                reports_covered = 0
            else:
                avg_max_score = sum(max_scores) / len(max_scores)
                # Count reports where the best match score is above a threshold (e.g., 0.5)
                reports_covered = sum(1 for score in max_scores if score > 0.5)

            self.stats_tree.insert("", tk.END, values=(
                code,
                req_texts[i][:100] + "...", # Truncate text for display
                f"{avg_max_score:.2f}",
                f"{reports_covered} / {len(self.report_pdf_paths)}"
            ))

if __name__ == '__main__':
    # Add new translations for this UI
    from translations import TRANSLATIONS
    
    new_en = {
        "multi_report_app_title": "Multi-Report Compliance Analyzer",
        "select_multiple_reports": "2. Select Reports",
        "run_analysis": "3. Run Analysis",
        "selected_files": "Selected Files",
        "summary_statistics": "Summary Statistics",
        "req_code": "Req. Code",
        "req_text": "Requirement Text",
        "avg_max_score": "Avg. Max Score",
        "reports_covered": "Reports Covered",
        "standard_ready_multi": "Standard loaded. Please select one or more reports.",
        "reports_ready_multi": "{count} reports selected. Ready for analysis.",
        "processing_report": "Processing report {current}/{total}: {name}...",
        "analysis_complete": "Analysis complete. Summary statistics are shown below."
    }
    
    new_de = {
        "multi_report_app_title": "Multi-Bericht Compliance-Analysator",
        "select_multiple_reports": "2. Berichte auswählen",
        "run_analysis": "3. Analyse durchführen",
        "selected_files": "Ausgewählte Dateien",
        "summary_statistics": "Zusammenfassende Statistiken",
        "req_code": "Anf.-Code",
        "req_text": "Anforderungstext",
        "avg_max_score": "Ø Max Score",
        "reports_covered": "Abgedeckte Berichte",
        "standard_ready_multi": "Standard geladen. Bitte einen oder mehrere Berichte auswählen.",
        "reports_ready_multi": "{count} Berichte ausgewählt. Bereit zur Analyse.",
        "processing_report": "Verarbeite Bericht {current}/{total}: {name}...",
        "analysis_complete": "Analyse abgeschlossen. Statistiken werden unten angezeigt."
    }

    TRANSLATIONS["en"].update(new_en)
    TRANSLATIONS["de"].update(new_de)

    app = MultiReportApp()
    app.mainloop()