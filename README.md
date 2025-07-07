# Sustainability Report Compliance with NLP

This project investigates the compliance of corporate sustainability reports with established reporting standards (such as GRI and ESRS) using modern Natural Language Processing (NLP) methods.

The goal is to develop a tool that semantically analyzes the textual content of sustainability reports and maps relevant passages to corresponding reporting requirements. The approach includes document parsing, segment-level encoding using Transformer-based models (e.g. BERT), and multi-label classification or semantic similarity matching.

## Key Features
- PDF parsing and preprocessing pipeline
- Segment-level semantic analysis
- Matching report content to specific GRI/ESRS indicators
- Evaluation using annotated data (optional)
- Easily extendable NLP architecture (SBERT, QA, or RAG)

## Technologies Used
- Python
- HuggingFace Transformers
- Sentence-BERT / BERT
- PyTorch
- Scikit-learn
- Streamlit (optional UI)

## Project Structure
- `data/` – input sustainability reports
- `models/` – fine-tuned NLP models
- `notebooks/` – experiments and prototyping
- `src/` – main pipeline code
- `app/` – (optional) Streamlit interface

## License
MIT License
