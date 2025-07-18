# Sustainability Report Compliance with NLP (Version 0.3)

This project analyzes the compliance of corporate sustainability reports with established reporting standards (such as GRI and ESRS) using modern Natural Language Processing (NLP) methods.

The tool extracts requirements from standards and matches relevant passages from sustainability reports to these requirements using semantic similarity techniques.

## Key Features
- PDF parsing and preprocessing pipeline
- Automatic extraction of requirements from standards
- Segment-level semantic analysis using Sentence-BERT
- Matching report content to specific GRI/ESRS indicators
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

## Project Structure
- `data/` – input sustainability reports and standards
- `src/` – main pipeline code and GUI
  - `extractor.py` – extracts requirements from standards
  - `parser.py` – parses paragraphs from reports
  - `embedder.py` – encodes text using Sentence-BERT
  - `matcher.py` – matches requirements to report paragraphs
  - `UI.py` – graphical user interface for single-report analysis
  - `MultiReporterUI.py` – graphical user interface for multi-report analysis
- `scripts/` – optional scripts for:
  - Extracting requirements using various LLMs (e.g., institutionally hosted large LLMs, internationally available LLMs like ChatGPT, or small local LLMs like T5)
  - Adapting extractors to specific standards such as GRI or ESRS

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
   - Export results for further analysis.

## License
MIT License
