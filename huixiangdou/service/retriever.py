# Copyright (c) OpenMMLab. All rights reserved.
"""extract feature and search with user query."""
import json
import os
import pdb
import time

import numpy as np
import pytoml
from BCEmbedding.tools.langchain import BCERerank
from langchain.retrievers import ContextualCompressionRetriever
from langchain.vectorstores.faiss import FAISS as Vectorstore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from loguru import logger
from sklearn.metrics import precision_recall_curve

from .file_operation import FileOperation
from .helper import QueryTracker
from .llm_reranker import LLMCompressionRetriever, LLMReranker
from .kg import KnowledgeGraph

class Retriever:
    """Tokenize and extract features from the project's documents, for use in
    the reject pipeline and response pipeline."""

    def __init__(self, config_path:str, embeddings, reranker, work_dir: str,
                 reject_throttle: float) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = reject_throttle
        self.rejecter = None
        self.retriever = None
        self.compression_retriever = None

        if not os.path.exists(work_dir):
            logger.warning('!!!warning, workdir not exist.!!!')
            return

        # load prebuilt knowledge graph gpickle
        self.kg = KnowledgeGraph(config_path=config_path)
        
        # dense retrieval, load refusal-to-answer and response feature database 
        rejection_path = os.path.join(work_dir, 'db_reject')
        retriever_path = os.path.join(work_dir, 'db_response')

        if os.path.exists(rejection_path):
            self.rejecter = Vectorstore.load_local(
                rejection_path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True)

        if os.path.exists(retriever_path):
            self.retriever = Vectorstore.load_local(
                retriever_path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True,
                distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT
            ).as_retriever(search_type='similarity',
                           search_kwargs={
                               'score_threshold': 0.15,
                               'k': 30
                           })

            if 'LLMReranker' in type(reranker).__name__:
                self.compression_retriever = LLMCompressionRetriever(
                    base_compressor=reranker, base_retriever=self.retriever)
            else:
                self.compression_retriever = ContextualCompressionRetriever(
                    base_compressor=reranker, base_retriever=self.retriever)

        if self.rejecter is None:
            logger.warning('rejecter is None')
        if self.retriever is None:
            logger.warning('retriever is None')

    def is_relative(self, question, k=30, disable_throttle=False, disable_graph=False):
        """If no search results below the threshold can be found from the
        database, reject this query."""

        if self.rejecter is None:
            return False, []

        if disable_throttle:
            # for searching throttle during update sample
            docs_with_score = self.rejecter.similarity_search_with_relevance_scores(
                question, k=1)
            if len(docs_with_score) < 1:
                return False, docs_with_score
            return True, docs_with_score
        else:
            # for retrieve result
            # if no chunk passed the throttle, give the max
            graph_delta = 0.0
            if not disable_graph and self.kg.is_available():
                candidates = self.kg.retrieve(query=question)
                graph_delta = 0.2 * min(100, len(candidates)) / 100

            docs_with_score = self.rejecter.similarity_search_with_relevance_scores(
                question, k=k)
            ret = []
            max_score = -1
            top1 = None
            for (doc, score) in docs_with_score:
                if score >= self.reject_throttle - graph_delta:
                    ret.append(doc)
                if score > max_score:
                    max_score = score
                    top1 = (doc, score)
            relative = True if len(ret) > 0 else False
            return relative, [top1]

    def update_throttle(self,
                        config_path: str = 'config.ini',
                        good_questions=[],
                        bad_questions=[]):
        """Update reject throttle based on positive and negative examples."""

        if len(good_questions) == 0 or len(bad_questions) == 0:
            raise Exception('good and bad question examples cat not be empty.')
        questions = good_questions + bad_questions
        predictions = []
        for question in questions:
            self.reject_throttle = -1
            _, docs = self.is_relative(question=question,
                                       disable_throttle=True)
            score = docs[0][1]
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

    def query(self,
              question: str,
              context_max_length: int = 16000,
              tracker: QueryTracker = None):
        """Processes a query and returns the best match from the vector store
        database. If the question is rejected, returns None.

        Args:
            question (str): The question asked by the user.

        Returns:
            str: The best matching chunk, or None.
            str: The best matching text, or None
        """
        if question is None or len(question) < 1:
            return None, None, []

        if len(question) > 512:
            logger.warning('input too long, truncate to 512')
            question = question[0:512]

        chunks = []
        context = ''
        references = []

        relative, docs = self.is_relative(question=question)
        # logger.debug('retriever.docs {}'.format(docs))
        if not relative:
            if len(docs) > 0:
                references.append(docs[0][0].metadata['source'])
            return None, None, references

        docs = self.compression_retriever.get_relevant_documents(question)
        if tracker is not None:
            tracker.log('retrieve', [doc.metadata['source'] for doc in docs])

        # add file text to context, until exceed `context_max_length`

        file_opr = FileOperation()
        for idx, doc in enumerate(docs):
            chunk = doc.page_content
            chunks.append(chunk)

            if 'read' not in doc.metadata:
                logger.error(
                    'If you are using the version before 20240319, please rerun `python3 -m huixiangdou.service.feature_store`'
                )
                raise Exception('huixiangdou version mismatch')
            file_text, error = file_opr.read(doc.metadata['read'])
            if error is not None:
                # read file failed, skip
                continue

            source = doc.metadata['source']
            logger.info('target {} file length {}'.format(
                source, len(file_text)))
            if len(file_text) + len(context) > context_max_length:
                if source in references:
                    continue
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

            if source not in references:
                context += file_text
                context += '\n'
                references.append(source)

        context = context[0:context_max_length]
        logger.debug('query:{} top1 file:{}'.format(question, references[0]))
        return '\n'.join(chunks), context, [
            os.path.basename(r) for r in references
        ]


class CacheRetriever:

    def __init__(self,
                 config_path: str,
                 cache_size: int = 4,
                 rerank_topn: int = 10):
        self.cache = dict()
        self.cache_size = cache_size
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)['feature_store']
            embedding_model_path = config['embedding_model_path']
            reranker_model_path = config['reranker_model_path']

        # load text2vec and rerank model
        logger.info('loading test2vec and rerank models')
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_path,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={
                'batch_size': 1,
                'normalize_embeddings': True
            })
        self.embeddings.client = self.embeddings.client.half()

        if self.use_llm_reranker(reranker_model_path):
            self.reranker = LLMReranker(model_name_or_path=reranker_model_path,
                                        topn=rerank_topn)
        else:
            logger.warning(
                'For higher rerank precision, we strong advice using `BAAI/bge-reranker-v2-minicpm-layerwise`'
            )
            reranker_args = {
                'model': reranker_model_path,
                'top_n': rerank_topn,
                'device': 'cuda',
                'use_fp16': True
            }
            self.reranker = BCERerank(**reranker_args)

    def use_llm_reranker(self, model_path):
        config_path = os.path.join(model_path, 'config.json')
        if not os.path.exists(config_path):
            if 'bge-reranker-v2-minicpm-layerwise' in config_path.lower():
                return True
            return False
        try:
            with open(config_path) as f:
                if 'bge-reranker-v2-minicpm-layerwise' in json.loads(
                        f.read())['_name_or_path']:
                    return True
        except Exception as e:
            logger.warning(e)
        return False

    def get(self,
            fs_id: str = 'default',
            config_path='config.ini',
            work_dir='workdir'):
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
                              embeddings=self.embeddings,
                              reranker=self.reranker,
                              work_dir=work_dir,
                              reject_throttle=reject_throttle)
        self.cache[fs_id] = {'retriever': retriever, 'time': time.time()}
        if retriever.rejecter is None:
            logger.warning('retriever.rejecter is None, check workdir')
        return retriever

    def pop(self, fs_id: str):
        if fs_id not in self.cache:
            return
        del_value = self.cache[fs_id]
        self.cache.pop(fs_id)
        # manually free memory
        del del_value
