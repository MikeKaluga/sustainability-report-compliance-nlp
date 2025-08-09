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

import warnings
# Suppress a specific FutureWarning from the transformers library
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")

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
from analyze import analyze_matches_with_llm
from exporter import export_requirements, is_export_available
from extractor import detect_standard_from_pdf

class MultiReportApp(tk.Tk):
    """
    An application for compliance analysis of one standard against multiple sustainability reports.
    """
    def __init__(self):
        super().__init__()
        self.title(translate("multi_report_app_title"))
        self.geometry("900x700")

        messagebox.showwarning(
            title=translate("dev_warning_title"),
            message=translate("dev_warning_message")
        )

        # --- Data storage ---
        self.standard_pdf_path = None
        self.report_pdf_paths = []
        self.requirements_data = {}
        self.standard_emb = None
        self.embedder = SBERTEmbedder()
        self.results = {} # {report_path: matches}
        self.llm_results_agg = {} # {req_code: (compliant_count, total_count)}

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

        self.llm_analysis_btn = ttk.Button(control_frame, text=translate("analyze_with_llm"), command=self._run_llm_analysis, state=tk.DISABLED)
        self.llm_analysis_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = ttk.Button(control_frame, text=translate("export_results"), command=self._show_export_menu, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=10)

        # --- Frame for selected files list ---
        files_frame = ttk.LabelFrame(main_frame, text=translate("selected_files"), padding="10")
        files_frame.pack(fill=tk.X, pady=10)
        self.selected_files_list = tk.Listbox(files_frame, height=5)
        self.selected_files_list.pack(fill=tk.X, expand=True)

        # --- Frame for results ---
        results_frame = ttk.LabelFrame(main_frame, text=translate("summary_statistics"), padding="10")
        results_frame.pack(expand=True, fill=tk.BOTH)

        # --- Treeview for statistics ---
        self.stats_tree = ttk.Treeview(results_frame, columns=("req_code", "req_text", "avg_max_score", "reports_covered", "llm_compliance"), show="headings")
        self.stats_tree.heading("req_code", text=translate("req_code"))
        self.stats_tree.heading("req_text", text=translate("req_text"))
        self.stats_tree.heading("avg_max_score", text=translate("avg_max_score"))
        self.stats_tree.heading("reports_covered", text=translate("reports_covered"))
        self.stats_tree.heading("llm_compliance", text=translate("llm_compliance"))

        self.stats_tree.column("req_code", width=100)
        self.stats_tree.column("req_text", width=350)
        self.stats_tree.column("avg_max_score", width=120, anchor=tk.CENTER)
        self.stats_tree.column("reports_covered", width=120, anchor=tk.CENTER)
        self.stats_tree.column("llm_compliance", width=120, anchor=tk.CENTER)
        
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
        self.llm_analysis_btn.config(state=tk.DISABLED)
        self.llm_results_agg = {}

        try:
            self.requirements_data = extract_requirements_from_standard_pdf(self.standard_pdf_path)
            if not self.requirements_data:
                messagebox.showerror(translate("error_processing_standard"), translate("no_reqs_found"))
                return

            # --- Detected standard (ESRS/GRI/UNKNOWN) ---
            self.detected_standard = detect_standard_from_pdf(self.standard_pdf_path)

            req_texts = list(self.requirements_data.values())
            self.standard_emb = self.embedder.encode(req_texts)
            
            self.selected_files_list.insert(tk.END, f"Standard: {os.path.basename(self.standard_pdf_path)}")
            self.select_reports_btn.config(state=tk.NORMAL)
            # --- Include detected standard in status ---
            self.status_label.config(text=f"{translate('standard_ready_multi')} {translate('standard_detected', standard=self.detected_standard or 'UNKNOWN')}")
        except Exception as e:
            messagebox.showerror(translate("error_processing_standard"), str(e))
            self.status_label.config(text=translate("error_try_again"))

    def _select_report_files(self):
        """Opens a dialog to select multiple report PDF files."""
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not paths:
            return
        
        self.report_pdf_paths = paths
        self.llm_analysis_btn.config(state=tk.DISABLED)
        self.llm_results_agg = {}
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
        self.llm_analysis_btn.config(state=tk.DISABLED)
        self.llm_results_agg = {}
        
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
        self.llm_analysis_btn.config(state=tk.NORMAL)

    def _run_llm_analysis(self):
        """Runs the LLM analysis in a separate thread."""
        self.run_analysis_btn.config(state=tk.DISABLED)
        self.select_standard_btn.config(state=tk.DISABLED)
        self.select_reports_btn.config(state=tk.DISABLED)
        self.llm_analysis_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._llm_analysis_thread)
        thread.start()

    def _llm_analysis_thread(self):
        """The actual LLM analysis logic that runs in a background thread."""
        total_reports = len(self.report_pdf_paths)
        self.llm_results_agg = {}

        for i, report_path in enumerate(self.report_pdf_paths):
            if report_path not in self.results:
                continue

            self.status_label.config(text=translate("llm_analysis_progress", current=i+1, total=total_reports, name=os.path.basename(report_path)))
            try:
                # Re-extract paragraphs as they are not stored to save memory
                report_paras = extract_paragraphs_from_pdf(report_path)
                if not report_paras:
                    continue
                
                # The matches from SBERT are already in self.results
                sbert_matches = self.results[report_path]
                
                # Run LLM analysis
                llm_matches = analyze_matches_with_llm(sbert_matches, list(self.requirements_data.values()), report_paras)
                
                # Store LLM results by augmenting the existing matches
                self.results[report_path] = llm_matches

            except Exception as e:
                print(f"Could not perform LLM analysis on {report_path}: {e}")

        self._aggregate_llm_results()
        self._update_treeview_with_llm_results()

        self.status_label.config(text=translate("llm_analysis_complete"))
        self.run_analysis_btn.config(state=tk.NORMAL)
        self.select_standard_btn.config(state=tk.NORMAL)
        self.select_reports_btn.config(state=tk.NORMAL)
        self.llm_analysis_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)

    def _aggregate_llm_results(self):
        """Aggregates LLM results from all reports for each requirement."""
        self.llm_results_agg = {}
        req_codes = list(self.requirements_data.keys())

        for i, code in enumerate(req_codes):
            llm_explanations = []
            for report_path in self.report_pdf_paths:
                if report_path in self.results and self.results[report_path][i]:
                    top_match = self.results[report_path][i][0]
                    # Check if LLM analysis was performed (tuple is longer and explanation exists)
                    if len(top_match) > 3 and top_match[3]: # top_match[3] is the llm_explanation
                        llm_explanations.append(top_match[3])
            # Store the first available explanation, or None if no explanations exist
            self.llm_results_agg[code] = llm_explanations[0] if llm_explanations else None

    def _update_treeview_with_llm_results(self):
        """Updates the 'LLM Compliance' column in the treeview without rebuilding it."""
        for item_id in self.stats_tree.get_children():
            req_code = self.stats_tree.item(item_id, "values")[0]
            if req_code in self.llm_results_agg:
                explanation = self.llm_results_agg[req_code]
                display_text = explanation[:50] + "..." if explanation and len(explanation) > 50 else (explanation or "No analysis")
                self.stats_tree.set(item_id, "llm_compliance", display_text)

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
                    top_match = self.results[report_path][i][0]
                    # top_match is (para_idx, sbert_score) or could be longer after LLM run
                    # We always use the SBERT score for this column.
                    top_match_score = top_match[1]
                    max_scores.append(top_match_score)
            
            if not max_scores:
                avg_max_score = 0.0
                reports_covered = 0
            else:
                avg_max_score = sum(max_scores) / len(max_scores)
                # Count reports where the best match score is above a threshold (e.g., 0.5)
                reports_covered = sum(1 for score in max_scores if score > 0.5)

            llm_compliance_text = self.llm_results_agg.get(code, "No analysis")
            if llm_compliance_text and len(llm_compliance_text) > 50:
                llm_compliance_text = llm_compliance_text[:50] + "..."""


            self.stats_tree.insert("", tk.END, values=(
                code,
                req_texts[i][:100] + "...", # Truncate text for display
                f"{avg_max_score:.2f}",
                f"{reports_covered} / {len(self.report_pdf_paths)}",
                llm_compliance_text
            ))

    def _show_export_menu(self):
        """Shows export options menu."""
        export_menu = tk.Toplevel(self)
        export_menu.title(translate("export_options"))
        export_menu.geometry("300x200")
        export_menu.transient(self)
        export_menu.grab_set()

        ttk.Label(export_menu, text=translate("select_export_format")).pack(pady=10)

        if is_export_available('csv'):
            ttk.Button(export_menu, text="CSV", command=lambda: self._export_data('csv')).pack(pady=5)
        
        if is_export_available('excel'):
            ttk.Button(export_menu, text="Excel", command=lambda: self._export_data('excel')).pack(pady=5)
        
        if is_export_available('pdf'):
            ttk.Button(export_menu, text="PDF", command=lambda: self._export_data('pdf')).pack(pady=5)

        ttk.Button(export_menu, text=translate("cancel"), command=export_menu.destroy).pack(pady=10)

    def _export_data(self, file_type):
        """Exports the current analysis results to the specified format."""
        if not self.results:
            messagebox.showwarning(translate("no_data"), translate("no_results_to_export"))
            return

        try:
            # Prepare data for export
            export_data = []
            req_codes = list(self.requirements_data.keys())
            req_texts = list(self.requirements_data.values())

            for i, code in enumerate(req_codes):
                # Calculate statistics for this requirement
                max_scores = []
                llm_explanations = []
                
                for report_path in self.report_pdf_paths:
                    if report_path in self.results and self.results[report_path][i]:
                        top_match = self.results[report_path][i][0]
                        max_scores.append(top_match[1])  # SBERT score
                        
                        # Check for LLM explanation
                        if len(top_match) > 3 and top_match[3]:
                            llm_explanations.append(top_match[3])

                avg_score = sum(max_scores) / len(max_scores) if max_scores else 0.0
                reports_covered = sum(1 for score in max_scores if score > 0.5)
                llm_analysis = llm_explanations[0] if llm_explanations else "No analysis"

                export_data.append({
                    'Requirement Code': code,
                    'Requirement Text': req_texts[i],
                    'Avg Max Score': f"{avg_score:.2f}",
                    'Reports Covered': f"{reports_covered} / {len(self.report_pdf_paths)}",
                    'LLM Analysis': llm_analysis
                })

            # Create DataFrame and export
            import pandas as pd
            df = pd.DataFrame(export_data)
            
            from tkinter import filedialog
            file_types = {
                'csv': [("CSV File", "*.csv")],
                'excel': [("Excel File", "*.xlsx")],
                'pdf': [("PDF File", "*.pdf")]
            }
            
            path = filedialog.asksaveasfilename(
                defaultextension=f".{file_type}",
                filetypes=file_types.get(file_type, []),
                initialfile="multi_report_analysis",
                title=f"{translate('export_as')} {file_type.upper()}"
            )
            
            if not path:
                return

            if file_type == 'csv':
                df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
            elif file_type == 'excel':
                df.to_excel(path, index=False)
            elif file_type == 'pdf':
                from exporter import _export_df_to_pdf
                _export_df_to_pdf(df, path, "Multi-Report Analysis Results")

            messagebox.showinfo(translate("export_successful"), translate("export_successful_text", path=path))

        except Exception as e:
            messagebox.showerror(translate("export_error"), translate("export_error_text", e=e))

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
        "llm_compliance": "LLM Compliance",
        "standard_ready_multi": "Standard loaded. Please select one or more reports.",
        "reports_ready_multi": "{count} reports selected. Ready for analysis.",
        "processing_report": "Processing report {current}/{total}: {name}...",
        "analysis_complete": "Analysis complete. Summary statistics are shown below.",
        "analyze_with_llm": "4. Analyze with LLM",
        "export_results": "5. Export",
        "export_options": "Export Options",
        "select_export_format": "Select export format:",
        "no_results_to_export": "No analysis results to export.",
        "llm_analysis_progress": "Performing LLM analysis on report {current}/{total}: {name}...",
        "llm_analysis_complete": "LLM analysis complete. Results updated.",
        "standard_detected": "Detected standard: {standard}",
        "dev_warning_title": "Development Warning",
        "dev_warning_message": "The multi-report analysis feature is currently under development and may not function as expected. Please use with caution."
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
        "llm_compliance": "LLM-Konformität",
        "standard_ready_multi": "Standard geladen. Bitte einen oder mehrere Berichte auswählen.",
        "reports_ready_multi": "{count} Berichte ausgewählt. Bereit zur Analyse.",
        "processing_report": "Verarbeite Bericht {current}/{total}: {name}...",
        "analysis_complete": "Analyse abgeschlossen. Statistiken werden unten angezeigt.",
        "analyze_with_llm": "4. Mit LLM analysieren",
        "export_results": "5. Exportieren",
        "export_options": "Export-Optionen",
        "select_export_format": "Export-Format auswählen:",
        "no_results_to_export": "Keine Analyseergebnisse zum Exportieren.",
        "llm_analysis_progress": "Führe LLM-Analyse für Bericht {current}/{total} durch: {name}...",
        "llm_analysis_complete": "LLM-Analyse abgeschlossen. Ergebnisse aktualisiert.",
        "standard_detected": "Erkannter Standard: {standard}",
        "dev_warning_title": "Entwicklungswarnung",
        "dev_warning_message": "Die Multi-Bericht-Analysefunktion befindet sich derzeit in der Entwicklung und funktioniert möglicherweise nicht wie erwartet. Bitte mit Vorsicht verwenden."
    }

    TRANSLATIONS["en"].update(new_en)
    TRANSLATIONS["de"].update(new_de)

    app = MultiReportApp()
    app.mainloop()