# Copyright (c) OpenMMLab. All rights reserved.
from __future__ import annotations

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


# heavily modified from langchain
def dependable_faiss_import(no_avx2: Optional[bool] = None) -> Any:
    """Import faiss if available, otherwise raise error. If FAISS_NO_AVX2
    environment variable is set, it will be considered to load FAISS with no
    AVX2 optimization.

    Args:
        no_avx2: Load FAISS strictly with no AVX2 optimization
            so that the vectorstore is portable and compatible with other devices.
    """
    if no_avx2 is None and 'FAISS_NO_AVX2' in os.environ:
        no_avx2 = bool(os.getenv('FAISS_NO_AVX2'))

    try:
        if no_avx2:
            from faiss import swigfaiss as faiss
        else:
            import faiss
    except ImportError:
        raise ImportError(
            'Could not import faiss python package. '
            'Please install it with `pip install faiss-gpu` (for CUDA supported GPU) '
            'or `pip install faiss-cpu` (depending on Python version).')
    return faiss


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
        faiss = dependable_faiss_import()

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

        ret = []
        for pair in pairs:
            if pair[1] >= threshold:
                ret.append(pair)
        return ret

    @classmethod
    def save_local(self, folder_path: str, chunks: List[Chunk],
                   embedder: Embedder) -> None:
        """Save FAISS index and store to disk.

        Args:
            folder_path: folder path to save.
            chunks: chunks to save.
            embedder: embedding function.
        """

        faiss = dependable_faiss_import()
        index = None

        for chunk in tqdm(chunks):
            if chunk.modal == 'text':
                np_feature = embedder.embed_query(text=chunk.content_or_path)
            elif chunk.modal == 'image':
                np_feature = embedder.embed_query(path=chunk.content_or_path)
            else:
                raise ValueError(f'Unimplement chunk type: {chunk.modal}')

            if index is None:
                dimension = np_feature.shape[-1]

                if embedder.distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
                    index = faiss.IndexFlatL2(dimension)
                elif embedder.distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
                    index = faiss.IndexFlatIP(dimension)

            index.add(np_feature)

        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)

        # save index separately since it is not picklable
        faiss.write_index(index, str(path / 'embedding.faiss'))

        # save chunks
        with open(path / 'chunk.pkl', 'wb') as f:
            pickle.dump(chunks, f)

    @classmethod
    def load_local(cls, folder_path: str) -> FAISS:
        """Load FAISS index and chunks from disk.

        Args:
            folder_path: folder path to load index and chunks from index.faiss
            index_name: for saving with a specific index file name
        """
        path = Path(folder_path)
        # load index separately since it is not picklable
        faiss = dependable_faiss_import()
        index = faiss.read_index(str(path / f'embedding.faiss'))
        strategy = DistanceStrategy.UNKNOWN
        
        if type(index) is faiss.IndexFlatL2:
            strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
        elif type(index) is faiss.IndexFlatIP:
            strategy = DistanceStrategy.MAX_INNER_PRODUCT
        else:
            raise ValueError('Cannot decide self.index type')

        # load docstore
        with open(path / f'chunk.pkl', 'rb') as f:
            chunks = pickle.load(f)

        return cls(index, chunks, strategy)
