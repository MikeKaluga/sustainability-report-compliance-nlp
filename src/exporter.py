"""
This module handles all data exporting functionalities for the compliance analysis application.
It supports exporting data to CSV, Excel, and PDF formats.
"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from translations import translate
from analyze import get_llm_analysis

def is_export_available(file_type=None):
    """Checks if all required export libraries for a specific file type are installed."""
    if file_type is None:
        # Check if any export format is available
        return PANDAS_AVAILABLE or REPORTLAB_AVAILABLE
    
    if file_type in ['csv']:
        return PANDAS_AVAILABLE
    elif file_type == 'excel':
        return PANDAS_AVAILABLE and OPENPYXL_AVAILABLE
    elif file_type == 'pdf':
        return REPORTLAB_AVAILABLE
    return False

def _get_save_path(file_type, default_name):
    """Opens a save dialog and returns the selected file path."""
    file_types = {
        'csv': [("CSV File", "*.csv")],
        'excel': [("Excel File", "*.xlsx")],
        'pdf': [("PDF File", "*.pdf")]
    }
    return filedialog.asksaveasfilename(
        defaultextension=f".{file_type}",
        filetypes=file_types.get(file_type, []),
        initialfile=default_name,
        title=f"{translate('export_as')} {file_type.upper()}"
    )

def _export_df_to_pdf(df, path, title):
    """Creates a PDF from a DataFrame."""
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReqCode', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='MatchScore', fontName='Helvetica-Oblique', fontSize=10, spaceAfter=4, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='SubHeading', fontName='Helvetica-Bold', fontSize=10, spaceBefore=8, spaceAfter=4, textColor=colors.darkslategray))
    
    elements = [Paragraph(title, styles['h1']), Spacer(1, 24)]

    if 'Requirement Code' in df.columns and 'LLM Analysis' not in df.columns:
        grouped = df.groupby(['Requirement Code', 'Requirement Text'])
        for (code, text), group in grouped:
            elements.extend([
                Paragraph(f"Requirement: {code}", styles['ReqCode']),
                Paragraph(text, styles['Normal']),
                Spacer(1, 12),
                Paragraph("Matched Report Paragraphs:", styles['SubHeading'])
            ])
            for _, row in group.iterrows():
                elements.extend([
                    Paragraph(f"Score: {row['Score']}", styles['MatchScore']),
                    Paragraph(row['Matched Report Paragraph'], styles['Normal']),
                    Spacer(1, 12)
                ])
            elements.append(Spacer(1, 24))
    elif 'Code' in df.columns:
        for _, row in df.iterrows():
            elements.extend([
                Paragraph(row['Code'], styles['ReqCode']),
                Paragraph(row['Requirement Text'], styles['Normal']),
                Spacer(1, 12)
            ])
    else:
        for _, row in df.iterrows():
            elements.extend([Paragraph(str(row[0]), styles['Normal']), Spacer(1, 12)])

    doc.build(elements)

def _export_dataframe(df, path, file_type, title):
    """Helper to export a DataFrame to the specified format."""
    try:
        if file_type == 'csv':
            df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
        elif file_type == 'excel':
            df.to_excel(path, index=False)
        elif file_type == 'pdf':
            _export_df_to_pdf(df, path, title)
        messagebox.showinfo(translate("export_successful"), translate("export_successful_text", path=path))
    except Exception as e:
        messagebox.showerror(translate("export_error"), translate("export_error_text", e=e))

def export_requirements(requirements_data, file_type):
    """Exports extracted requirements."""
    if not is_export_available(file_type):
        if file_type == 'excel':
            messagebox.showerror("Missing Library", "Excel export requires the 'openpyxl' library. Please install it with: pip install openpyxl")
        else:
            messagebox.showerror(translate("missing_libs"), translate("missing_libs_text"))
        return
    if not requirements_data:
        messagebox.showwarning(translate("no_data"), translate("no_reqs_to_export"))
        return
    path = _get_save_path(file_type, "requirements")
    if not path: return
    df = pd.DataFrame(list(requirements_data.items()), columns=['Code', 'Requirement Text'])
    _export_dataframe(df, path, file_type, "Requirements List")

def export_report_paras(report_paras, file_type):
    """Exports parsed report paragraphs."""
    if not is_export_available(file_type):
        if file_type == 'excel':
            messagebox.showerror("Missing Library", "Excel export requires the 'openpyxl' library. Please install it with: pip install openpyxl")
        else:
            messagebox.showerror(translate("missing_libs"), translate("missing_libs_text"))
        return
    if not report_paras:
        messagebox.showwarning(translate("no_data"), translate("no_paras_to_export"))
        return
    path = _get_save_path(file_type, "report_paragraphs")
    if not path: return
    df = pd.DataFrame(report_paras, columns=['Parsed Report Paragraphs'])
    _export_dataframe(df, path, file_type, "Report Paragraphs")

def export_matches(matches, requirements_data, report_paras, file_type):
    """Exports matching results."""
    if not is_export_available(file_type):
        if file_type == 'excel':
            messagebox.showerror("Missing Library", "Excel export requires the 'openpyxl' library. Please install it with: pip install openpyxl")
        else:
            messagebox.showerror(translate("missing_libs"), translate("missing_libs_text"))
        return
    if not matches:
        messagebox.showwarning(translate("no_data"), translate("no_matches_to_export"))
        return
    
    path = _get_save_path(file_type, "matching_results")
    if not path: return
    
    export_data = []
    req_codes = list(requirements_data.keys())
    req_texts = list(requirements_data.values())
    for i, match_list in enumerate(matches):
        for report_idx, score in match_list:
            export_data.append({
                'Requirement Code': req_codes[i],
                'Requirement Text': req_texts[i],
                'Matched Report Paragraph': report_paras[report_idx],
                'Score': f"{score:.4f}"
            })
    df = pd.DataFrame(export_data)
    _export_dataframe(df, path, file_type, "Matching Results")

def export_llm_analysis(app):
    """Performs and exports LLM analysis for all requirements."""
    if not is_export_available('csv'):
        messagebox.showerror(translate("missing_libs"), translate("missing_libs_text"))
        return
    if not app.matches:
        messagebox.showwarning(translate("no_data"), translate("no_matches_to_export"))
        return

    path = _get_save_path('csv', "llm_analysis_results")
    if not path: return

    progress_win = tk.Toplevel(app)
    progress_win.title("LLM Analysis Progress")
    progress_win.geometry("400x150")
    progress_win.transient(app)
    progress_win.grab_set()

    ttk.Label(progress_win, text="Preparing analysis...").pack(pady=10)
    progress_var = tk.DoubleVar()
    ttk.Progressbar(progress_win, variable=progress_var, maximum=100).pack(pady=10, padx=20, fill=tk.X)
    progress_info = ttk.Label(progress_win, text="")
    progress_info.pack(pady=5)
    
    app._cancel_analysis = False
    def cancel_action():
        app._cancel_analysis = True
    ttk.Button(progress_win, text="Cancel", command=cancel_action).pack(pady=5)

    analysis_results = []
    req_codes = list(app.requirements_data.keys())
    req_texts = list(app.requirements_data.values())
    total_reqs = len(req_codes)

    try:
        for i, match_list in enumerate(app.matches):
            if app._cancel_analysis:
                break
            
            progress_var.set((i / total_reqs) * 100)
            progress_info.config(text=f"Analyzing requirement {i + 1}/{total_reqs}: {req_codes[i]}")
            progress_win.update()

            if not match_list:
                analysis_results.append({'Requirement Code': req_codes[i], 'Requirement Text': req_texts[i], 'LLM Analysis': 'No matches found.'})
                continue

            paragraphs = [app.report_paras[idx] for idx, _ in match_list]
            llm_response = get_llm_analysis(req_texts[i], paragraphs)
            analysis_results.append({'Requirement Code': req_codes[i], 'Requirement Text': req_texts[i], 'LLM Analysis': llm_response})

        if not app._cancel_analysis:
            progress_var.set(100)
            progress_info.config(text="Saving results...")
            progress_win.update()
            df = pd.DataFrame(analysis_results)
            _export_dataframe(df, path, 'csv', "LLM Analysis Results")
        else:
            messagebox.showinfo("Cancelled", "LLM analysis was cancelled.")
    except Exception as e:
        messagebox.showerror("LLM Analysis Error", f"An error occurred during LLM analysis export:\n{e}")
    finally:
        progress_win.destroy()
        app.status_label.config(text=translate("matching_completed_label"))
