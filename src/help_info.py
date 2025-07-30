"""
This module provides functions to display the help and about windows for the compliance analysis application.
"""

import tkinter as tk
from tkinter import Text
from translations import translate


def show_help(app):
    """
    Displays a help/FAQ window with instructions on how to use the application.
    Args:
        app: The main ComplianceApp instance.
    """
    help_win = tk.Toplevel(app)
    help_win.title(translate("help"))
    help_win.geometry("600x500")
    help_win.transient(app)  # Keep window on top

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


def show_about(app):
    """
    Displays an 'About' window with information about the application.
    Args:
        app: The main ComplianceApp instance.
    """
    about_win = tk.Toplevel(app)
    about_win.title(translate("about"))
    about_win.geometry("500x350")
    about_win.transient(app)

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
