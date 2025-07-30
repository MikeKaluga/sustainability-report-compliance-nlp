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
from translations import translate  # Import the translation functions
from analyze import run_llm_analysis  # Analyze matching results with a local LLM
from help_info import show_help, show_about  # Import the help and about functions
from language_manager import switch_language_and_update_ui  # Import the new function
from menu_manager import configure_export_menu  # Import the new function

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
        configure_export_menu(self, self.export_menu)  # Delegate export menu configuration
        self.menu_bar.add_cascade(label="Export", menu=self.export_menu)

        # --- FAQ Menu ---
        self.faq_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="FAQ", menu=self.faq_menu)
        self.faq_menu.add_command(label=translate("help"), command=lambda: show_help(self))
        self.faq_menu.add_command(label=translate("about"), command=lambda: show_about(self))

        # --- Language switch menu ---
        self.menu_bar.add_command(label="DE/EN", command=lambda: switch_language_and_update_ui(self))

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

if __name__ == '__main__':
    if not os.path.exists('data'):
        os.makedirs('data')
        
    app = ComplianceApp()
    app.mainloop()