from sentence_transformers import SentenceTransformer


class SBERTEmbedder:
    """
    A class to handle text embedding using Sentence-BERT (SBERT).
    This class uses a pre-trained SBERT model to convert text segments into numerical embeddings.
    """

    def __init__(
        self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initializes the SBERTEmbedder with a specified pre-trained model.

        Args:
            model_name (str): The name of the pre-trained SBERT model to use.
                             Defaults to 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'.
        """
        self.model = SentenceTransformer(model_name)

    def encode(self, segments):
        """
        Encodes a list of text segments into numerical embeddings using the SBERT model.

        Args:
            segments (list of str): A list of text segments to be encoded.

        Returns:
            torch.Tensor: A tensor containing the embeddings for the input segments.
                          Each row corresponds to the embedding of a segment.
        """
        return self.model.encode(segments, convert_to_tensor=True)
