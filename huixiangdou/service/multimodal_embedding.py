# 
from typing import List, Any

class MultiModalEmbedding:
    """Wrap Visual-BGE as langchain.embedding API"""
    client: Any

    def __init__(self):
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]
