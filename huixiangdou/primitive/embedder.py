# Copyright (c) OpenMMLab. All rights reserved.
#
from typing import Any, List
from loguru import logger
import os
import torch
import pdb

class Embedder:
    """Wrap text2vec (multimodal) model."""
    client: Any

    def __init__(self, model_path: str):
        from FlagEmbedding.visual.modeling import Visualized_BGE
        vision_weight_path = os.path.join(model_path, 'Visualized_m3.pth')
        self.client = Visualized_BGE(model_name_bge=model_path, model_weight=vision_weight_path).eval()

    @classmethod
    def use_multimodal(self, model_path):
        """Check text2vec model using multimodal or not."""

        if 'bge-m3' not in model_path.lower():
            return False
        
        vision_weight = os.path.join(model_path, 'Visualized_m3.pth')
        if not os.path.exists(vision_weight):
            logger.warning('`Visualized_m3.pth` (vision model weight) not exist')
            return False
        return True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        features = []
        with torch.no_grad():
            for text in texts:
                feature = self.client.encode(text=text)
                features.append(feature)
        return torch.cat(features, dim=0)

    def embed_text(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_texts([text])[0]

    def embed_images(self, paths: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            paths: The list of image paths to embed.

        Returns:
            List of embeddings, one for each image.
        """
        features = []
        with torch.no_grad():
            for path in paths:
                feature = self.client.encode(image=path)
                features.append(feature)
        
        return torch.cat(features, dim=0)

    def embed_image(self, path: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            path: Image path

        Returns:
            Embeddings for the image.
        """
        return self.embed_images([path])[0]

    def embed_query(self, text: str=None, path: str=None) -> List[float]:
        with torch.no_grad():
            feature = self.client.encode(text=text, image=path)
            return feature
