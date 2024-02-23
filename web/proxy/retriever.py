# Copyright (c) OpenMMLab. All rights reserved.
"""extract feature and search with user query."""
import argparse
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np
from BCEmbedding.tools.langchain import BCERerank
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.text_splitter import (MarkdownHeaderTextSplitter,
                                     MarkdownTextSplitter,
                                     RecursiveCharacterTextSplitter)
from langchain.vectorstores.faiss import FAISS as Vectorstore
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
from loguru import logger
from sklearn.metrics import precision_recall_curve
from torch.cuda import empty_cache


class Retriever:
    """Tokenize and extract features from the project's documents, for use in
    the reject pipeline and response pipeline."""

    def __init__(self, embeddings, reranker, work_dir: str,
                 reject_throttle: float) -> None:
        """Init with model device type and config."""
        self.reject_throttle = reject_throttle
        self.rejecter = Vectorstore.load_local(os.path.join(
            work_dir, 'db_reject'),
                                               embeddings=self.embeddings)
        self.retriever = Vectorstore.load_local(
            os.path.join(work_dir, 'db_response'),
            embeddings=embeddings,
            distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT).as_retriever(
                search_type='similarity',
                search_kwargs={
                    'score_threshold': 0.2,
                    'k': 30
                })
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.reranker, base_retriever=self.retriever)

    def cos_similarity(self, v1: list, v2: list):
        """Compute cos distance."""
        num = float(np.dot(v1, v2))
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        return 0.5 + 0.5 * (num / denom) if denom != 0 else 0

    def distance(self, text1: str, text2: str):
        """Compute feature distance."""
        feature1 = self.embeddings.embed_query(text1)
        feature2 = self.embeddings.embed_query(text2)
        return self.cos_similarity(feature1, feature2)

    def is_reject(self, question, k=20, disable_throttle=False):
        """If no search results below the threshold can be found from the
        database, reject this query."""
        docs = []
        if disable_throttle:
            docs = self.rejecter.similarity_search_with_relevance_scores(
                question, k=1)
        else:
            docs = self.rejecter.similarity_search_with_relevance_scores(
                question, k=k, score_threshold=self.reject_throttle)
        if len(docs) < 1:
            return True, docs
        return False, docs

    def query(self, question: str, context_max_length: int = 16000):
        """Processes a query and returns the best match from the vector store
        database. If the question is rejected, returns None.

        Args:
            question (str): The question asked by the user.

        Returns:
            str: The best matching chunk, or None.
            str: The best matching text, or None
        """
        if question is None or len(question) < 1:
            return None, None

        reject, docs = self.is_reject(question=question)
        if reject:
            return None, None

        docs = self.compression_retriever.get_relevant_documents(question)
        chunks = []
        context = ''
        references = []
        # for doc in docs:
        # logger.debug(('db', doc.metadata, question))
        # chunks.append(doc.page_content)
        # filepath = doc.metadata['source']
        # if filepath not in files:
        #     files.append(filepath)

        # add file content to context, within `context_max_length`
        for idx, doc in enumerate(docs):
            chunk = doc.page_content
            chunks.append(chunk)

            file_text = ''
            source = doc.metadata['source']
            with open(source) as f:
                file_text = f.read()
            if len(file_text) + len(context) > context_max_length:
                references.append(source)
                # add and break
                add_len = context_max_length - len(context)
                if add_len <= 0:
                    break
                chunk_index = file_text.find(chunk)
                if chunk_index == -1:
                    # chunk not in file_text
                    context += chunk
                    context += '\n'
                    context += file_text[0:add_len - len(chunk) - 1]
                else:
                    start_index = max(0, chunk_index - (add_len - len(chunk)))
                    context += file_text[start_index:start_index + add_len]
                break
            context += '\n'
            context += file_text

        assert (len(context) <= context_max_length)
        logger.debug('query:{} top1 file:{}'.format(question, references[0]))
        return '\n'.join(chunks), context, references
