# Copyright (c) OpenMMLab. All rights reserved.
#
from typing import Any, List


class MultiModalEmbedding:
    """TODO, Wrap MultiModal model as langchain.embedding API."""
    client: Any

    def __init__(self):
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            texts: The list of texts to embed. Compatible with langchain API.

        Returns:
            List of embeddings, one for each text.
        """
        pass

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.
        Compatible with langchain API.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]

    def embed_images(self, paths: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            paths: The list of image paths to embed.

        Returns:
            List of embeddings, one for each image.
        """
        pass

    def embed_query_image(self, path: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            path: Image path

        Returns:
            Embeddings for the image.
        """
        return self.embed_documents([path])[0]
