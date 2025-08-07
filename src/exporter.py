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
    styles.add(ParagraphStyle(name='LLMAnalysis', fontName='Helvetica', fontSize=10, spaceAfter=4, leftIndent=10))
    
    elements = [Paragraph(title, styles['h1']), Spacer(1, 24)]

    if 'Requirement Code' in df.columns and 'LLM Analysis' in df.columns and 'Avg Max Score' in df.columns:
        # This is the multi-report summary export
        for _, row in df.iterrows():
            elements.extend([
                Paragraph(f"Requirement: {row['Requirement Code']}", styles['ReqCode']),
                Paragraph(row['Requirement Text'], styles['Normal']),
                Spacer(1, 6),
                Paragraph(f"<b>Avg Max Score:</b> {row['Avg Max Score']}", styles['Normal']),
                Paragraph(f"<b>Reports Covered:</b> {row['Reports Covered']}", styles['Normal']),
                Paragraph("<b>LLM Analysis:</b>", styles['SubHeading']),
                Paragraph(row['LLM Analysis'], styles['LLMAnalysis']),
                Spacer(1, 24)
            ])
    elif 'Requirement Code' in df.columns and 'LLM Analysis' not in df.columns:
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
                Paragraph(f"Requirement: {row['Code']}", styles['ReqCode']),
                Paragraph(row['Requirement Text'], styles['Normal']),
                Spacer(1, 12)
            ])
    else:
        for _, row in df.iterrows():
            # Convert row to string properly
            text = str(row.iloc[0]) if len(row) > 0 else "No data"
            elements.extend([Paragraph(text, styles['Normal']), Spacer(1, 12)])

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
    
    # Convert requirements_data to the expected format
    export_data = []
    for code, req_data in requirements_data.items():
        if isinstance(req_data, dict):
            text = req_data['full_text']
        else:
            # Fallback for old format
            text = req_data
        export_data.append({'Code': code, 'Requirement Text': text})
    
    df = pd.DataFrame(export_data)
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
    
    # Debug: Print the structure of matches and requirements_data
    print(f"DEBUG: matches type: {type(matches)}")
    print(f"DEBUG: matches keys (first 3): {list(matches.keys())[:3] if isinstance(matches, dict) else 'Not a dict'}")
    print(f"DEBUG: requirements_data type: {type(requirements_data)}")
    print(f"DEBUG: requirements_data keys (first 3): {list(requirements_data.keys())[:3]}")
    
    export_data = []
    
    # Handle the new matches structure (dict mapping text -> matches)
    if isinstance(matches, dict):
        for text, match_list in matches.items():
            # Find the corresponding requirement code for this text
            req_code = None
            req_text = None
            
            for code, req_data in requirements_data.items():
                if isinstance(req_data, dict):
                    # Check if this text matches the full text or any sub-point
                    if text == req_data['full_text'].strip():
                        req_code = code
                        req_text = req_data['full_text']
                        break
                    elif text in [sp.strip() for sp in req_data['sub_points']]:
                        req_code = f"{code} (Sub-point)"
                        req_text = text
                        break
                else:
                    # Old format fallback
                    if text == req_data.strip():
                        req_code = code
                        req_text = req_data
                        break
            
            # If we couldn't find a matching requirement, use the text as both code and text
            if req_code is None:
                req_code = "Unknown"
                req_text = text
            
            for report_idx, score in match_list:
                export_data.append({
                    'Requirement Code': req_code,
                    'Requirement Text': req_text,
                    'Matched Report Paragraph': report_paras[report_idx],
                    'Score': f"{score:.4f}"
                })
    else:
        # Old format: matches is a list
        req_codes = list(requirements_data.keys())
        req_texts = []
        for req_data in requirements_data.values():
            if isinstance(req_data, dict):
                req_texts.append(req_data['full_text'])
            else:
                req_texts.append(req_data)
        
        for i, match_list in enumerate(matches):
            for report_idx, score in match_list:
                export_data.append({
                    'Requirement Code': req_codes[i],
                    'Requirement Text': req_texts[i],
                    'Matched Report Paragraph': report_paras[report_idx],
                    'Score': f"{score:.4f}"
                })
    
    print(f"DEBUG: export_data length: {len(export_data)}")
    if export_data:
        print(f"DEBUG: First export entry: {export_data[0]}")
    
    if not export_data:
        messagebox.showwarning(translate("no_data"), "No matching data could be processed for export.")
        return
    
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
    
    # Handle the new matches structure (dict mapping text -> matches)
    if isinstance(app.matches, dict):
        total_items = len(app.matches)
        for i, (text, match_list) in enumerate(app.matches.items()):
            if app._cancel_analysis:
                break
            
            progress_var.set((i / total_items) * 100)
            progress_info.config(text=f"Analyzing item {i + 1}/{total_items}")
            progress_win.update()

            # Find the corresponding requirement code for this text
            req_code = "Unknown"
            req_text = text
            
            for code, req_data in app.requirements_data.items():
                if isinstance(req_data, dict):
                    if text == req_data['full_text'].strip():
                        req_code = code
                        req_text = req_data['full_text']
                        break
                    elif text in [sp.strip() for sp in req_data['sub_points']]:
                        req_code = f"{code} (Sub-point)"
                        req_text = text
                        break
                else:
                    if text == req_data.strip():
                        req_code = code
                        req_text = req_data
                        break

            if not match_list:
                analysis_results.append({'Requirement Code': req_code, 'Requirement Text': req_text, 'LLM Analysis': 'No matches found.'})
                continue

            paragraphs = [app.report_paras[idx] for idx, _ in match_list]
            llm_response = get_llm_analysis(req_text, paragraphs)
            analysis_results.append({'Requirement Code': req_code, 'Requirement Text': req_text, 'LLM Analysis': llm_response})
    else:
        # Old format fallback
        req_codes = list(app.requirements_data.keys())
        req_texts = []
        for req_data in app.requirements_data.values():
            if isinstance(req_data, dict):
                req_texts.append(req_data['full_text'])
            else:
                req_texts.append(req_data)
        
        total_reqs = len(req_codes)
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

    try:
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
