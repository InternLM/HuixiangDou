"""Pipeline."""
import argparse
import datetime
import json
import time
import pdb
from abc import ABC, abstractmethod
from typing import List, Union, AsyncGenerator, Tuple

import pytoml
from loguru import logger

from huixiangdou.primitive import Query

from .helper import ErrorCode, is_truth
from .llm import LLM
from .retriever import CacheRetriever, Retriever
from .session import Session
from .web_search import WebSearch
from .prompt import (INTENTION_TEMPLATE_CN, TOPIC_TEMPLATE_CN, SCORING_RELAVANCE_TEMPLATE_CN, KEYWORDS_TEMPLATE_CN, PERPLESITY_TEMPLATE_CN, SECURITY_TEMAPLTE_CN, GENERATE_TEMPLATE_CITATION_HEAD_CN)
from .prompt import (INTENTION_TEMPLATE_EN, TOPIC_TEMPLATE_EN, SCORING_RELAVANCE_TEMPLATE_EN, KEYWORDS_TEMPLATE_EN, PERPLESITY_TEMPLATE_EN, SECURITY_TEMAPLTE_EN, GENERATE_TEMPLATE_CITATION_HEAD_EN)
from .prompt import CitationGeneratePrompt

class Node(ABC):
    """Base abstract for compute graph."""

    @abstractmethod
    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        pass

class PreprocNode:
    """PreprocNode is for coreference resolution and scoring based on group
    chats.

    See https://arxiv.org/abs/2405.02817
    """

    def __init__(self, config: dict, llm: LLM, language: str):
        self.llm = llm

        if language == 'zh':
            self.INTENTION_TEMPLATE = INTENTION_TEMPLATE_CN
        else:
            self.INTENTION_TEMPLATE = INTENTION_TEMPLATE_EN

    async def process(self, sess: Session) -> AsyncGenerator[Session, Session]:
        assert isinstance(sess.history, list), "sess.history is not list"
        if len(sess.history) > 0:
            yield sess
            return

        prompt = self.INTENTION_TEMPLATE.format(sess.query.text)
        json_str = await self.llm.chat(prompt=prompt)
        sess.debug['PreprocNode_intention_response'] = json_str
        logger.info('intention response {}'.format(json_str))
        try:
            if json_str.startswith('```json'):
                json_str = json_str[len('```json'):]

            if json_str.endswith('```'):
                json_str = json_str[0:-3]
            
            json_obj = json.loads(json_str)
            intention = json_obj['intention']
            if intention is not None:
                intention = intention.lower()
            else:
                intention = 'undefine'
            topic = json_obj['topic']
            if topic is not None:
                topic = topic.lower()
            else:
                topic = 'undefine'
            
            for block_intention in ['问候', 'greeting', 'undefine']:
                if block_intention in intention:
                    sess.code = ErrorCode.NOT_A_QUESTION
                    yield sess
                    return

            for block_topic in ['身份', 'identity', 'undefine']:
                if block_topic in topic:
                    sess.code = ErrorCode.NOT_A_QUESTION
                    yield sess
                    return
        except Exception as e:
            logger.error(str(e))

class Text2vecNode(Node):
    """Text2vecNode is for retrieve from knowledge base."""

    def __init__(self, config: dict, llm: LLM, retriever: Retriever,
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
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
        else:
            self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_EN
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
        self.max_length = self.context_max_length - 2 * len(
            self.GENERATE_TEMPLATE)
        self.language = language

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Try get reply with text2vec & rerank model."""

        # retrieve from knowledge base
        sess.chunk, sess.knowledge, sess.references, context_texts = self.retriever.query(sess.query,
            context_max_length=self.max_length)
        sess.debug['Text2vecNode_chunk'] = sess.chunk
        if sess.knowledge is None:
            sess.code = ErrorCode.UNRELATED
            yield sess
            return

        yield sess

        # get relavance between query and knowledge base
        prompt = self.SCORING_RELAVANCE_TEMPLATE.format(
            sess.query.text, sess.chunk)
        truth, logs = await is_truth(llm=self.llm,
                               prompt=prompt,
                               throttle=5,
                               default=10)
        sess.debug['Text2vecNode_chunk_relavance'] = logs
        if not truth:
            yield sess
            return

        # answer the question
        citation = CitationGeneratePrompt(self.language)
        prompt = citation.build(texts=context_texts, question=sess.query.text)
        response = await self.llm.chat(prompt=prompt,
                                              history=sess.history)

        sess.code = ErrorCode.SUCCESS
        sess.response = response
        yield sess


class WebSearchNode(Node):
    """WebSearchNode is for web search, use `ddgs` or `serper`"""

    def __init__(self, config: dict, config_path: str, llm: LLM,
                 language: str):
        self.llm = llm
        self.config_path = config_path
        self.enable = config['worker']['enable_web_search']
        llm_config = config['llm']
        self.context_max_length = llm_config['server'][
            'local_llm_max_text_length']
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_llm_max_text_length']
        if language == 'zh':
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_CN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
        else:
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_EN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
        self.max_length = self.context_max_length - 2 * len(
            self.GENERATE_TEMPLATE)
        self.language = language

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Try web search."""
        
        if not self.enable:
            logger.debug('disable web_search')
            yield sess
            return

        engine = WebSearch(config_path=self.config_path)

        prompt = self.KEYWORDS_TEMPLATE.format(sess.groupname, sess.query.text)
        search_keywords = await self.llm.chat(prompt)
        sess.debug['WebSearchNode_keywords'] = prompt
        articles, error = engine.get(query=search_keywords, max_article=2)

        if error is not None:
            sess.code = ErrorCode.WEB_SEARCH_FAIL
            yield sess
            return

        texts = []
        for article_id, article in enumerate(articles):
            article.cut(0, self.max_length)
            sess.web_knowledge += '\n'
            sess.web_knowledge += article.content
            sess.references.append(article.source)
            
            texts.append(article.content)

        sess.web_knowledge = sess.web_knowledge[0:self.max_length].strip()
        if len(sess.web_knowledge) < 1:
            sess.code = ErrorCode.NO_SEARCH_RESULT
            yield sess
            return

        citation = CitationGeneratePrompt(self.language)
        prompt = citation.build(texts=texts, question=sess.query.text)
        sess.response = await self.llm.chat(prompt=prompt, history=sess.history)
        sess.code = ErrorCode.SUCCESS
        yield sess

class SecurityNode(Node):
    """SecurityNode is for result check."""

    def __init__(self, llm: LLM, language: str):
        self.llm = llm
        if language == 'zh':
            self.PERPLESITY_TEMPLATE = PERPLESITY_TEMPLATE_CN
            self.SECURITY_TEMAPLTE = SECURITY_TEMAPLTE_CN
        else:
            self.PERPLESITY_TEMPLATE = PERPLESITY_TEMPLATE_EN
            self.SECURITY_TEMAPLTE = SECURITY_TEMAPLTE_EN

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Check result with security."""
        if len(sess.response) < 1:
            sess.code = ErrorCode.BAD_ANSWER
            yield sess
            return
        prompt = self.PERPLESITY_TEMPLATE.format(sess.query.text,
                                                 sess.response)
        truth, logs = await is_truth(llm=self.llm,
                               prompt=prompt,
                               throttle=9,
                               default=0)
        sess.debug['SecurityNode_qa_perplex'] = logs
        if truth:
            sess.code = ErrorCode.BAD_ANSWER
            yield sess
            return

        prompt = self.SECURITY_TEMAPLTE.format(sess.response)
        truth, logs = await is_truth(llm=self.llm,
                               prompt=prompt,
                               throttle=8,
                               default=0)
        sess.debug['SecurityNode_template'] = logs
        if truth:
            sess.code = ErrorCode.SECURITY
            yield sess


class SerialPipeline:
    """The SerialPipeline class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A LLM instance that communicates with the language model.
        fs: An instance of FeatureStore for loading and querying features.
        config_path: A string indicating the path of the configuration file.
        config: A dictionary holding the configuration settings.
        language: A string indicating the language of the chat, default is 'zh' (Chinese).  # noqa E501
        context_max_length: An integer representing the maximum length of the context used by the language model.  # noqa E501

        Several template strings for various prompts are also defined.
    """

    def __init__(self, work_dir: str, config_path: str, language: str = 'zh'):
        """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
            language (str, optional): Specifies the language to be used. Defaults to 'zh' (Chinese).  # noqa E501
        """
        self.llm = LLM(config_path=config_path)
        self.retriever = CacheRetriever(config_path=config_path).get()

        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

    def notify_badcase(self):
        """Receiving revert command means the current threshold is too low, use
        higher one."""
        delta = max(0, 1 - self.retriever.reject_throttle) * 0.02
        logger.info(
            'received badcase, use bigger reject_throttle. Current {}, delta {}'
            .format(self.retriever.reject_throttle, delta))

        # this throttle also means quality, cannot exceed 0.5
        self.retriever.reject_throttle = min(
            self.retriever.reject_throttle + delta, 0.5)
        with open('throttle', 'w') as f:
            f.write(str(self.retriever.reject_throttle))

    def work_time(self):
        """If worktime enabled, determines the current time falls within the
        scheduled working hours of the chat assistant.

        Returns:
            bool: True if the current time is within working hours, otherwise False.  # noqa E501
        """

        time_config = self.config['worker']['time']
        if 'enable' in time_config:
            # work time not enabled, start work
            if not time_config['enable']:
                return True

        beginWork = datetime.datetime.now().strftime(
            '%Y-%m-%d') + ' ' + time_config['start']
        endWork = datetime.datetime.now().strftime(
            '%Y-%m-%d') + ' ' + time_config['end']
        beginWorkSeconds = time.time() - time.mktime(
            time.strptime(beginWork, '%Y-%m-%d %H:%M:%S'))
        endWorkSeconds = time.time() - time.mktime(
            time.strptime(endWork, '%Y-%m-%d %H:%M:%S'))

        if int(beginWorkSeconds) > 0 and int(endWorkSeconds) < 0:
            if not time_config['has_weekday']:
                return True

            if int(datetime.datetime.now().weekday()) in range(7):
                return True
        return False

    async def generate(self,
                 query: Union[Query, str],
                 history: List[Tuple[str, str]] = [],
                 groupname: str = '',
                 groupchats: List[str] = []):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (Union[Query,str]): User's multimodal query.
            history (str): Chat history.
            groupname (str): The group name in which user asked the query.
            groupchats (List[str]): The history conversation in group before user query.

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
                       groupname=groupname,
                       log_path=self.config['worker']['save_path'],
                       groupchats=groupchats)

        # build pipeline
        preproc = PreprocNode(self.config, self.llm, self.language)
        text2vec = Text2vecNode(self.config, self.llm, self.retriever,
                                self.language)
        websearch = WebSearchNode(self.config, self.config_path, self.llm,
                                  self.language)
        check = SecurityNode(self.llm, self.language)
        pipeline = [preproc, text2vec, websearch]

        # run
        exit_states = [
            ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION,
            ErrorCode.NO_TOPIC, ErrorCode.UNRELATED
        ]
        for node in pipeline:

            async for sess in node.process(sess):
                yield sess

            # unrelated to knowledge base or bad input, exit
            if sess.code in exit_states:
                break

            if sess.code == ErrorCode.SUCCESS:
                async for sess in check.process(sess):
                    yield sess

            # check success, return
            if sess.code == ErrorCode.SUCCESS:
                break

        logger.debug(sess.debug)
        return sess
        # return sess.code, sess.response, sess.references

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
    bot = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    queries = ['茴香豆是怎么做的']
    for example in queries:
        print(bot.generate(query=example, history=[], groupname=''))
