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
from tkinter import filedialog, ttk, Listbox, Scrollbar, messagebox, Text
import os
import warnings

# --- Core functionality imports ---
from extractor import extract_requirements_from_standard_pdf  # Extract requirements from a standard PDF
from parser import extract_paragraphs_from_pdf  # Extract paragraphs from a report PDF
from embedder import SBERTEmbedder  # Create embeddings using Sentence-BERT
from matcher import match_requirements_to_report  # Match requirements to report paragraphs
from translations import translate, switch_language  # Import the translation functions

# --- Export functionality imports ---
try:
    import pandas as pd
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    EXPORT_LIBS_AVAILABLE = True
except ImportError:
    EXPORT_LIBS_AVAILABLE = False


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

        self.select_standard_btn = ttk.Button(top_frame, text=translate("select_standard"), command=self.select_standard_file)
        self.select_standard_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.select_report_btn = ttk.Button(top_frame, text=translate("select_report"), command=self.select_report_file, state=tk.DISABLED)
        self.select_report_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.run_match_btn = ttk.Button(top_frame, text=translate("run_matching"), command=self.run_matching, state=tk.DISABLED)
        self.run_match_btn.pack(side=tk.LEFT)

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
        self.req_export_menu.add_command(label="as CSV...", command=lambda: self.export_requirements('csv'))
        self.req_export_menu.add_command(label="as Excel...", command=lambda: self.export_requirements('excel'))
        self.req_export_menu.add_command(label="as PDF...", command=lambda: self.export_requirements('pdf'))
        self.export_menu.add_cascade(label=translate("export_reqs"), menu=self.req_export_menu, state=tk.DISABLED)

        # Submenu for exporting report paragraphs
        self.paras_export_menu = tk.Menu(self.export_menu, tearoff=0)
        self.paras_export_menu.add_command(label="as CSV...", command=lambda: self.export_report_paras('csv'))
        self.paras_export_menu.add_command(label="as Excel...", command=lambda: self.export_report_paras('excel'))
        self.paras_export_menu.add_command(label="as PDF...", command=lambda: self.export_report_paras('pdf'))
        self.export_menu.add_cascade(label=translate("export_paras"), menu=self.paras_export_menu, state=tk.DISABLED)

        # Submenu for exporting matching results
        self.matches_export_menu = tk.Menu(self.export_menu, tearoff=0)
        self.matches_export_menu.add_command(label="as CSV...", command=lambda: self.export_matches('csv'))
        self.matches_export_menu.add_command(label="as Excel...", command=lambda: self.export_matches('excel'))
        self.matches_export_menu.add_command(label="as PDF...", command=lambda: self.export_matches('pdf'))
        self.export_menu.add_cascade(label=translate("export_matches"), menu=self.matches_export_menu, state=tk.DISABLED)

        # --- FAQ Menu ---
        self.faq_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="FAQ", menu=self.faq_menu)
        self.faq_menu.add_command(label=translate("help"), command=self._show_help)
        self.faq_menu.add_command(label=translate("about"), command=self._show_about)

        # --- Language switch menu ---
        self.menu_bar.add_command(label="DE/EN", command=self._switch_language)

        # Disable export options if required libraries are not available
        if not EXPORT_LIBS_AVAILABLE:
            self.export_menu.entryconfig(0, state=tk.DISABLED)
            self.export_menu.entryconfig(1, state=tk.DISABLED)
            self.export_menu.entryconfig(2, state=tk.DISABLED)
            messagebox.showwarning(translate("missing_libs"), 
                                   translate("missing_libs_text"))

    def select_standard_file(self):
        """
        Handles the selection of the standard PDF file, extracts requirements, and updates the UI.
        """
        path = filedialog.askopenfilename(title=translate("select_standard"), filetypes=[("PDF Files", "*.pdf")])
        if not path: return

        self.standard_pdf_path = path
        self.status_label.config(text=f"Standard: {os.path.basename(path)}. {translate('extracting_requirements')}")
        self.update_idletasks()

        try:
            # Extract requirements directly from the selected standard PDF
            self.requirements_data = extract_requirements_from_standard_pdf(self.standard_pdf_path)
            
            # Populate the listbox with the extracted requirements
            self.req_listbox.delete(0, tk.END)
            for code in self.requirements_data.keys():
                self.req_listbox.insert(tk.END, code)
            if not self.requirements_data:
                self.req_listbox.insert(tk.END, translate("no_reqs_found"))

            self.status_label.config(text=f"{len(self.requirements_data)} {translate('reqs_loaded')}")
            self.update_idletasks()
            
            standard_paras = list(self.requirements_data.values())
            self.standard_emb = self.embedder.encode(standard_paras)
            
            self.status_label.config(text=translate("standard_ready"))
            self.select_report_btn.config(state=tk.NORMAL)
            self.export_menu.entryconfig(0, state=tk.NORMAL)  # Use index 0 for "Export Requirements"
        except Exception as e:
            messagebox.showerror(translate("error_processing_standard"), f"An error occurred:\n{e}")
            self.status_label.config(text=translate("error_try_again"))

    def select_report_file(self):
        """
        Handles the selection of the report PDF file, extracts paragraphs, and updates the UI.
        """
        path = filedialog.askopenfilename(title=translate("select_report"), filetypes=[("PDF Files", "*.pdf")])
        if not path: return

        self.report_pdf_path = path
        self.status_label.config(text=f"Report: {os.path.basename(path)}. Parsing paragraphs...")
        self.update_idletasks()

        try:
            self.report_paras = extract_paragraphs_from_pdf(self.report_pdf_path)

            self.status_label.config(text=f"{len(self.report_paras)} {translate('paras_found')}")
            self.update_idletasks()

            self.report_emb = self.embedder.encode(self.report_paras)
            
            self.status_label.config(text=translate("report_ready"))
            self.run_match_btn.config(state=tk.NORMAL)
            self.export_menu.entryconfig(1, state=tk.NORMAL)  # Use index 1 for "Export Report Paragraphs"
        except Exception as e:
            messagebox.showerror(translate("error_processing_report"), f"An error occurred:\n{e}")
            self.status_label.config(text=translate("error_try_again"))

    def run_matching(self):
        """
        Performs the matching between the requirements and the report paragraphs.
        """
        self.status_label.config(text=translate("performing_matching"))
        self.update_idletasks()
        
        self.matches = match_requirements_to_report(self.standard_emb, self.report_emb, top_k=5)
        
        self.status_label.config(text=translate("matching_completed_label"))
        self.export_menu.entryconfig(2, state=tk.NORMAL)  # Use index 2 for "Export Matching Results"
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
            else:
                for report_idx, score in match_list:
                    self.text_display.insert(tk.END, f"(Score: {score:.2f})\n", "score")
                    self.text_display.insert(tk.END, f"{self.report_paras[report_idx]}\n\n")

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
        help_win.transient(self) # Keep window on top

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

        # --- Tag Configuration ---
        text_area.tag_config("h1", font=("Segoe UI", 16, "bold"), spacing3=10)
        text_area.tag_config("h2", font=("Segoe UI", 12, "bold"), spacing3=5)
        text_area.config(state=tk.DISABLED) # Make read-only

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

    def _get_save_path(self, file_type, default_name):
        """
        Opens a save dialog and returns the selected file path.

        Args:
            file_type (str): The type of file to save (e.g., 'csv', 'excel', 'pdf').
            default_name (str): The default name for the file.

        Returns:
            str: The selected file path.
        """
        file_types = {
            'csv': [("CSV File", "*.csv")],
            'excel': [("Excel File", "*.xlsx")],
            'pdf': [("PDF File", "*.pdf")]
        }
        return filedialog.asksaveasfilename(
            defaultextension=f".{file_type}",
            filetypes=file_types[file_type],
            initialfile=default_name,
            title=f"{translate('export_as')} {file_type.upper()}"
        )

    def export_requirements(self, file_type):
        """
        Exports the extracted requirements to a file in the specified format (CSV, Excel, PDF).

        Args:
            file_type (str): The format to export the requirements (e.g., 'csv', 'excel', 'pdf').
        """
        if not self.requirements_data:
            messagebox.showwarning(translate("no_data"), translate("no_reqs_to_export"))
            return
        
        path = self._get_save_path(file_type, "requirements")
        if not path: return

        df = pd.DataFrame(list(self.requirements_data.items()), columns=['Code', 'Requirement Text'])
        self._export_dataframe(df, path, file_type, "Requirements List")

    def export_report_paras(self, file_type):
        """
        Exports the extracted report paragraphs to a file in the specified format (CSV, Excel, PDF).

        Args:
            file_type (str): The format to export the report paragraphs (e.g., 'csv', 'excel', 'pdf').
        """
        if not self.report_paras:
            messagebox.showwarning(translate("no_data"), translate("no_paras_to_export"))
            return

        path = self._get_save_path(file_type, "report_paragraphs")
        if not path: return

        df = pd.DataFrame(self.report_paras, columns=['Parsed Report Paragraphs'])
        self._export_dataframe(df, path, file_type, "Report Paragraphs")

    def export_matches(self, file_type):
        """
        Exports the matching results between requirements and report paragraphs to a file in the specified format (CSV, Excel, PDF).

        Args:
            file_type (str): The format to export the matching results (e.g., 'csv', 'excel', 'pdf').
        """
        if not self.matches:
            messagebox.showwarning(translate("no_data"), translate("no_matches_to_export"))
            return
        
        path = self._get_save_path(file_type, "matching_results")
        if not path: return

        # Prepare data for export
        export_data = []
        req_codes = list(self.requirements_data.keys())
        req_texts = list(self.requirements_data.values())

        for i, match_list in enumerate(self.matches):
            for report_idx, score in match_list:
                export_data.append({
                    'Requirement Code': req_codes[i],
                    'Requirement Text': req_texts[i],
                    'Matched Report Paragraph': self.report_paras[report_idx],
                    'Score': f"{score:.4f}"
                })
        
        df = pd.DataFrame(export_data)
        self._export_dataframe(df, path, file_type, "Matching Results")

    def _export_dataframe(self, df, path, file_type, title):
        """Helper function to export a Pandas DataFrame to the specified file type."""
        try:
            if file_type == 'csv':
                df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
            elif file_type == 'excel':
                df.to_excel(path, index=False)
            elif file_type == 'pdf':
                self._export_df_to_pdf(df, path, title)
            
            messagebox.showinfo(translate("export_successful"), translate("export_successful_text", path=path))
        except Exception as e:
            messagebox.showerror(translate("export_error"), translate("export_error_text", e=e))

    def _export_df_to_pdf(self, df, path, title):
        """Creates a PDF from a DataFrame, formatting the data as a flowing list."""
        doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        # Custom styles for a clean outline
        styles.add(ParagraphStyle(name='ReqCode', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6))
        styles.add(ParagraphStyle(name='MatchScore', fontName='Helvetica-Oblique', fontSize=10, spaceAfter=4, textColor=colors.darkblue))
        styles.add(ParagraphStyle(name='SubHeading', fontName='Helvetica-Bold', fontSize=10, spaceBefore=8, spaceAfter=4, textColor=colors.darkslategray))
        
        elements = []
        elements.append(Paragraph(title, styles['h1']))
        elements.append(Spacer(1, 24))

        # Depending on the DataFrame content, a different list formatting is used.
        # Case 1: Export of matching results (grouped)
        if 'Requirement Code' in df.columns:
            # Group results by requirement, so each is listed only once.
            grouped = df.groupby(['Requirement Code', 'Requirement Text'])
            
            for (code, text), group in grouped:
                # Output requirement title and text once
                elements.append(Paragraph(f"Requirement: {code}", styles['ReqCode']))
                elements.append(Paragraph(text, styles['Normal']))
                elements.append(Spacer(1, 12))
                
                elements.append(Paragraph("Matched Report Paragraphs:", styles['SubHeading']))
                
                # List all matches for this requirement
                for index, row in group.iterrows():
                    elements.append(Paragraph(f"Score: {row['Score']}", styles['MatchScore']))
                    elements.append(Paragraph(row['Matched Report Paragraph'], styles['Normal']))
                    elements.append(Spacer(1, 12)) # Space between individual matches
                
                # Separator line for better readability between requirement groups
                elements.append(Spacer(1, 24))

        # Case 2: Export of requirements
        elif 'Code' in df.columns:
            for index, row in df.iterrows():
                elements.append(Paragraph(row['Code'], styles['ReqCode']))
                elements.append(Paragraph(row['Requirement Text'], styles['Normal']))
                elements.append(Spacer(1, 12))

        # Case 3: Simple export (e.g., just report paragraphs)
        else:
            for index, row in df.iterrows():
                # Takes the content of the first column
                elements.append(Paragraph(str(row[0]), styles['Normal']))
                elements.append(Spacer(1, 12))

        doc.build(elements)

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