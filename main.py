import warnings
from src.parser import (
    extract_paragraphs_from_pdf,
)  # Function to extract paragraphs from a report (PDF)
from src.embedder import (
    SBERTEmbedder,
)  # Class for creating embeddings using Sentence-BERT
from src.matcher import (
    match_requirements_to_report,
)  # Function to match requirements with report content
from src.extractor import (
    extract_requirements_from_standard_pdf,
)  # Function to extract requirements from a standard (PDF)


def main():
    # Suppress specific warnings from Transformers and Torch to keep console output clean
    warnings.filterwarnings(
        "ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Torch was not compiled with flash attention.*",
        category=UserWarning,
    )

    # Define the paths to the input files
    standard_file = "data/standard.pdf"  # Standard PDF containing the requirements
    report_file = "data/bericht.pdf"  # Report PDF to be analyzed

    print("Extracting requirements from the standard and paragraphs from the report...")
    # Extract requirements from the standard PDF
    # The function returns a dictionary where keys are requirement codes and values are the corresponding texts
    req_dict = extract_requirements_from_standard_pdf(standard_file)
    standard_paras = list(
        req_dict.values()
    )  # Convert the dictionary values to a list of requirement texts

    # Extract paragraphs from the report PDF
    # The function returns a list of paragraphs extracted from the report
    report_paras = extract_paragraphs_from_pdf(report_file)

    # Print the number of found requirements and report paragraphs
    print(
        f"Found requirements: {len(standard_paras)}, relevant report paragraphs: {len(report_paras)}"
    )

    print("Embedding paragraphs...")
    # Initialize the SBERT embedder
    embedder = SBERTEmbedder()

    # Create embeddings for the requirements and report paragraphs
    # The embeddings are numerical representations of the texts used for matching
    standard_emb = embedder.encode(standard_paras)
    report_emb = embedder.encode(report_paras)

    print("Matching segments...")
    # Perform matching to link requirements with report paragraphs
    # The function returns a list of matches, where each match is a list of (index, score) tuples
    matches = match_requirements_to_report(standard_emb, report_emb, top_k=5)

    # Print the matching results
    # For each requirement, display the best matching paragraphs from the report with their scores
    for i, match_list in enumerate(matches):
        print(
            f"\nRequirement {i+1}: {standard_paras[i][:80]}..."
        )  # Show the first 80 characters of the requirement
        for idx, score in match_list:
            print(
                f" ({score:.2f}) {report_paras[idx][:100]}..."
            )  # Show the first 100 characters of the matching paragraph


if __name__ == "__main__":
    # Start the main program
    main()
