# Copyright (c) OpenMMLab. All rights reserved.
from __future__ import annotations

import time
import logging
import os
import pdb
import pickle
from pathlib import Path
from typing import (Any, Callable, Dict, Iterable, List, Optional, Sized,
                    Tuple, Union)

import numpy as np
from loguru import logger
from tqdm import tqdm

from .embedder import Embedder
from .query import Query, DistanceStrategy
from .chunk import Chunk
try:
    import faiss
except ImportError:
    raise ImportError(
        'Could not import faiss python package. '
        'Please install it with `pip install faiss-gpu` (for CUDA supported GPU) '
        'or `pip install faiss-cpu` (depending on Python version).')

class Faiss():

    def __init__(self, index: Any, chunks: List[Chunk], strategy:DistanceStrategy, k: int = 30):
        """Initialize with necessary components."""
        self.index = index
        self.chunks = chunks
        self.strategy = strategy
        self.k = k

    def similarity_search(self,
                          embedding: np.ndarray) -> List[Tuple[Chunk, float]]:
        """Return chunks most similar to query.

        Args:
            embedding: Embedding vector to look up chunk similar to.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. High score represents more similarity.
        """
        embedding = embedding.astype(np.float32)
        scores, indices = self.index.search(embedding, self.k)
        pairs = []
        for j, i in enumerate(indices[0]):
            if i == -1:
                # no enough chunks are returned.
                continue
            chunk = self.chunks[i]
            score = scores[0][j]

            if self.strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
                rel_score = DistanceStrategy.euclidean_relevance_score_fn(score)
            elif self.strategy == DistanceStrategy.MAX_INNER_PRODUCT:
                rel_score = DistanceStrategy.max_inner_product_relevance_score_fn(score)
            else:
                raise ValueError('self.strategy unset')
            pairs.append((chunk, rel_score))
        
        if len(pairs) >= 2:
            assert pairs[0][1] >= pairs[1][1]
        return pairs

    def similarity_search_with_query(self,
                                     embedder: Embedder,
                                     query: Query,
                                     threshold: float = -1):
        """Return chunks most similar to query.

        Args:
            query: Multimodal query.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. Lower score represents more similarity.
        """
        if query.text is None and query.image is None:
            raise ValueError(f'Input query is None')

        if query.text is None and query.image is not None:
            if not embedder.support_image:
                logger.info('Embedder not support image')
                return []

        np_feature = embedder.embed_query(text=query.text, path=query.image)
        pairs = self.similarity_search(embedding=np_feature)
        # ret = list(filter(lambda x: x[1] >= threshold, pairs))

        highest_score = -1.0
        ret = []
        for pair in pairs:
            if pair[1] >= threshold:
                ret.append(pair)
            if highest_score < pair[1]:
                highest_score = pair[1]

        if len(ret) < 1:
            logger.info('highest score {}, threshold {}'.format(highest_score, threshold))
        return ret

    @classmethod
    def split_by_batchsize(self, chunks: List[Chunk] = [], batchsize:int = 4):
        texts = [c for c in chunks if c.modal == 'text']
        images = [c for c in chunks if c.modal == 'image']

        block_text = []
        for i in range(0, len(texts), batchsize):
            block_text.append(texts[i:i+batchsize])

        block_image = []
        for i in range(0, len(images), batchsize):
            block_image.append(images[i:i+batchsize])
        return block_text, block_image

    @classmethod
    def build_index(self, np_feature: np.ndarray, distance_strategy: DistanceStrategy):
            dimension = np_feature.shape[-1]
            M = 16
            # max neighours for each node 
            # see https://github.com/facebookresearch/faiss/wiki/Indexing-1M-vectors
            if distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
                # index = faiss.IndexFlatL2(dimension)
                index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_L2)
            elif distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
                # index = faiss.IndexFlatIP(dimension)
                index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_IP)
            else:
                raise ValueError('Unknown distance {}'.format(distance_strategy))
            index.hnsw.efSearch = 128
            return index

    @classmethod
    def save_local(self, folder_path: str, chunks: List[Chunk],
                   embedder: Embedder) -> None:
        """Save FAISS index and store to disk.

        Args:
            folder_path: folder path to save.
            chunks: chunks to save.
            embedder: embedding function.
        """

        index = None
        batchsize = 1
        # max neighbours for each node

        try:
            batchsize_str = os.getenv('HUIXIANGDOU_BATCHSIZE')
            if batchsize_str is None:
                logger.info('`export HUIXIANGDOU_BATCHSIZE=64` for faster feature building.')
            else:
                batchsize = int(batchsize_str)
        except Exception as e:
            logger.error(str(e))
            batchsize = 1

        if batchsize == 1:
            for chunk in tqdm(chunks, 'chunks'):
                np_feature = None
                try:
                    if chunk.modal == 'text':
                        np_feature = embedder.embed_query(text=chunk.content_or_path)
                    elif chunk.modal == 'image':
                        np_feature = embedder.embed_query(path=chunk.content_or_path)
                    else:
                        raise ValueError(f'Unimplement chunk type: {chunk.modal}')
                except Exception as e:
                    logger.error('{}'.format(e))

                if np_feature is None:
                    logger.error('np_feature is None')
                    continue

                if index is None:
                    index = self.build_index(np_feature=np_feature, distance_strategy=embedder.distance_strategy)
                index.add(np_feature)
        else:
            # batching
            block_text, block_image = self.split_by_batchsize(chunks=chunks, batchsize=batchsize)
            for subchunks in tqdm(block_text, 'build_text'):
                np_features = embedder.embed_query_batch_text(chunks=subchunks)
                
                if index is None:
                    index = self.build_index(np_feature=np_features, distance_strategy=embedder.distance_strategy)
                index.add(np_features)

            for subchunks in tqdm(block_image, 'build_image'):
                for chunk in subchunks:
                    np_feature = embedder.embed_query(path=chunk.content_or_path)
                    if np_feature is None:
                        logger.error('np_feature is None')
                        continue

                    if index is None:
                        index = self.build_index(np_feature=np_feature, distance_strategy=embedder.distance_strategy)
                    index.add(np_feature)

        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)

        # save index separately since it is not picklable
        faiss.write_index(index, str(path / 'embedding.faiss'))

        # save chunks
        data = {
            'chunks': chunks,
            'strategy': str(embedder.distance_strategy)
        }
        with open(path / 'chunks_and_strategy.pkl', 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load_local(cls, folder_path: str) -> FAISS:
        """Load FAISS index and chunks from disk.

        Args:
            folder_path: folder path to load index and chunks from index.faiss
            index_name: for saving with a specific index file name
        """
        path = Path(folder_path)
        # load index separately since it is not picklable
        
        t1 = time.time()
        index = faiss.read_index(str(path / f'embedding.faiss'))
        strategy = DistanceStrategy.UNKNOWN
        t2 = time.time()
        
        # load docstore
        with open(path / f'chunks_and_strategy.pkl', 'rb') as f:
            data = pickle.load(f)
            chunks = data['chunks']
            strategy_str = data['strategy']

            if 'EUCLIDEAN_DISTANCE' in strategy_str:
                strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
            elif 'MAX_INNER_PRODUCT' in strategy_str:
                strategy = DistanceStrategy.MAX_INNER_PRODUCT
            else:
                raise ValueError('Unknown strategy type {}'.format(strategy_str))

        t3 = time.time()
        logger.info('Timecost for load dense, load faiss {} seconds, load chunk {} seconds'.format(int(t2-t1), int(t3-t2)))
        return cls(index, chunks, strategy)
