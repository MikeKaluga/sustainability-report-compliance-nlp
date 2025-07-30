import tkinter as tk
from exporter import (
    is_export_available,
    export_requirements,
    export_report_paras,
    export_matches
)
from translations import translate

def configure_export_menu(app, export_menu):
    """
    Configures the export menu with options for exporting requirements, report paragraphs, and matches.
    """
    # Submenu for exporting requirements
    req_export_menu = tk.Menu(export_menu, tearoff=0)
    req_export_menu.add_command(label="as CSV...", command=lambda: export_requirements(app.requirements_data, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
    req_export_menu.add_command(label="as Excel...", command=lambda: export_requirements(app.requirements_data, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
    req_export_menu.add_command(label="as PDF...", command=lambda: export_requirements(app.requirements_data, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
    export_menu.add_cascade(label=translate("export_reqs"), menu=req_export_menu, state=tk.DISABLED)

    # Submenu for exporting report paragraphs
    paras_export_menu = tk.Menu(export_menu, tearoff=0)
    paras_export_menu.add_command(label="as CSV...", command=lambda: export_report_paras(app.report_paras, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
    paras_export_menu.add_command(label="as Excel...", command=lambda: export_report_paras(app.report_paras, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
    paras_export_menu.add_command(label="as PDF...", command=lambda: export_report_paras(app.report_paras, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
    export_menu.add_cascade(label=translate("export_paras"), menu=paras_export_menu, state=tk.DISABLED)

    # Submenu for exporting matching results
    matches_export_menu = tk.Menu(export_menu, tearoff=0)
    matches_export_menu.add_command(label="as CSV...", command=lambda: export_matches(app.matches, app.requirements_data, app.report_paras, 'csv'), state=tk.NORMAL if is_export_available('csv') else tk.DISABLED)
    matches_export_menu.add_command(label="as Excel...", command=lambda: export_matches(app.matches, app.requirements_data, app.report_paras, 'excel'), state=tk.NORMAL if is_export_available('excel') else tk.DISABLED)
    matches_export_menu.add_command(label="as PDF...", command=lambda: export_matches(app.matches, app.requirements_data, app.report_paras, 'pdf'), state=tk.NORMAL if is_export_available('pdf') else tk.DISABLED)
    export_menu.add_cascade(label=translate("export_matches"), menu=matches_export_menu, state=tk.DISABLED)
