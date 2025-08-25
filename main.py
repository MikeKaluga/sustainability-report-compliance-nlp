"""
Version: v1.4

This script serves as the unified entry point for analyzing the compliance of sustainability reports
with established standards. It provides a graphical user interface to select between analyzing a single report or multiple reports.

Key Features:
- Provides a GUI to choose between single and multi-report analysis.
- Launches the appropriate UI for the selected analysis type.

Usage:
- Run the script and select an option from the GUI window.
"""

import warnings
import sys
import os
import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time

# Add the project root to the Python path to resolve module imports
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)


# Translations
TRANSLATIONS = {
    'en': {
        'app_title': 'Sustainability Report Compliance Analysis',
        'select_type': 'Please select an analysis type:',
        'single_button': 'Analyze Single Report',
        'multi_button': 'Analyze Multiple Reports',
        'loading_title': 'Loading...',
        'starting': 'Starting {title}...',
        'patience': 'The application may take a moment to load.\nPlease be patient.',
        'single_title': 'Single Report Analysis',
        'multi_title': 'Multi-Report Analysis',
        'language_label': 'Language',
        'english': 'English',
        'german': 'Deutsch',
    },
    'de': {
        'app_title': 'Untersuchung von Nachhaltigkeitsberichten',
        'select_type': 'Bitte wählen Sie eine Untersuchungsart:',
        'single_button': 'Einzelbericht untersuchen',
        'multi_button': 'Mehrere Berichte untersuchen',
        'loading_title': 'Laden...',
        'starting': 'Starte {title}...',
        'patience': 'Die Anwendung wird geladen.\nBitte haben Sie Geduld.',
        'single_title': 'Einzelbericht-Untersuchung',
        'multi_title': 'Untersuchung mehrerer Berichte',
        'language_label': 'Sprache',
        'english': 'English',
        'german': 'Deutsch',
    },
}

def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def show_loading_window(title, lang='en'):
    """Show a loading window with animation while the UI is starting."""
    loading_window = tk.Toplevel()
    loading_window.title(_t(lang, 'loading_title'))
    loading_window.geometry("300x180")
    loading_window.resizable(False, False)
    
    # Center the loading window
    loading_window.transient()
    loading_window.grab_set()
    
    frame = ttk.Frame(loading_window, padding="20")
    frame.pack(expand=True, fill=tk.BOTH)
    
    # Progress bar with indeterminate mode (spinner effect)
    progress = ttk.Progressbar(frame, mode='indeterminate', length=200)
    progress.pack(pady=(20, 10))
    progress.start(10)  # Start animation
    
    # Loading text
    label = ttk.Label(frame, text=_t(lang, 'starting').format(title=title), font=("Arial", 11))
    label.pack()
    
    # Patience message
    patience_label = ttk.Label(
        frame,
        text=_t(lang, 'patience'),
        font=("Arial", 9), foreground="gray", justify=tk.CENTER
    )
    patience_label.pack(pady=(10, 0))
    
    return loading_window


def main():
    """
    Main entry point for the application.
    Creates a GUI window to allow the user to choose between analyzing a single report or multiple reports.
    """
    # Suppress specific warnings from Transformers and Torch to keep console output clean
    warnings.filterwarnings(
        "ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Torch was not compiled with flash attention.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="`clean_up_tokenization_spaces` was not set. It will be set to `True` by default. This behavior will be depracted in transformers v4.45, and will be then set to `False` by default. For more details check this issue: https://github.com/huggingface/transformers/issues/31884",
        category=FutureWarning,
    )

    root = tk.Tk()

    # Language state and selector (default is german)
    lang_var = tk.StringVar(value='de')
    # Display names mapped to codes
    lang_display_to_code = {
        TRANSLATIONS['en']['english']: 'en',
        TRANSLATIONS['de']['german']: 'de',
    }
    lang_code_to_display = {v: k for k, v in lang_display_to_code.items()}
    lang_display_var = tk.StringVar(value=lang_code_to_display[lang_var.get()])

    def update_ui_texts():
        lang = lang_var.get()
        root.title(f"{_t(lang, 'app_title')} (v1.4)")
        select_label.configure(text=_t(lang, 'select_type'))
        single_btn.configure(text=_t(lang, 'single_button'))
        multi_btn.configure(text=_t(lang, 'multi_button'))
        #lang_label.configure(text=_t(lang, 'language_label'))

    def on_lang_change(_evt=None):
        # Map display value to code and update UI
        selected_display = lang_display_var.get()
        lang_var.set(lang_display_to_code.get(selected_display, 'en'))
        update_ui_texts()

    # Initial window title will be set by update_ui_texts()
    root.geometry("400x180")

    def run_single_report_analysis():
        """Start the single report analysis UI."""
        lang = lang_var.get()
        # Show loading animation
        loading_win = show_loading_window(_t(lang, 'single_title'), lang)
        
        def start_ui():
            try:
                time.sleep(1.0)
                ui_path = os.path.join(project_root, 'src', 'UI.py')
                process = subprocess.Popen([sys.executable, ui_path, '--lang', lang])
                start_time = time.time()
                while time.time() - start_time < 10:
                    if process.poll() is not None:
                        break
                    time.sleep(1.0)
                time.sleep(1.0)
                loading_win.destroy()
                root.destroy()
                process.wait()
            except Exception:
                loading_win.destroy()
                root.destroy()
        
        threading.Thread(target=start_ui, daemon=True).start()

    def run_multi_report_analysis():
        """Start the multi-report analysis UI."""
        lang = lang_var.get()
        # Show loading animation
        loading_win = show_loading_window(_t(lang, 'multi_title'), lang)
        
        def start_multi_ui():
            try:
                time.sleep(1.0)
                multi_ui_path = os.path.join(project_root, 'src', 'MultiReportUI.py')
                process = subprocess.Popen([sys.executable, multi_ui_path, '--lang', lang])
                start_time = time.time()
                while time.time() - start_time < 10:
                    if process.poll() is not None:
                        break
                    time.sleep(1.0)
                time.sleep(1.0)
                loading_win.destroy()
                root.destroy()
                process.wait()
            except Exception:
                loading_win.destroy()
                root.destroy()
        
        threading.Thread(target=start_multi_ui, daemon=True).start()

    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill=tk.BOTH)

    # Language selector row
    lang_row = ttk.Frame(main_frame)
    lang_row.pack(fill=tk.X, pady=(0, 8))
    #lang_label = ttk.Label(lang_row, text=_t(lang_var.get(), 'language_label'), font=("Arial", 9))
    #lang_label.pack(side=tk.LEFT)
    lang_combo = ttk.Combobox(
        lang_row,
        textvariable=lang_display_var,
        values=list(lang_display_to_code.keys()),
        state="readonly"
    )
    lang_combo.pack(side=tk.RIGHT)
    lang_combo.bind("<<ComboboxSelected>>", on_lang_change)

    select_label = ttk.Label(
        main_frame,
        text=_t(lang_var.get(), 'select_type'),
        font=("Arial", 12)
    )
    select_label.pack(pady=(0, 10))

    single_btn = ttk.Button(
        main_frame,
        text=_t(lang_var.get(), 'single_button'),
        command=run_single_report_analysis,
    )
    single_btn.pack(pady=5, fill=tk.X)

    multi_btn = ttk.Button(
        main_frame,
        text=_t(lang_var.get(), 'multi_button'),
        command=run_multi_report_analysis,
    )
    multi_btn.pack(pady=5, fill=tk.X)

    # Initial text update (also sets window title)
    update_ui_texts()

    root.mainloop()


if __name__ == "__main__":
    # Start the main program
    main()