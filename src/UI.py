"""
This script provides a graphical user interface (GUI) for analyzing the compliance of sustainability reports
with established standards. It allows users to extract requirements from a standard PDF, parse paragraphs
from a report PDF, and match the requirements to the report content using semantic similarity.

Key Features:
- Extracts requirements from a standard PDF and displays them in a list.
- Parses paragraphs from a report PDF and prepares them for analysis.
- Matches requirements to report paragraphs using Sentence-BERT embeddings and cosine similarity.
- Exports extracted requirements, report paragraphs, and matching results in CSV, Excel, or PDF formats.
- Supports multilingual functionality (English and German) with a language toggle.

Usage:
- Run the script to launch the GUI.
- Use the interface to select a standard PDF and a report PDF.
- Perform matching and view results, including similarity scores and matched paragraphs.
- Export the results for further analysis or reporting.
"""

import tkinter as tk
from tkinter import ttk, Listbox, Scrollbar, messagebox, Text
import os
import warnings

# --- Core functionality imports ---
from embedder import SBERTEmbedder  # Create embeddings using Sentence-BERT
from matcher import match_requirements_to_report  # Match requirements to report paragraphs
from translations import translate, switch_language  # Import the translation functions
from analyze import run_llm_analysis  # Analyze matching results with a local LLM

# --- File and Export functionality imports ---
from file_handler import select_standard_file, select_report_file
from exporter import (
    is_export_available,
    export_requirements,
    export_report_paras,
    export_matches,
    export_llm_analysis as export_llm_analysis_func
)


class ComplianceApp(tk.Tk):
    """
    A GUI application for analyzing the compliance of sustainability reports with established standards.
    This application allows users to:
    - Select a standard PDF and extract requirements.
    - Select a report PDF and extract paragraphs.
    - Match the extracted requirements to the report paragraphs using semantic similarity.
    - Export the results in various formats (CSV, Excel, PDF).
    """

    def __init__(self):
        """
        Initializes the ComplianceApp GUI, sets up the main layout, and initializes state variables.
        """
        super().__init__()

        # Suppress specific warnings to keep the console output clean
        warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*Torch was not compiled with flash attention.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*Series.__getitem__ treating keys as positions is deprecated.*", category=FutureWarning)

        self.title(translate("app_title"))
        self.geometry("1200x800")

        # --- Initialize state variables ---
        self.standard_pdf_path = None  # Path to the selected standard PDF
        self.report_pdf_path = None  # Path to the selected report PDF
        self.requirements_data = {}  # Dictionary to store extracted requirements {code: text}
        self.report_paras = []  # List to store extracted paragraphs from the report
        self.standard_emb = None  # Embeddings for the requirements
        self.report_emb = None  # Embeddings for the report paragraphs
        self.matches = None  # Matching results between requirements and report paragraphs
        self.embedder = SBERTEmbedder()  # Initialize the Sentence-BERT embedder

        # --- Create the GUI layout ---
        self._create_menu()  # Create the menu bar
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top frame for file selection and processing ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        self.select_standard_btn = ttk.Button(top_frame, text=translate("select_standard"), command=lambda: select_standard_file(self))
        self.select_standard_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.select_report_btn = ttk.Button(top_frame, text=translate("select_report"), command=lambda: select_report_file(self), state=tk.DISABLED)
        self.select_report_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.run_match_btn = ttk.Button(top_frame, text=translate("run_matching"), command=self.run_matching, state=tk.DISABLED)
        self.run_match_btn.pack(side=tk.LEFT)

        self.export_llm_btn = ttk.Button(top_frame, text=translate("export_llm_analysis"), command=lambda: export_llm_analysis_func(self), state=tk.DISABLED)
        self.export_llm_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.status_label = ttk.Label(top_frame, text=translate("initial_status"))
        self.status_label.pack(side=tk.LEFT, padx=20)

        # --- Bottom frame for displaying results ---
        bottom_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # --- Left pane: List of requirements ---
        self.list_container = ttk.LabelFrame(bottom_frame, text=translate("requirements_from_standard"), padding="5")
        bottom_frame.add(self.list_container, weight=1)

        self.req_scrollbar = Scrollbar(self.list_container)
        self.req_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.req_listbox = Listbox(self.list_container, yscrollcommand=self.req_scrollbar.set)
        self.req_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.req_listbox.bind('<<ListboxSelect>>', self.on_requirement_select)
        self.req_scrollbar.config(command=self.req_listbox.yview)

        # --- Right pane: Requirement text and matches ---
        self.text_container = ttk.LabelFrame(bottom_frame, text=translate("requirement_text_and_matches"), padding="5")
        bottom_frame.add(self.text_container, weight=3)

        # Frame for buttons above the text display
        action_frame = ttk.Frame(self.text_container)
        action_frame.pack(fill=tk.X, pady=(0, 5))

        self.analyze_llm_btn = ttk.Button(action_frame, text="Analyze with LLM", command=lambda: run_llm_analysis(self, self.req_listbox, self.requirements_data, self.matches, self.report_paras, self.status_label, self.update_idletasks, translate), state=tk.DISABLED)
        self.analyze_llm_btn.pack(side=tk.RIGHT)

        self.text_display = Text(self.text_container, wrap=tk.WORD, state=tk.DISABLED, font=("Segoe UI", 10))
        self.text_display.pack(fill=tk.BOTH, expand=True)

    def _create_menu(self):
        """
        Creates the menu bar for the application, including options for exporting data and switching language.
        """
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # --- Export menu ---
        self.export_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Export", menu=self.export_menu)

        # Submenu for exporting requirements
        self.req_export_menu = tk.Menu(self.export_menu, tearoff=0)
        self.req_export_menu.add_command(label="as CSV...", command=lambda: export_requirements(self.requirements_data, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
        self.req_export_menu.add_command(label="as Excel...", command=lambda: export_requirements(self.requirements_data, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
        self.req_export_menu.add_command(label="as PDF...", command=lambda: export_requirements(self.requirements_data, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
        self.export_menu.add_cascade(label=translate("export_reqs"), menu=self.req_export_menu, state=tk.DISABLED)

        # Submenu for exporting report paragraphs
        self.paras_export_menu = tk.Menu(self.export_menu, tearoff=0)
        self.paras_export_menu.add_command(label="as CSV...", command=lambda: export_report_paras(self.report_paras, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
        self.paras_export_menu.add_command(label="as Excel...", command=lambda: export_report_paras(self.report_paras, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
        self.paras_export_menu.add_command(label="as PDF...", command=lambda: export_report_paras(self.report_paras, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
        self.export_menu.add_cascade(label=translate("export_paras"), menu=self.paras_export_menu, state=tk.DISABLED)

        # Submenu for exporting matching results
        self.matches_export_menu = tk.Menu(self.export_menu, tearoff=0)
        self.matches_export_menu.add_command(label="as CSV...", command=lambda: export_matches(self.matches, self.requirements_data, self.report_paras, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
        self.matches_export_menu.add_command(label="as Excel...", command=lambda: export_matches(self.matches, self.requirements_data, self.report_paras, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
        self.matches_export_menu.add_command(label="as PDF...", command=lambda: export_matches(self.matches, self.requirements_data, self.report_paras, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
        self.export_menu.add_cascade(label=translate("export_matches"), menu=self.matches_export_menu, state=tk.DISABLED)

        # --- FAQ Menu ---
        self.faq_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="FAQ", menu=self.faq_menu)
        self.faq_menu.add_command(label=translate("help"), command=self._show_help)
        self.faq_menu.add_command(label=translate("about"), command=self._show_about)

        # --- Language switch menu ---
        self.menu_bar.add_command(label="DE/EN", command=self._switch_language)

        # Show warning only if no export formats are available at all
        if not is_export_available('csv') and not is_export_available('excel') and not is_export_available('pdf'):
            messagebox.showwarning(translate("missing_libs"), 
                                   translate("missing_libs_text"))

    def run_matching(self):
        """
        Performs the matching between the requirements and the report paragraphs.
        """
        self.status_label.config(text=translate("performing_matching"))
        self.update_idletasks()
        
        self.matches = match_requirements_to_report(self.standard_emb, self.report_emb, top_k=5)
        
        self.status_label.config(text=translate("matching_completed_label"))
        self.export_menu.entryconfig(2, state=tk.NORMAL)  # Use index 2 for "Export Matching Results"
        self.export_llm_btn.config(state=tk.NORMAL)
        messagebox.showinfo(translate("completed"), translate("matching_completed"))

    def on_requirement_select(self, event):
        """
        Handles the selection of a requirement from the listbox and displays its matches.
        """
        selected_indices = self.req_listbox.curselection()
        if not selected_indices: return
        
        index = selected_indices[0]
        selected_code = self.req_listbox.get(index)
        req_text = self.requirements_data.get(selected_code, "Text not found.")
        
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete('1.0', tk.END)
        
        self.text_display.insert(tk.END, translate("req_text_label") + "\n", "h1")
        self.text_display.insert(tk.END, f"{req_text}\n\n")
        
        if self.matches and index < len(self.matches):
            self.text_display.insert(tk.END, translate("matches_found_label") + "\n", "h1")
            match_list = self.matches[index]
            if not match_list:
                self.text_display.insert(tk.END, translate("no_matches_found"))
                self.analyze_llm_btn.config(state=tk.DISABLED)
            else:
                for report_idx, score in match_list:
                    self.text_display.insert(tk.END, f"(Score: {score:.2f})\n", "score")
                    self.text_display.insert(tk.END, f"{self.report_paras[report_idx]}\n\n")
                self.analyze_llm_btn.config(state=tk.NORMAL)
        else:
            self.analyze_llm_btn.config(state=tk.DISABLED)

        self.text_display.config(state=tk.DISABLED)
        self.text_display.tag_config("h1", font=("Segoe UI", 12, "bold"), spacing1=5, spacing3=5)
        self.text_display.tag_config("score", font=("Segoe UI", 10, "italic"), foreground="blue")

    def _show_help(self):
        """
        Displays a help/FAQ window with instructions on how to use the application.
        """
        help_win = tk.Toplevel(self)
        help_win.title(translate("help"))
        help_win.geometry("600x500")
        help_win.transient(self)  # Keep window on top

        text_area = Text(help_win, wrap=tk.WORD, font=("Segoe UI", 10), padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)

        # --- Help Content ---
        text_area.insert(tk.END, translate("help_title") + "\n\n", "h1")
        text_area.insert(tk.END, translate("help_step1_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step1_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step2_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step2_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step3_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step3_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step4_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step4_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step5_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step5_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step6_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step6_text") + "\n\n")
        text_area.insert(tk.END, translate("help_step7_title") + "\n", "h2")
        text_area.insert(tk.END, translate("help_step7_text") + "\n\n")

        # --- Tag Configuration ---
        text_area.tag_config("h1", font=("Segoe UI", 16, "bold"), spacing3=10)
        text_area.tag_config("h2", font=("Segoe UI", 12, "bold"), spacing3=5)
        text_area.config(state=tk.DISABLED)  # Make read-only

    def _show_about(self):
        """
        Displays an 'About' window with information about the application.
        """
        about_win = tk.Toplevel(self)
        about_win.title(translate("about"))
        about_win.geometry("500x350")
        about_win.transient(self)

        text_area = Text(about_win, wrap=tk.WORD, font=("Segoe UI", 10), padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)

        # --- About Content ---
        text_area.insert(tk.END, translate("about_title") + "\n\n", "h1")
        text_area.insert(tk.END, translate("about_text") + "\n\n")
        text_area.insert(tk.END, translate("about_version") + "\n", "bold")
        text_area.insert(tk.END, translate("about_author") + "\n", "bold")

        # --- Tag Configuration ---
        text_area.tag_config("h1", font=("Segoe UI", 16, "bold"), spacing3=10)
        text_area.tag_config("bold", font=("Segoe UI", 10, "bold"))
        text_area.config(state=tk.DISABLED)

    def _switch_language(self):
        """
        Switches the application language and updates all UI elements.
        """
        switch_language()
        self._update_ui_texts()

    def _update_ui_texts(self):
        """
        Updates all UI elements with the current language.
        """
        self.title(translate("app_title"))
        self.select_standard_btn.config(text=translate("select_standard"))
        self.select_report_btn.config(text=translate("select_report"))
        self.run_match_btn.config(text=translate("run_matching"))
        self.export_llm_btn.config(text=translate("export_llm_analysis"))
        self.analyze_llm_btn.config(text=translate("analyze_with_llm"))
        
        # Update status label based on current state
        if not self.standard_pdf_path:
            self.status_label.config(text=translate("initial_status"))
        elif not self.report_pdf_path:
            self.status_label.config(text=translate("standard_ready"))
        elif not self.matches:
            self.status_label.config(text=translate("report_ready"))
        else:
            self.status_label.config(text=translate("matching_completed_label"))

        # Update labels of the sub-menus inside the "Export" menu
        self.export_menu.entryconfig(0, label=translate("export_reqs"))
        self.export_menu.entryconfig(1, label=translate("export_paras"))
        self.export_menu.entryconfig(2, label=translate("export_matches"))
        
        # Update FAQ menu's sub-items
        self.faq_menu.entryconfig(0, label=translate("help"))
        self.faq_menu.entryconfig(1, label=translate("about"))

        self.list_container.config(text=translate("requirements_from_standard"))
        self.text_container.config(text=translate("requirement_text_and_matches"))

if __name__ == '__main__':
    if not os.path.exists('data'):
        os.makedirs('data')
        
    app = ComplianceApp()
    app.mainloop()