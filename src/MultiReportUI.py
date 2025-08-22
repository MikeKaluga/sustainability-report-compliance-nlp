"""Multi-report GUI aligned with latest single-report UI architecture.

Features (per loaded report):
 - Extract requirements (with sub-points) from a standard PDF (ESRS / GRI autodetect).
 - Load multiple report PDFs.
 - For each report: parse paragraphs, embed, match (top-k) per requirement or sub-point.
 - Select a report + requirement + optional sub-point to view matches.
 - Run LLM analysis (current selection) using shared logic from analyze.run_llm_analysis.
 - Export (requirements / paragraphs / matches / LLM analysis) for the currently selected report via shared exporter.
 - Language switching, Help/About reuse existing managers.

Data structures:
 self.requirements_data: {code: {'full_text': str, 'sub_points': [...], ...}}
 self.reports: {path: {'paras': [...], 'emb': tensor, 'matches': {text->[(idx, score), ...]}}}

Matching stores results separately per report; current report selection is projected onto self.report_paras & self.matches
 so existing event_handlers + exporter logic work unchanged.
"""

import warnings
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning)

import tkinter as tk
from tkinter import ttk, Listbox, Scrollbar, messagebox, filedialog
import os

from embedder import SBERTEmbedder
from matcher import match_requirements_to_report
from translations import translate
from extractor import extract_requirements_from_standard_pdf, detect_standard_from_pdf
from parser import extract_paragraphs_from_pdf
from menu_manager import configure_export_menu
from language_manager import switch_language_and_update_ui
from event_handlers import handle_requirement_selection


class MultiReportApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(translate("multi_report_app_title") if translate("multi_report_app_title") != "multi_report_app_title" else translate("app_title") + " (Multi)")
        self.geometry("1400x850")

        # State (mirrors single-report UI where possible)
        self.standard_pdf_path = None
        self.detected_standard = None
        self.requirements_data = {}
        self.standard_emb = None
        self.embedder = SBERTEmbedder()
        self.current_req_code = None
        self.current_report_path = None
        self.reports = {}  # path -> {'paras': [...], 'emb': tensor, 'matches': {text:[(idx, score), ...]}}
        self.matches = None  # projection of current report matches (for exporter/event_handlers compatibility)
        self.report_paras = []  # projection of current report paragraphs

        self._create_menu()
        self._create_layout()

        # Compatibility aliases for language_manager (single-report naming)
        # language_manager.update_ui_texts expects these attributes
        self.select_report_btn = self.add_reports_btn
        self.parse_btn = self.parse_reports_btn
        self.subpoint_container = self.sub_point_container
        # Alias for single-report's selected report path
        self.report_pdf_path = self.current_report_path

        # Provide a no-op placeholder so language_manager can safely call .config(...)
        class _NoOpWidget:
            def config(self, *args, **kwargs):  # no-op
                pass
        self.analyze_llm_btn = _NoOpWidget()

    def update_ui_texts(self):
        """Update all UI widgets with translated text after language switch."""
        # Window title
        title = translate("multi_report_app_title")
        if title == "multi_report_app_title":
            title = translate("app_title") + " (Multi)"
        self.title(title)

        # Cascades (indices based on creation order)
        try:
            exp_label = translate("export")
            if exp_label == "export":
                exp_label = "Export"
            self.menu_bar.entryconfig(0, label=exp_label)   # Export
            self.menu_bar.entryconfig(1, label="FAQ")       # Keep 'FAQ' label simple
            self.menu_bar.entryconfig(2, label="DE/EN")
        except Exception:
            pass

        # Export submenu items (indices depend on configure_export_menu)
        try:
            self.export_menu.entryconfig(0, label=translate("export_requirements"))
            self.export_menu.entryconfig(1, label=translate("export_paragraphs"))
            self.export_menu.entryconfig(2, label=translate("export_matches"))
            self.export_menu.entryconfig(3, label=translate("export_llm_analysis"))
        except Exception:
            pass

        # Buttons
        self.select_standard_btn.config(text=translate("select_standard"))
        reports_text = translate("select_reports")
        if reports_text == "select_reports":
            reports_text = "Select Reports"
        self.add_reports_btn.config(text=reports_text)
        parse_text = translate("parse_reports")
        if parse_text == "parse_reports":
            parse_text = "Parse Reports"
        self.parse_reports_btn.config(text=parse_text)
        self.run_match_btn.config(text=translate("run_matching"))
        self.export_llm_btn.config(text=translate("export_llm_analysis"))
        # removed: self.analyze_llm_btn.config(text=translate("analyze_with_llm"))

        # Frames / labels
        self.list_container.config(text=translate("requirements_from_standard"))
        self.sub_point_container.config(text=translate("sub_points"))
        self.text_container.config(text=translate("requirement_text_and_matches"))
        reports_label = translate("reports")
        if reports_label == "reports":
            reports_label = "Reports"
        # Update the LabelFrame holding the report list
        try:
            self.report_listbox.master.config(text=reports_label)
        except Exception:
            pass

    def _validate_state_for_operation(self, operation):
        """Validate application state before performing operations."""
        warn = translate("warning") if translate("warning") != "warning" else "Warning"
        if operation == "select_reports" and not self.standard_pdf_path:
            messagebox.showwarning(warn, translate("select_standard_first") if translate("select_standard_first") != "select_standard_first" else "Please select a standard PDF first.")
            return False
        if operation == "parse_reports" and not self.reports:
            messagebox.showwarning(warn, translate("select_reports_first") if translate("select_reports_first") != "select_reports_first" else "Please select reports first.")
            return False
        if operation == "matching" and not any(data['paras'] for data in self.reports.values()):
            messagebox.showwarning(warn, translate("parse_reports_first") if translate("parse_reports_first") != "parse_reports_first" else "Please parse reports first.")
            return False
        return True

    def _update_progress_status(self, message, progress=None):
        """Update status."""
        self.status_label.config(text=message)
        self.update_idletasks()

    def _cleanup_large_data(self):
        """Clean up large data structures to free memory."""
        for data in self.reports.values():
            # If matching was completed, embeddings are no longer needed
            if data.get('matches') and data.get('emb') is not None:
                data['emb'] = None

    # ---------------- UI Construction -----------------
    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Export menu (reused; state updated based on selected report)
        self.export_menu = tk.Menu(self.menu_bar, tearoff=0)
        configure_export_menu(self, self.export_menu)
        # Use translated cascade label
        exp_label = translate("export")
        if exp_label == "export":
            exp_label = "Export"
        self.menu_bar.add_cascade(label=exp_label, menu=self.export_menu)

        # FAQ
        from help_info import show_help, show_about
        self.faq_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.faq_menu.add_command(label=translate("help"), command=lambda: show_help(self))
        self.faq_menu.add_command(label=translate("about"), command=lambda: show_about(self))
        self.menu_bar.add_cascade(label="FAQ", menu=self.faq_menu)

        # Language switch
        self.menu_bar.add_command(label="DE/EN", command=lambda: switch_language_and_update_ui(self))

    def _create_layout(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        self.select_standard_btn = ttk.Button(top_frame, text=translate("select_standard"), command=self._select_standard_file)
        self.select_standard_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.add_reports_btn = ttk.Button(
            top_frame,
            text=translate("select_reports") if translate("select_reports") != "select_reports" else "Select Reports",
            command=self._select_reports,
            state=tk.DISABLED
        )
        self.add_reports_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.parse_reports_btn = ttk.Button(
            top_frame,
            text=translate("parse_reports") if translate("parse_reports") != "parse_reports" else "Parse Reports",
            command=self._parse_reports,
            state=tk.DISABLED
        )
        self.parse_reports_btn.pack(side=tk.LEFT)

        self.run_match_btn = ttk.Button(
            top_frame,
            text=translate("run_matching"),
            command=self._run_all_matching,
            state=tk.DISABLED
        )
        self.run_match_btn.pack(side=tk.LEFT)

        self.export_llm_btn = ttk.Button(
            top_frame,
            text=translate("export_llm_analysis"),
            command=self._export_llm_all_reports,
            state=tk.DISABLED
        )
        self.export_llm_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.status_label = ttk.Label(top_frame, text=translate("initial_status"))
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Second row: Report selection list
        report_frame = ttk.LabelFrame(main_frame, text=translate("reports") if translate("reports") != "reports" else "Reports", padding=5)
        report_frame.pack(fill=tk.X, pady=5)

        self.report_listbox = Listbox(report_frame, height=4)
        self.report_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.report_listbox.bind('<<ListboxSelect>>', self._on_report_select)
        report_scroll = Scrollbar(report_frame, command=self.report_listbox.yview)
        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_listbox.config(yscrollcommand=report_scroll.set)

        # Current report indicator
        self.current_report_label = ttk.Label(main_frame, text="", foreground="#444")
        self.current_report_label.pack(fill=tk.X, pady=(0,4))

        # Bottom panes (reuse single-report structure)
        bottom_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.list_container = ttk.LabelFrame(bottom_frame, text=translate("requirements_from_standard"), padding=5)
        bottom_frame.add(self.list_container, weight=1)
        self.req_scrollbar = Scrollbar(self.list_container)
        self.req_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.req_listbox = Listbox(self.list_container, yscrollcommand=self.req_scrollbar.set)
        self.req_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.req_listbox.bind('<<ListboxSelect>>', self._on_requirement_select)
        self.req_scrollbar.config(command=self.req_listbox.yview)

        self.sub_point_container = ttk.LabelFrame(bottom_frame, text=translate("sub_points"), padding=5)
        bottom_frame.add(self.sub_point_container, weight=2)
        self.sub_point_scrollbar = Scrollbar(self.sub_point_container)
        self.sub_point_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sub_point_listbox = Listbox(self.sub_point_container, yscrollcommand=self.sub_point_scrollbar.set)
        self.sub_point_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sub_point_listbox.bind('<<ListboxSelect>>', self._on_sub_point_select)
        self.sub_point_scrollbar.config(command=self.sub_point_listbox.yview)

        self.text_container = ttk.LabelFrame(bottom_frame, text=translate("requirement_text_and_matches"), padding=5)
        bottom_frame.add(self.text_container, weight=3)
        self.text_display = tk.Text(self.text_container, wrap=tk.WORD, state=tk.DISABLED, font=("Segoe UI", 10))
        self.text_display.pack(fill=tk.BOTH, expand=True)

    # ---------------- Actions -----------------
    def _select_standard_file(self):
        # ...existing code before dialog...
        path = filedialog.askopenfilename(title=translate("select_standard"), filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        # Validate file accessibility
        try:
            if not os.path.exists(path) or not os.access(path, os.R_OK):
                messagebox.showerror(translate("error") if translate("error") != "error" else "Error", "File not accessible.")
                return
        except Exception as e:
            messagebox.showerror(translate("error") if translate("error") != "error" else "Error", f"File validation error: {str(e)}")
            return

        self.standard_pdf_path = path
        self._update_progress_status(translate("extracting_requirements"))
        try:
            self.requirements_data = extract_requirements_from_standard_pdf(path)
            self.detected_standard = detect_standard_from_pdf(path)
            if not self.requirements_data:
                messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                       translate("no_requirements_found") if translate("no_requirements_found") != "no_requirements_found" else "No requirements found in the PDF.")
                return
            # Populate requirements list
            self.req_listbox.delete(0, tk.END)
            for code in self.requirements_data.keys():
                self.req_listbox.insert(tk.END, code)
            # Prepare texts for embedding (sub-points first)
            standard_texts_for_embedding = []
            for req_data in self.requirements_data.values():
                if req_data['sub_points']:
                    standard_texts_for_embedding.extend([sp.strip() for sp in req_data['sub_points']])
                else:
                    standard_texts_for_embedding.append(req_data['full_text'].strip())
            if standard_texts_for_embedding:
                self.standard_emb = self.embedder.encode(standard_texts_for_embedding)
            else:
                messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                       translate("no_text_for_embedding") if translate("no_text_for_embedding") != "no_text_for_embedding" else "No text found for embedding.")
                return
            self.status_label.config(text=f"{len(self.requirements_data)} {translate('reqs_loaded')} {translate('standard_detected', standard=self.detected_standard or 'UNKNOWN')}")
            self.add_reports_btn.config(state=tk.NORMAL)
            self.export_menu.entryconfig(0, state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror(translate("error_processing_standard"), str(e))
            self.status_label.config(text=translate("error_try_again"))
            # Reset state on error
            self.standard_pdf_path = None
            self.requirements_data = {}
            self.standard_emb = None

    def _select_reports(self):
        # Ensure standard chosen (button is disabled before, but double-check)
        if not self._validate_state_for_operation("select_reports"):
            return
        paths = filedialog.askopenfilenames(
            title=translate("select_reports") if translate("select_reports") != "select_reports" else "Select Reports",
            filetypes=[("PDF", "*.pdf")]
        )
        if not paths:
            return
        # Validate all files before adding
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
        new_paths = [p for p in paths if p not in self.reports]
        for p in new_paths:
            self.reports[p] = {'paras': [], 'emb': None, 'matches': None}
            self.report_listbox.insert(tk.END, os.path.basename(p))
        if self.reports and not self.current_report_path:
            self.report_listbox.select_set(0)
            self.current_report_path = list(self.reports.keys())[0]
            # Keep alias in sync for language_manager
            self.report_pdf_path = self.current_report_path
        self.parse_reports_btn.config(state=tk.NORMAL)
        self.run_match_btn.config(state=tk.DISABLED)
        self.status_label.config(text=translate("reports_ready_multi", count=len(self.reports)) if translate("reports_ready_multi", count=0) != "reports_ready_multi" else f"{len(self.reports)} reports selected.")
        self.export_menu.entryconfig(1, state=tk.DISABLED)  # paragraphs export until parsing done

    def _parse_reports(self):
        if not self._validate_state_for_operation("parse_reports"):
            return
        if not self.reports:
            return
        total = len(self.reports)
        parsed_count = 0
        for i, (path, data) in enumerate(self.reports.items(), start=1):
            if data['paras']:
                parsed_count += 1
                continue
            prog_txt = translate('parsing_report', current=i, total=total, name=os.path.basename(path))
            if prog_txt == 'parsing_report':
                prog_txt = f"Parsing report {i}/{total}: {os.path.basename(path)}"
            self._update_progress_status(prog_txt, int((i - 1) / total * 100))
            try:
                data['paras'] = extract_paragraphs_from_pdf(path)
                if data['paras']:
                    data['emb'] = self.embedder.encode(data['paras'])
                    parsed_count += 1
                else:
                    print(f"No paragraphs extracted from {path}")
            except Exception as e:
                print(f"Error parsing {path}: {e}")
                messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                       f"Failed to parse: {os.path.basename(path)}")
        if parsed_count:
            self.status_label.config(text=translate('reports_parsed_status', count=parsed_count) if translate('reports_parsed_status', count=0) != 'reports_parsed_status' else f'{parsed_count} reports parsed.')
            self.parse_reports_btn.config(state=tk.NORMAL)
            self.run_match_btn.config(state=tk.NORMAL)
            self.export_menu.entryconfig(1, state=tk.NORMAL)  # paragraphs export
        else:
            self.status_label.config(text=translate('no_paras_to_export'))
            messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                   translate('no_paras_to_export'))

    def _run_all_matching(self):
        if not self._validate_state_for_operation("matching"):
            return
        if self.standard_emb is None:
            messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                   translate("standard_embeddings_not_ready") if translate("standard_embeddings_not_ready") != "standard_embeddings_not_ready" else "Standard embeddings not ready.")
            return
        self._update_progress_status(translate("performing_matching"))
        # Prepare standard texts in the same order as embedding
        standard_texts = []
        for req in self.requirements_data.values():
            if req['sub_points']:
                standard_texts.extend([sp.strip() for sp in req['sub_points']])
            else:
                standard_texts.append(req['full_text'].strip())
        total_reports = sum(1 for d in self.reports.values() if d['paras'])
        if total_reports == 0:
            messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                   translate("no_parsed_reports") if translate("no_parsed_reports") != "no_parsed_reports" else "No parsed reports available for matching.")
            return
        processed = 0
        for path, data in self.reports.items():
            if not data['paras'] or data['emb'] is None:
                continue
            processed += 1
            base_status = translate('processing_report', current=processed, total=total_reports, name=os.path.basename(path))
            if base_status == 'processing_report':
                base_status = f"Processing report {processed}/{total_reports}: {os.path.basename(path)}"
            self._update_progress_status(base_status, int(processed / total_reports * 100))
            try:
                all_matches = match_requirements_to_report(self.standard_emb, data['emb'])
                text_matches = {text: all_matches[idx] for idx, text in enumerate(standard_texts) if idx < len(all_matches)}
                data['matches'] = text_matches
                # Free memory after matching
                data['emb'] = None
            except Exception as e:
                print(f"Error matching {path}: {e}")
                messagebox.showwarning(translate("warning") if translate("warning") != "warning" else "Warning",
                                       f"Matching failed for: {os.path.basename(path)}")
        if self.current_report_path and self.reports[self.current_report_path].get('matches'):
            self._project_current_report(self.current_report_path)
        self.status_label.config(text=translate("matching_completed_label"))
        self.export_menu.entryconfig(2, state=tk.NORMAL)  # matches export
        self.export_llm_btn.config(state=tk.NORMAL)
        # removed: self.analyze_llm_btn.config(state=tk.NORMAL)
        self.export_menu.entryconfig(1, state=tk.NORMAL)
        done_msg = translate("matching_completed") if translate("matching_completed") != 'matching_completed' else 'Matching completed.'
        messagebox.showinfo(translate("completed"), done_msg)

    # ---------------- Selection Handlers -----------------
    def _on_report_select(self, event):
        if not self.report_listbox.curselection():
            return
        idx = self.report_listbox.curselection()[0]
        path = list(self.reports.keys())[idx]
        self.current_report_path = path
        self._project_current_report(path)
        # Refresh requirement display (if one selected) to reflect new matches
        if self.current_req_code:
            if self.sub_point_listbox.curselection():
                sp_idx = self.sub_point_listbox.curselection()[0]
                sp_text = self.sub_point_listbox.get(sp_idx).strip()
                handle_requirement_selection(self, None, sub_point_text=sp_text)
            else:
                handle_requirement_selection(self, None)
        # If no matches yet for this report, show hint in text area
        if not self.matches and self.current_req_code:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.insert(tk.END, "\n(No matches for this report yet. Run matching after parsing.)")
            self.text_display.config(state=tk.DISABLED)

    def _on_requirement_select(self, event):
        if not self.req_listbox.curselection():
            return
        sel_index = self.req_listbox.curselection()[0]
        code = self.req_listbox.get(sel_index)
        self.current_req_code = code
        self.sub_point_listbox.delete(0, tk.END)
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.config(state=tk.DISABLED)
        # removed: self.analyze_llm_btn.config(state=tk.DISABLED)
        if code in self.requirements_data:
            req_data = self.requirements_data[code]
            if req_data['sub_points']:
                for sp in req_data['sub_points']:
                    self.sub_point_listbox.insert(tk.END, sp)
            handle_requirement_selection(self, event)

    def _on_sub_point_select(self, event):
        if not self.current_req_code or not self.sub_point_listbox.curselection():
            return
        sp_index = self.sub_point_listbox.curselection()[0]
        sp_text = self.sub_point_listbox.get(sp_index)
        handle_requirement_selection(self, event, sub_point_text=sp_text.strip())

    # ---------------- LLM Analysis -----------------
    # removed: def _run_llm_analysis_current(self): ...

    def _export_llm_all_reports(self):
        # Export only for currently projected report (consistent with single-report exporter)
        if not self.current_report_path:
            messagebox.showwarning(translate("no_data"), translate("no_paras_to_export"))
            return
        try:
            from exporter import export_llm_analysis as export_llm_analysis_func
            export_llm_analysis_func(self)
        except Exception as e:
            messagebox.showerror(translate("error") if translate("error") != "error" else "Error",
                                 f"Export failed: {str(e)}")

    def destroy(self):
        """Clean up resources before closing."""
        try:
            self._cleanup_large_data()
        except Exception:
            pass
        super().destroy()

    # Project current report state into single-report compatible fields
    def _project_current_report(self, report_path):
        data = self.reports.get(report_path)
        if not data:
            return
        self.report_paras = data.get('paras', [])
        self.matches = data.get('matches')
        # Keep alias in sync for language_manager
        self.report_pdf_path = report_path
        # Update current report label
        base = os.path.basename(report_path)
        para_info = f"{len(self.report_paras)} paras" if self.report_paras else "no paragraphs"
        match_info = f"{len(self.matches)} texts matched" if self.matches else "no matches yet"
        self.current_report_label.config(text=f"Active report: {base}  |  {para_info}  |  {match_info}")
        # removed: toggle analyze_llm_btn state


if __name__ == '__main__':
    app = MultiReportApp()
    app.mainloop()