"""
Version: v1.2

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


def show_loading_window(title):
    """Show a loading window with animation while the UI is starting."""
    loading_window = tk.Toplevel()
    loading_window.title("Loading...")
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
    label = ttk.Label(frame, text=f"Starting {title}...", font=("Arial", 11))
    label.pack()
    
    # Patience message
    patience_label = ttk.Label(frame, text="The application may take a moment to load.\nPlease be patient.", 
                              font=("Arial", 9), foreground="gray", justify=tk.CENTER)
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
    root.title("Sustainability Report Compliance Analysis (v1.2)")
    root.geometry("400x150")

    def run_single_report_analysis():
        """Start the single report analysis UI."""
        # Show loading animation
        loading_win = show_loading_window("Single Report Analysis")
        
        def start_ui():
            try:
                # Give the loading window time to appear
                time.sleep(1.0)
                # Run the UI module as a separate process
                ui_path = os.path.join(project_root, 'src', 'UI.py')
                process = subprocess.Popen([sys.executable, ui_path])
                
                # Wait for the UI process to actually start and stabilize
                # Check if process is running for a longer period
                start_time = time.time()
                while time.time() - start_time < 10:  # Wait up to 10 seconds
                    if process.poll() is not None:  # Process ended unexpectedly
                        break
                    time.sleep(1.0)
                
                # Give additional time for UI to fully load
                time.sleep(1.0)
                loading_win.destroy()
                root.destroy()
                # Wait for the process to complete
                process.wait()
            except Exception as e:
                loading_win.destroy()
                root.destroy()
        
        # Start UI in separate thread to keep loading animation responsive
        threading.Thread(target=start_ui, daemon=True).start()

    def run_multi_report_analysis():
        """Start the multi-report analysis UI."""
        # Show loading animation
        loading_win = show_loading_window("Multi-Report Analysis")
        
        def start_multi_ui():
            try:
                # Give the loading window time to appear
                time.sleep(1.0)
                # Run the MultiReportUI module as a separate process
                multi_ui_path = os.path.join(project_root, 'src', 'MultiReportUI.py')
                process = subprocess.Popen([sys.executable, multi_ui_path])
                
                # Wait for the UI process to actually start and stabilize
                # Check if process is running for a longer period
                start_time = time.time()
                while time.time() - start_time < 10:  # Wait up to 10 seconds
                    if process.poll() is not None:  # Process ended unexpectedly
                        break
                    time.sleep(1.0)
                
                # Give additional time for UI to fully load
                time.sleep(1.0)
                loading_win.destroy()
                root.destroy()
                # Wait for the process to complete
                process.wait()
            except Exception as e:
                loading_win.destroy()
                root.destroy()
        
        # Start UI in separate thread to keep loading animation responsive
        threading.Thread(target=start_multi_ui, daemon=True).start()

    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(
        main_frame,
        text="Please select an analysis type:",
        font=("Arial", 12)
    ).pack(pady=(0, 10))

    ttk.Button(
        main_frame,
        text="Analyze Single Report",
        command=run_single_report_analysis,
    ).pack(pady=5, fill=tk.X)

    ttk.Button(
        main_frame,
        text="Analyze Multiple Reports",
        command=run_multi_report_analysis,
    ).pack(pady=5, fill=tk.X)

    root.mainloop()


if __name__ == "__main__":
    # Start the main program
    main()