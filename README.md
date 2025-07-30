# Sustainability Report Compliance with NLP (Version 0.4)

This project analyzes the compliance of corporate sustainability reports with established reporting standards (such as GRI and ESRS) using modern Natural Language Processing (NLP) methods.

The tool extracts requirements from standards and matches relevant passages from sustainability reports to these requirements using semantic similarity techniques.

## Key Features
- PDF parsing and preprocessing pipeline
- Automatic extraction of requirements from standards
- Segment-level semantic analysis using Sentence-BERT
- Matching report content to specific GRI/ESRS indicators
- Qualitative analysis of matches using a local LLM
- Multi-report analysis: Compare multiple sustainability reports against the same standard via the GUI
- Export functionality for requirements, report paragraphs, and matching results
- Advanced filtering of irrelevant content (e.g., footers, headers)

## Technologies Used
- Python
- HuggingFace Transformers
- Sentence-BERT
- PyTorch
- Scikit-learn
- Tkinter (GUI)
- Local LLMs (e.g., Llama 8B)

## Project Structure
- `data/` – input sustainability reports and standards
- `src/` – main pipeline code and GUI
  - `extractor.py` – extracts requirements from standards
  - `parser.py` – parses paragraphs from reports
  - `embedder.py` – encodes text using Sentence-BERT
  - `matcher.py` – matches requirements to report paragraphs
  - `analyze.py` – performs qualitative analysis using a local LLM
  - `UI.py` – graphical user interface for single-report analysis
  - `MultiReporterUI.py` – graphical user interface for multi-report analysis
- `scripts/` – optional scripts

## How to Run
1. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Place the standard PDF and report PDFs in the `data/` folder.
3. Run the GUI:
   ```bash
   python src/UI.py  # For single-report analysis
   python src/MultiReporterUI.py  # For multi-report analysis
   ```
4. Use the interface to:
   - Select the standard and one or more report PDFs.
   - Perform matching for individual or multiple reports.
   - **Analyze matches with LLM**: After matching, select a requirement and click "Analyze with LLM" to perform a qualitative analysis using a local LLM.
     - The application uses **Ollama** for local LLM execution.
     - Supported LLM models include:
       - `dolphin-mixtral`
       - `solar`
       - `command-r`
       - `mistral`
       - `llama3`
       - `phi3`
     - **Note**: The artifact has only been tested with the `llama3` model on the following hardware:
       - **GPU**: NVIDIA GeForce GTX 3070 (8GB VRAM)
       - **RAM**: 32GB DDR5 (4800MT/s)
       - **CPU**: AMD Ryzen 7 6800H (16 Threads)
   - Export results for further analysis.

## License
MIT License
