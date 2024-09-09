# Copyright (c) OpenMMLab. All rights reserved.
#
import os
import pdb
import requests
import json

from typing import Any, List

import numpy as np
from loguru import logger
from .query import DistanceStrategy
from .limitter import RPM, TPM
from .chunk import Chunk

class Embedder:
    """Wrap text2vec (multimodal) model."""
    client: Any
    _type: str

    def __init__(self, model_config: dict):
        self.support_image = False
        # bce also use euclidean distance.
        self.distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
        
        model_path = model_config['embedding_model_path']
        self._type = self.model_type(model_path=model_path)
        if 'bce' in self._type:
            from sentence_transformers import SentenceTransformer
            self.client = SentenceTransformer(model_name_or_path=model_path).half()
        elif 'bge' in self._type:
            from FlagEmbedding.visual.modeling import Visualized_BGE
            self.support_image = True
            vision_weight_path = os.path.join(model_path, 'Visualized_m3.pth')
            self.client = Visualized_BGE(
                model_name_bge=model_path,
                model_weight=vision_weight_path).eval()
        elif 'siliconcloud' in self._type:
            api_token = model_config['api_token'].strip()
            if len(api_token) < 1:
                api_token = os.getenv('SILICONCLOUD_TOKEN')
                if api_token is None or len(api_token) < 1:
                    raise ValueError('siliconclud remote embedder api token is None')

            if 'Bearer' not in api_token:
                api_token = 'Bearer ' + api_token
            api_rpm = max(1, int(model_config['api_rpm']))
            api_tpm = max(1, int(model_config['api_tpm']))

            self.client = {
                'api_token': api_token,
                'api_rpm': RPM(api_rpm),
                'api_tpm': TPM(api_tpm)
            }

        else:
            raise ValueError('Unknown type {}'.format(self._type))

    @classmethod
    def model_type(self, model_path):
        """Check text2vec model using multimodal or not."""
        if model_path.startswith('https'):
            return 'siliconcloud'

        if 'bge-m3' not in model_path.lower():
            return 'bce'

        vision_weight = os.path.join(model_path, 'Visualized_m3.pth')
        if not os.path.exists(vision_weight):
            logger.warning(
                '`Visualized_m3.pth` (vision model weight) not exist')
            return 'bce'
        return 'bge'

    def token_length(self, text: str) -> int:
        if 'bge' in self._type or 'bce' in self._type:
            return len(self.client.tokenizer(text, padding=False, truncation=False)['input_ids'])
        else:
            return len(text) // 2

    def distance(self, text1:str, text2:str) -> float:
        emb1 = self.embed_query(text=text1)
        emb2 = self.embed_query(text=text2)

        if self.distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
            distance = np.linalg.norm(emb1 - emb2)
            return distance
        raise ValueError('Unsupported distance strategy')

    def embed_query(self, text: str = None, path: str = None) -> np.ndarray:
        """Embed input text or image as feature, output np.ndarray with np.float32"""
        if 'bge' in self._type:
            import torch
            with torch.no_grad():
                feature = self.client.encode(text=text, image=path)
                return feature.cpu().numpy().astype(np.float32)
        elif 'bce' in self._type:
            if text is None:
                raise ValueError('This model only support text')
            emb = self.client.encode([text], show_progress_bar=False, normalize_embeddings=True)
            emb = emb.astype(np.float32)
            # for norm in np.linalg.norm(emb, axis=1):
            #     assert abs(norm - 1) < 0.001
            return emb
        else:
            self.client['api_rpm'].wait(silent=True)
            self.client['api_tpm'].wait(silent=True, token_count=len(text))

            # siliconcloud bce API
            if text is None:
                raise ValueError('This api only support text')
            
            url = "https://api.siliconflow.cn/v1/embeddings"

            payload = {
                "model": "netease-youdao/bce-embedding-base_v1",
                # Since siliconcloud API return 50400 for long input, we have to truncate it.
                "input": text,
                "encoding_format": "float"
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": self.client['api_token']
            }

            response = requests.post(url, json=payload, headers=headers)
            json_obj = json.loads(response.text)
            emb_list = json_obj['data'][0]['embedding']
            emb = np.array(emb_list).astype(np.float32).reshape(1, -1)
            return emb

    def embed_query_batch_text(self, chunks: List[Chunk] = []) -> np.ndarray:
        """Embed input text or image as feature, output np.ndarray with np.float32"""
        if 'bge' in self._type:
            import torch
            with torch.no_grad():
                features = []
                for c in chunks:
                    feature = self.client.encode(text=c.content_or_path)
                    features.append(feature.cpu().numpy())
                return np.concatenate(features).reshape(len(chunks), -1).astype(np.float32)

        elif 'bce' in self._type:
            texts = []
            for c in chunks:
                texts.append(c.content_or_path)
            emb = self.client.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return emb.astype(np.float32)

        else:
            features = []
            for c in chunks:
                feature = self.embed_query(text=c.content_or_path)
                features.append(feature)
            return np.concatenate(features).reshape(len(chunks), -1).astype(np.float32)
