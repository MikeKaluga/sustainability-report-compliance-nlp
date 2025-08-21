"""
This script provides functionality to match requirements to report paragraphs based on their embeddings.
It uses cosine similarity to identify the most relevant paragraphs for each requirement.

Key Features:
- Computes cosine similarity between requirement embeddings and report paragraph embeddings.
- Returns the top-k most similar paragraphs for each requirement along with their similarity scores.

Usage:
- Use the `match_requirements_to_report` function to find matches between requirements and report content.
- Input embeddings should be provided as PyTorch tensors, and the output is a list of matches for each requirement.
"""

from sklearn.metrics.pairwise import cosine_similarity


def match_requirements_to_report(req_embeddings, report_embeddings, top_k=10, min_score=0.6):
    """
    Matches requirements to report paragraphs based on cosine similarity.

    Args:
        req_embeddings (torch.Tensor): A tensor containing the embeddings of the requirements.
                                       Each row corresponds to the embedding of a requirement.
        report_embeddings (torch.Tensor): A tensor containing the embeddings of the report paragraphs.
                                          Each row corresponds to the embedding of a paragraph.
        top_k (int): The number of top matches to return for each requirement.
        min_score (float): Minimum cosine similarity threshold; matches below this are discarded.

    Returns:
        list of list of tuple: A list where each element corresponds to a requirement.
                               Each element is a list of tuples, where each tuple contains:
                               - The index of the matching paragraph in the report.
                               - The cosine similarity score of the match.
    """

    matches = []  # List to store the matches for each requirement

    # Convert PyTorch tensors to NumPy arrays for compatibility with scikit-learn
    req_np = req_embeddings.cpu().numpy()  # Convert requirement embeddings to NumPy
    rep_np = report_embeddings.cpu().numpy()  # Convert report embeddings to NumPy

    # Iterate over each requirement embedding
    for i, req_vec in enumerate(req_np):
        # Compute cosine similarity between the current requirement and all report paragraphs
        sims = cosine_similarity(req_vec.reshape(1, -1), rep_np)[0]

        # Sort indices by similarity descending
        sorted_idx = sims.argsort()[::-1]

        # Filter by threshold and then take up to top_k
        filtered_idx = [idx for idx in sorted_idx if sims[idx] >= min_score][:top_k]
        top_scores = [float(sims[idx]) for idx in filtered_idx]

        # Store the matches as a list of (index, score) tuples
        matches.append(list(zip(filtered_idx, top_scores)))

    return matches
