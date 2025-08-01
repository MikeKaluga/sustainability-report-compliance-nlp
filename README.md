# Sustainability Report Compliance with NLP (Version 0.7)

This project analyzes the compliance of corporate sustainability reports with established reporting standards (such as GRI and ESRS) using modern Natural Language Processing (NLP) methods.

The tool extracts requirements from standards and matches relevant passages from sustainability reports to these requirements using semantic similarity techniques.

## Key Features
- Unified entry point via `main.py`:
  - Single-report analysis
  - Multi-report analysis
- PDF parsing and preprocessing pipeline
- Automatic extraction of requirements from standards
- Segment-level semantic analysis using Sentence-BERT
- Matching report content to specific GRI/ESRS indicators
- Qualitative analysis of matches using a local LLM
- Export functionality for:
  - Requirements
  - Report paragraphs
  - Matching results
  - LLM analysis results
- Advanced filtering of irrelevant content (e.g., footers, headers)
- Multilingual support (English and German) with a language toggle

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
  - `file_handler.py` – handles file selection and processing
  - `exporter.py` – handles exporting data to CSV, Excel, and PDF formats
  - `language_manager.py` – manages language switching and UI text updates
  - `menu_manager.py` – configures the export menu
  - `UI.py` – graphical user interface for single-report analysis
  - `MultiReporterUI.py` – graphical user interface for multi-report analysis
  - `event_handlers.py` – manages event-driven interactions in the GUI, such as button clicks and user input validation
- `scripts/` – optional scripts

## How to Run
1. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Place the standard PDF and report PDFs in the `data/` folder.
3. Run the application:
   ```bash
   python main.py
   ```
4. Use the interface to:
   - Select the standard and one or more report PDFs.
   - Perform matching for individual or multiple reports.
   - Analyze matches with LLM: After matching, select a requirement and click "Analyze with LLM" to perform a qualitative analysis using a local LLM.
     - The application uses **Ollama** for local LLM execution.
     - Supported LLM models include:
       - `dolphin-mixtral`
       - `solar`
       - `command-r`
       - `mistral`
       - `llama3`
       - `phi3`
     - Note: The artifact has only been tested with the `llama3` model on the following hardware:
       - GPU: NVIDIA GeForce GTX 3070 (8GB VRAM)
       - RAM: 32GB DDR5 (4800MT/s)
       - CPU: AMD Ryzen 7 6800H (16 Threads)
   - Export LLM analysis results: After performing the LLM analysis, click "Export LLM Analysis" to save the results for all requirements and their matches to a CSV file.
   - Export other results for further analysis.

## License
MIT License
