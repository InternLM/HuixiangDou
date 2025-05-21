
"""extract feature and search with user query."""
import json
import os
import pdb
import time

import numpy as np
import pytoml
from loguru import logger
from sklearn.metrics import precision_recall_curve
from typing import Any, Union, Tuple, List

from huixiangdou.primitive import Embedder, Faiss, LLMReranker, Query, Chunk, BM25Okapi, FileOperation, NamedEntity2Chunk
from .helper import QueryTracker
from .kg import KnowledgeGraph

class Retriever:
    """Tokenize and extract features from the project's chunks, for use in the
    reject pipeline and response pipeline."""

    def __init__(self, config_path: str, embedder: Any, reranker: Any,
                 work_dir: str, reject_throttle: float) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = reject_throttle

        self.embedder = embedder
        self.reranker = reranker
        self.faiss = None
        self.work_dir = work_dir

        if not os.path.exists(work_dir):
            logger.warning('!!!warning, workdir not exist.!!!')
            return

        # load prebuilt knowledge graph gpickle
        self.kg = KnowledgeGraph(config_path=config_path)

        # dense retrieval, load refusal-to-answer and response feature database
        dense_dir = os.path.join(work_dir, 'db_dense')
        if not os.path.exists(dense_dir):
            logger.warning('Dense retriever is None, skip load faiss')
            self.faiss = None
        else:
            self.faiss = Faiss.load_local(dense_dir)

        # sparse retrieval for python code
        sparse_dir = os.path.join(work_dir, 'db_sparse')
        if not os.path.exists(sparse_dir):
            logger.warning('Sparse retriever is None, skip load bm25')
            self.bm25 = None
        else:
            self.bm25 = BM25Okapi()
            self.bm25.load(sparse_dir)

    def update_throttle(self,
                        config_path: str = 'config.ini',
                        good_questions=[],
                        bad_questions=[]):
        """Update reject throttle based on positive and negative examples."""

        if len(good_questions) == 0 or len(bad_questions) == 0:
            raise Exception('good and bad question examples cat not be empty.')
        questions = good_questions + bad_questions
        predictions = []
        self.reject_throttle = -1

        for question in questions:
            _, score = self.is_relative(query=question,
                                       enable_kg=True, enable_threshold=False)
            predictions.append(max(0, score))

        labels = [1 for _ in range(len(good_questions))
                  ] + [0 for _ in range(len(bad_questions))]
        precision, recall, thresholds = precision_recall_curve(
            labels, predictions)

        # get the best index for sum(precision, recall)
        sum_precision_recall = precision[:-1] + recall[:-1]
        index_max = np.argmax(sum_precision_recall)
        optimal_threshold = max(thresholds[index_max], 0.0)

        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)
        config['feature_store']['reject_throttle'] = float(optimal_threshold)
        with open(config_path, 'w', encoding='utf8') as f:
            pytoml.dump(config, f)
        logger.info(
            f'The optimal threshold is: {optimal_threshold}, saved it to {config_path}'  # noqa E501
        )
        
    def inverted_index_retrieve(self, query: Union[Query, str], topk=100) -> List[Chunk]:
        """Retrieve chunks by named entity."""
        # reverted index retrieval
        
        reverted_index_dir = os.path.join(self.work_dir, 'db_reverted_index')
        if not os.path.exists(reverted_index_dir):
            return []
        
        # In async executor, `reverted_indexer` must lazy build and destroy
        reverted_indexer = NamedEntity2Chunk(reverted_index_dir)
        if type(query) is str:
            query = Query(text=query)
        
        entity_ids = reverted_indexer.parse(query.text)
        # chunk_id match counter
        chunk_id_score_list = reverted_indexer.get_chunk_ids(entity_ids=entity_ids)
        chunk_id_score_list = chunk_id_score_list[0:topk]
        del reverted_indexer
        
        chunks = []
        for chunk_id, ref_count in chunk_id_score_list:
            chunks.append(self.faiss.chunks[chunk_id])
        return chunks
        
    def text2vec_retrieve(self, query: Union[Query, str]) -> List[Chunk]:
        """Retrieve chunks by text2vec model or knowledge graph. 
        
        Args:
            query (Query): The multimodal question asked by the user.
        
        Returns:
            List[Chunk]: ref chunks.
        """
        if type(query) is str:
            query = Query(text=query)

        graph_delta = 0.0
        if self.kg.is_available():
            try:
                docs = self.kg.retrieve(query=query.text)
                graph_delta = 0.2 * min(100, len(docs)) / 100
            except Exception as e:
                logger.warning(str(e))
                logger.info('KG folder exists, but search failed, skip.')

        threshold = self.reject_throttle - graph_delta
        t1 = time.time()
        pairs = self.faiss.similarity_search_with_query(self.embedder,
                                                        query=query, threshold=threshold)
        t2 = time.time()
        logger.info('Timecost for text2vec_retrieve {} seconds'.format(float(t2-t1))) # 280ms
        chunks = [pair[0] for pair in pairs]
        return chunks
    
    def rerank_fuse(self, query: Union[Query, str], chunks: List[Chunk], context_max_length:int) -> Tuple[str, str, List[str], List[str]]:
        """Rerank chunks and extract content
        
        Args:
            chunks (List[Chunk]): filtered chunks.
        
        Returns:
            str: Joined chunks, or empty string
            str: Matched context from origin file content
            List[str]: References
        """
        if type(query) is str:
            query = Query(text=query)

        rerank_chunks = self.reranker.rerank(query=query.text,
                                      chunks=chunks)

        file_opr = FileOperation()
        # Add file text to context, until exceed `context_max_length`
        # If `file_length` > `context_max_length` (for example file_length=300 and context_max_length=100)
        # then centered on the chunk, read a length of 200
        splits = []
        context = ''
        references = []
        ref_texts = []
        for chunk in rerank_chunks:

            content = chunk.content_or_path
            splits.append(content)

            source = chunk.metadata['source']
            if '://' in source:
                # url
                file_text = content
            elif chunk.modal == 'text':
                file_text, error = file_opr.read(chunk.metadata['read'])
                if error is not None:
                    # read file failed, skip
                    continue
            elif chunk.modal == 'qa':
                file_text = chunk.metadata['qa']
     
            logger.info('target {} content length {}'.format(
                source, len(file_text)))
            if len(file_text) + len(context) > context_max_length:
                if source in references:
                    continue
                references.append(source)

                # add and break
                add_len = context_max_length - len(context)
                if add_len <= 0:
                    break
                content_index = file_text.find(content)
                if content_index == -1:
                    # content not in file_text
                    delta = '{}\n{}'.format(content, file_text[0:add_len - len(content) - 1])
                    context += delta
                    ref_texts.append(delta)
                else:
                    start_index = max(0,
                                      content_index - (add_len - len(content)))
                    delta = file_text[start_index:start_index + add_len]
                    context += delta
                    ref_texts.append(delta)
                break

            if source not in references:
                context += file_text
                context += '\n'
                references.append(source)
                ref_texts.append(file_text)

        context = context[0:context_max_length]
        logger.debug('query:{} files:{}'.format(query, references))
        return '\n'.join(splits), context, [
            os.path.basename(r) for r in references
        ], ref_texts

    def query(self,
              query: Union[Query, str],
              context_max_length: int = 40000,
              tracker: QueryTracker = None):
        """Processes a query and returns the best match from the vector store
        database. If the question is rejected, returns None.

        Args:
            query (Query): The multimodal question asked by the user.
            context_max_length (int): Max contenxt length for LLM.
            tracker (QueryTracker): Log tracker.

        Returns:
            str: Matched chunks, or empty string
            str: Matched context from origin file content
            List[str]: References 
        """
        if type(query) is str:
            query = Query(text=query)

        if query.text is None or len(query.text) < 1 or self.faiss is None:
            return None, None, []

        if len(query.text) > 512:
            logger.warning('input too long, truncate to 512')
            query.text = query.text[0:512]

        high_score_chunks = self.text2vec_retrieve(query=query)
        if tracker is not None:
            tracker.log('retrieve', [c.metadata['source'] for c in high_score_chunks])
    
        # compatible with old interface    
        return self.rerank_fuse(query=query, chunks=high_score_chunks, context_max_length=context_max_length)
    
    def is_relative(self,
                    query,
                    k=30,
                    enable_kg=True,
                    enable_threshold=True) -> Tuple[bool, float]:
        """Is input query relative with knowledge base. Return true or false, and the maxisum score"""
        if type(query) is str:
            query = Query(text=query)

        if query.text is None or len(query.text) < 1 or self.faiss is None:
            raise ValueError('input query {}, faiss {}'.format(query, self.faiss))

        graph_delta = 0.0
        if not enable_kg and self.kg.is_available():
            try:
                docs = self.kg.retrieve(query=query.text)
                graph_delta = 0.2 * min(100, len(docs)) / 100
            except Exception as e:
                logger.warning(str(e))
                logger.info('KG folder exists, but search failed, skip.')

        threshold = self.reject_throttle - graph_delta
        if enable_threshold:
            pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=threshold)
        else:
            pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=-1)
        if len(pairs) > 0:
            return True, pairs[0][1]
        return False, -1

class CacheRetriever:

    def __init__(self,
                 config_path: str,
                 cache_size: int = 4,
                 rerank_topn: int = 4):
        self.cache = dict()
        self.cache_size = cache_size
        with open(config_path, encoding='utf8') as f:
            fs_config = pytoml.load(f)['feature_store']

        # load text2vec and rerank model
        logger.info('loading test2vec and rerank models')
        self.embedder = Embedder(model_config=fs_config)
        self.reranker = LLMReranker(model_config=fs_config,
                                    topn=rerank_topn)

    def get(self,
            fs_id: str = 'default',
            config_path='config.ini',
            work_dir='workdir'):
        """Get database by id."""

        if fs_id in self.cache:
            self.cache[fs_id]['time'] = time.time()
            return self.cache[fs_id]['retriever']

        with open(config_path, encoding='utf8') as f:
            reject_throttle = pytoml.load(
                f)['feature_store']['reject_throttle']

        if len(self.cache) >= self.cache_size:
            # drop the oldest one
            del_key = None
            min_time = time.time()
            for key, value in self.cache.items():
                cur_time = value['time']
                if cur_time < min_time:
                    min_time = cur_time
                    del_key = key

            if del_key is not None:
                del_value = self.cache[del_key]
                self.cache.pop(del_key)
                del del_value['retriever']

        retriever = Retriever(config_path=config_path,
                              embedder=self.embedder,
                              reranker=self.reranker,
                              work_dir=work_dir,
                              reject_throttle=reject_throttle)
        self.cache[fs_id] = {'retriever': retriever, 'time': time.time()}
        return retriever

    def pop(self, fs_id: str):
        """Drop database by id."""

        if fs_id not in self.cache:
            return
        del_value = self.cache[fs_id]
        self.cache.pop(fs_id)
        # manually free memory
        del del_value
