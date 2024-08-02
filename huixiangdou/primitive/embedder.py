# Copyright (c) OpenMMLab. All rights reserved.
#
import os
import pdb
from typing import Any, List

import numpy as np
import torch
# from BCEmbedding import EmbeddingModel
from sentence_transformers import SentenceTransformer
from FlagEmbedding.visual.modeling import Visualized_BGE
from loguru import logger
from .query import DistanceStrategy

class Embedder:
    """Wrap text2vec (multimodal) model."""
    client: Any

    def __init__(self, model_path: str):
        self.support_image = False
        # bce also use euclidean distance.
        self.distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
        
        if self.use_multimodal(model_path=model_path):
            self.support_image = True
            vision_weight_path = os.path.join(model_path, 'Visualized_m3.pth')
            self.client = Visualized_BGE(
                model_name_bge=model_path,
                model_weight=vision_weight_path).eval()
        else:
            self.client = SentenceTransformer(model_name_or_path=model_path).half()

    @classmethod
    def use_multimodal(self, model_path):
        """Check text2vec model using multimodal or not."""

        if 'bge-m3' not in model_path.lower():
            return False

        vision_weight = os.path.join(model_path, 'Visualized_m3.pth')
        if not os.path.exists(vision_weight):
            logger.warning(
                '`Visualized_m3.pth` (vision model weight) not exist')
            return False
        return True

    def embed_query(self, text: str = None, path: str = None) -> np.ndarray:
        """Embed input text or image as feature, output np.ndarray with np.float32"""
        if type(self.client) is Visualized_BGE:
            with torch.no_grad():
                feature = self.client.encode(text=text, image=path)
                return feature.cpu().numpy().astype(np.float32)
        else:
            if text is None:
                raise ValueError('This model only support text')
            emb = self.client.encode([text], show_progress_bar=False, normalize_embeddings=True)
            emb = emb.astype(np.float32)
            for norm in np.linalg.norm(emb, axis=1):
                assert abs(norm - 1) < 0.001
            return emb
