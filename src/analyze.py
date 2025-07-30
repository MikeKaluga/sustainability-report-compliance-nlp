"""
This module provides functionality for qualitative analysis of matching results using a local LLM (Llama3).
It includes a function to send selected requirements and their matched paragraphs to the LLM for analysis
and display the results in a user-friendly format.

Key Features:
- Constructs a detailed prompt for the LLM based on the selected requirement and its matches.
- Sends the prompt to a local LLM API endpoint for analysis.
- Displays the LLM's response in a new pop-up window.

Dependencies:
- Requires the `requests` library for making HTTP requests to the LLM API.
- Requires `tkinter` for GUI components.

Usage:
- Call `run_llm_analysis` with the necessary parameters to perform the analysis.
"""

import requests
import tkinter as tk
from tkinter import messagebox, Text
import re

def get_llm_analysis(requirement_text, paragraphs):
    """
    Sends a single requirement and its paragraphs to the LLM and returns the analysis.
    This is a non-GUI function intended for batch processing.

    Args:
        requirement_text (str): The text of the requirement.
        paragraphs (list): A list of matched paragraph strings.

    Returns:
        str: The LLM's analysis response or an error message.
    """
    prompt = f"""
You are an expert in sustainability reporting according to ESRS and GRI.
Refer to the following requirement:

"{requirement_text}"

Now analyze the following paragraphs from a sustainability report and answer:
- Which elements of the requirement are already present in the text?
- What is missing to fully meet the requirement?

Based on your analysis, please provide your answer in the format:
Degree of fulfillment (0-2): 0 = not fulfilled, 1 = partially, 2 = completely
Justification: ...

Paragraphs:
{chr(10).join(paragraphs)}
"""
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "No response text found.")
    except requests.exceptions.RequestException as e:
        return f"LLM Connection Error: Could not connect to the local LLM. Please ensure Ollama is running. Error: {e}"

def analyze_matches_with_llm(matches, requirements_texts, report_paras):
    """
    Analyzes a list of matches using an LLM and enriches them with the LLM's score.

    Args:
        matches (list): The list of matches from SBERT. Format: [[(para_idx, sbert_score), ...], ...]
        requirements_texts (list): A list of all requirement texts.
        report_paras (list): A list of all paragraphs from the report.

    Returns:
        list: The enriched matches. Format: [[(para_idx, sbert_score, llm_score, llm_explanation), ...], ...]
    """
    enriched_matches = []
    for i, req_matches in enumerate(matches):
        if not req_matches:
            enriched_matches.append([])
            continue

        # We only analyze the top match (top_k=1 was used)
        top_match = req_matches[0]
        para_idx, sbert_score = top_match
        
        requirement_text = requirements_texts[i]
        paragraph_text = report_paras[para_idx]

        llm_response = get_llm_analysis(requirement_text, [paragraph_text])

        # Parse the LLM response to get the score
        score = 0.0
        match = re.search(r"Degree of fulfillment \(0-2\):\s*([0-2])", llm_response, re.IGNORECASE)
        if match:
            score = float(match.group(1))

        enriched_matches.append([(para_idx, sbert_score, score, llm_response)])
    
    return enriched_matches

def run_llm_analysis(parent, req_listbox, requirements_data, matches, report_paras, status_label, update_idletasks, translate):
    """
    Performs qualitative analysis of a selected requirement and its top matches using a local LLM.

    This function retrieves the selected requirement and its top-matched paragraphs from the report,
    constructs a detailed prompt for the LLM, and sends it to a local LLM API endpoint. The LLM's response
    is displayed in a new pop-up window.

    Args:
        parent (tk.Tk): The parent Tkinter window.
        req_listbox (tk.Listbox): The listbox containing the requirements.
        requirements_data (dict): A dictionary of requirements with their codes as keys and texts as values.
        matches (list): A list of matching results for each requirement, where each entry contains tuples of
                        (report paragraph index, similarity score).
        report_paras (list): A list of paragraphs extracted from the report.
        status_label (tk.Label): The status label to update the application's status.
        update_idletasks (function): A function to refresh the UI during long-running operations.
        translate (function): A function to retrieve translated text for UI elements.

    Raises:
        requests.exceptions.RequestException: If the LLM API endpoint is unreachable or returns an error.

    Returns:
        None
    """
    selected_indices = req_listbox.curselection()
    if not selected_indices:
        return

    index = selected_indices[0]
    requirement_code = req_listbox.get(index)
    requirement_text = requirements_data.get(requirement_code, "")
    
    if not matches or index >= len(matches) or not matches[index]:
        messagebox.showinfo("LLM Analysis", "No matches available to analyze for this requirement.")
        return

    paragraphs = [report_paras[report_idx] for report_idx, score in matches[index]]

    prompt = f"""
You are an expert in sustainability reporting according to ESRS and GRI.
Refer to the following requirement:

"{requirement_text}"

Now analyze the following paragraphs from a sustainability report and answer:
- Which elements of the requirement are already present in the text?
- What is missing to fully meet the requirement?

Based on your analysis, please provide your answer in the format:
Degree of fulfillment (0-2): 0 = not fulfilled, 1 = partially, 2 = completely
Justification: ...

Paragraphs:
{chr(10).join(paragraphs)}
"""
    try:
        status_label.config(text="Querying LLM... Please wait.")
        update_idletasks()

        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }, timeout=120) # 120-second timeout
        response.raise_for_status()
        
        llm_response = response.json().get("response", "No response text found.")

        # Display the result in a new window
        result_win = tk.Toplevel(parent)
        result_win.title(f"LLM Analysis for {requirement_code}")
        result_win.geometry("700x500")
        result_win.transient(parent)

        text_area = Text(result_win, wrap=tk.WORD, font=("Segoe UI", 10), padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, llm_response)
        text_area.config(state=tk.DISABLED)

    except requests.exceptions.RequestException as e:
        messagebox.showerror("LLM Connection Error", 
                             f"Could not connect to the local LLM at http://localhost:11434.\n"
                             f"Please ensure the Ollama service is running and Llama3 is installed.\n\nError: {e}")
    finally:
        status_label.config(text=translate("matching_completed_label"))
