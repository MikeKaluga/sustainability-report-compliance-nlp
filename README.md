# Sustainability Report Compliance with NLP

This project analyzes the compliance of corporate sustainability reports with established reporting standards (such as GRI and ESRS) using modern Natural Language Processing (NLP) methods.

The tool extracts requirements from standards and matches relevant passages from sustainability reports to these requirements using semantic similarity techniques.

## Key Features
- PDF parsing and preprocessing pipeline
- Automatic extraction of requirements from standards
- Segment-level semantic analysis using Sentence-BERT
- Matching report content to specific GRI/ESRS indicators
- Export functionality for requirements, report paragraphs, and matching results

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
  - `UI.py` – graphical user interface for the tool
- `scripts/` – optional scripts for:
  - Extracting requirements using various LLMs (e.g., institutionally hosted large LLMs, internationally available LLMs like ChatGPT, or small local LLMs like T5)
  - Adapting extractors to specific standards such as GRI or ESRS

## How to Run
1. Place the standard PDF and report PDF in the `data/` folder.
2. Run the GUI:
   ```bash
   python src/UI.py
   ```
3. Use the interface to select the standard and report PDFs, perform matching, and export results.

## License
MIT License
