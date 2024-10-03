# Copyright (c) OpenMMLab. All rights reserved.
"""Pipeline."""
import argparse
import asyncio
import datetime
import json
import os
import re
import time
import pdb
import copy
from abc import ABC, abstractmethod
from typing import List, Tuple, Union, Generator, AsyncGenerator

import pytoml
from loguru import logger

from huixiangdou.primitive import Query, Chunk

from .helper import ErrorCode, is_truth
from .llm_client import ChatClient
from .retriever import CacheRetriever
from .session import Session
from .web_search import WebSearch
from .prompt import (SCORING_QUESTION_TEMPLTE_CN, CR_CN, TOPIC_TEMPLATE_CN, SCORING_RELAVANCE_TEMPLATE_CN, GENERATE_TEMPLATE_CN, KEYWORDS_TEMPLATE_CN, PERPLESITY_TEMPLATE_CN, SECURITY_TEMAPLTE_CN)
from .prompt import (SCORING_QUESTION_TEMPLTE_EN, CR_EN, TOPIC_TEMPLATE_EN, SCORING_RELAVANCE_TEMPLATE_EN, GENERATE_TEMPLATE_EN, KEYWORDS_TEMPLATE_EN, PERPLESITY_TEMPLATE_EN, SECURITY_TEMAPLTE_EN)

class PreprocNode:
    """PreprocNode is for coreference resolution and scoring based on group
    chats.

    See https://arxiv.org/abs/2405.02817
    """

    def __init__(self, config: dict, llm: ChatClient, language: str):
        self.llm = llm
        self.enable_cr = config['worker']['enable_cr']

        if language == 'zh':
            self.SCORING_QUESTION_TEMPLTE = SCORING_QUESTION_TEMPLTE_CN
            self.CR = CR_CN
        else:
            self.SCORING_QUESTION_TEMPLTE = SCORING_QUESTION_TEMPLTE_EN
            self.CR = CR_EN

    def process(self, sess: Session) -> Generator[Session, None, None]:
        # check input
        if sess.query.text is None or len(sess.query.text) < 2:
            sess.code = ErrorCode.QUESTION_TOO_SHORT
            yield sess
            return

        prompt = self.SCORING_QUESTION_TEMPLTE.format(sess.query.text)
        truth, logs = is_truth(llm=self.llm,
                               prompt=prompt,
                               throttle=6,
                               default=3)
        sess.debug['PreprocNode_is_question'] = logs
        if not truth:
            sess.code = ErrorCode.NOT_A_QUESTION
            yield sess
            return

        if not self.enable_cr:
            yield sess
            return

        if len(sess.groupchats) < 1:
            logger.debug('history conversation empty, skip CR')
            yield sess
            return

        talks = []

        # rewrite user_id to ABCD..
        name_map = dict()
        name_int = ord('A')
        for msg in sess.groupchats:
            sender = msg.sender
            if sender not in name_map:
                name_map[sender] = chr(name_int)
                name_int += 1
            talks.append({'sender': name_map[sender], 'content': msg.query})

        talk_str = json.dumps(talks, ensure_ascii=False)
        prompt = self.CR.format(talk_str, sess.query.text)
        self.cr = self.llm.generate_response(prompt=prompt, backend='remote')
        if self.cr.startswith('“') and self.cr.endswith('”'):
            self.cr = self.cr[1:len(self.cr) - 1]
        if self.cr.startswith('"') and self.cr.endswith('"'):
            self.cr = self.cr[1:len(self.cr) - 1]
        sess.debug['cr'] = self.cr

        # rewrite query
        queries = [sess.query.text, self.cr]
        self.query = '\n'.join(queries)
        logger.debug('merge query and cr, query: {} cr: {}'.format(
            self.query, self.cr))


class Text2vecRetrieval:
    """Text2vecNode is for retrieve from knowledge base."""

    def __init__(self, config: dict, llm: ChatClient, retriever: CacheRetriever,
                 language: str):
        self.llm = llm
        self.retriever = retriever
        llm_config = config['llm']
        self.context_max_length = llm_config['server'][
            'local_llm_max_text_length']
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_llm_max_text_length']
        if language == 'zh':
            self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_CN
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CN
        else:
            self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_EN
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_EN
        self.max_length = self.context_max_length - 2 * len(
            self.GENERATE_TEMPLATE)

    async def process_coroutine(self, sess: Session) -> Session:
        """Try get reply with text2vec & rerank model."""

        # retrieve from knowledge base
        sess.parallel_chunks = await asyncio.to_thread(self.retriever.text2vec_retrieve, sess.query)
        return sess

class CodeRetrieval:
    """CodeNode is for retrieve from codebase."""

    def __init__(self, retriever: CacheRetriever):
        self.retriever = retriever

    async def process_coroutine(self, sess: Session) -> Session:
        """Try get reply with text2vec & rerank model."""

        # retrieve from knowledge base
        if self.retriever.bm25 is None:
            sess.parallel_chunks = []
            return sess
        
        sess.parallel_chunks = self.retriever.bm25_retrieve(query=sess.query)
        return sess

class WebSearchRetrieval:
    """WebSearchNode is for web search, use `ddgs` or `serper`"""

    def __init__(self, config: dict, config_path: str, llm: ChatClient,
                 language: str):
        self.llm = llm
        self.config_path = config_path
        self.enable = config['worker']['enable_web_search']
        llm_config = config['llm']
        self.context_max_length = llm_config['server'][
            'local_llm_max_text_length']
        self.language = language
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_llm_max_text_length']
        if language == 'zh':
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_CN
        else:
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_EN

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Try web search."""
        
        if not self.enable:
            logger.debug('disable web_search')
            yield sess
            return

        engine = WebSearch(config_path=self.config_path, language=self.language)

        prompt = self.KEYWORDS_TEMPLATE.format(sess.groupname, sess.query.text)
        search_keywords = self.llm.generate_response(prompt)
        search_keywords = search_keywords.replace('"', '')
        sess.debug['WebSearchNode_keywords'] = prompt

        articles, error = await asyncio.to_thread(engine.get, search_keywords, 4) 

        if error is not None:
            sess.code = ErrorCode.WEB_SEARCH_FAIL
            sess.parallel_chunks = []
            yield sess
            return

        if len(articles) < 1:
            sess.code = ErrorCode.NO_SEARCH_RESULT
            sess.parallel_chunks = []
            yield sess
            return

        for article_id, article in enumerate(articles):
            article.cut(0, self.context_max_length)
            c = Chunk(content_or_path=article.content, metadata={'source': article.source})
            sess.parallel_chunks.append(c)
        yield sess

    async def process_coroutine(self, sess: Session) -> Session:
        results = []
        async for value in self.process(sess=sess):
            results.append(value)
        return results[-1]


class ReduceGenerate:
    def __init__(self, config: dict, llm: ChatClient, retriever: CacheRetriever, language: str):
        self.llm = llm
        self.retriever = retriever
        if language == 'zh':
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CN
        else:
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_EN
        llm_config = config['llm']
        self.context_max_length = llm_config['server']['local_llm_max_text_length']
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server']['remote_llm_max_text_length']

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        question = sess.query.text 
        history = sess.history

        if len(sess.parallel_chunks) < 1:
            # direct chat
            async for part in self.llm.chat_stream(prompt=question, history=history):
                sess.delta = part
                yield sess
        else:
            _, context_str, references = self.retriever.rerank_fuse(query=sess.query, chunks=sess.parallel_chunks, context_max_length=self.context_max_length)
            sess.references = references
            prompt = self.GENERATE_TEMPLATE.format(context_str, sess.query.text)
            async for part in self.llm.chat_stream(prompt=prompt, history=history):
                sess.delta = part
                yield sess


class ParallelPipeline:
    """The ParallelPipeline class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A ChatClient instance that communicates with the language model.
        fs: An instance of FeatureStore for loading and querying features.
        config_path: A string indicating the path of the configuration file.
        config: A dictionary holding the configuration settings.
        context_max_length: An integer representing the maximum length of the context used by the language model.  # noqa E501

        Several template strings for various prompts are also defined.
    """

    def __init__(self, work_dir: str, config_path: str):
        """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
        """
        self.llm = ChatClient(config_path=config_path)
        self.retriever = CacheRetriever(config_path=config_path)

        self.config_path = config_path
        self.config = None
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')


    async def generate(self,
                 query: Union[Query, str],
                 history: List[Tuple[str]]=[], 
                 language: str='zh', 
                 enable_web_search: bool=True,
                 enable_code_search: bool=True):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (Union[Query,str]): User's multimodal query.
            history (str): Chat history.
            language (str): zh or en.
            enable_web_search (bool): enable web search or not, default value is True.
            enable_code_search (bool): enable code search or not, default value is True.

        Returns:
            Session: Sync generator, this function would yield session which contains:
                ErrorCode: An error code indicating the status of response generation.  # noqa E501
                str: Generated response to the user query.
                references: List for referenced filename or web url
        """
        # format input
        if type(query) is str:
            query = Query(text=query)

        # build input session
        sess = Session(query=query,
                       history=history,
                       log_path=self.config['worker']['save_path'])

        # build pipeline
        preproc = PreprocNode(self.config, self.llm, language)
        text2vec = Text2vecRetrieval(self.config, self.llm, self.retriever, language)
        coderetrieval = CodeRetrieval(self.retriever)
        websearch = WebSearchRetrieval(self.config, self.config_path, self.llm, language)
        reduce = ReduceGenerate(self.config, self.llm, self.retriever, language)

        direct_chat_states = [
            ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION,
            ErrorCode.NO_TOPIC, ErrorCode.UNRELATED
        ]

        # if not a good question, return
        for sess in preproc.process(sess):
            if sess.code in direct_chat_states:
                async for resp in reduce.process(sess):
                    yield resp
                return

        # parallel run text2vec, websearch and codesearch
        tasks = [text2vec.process_coroutine(copy.deepcopy(sess))]
        if enable_web_search:
            tasks.append(websearch.process_coroutine(copy.deepcopy(sess)))

        if enable_code_search:
            tasks.append(coderetrieval.process_coroutine(copy.deepcopy(sess)))

        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in task_results:
            if type(result) is Session:
                sess.parallel_chunks += result.parallel_chunks
                continue
            logger.error(result)

        async for sess in reduce.process(sess):
            yield sess
        return


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='SerialPipeline configuration path. Default value is config.ini')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    bot = ParallelPipeline(work_dir=args.work_dir, config_path=args.config_path)
    loop = asyncio.get_event_loop()
    queries = ['茴香豆是什么？', 'HuixiangDou 是什么？']

    for q in queries:
        async def wrap_async_as_coroutine():
            async for sess in bot.generate(query=q, history=[], enable_web_search=False):
                print(sess.delta, end='', flush=True)
                pass
            print('\n')
            print(sess.references)
        loop.run_until_complete(wrap_async_as_coroutine())
