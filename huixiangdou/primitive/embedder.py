# Copyright (c) OpenMMLab. All rights reserved.
#
from typing import Any, List
from loguru import logger
import os
import torch
import pdb
import numpy as np
from FlagEmbedding.visual.modeling import Visualized_BGE
from BCEmbedding import EmbeddingModel

class Embedder:
    """Wrap text2vec (multimodal) model."""
    client: Any

    def __init__(self, model_path: str):
        self.support_image = False
        if self.use_multimodal:
            self.support_image = True
            vision_weight_path = os.path.join(model_path, 'Visualized_m3.pth')
            self.client = Visualized_BGE(model_name_bge=model_path, model_weight=vision_weight_path).eval()
        else:
            self.client = EmbeddingModel(model_name_or_path=model_path)

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

    def embed_query(self, text: str=None, path: str=None) -> List[float]:
        if type(self.client) is Visualized_BGE:
            with torch.no_grad():
                feature = self.client.encode(text=text, image=path)
                return feature.cpu().numpy().astype(np.float32)
        else:
            if text is None:
                raise ValueError('This model only support text')
            return self.client.encode([text])
