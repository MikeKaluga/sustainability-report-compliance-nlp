"""
This module provides functionality for qualitative analysis of matching results using a local LLM (Llama3).
It includes functions to send requirements and their matched paragraphs to the LLM for batch analysis.

Key Features:
- Constructs a detailed prompt for the LLM based on a requirement and its matches.
- Sends the prompt to a local LLM API endpoint for analysis.
- Enriches match data with LLM scores and explanations for export.

Dependencies:
- Requires the `requests` library for making HTTP requests to the LLM API.

Usage:
- Call `analyze_matches_with_llm` to perform batch analysis on a set of matches.
"""

import requests
import re


def get_llm_analysis(requirement_text, paragraphs):
    """
    Sends a single requirement and its paragraphs to the LLM and returns the analysis.
    This is a non-GUI function intended for batch processing.

    Args:
        requirement_text (str or dict): The text of the requirement or dict with 'text' and 'sub_requirements'.
        paragraphs (list): A list of matched paragraph strings.

    Returns:
        str: The LLM's analysis response or an error message.
    """
    if isinstance(requirement_text, dict):
        main_text = requirement_text.get('text', '')
        sub_requirements = requirement_text.get('sub_requirements', [])
    else:
        main_text = requirement_text
        sub_requirements = []

    sub_req_prompt_part = ""
    if sub_requirements:
        sub_req_analysis_prompts = []
        for i, sub_req in enumerate(sub_requirements):
            sub_req_analysis_prompts.append(f"""
Sub-requirement {i+1}: "{sub_req}"
- Fulfillment (0-2):
- Justification:""")

        sub_req_prompt_part = f"""
First, analyze each of the following sub-requirements individually based on the provided paragraphs. For each, provide a fulfillment score and a brief justification.

{''.join(sub_req_analysis_prompts)}

Finally, provide an overall assessment:
- Overall Degree of fulfillment (0-2): 0 = not fulfilled, 1 = partially, 2 = completely
- Overall Justification: ...
"""
    else:
        sub_req_prompt_part = """
Based on your analysis, please provide your answer in the format:
Degree of fulfillment (0-2): 0 = not fulfilled, 1 = partially, 2 = completely
Justification: ...
"""

    prompt = f"""
You are an expert in sustainability reporting according to ESRS and GRI.
Refer to the following requirement:

"{main_text}"

Now analyze the following paragraphs from a sustainability report and answer:
- Which elements of the requirement are already present in the text?
- What is missing to fully meet the requirement?

{sub_req_prompt_part}

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

        # Only analyze the top k matches
        top_match = req_matches[0]
        para_idx, sbert_score = top_match

        requirement_text = requirements_texts[i]
        paragraph_text = report_paras[para_idx]

        llm_response = get_llm_analysis(requirement_text, [paragraph_text])

        # Parse the LLM response to get the score
        score = 0.0
        match = re.search(
            r"Degree of fulfillment \(0-2\):\s*([0-2])", llm_response, re.IGNORECASE)
        if match:
            score = float(match.group(1))

        enriched_matches.append([(para_idx, sbert_score, score, llm_response)])

    return enriched_matches
