# Copyright (c) OpenMMLab. All rights reserved.
"""Pipeline."""
import argparse
import datetime
import re
import time
import os
import json

from abc import ABC, abstractmethod
import pytoml
from openai import OpenAI
from loguru import logger

from .helper import ErrorCode, QueryTracker
from .llm_client import ChatClient
from .retriever import CacheRetriever, Retriever
from .sg_search import SourceGraphProxy
from .web_search import WebSearch
from .primitive import is_truth

class Session:
    """
    For compute graph, `session` takes all parameter.
    """
    def __init__(self, query:str, history: list, groupname: str, log_path: str = 'logs/generate.jsonl', groupchats:list=[]):
        self.query = query
        self.history = history
        self.groupname = groupname
        self.groupchats = groupchats

        # init
        self.response = ''
        self.references = []
        self.topic = ''
        self.code = ErrorCode.INIT

        # coreference resolution results
        self.cr = ''

        # text2vec results
        self.chunk = ''
        self.knowledge = ''

        # web search results
        self.web_knowledge = ''

        # source graph search results
        self.sg_knowledge = ''

        # debug logs
        self.debug = dict()
        self.log_path = log_path

    def __del__(self):
        dirname = os.path.dirname(self.log_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        with open(self.log_path, 'a') as f:
            json_str = json.dumps(self.debug, indent=2, ensure_ascii=False)
            f.write(json_str)
            f.write('\n')

    
class Node(ABC):
    """Base abstractfor compute graph."""
    @abstractmethod
    def process(self, sess: Session):
        pass


class PreprocNode(Node):
    """
    PreprocNode is for coreference resolution and scoring based on group chats.
    See https://arxiv.org/abs/2405.02817
    """
    def __init__(self, config: dict, llm: ChatClient, language: str):
        self.llm = llm
        self.enable_cr = config['worker']['enable_cr']
        self.cr_client = OpenAI(
            base_url=config['coreference_resolution']['base_url'],
            api_key=config['coreference_resolution']['api_key']
        )

        if language == 'zh':
            self.SCORING_QUESTION_TEMPLTE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
            self.CR_NEED = """群聊场景中“这”、“它”、“哪”等代词需要查看上下文和其他用户的回复才能确定具体指什么，请完成群聊场景代词替换任务。
以下是历史对话，可能有多个人的发言：
{}
输入内容：{}
输入内容的信息是否完整，是否需要从历史对话中提取代词或宾语来替代 content 中的一部分词汇？ A：不需要提取，信息完整  B：需要  C：不知道 
一步步分析，首先历史消息包含哪些话题；其次哪个话题与问题最相关；如果都不相关就不提取。"""
            self.CR = """请根据历史对话，重写输入的文本。
以下是历史对话，可能有多个人的发言：
{}
输入的文本
“{}”
一步步分析，首先历史对话包含哪些话题；其次哪个话题与输入文本中的代词最相关；用相关的话题，替换输入中的代词和缺失的部分。直接返回重写后的文本不要解释。"""

        else:
            self.SCORING_QUESTION_TEMPLTE = '"{}"\nPlease read the content above carefully and judge whether the sentence is a thematic question. Rate it on a scale of 0-10. Only provide the score, no explanation.\nThe criteria are as follows: a sentence gets 10 points if it has a subject, predicate, object and is a question; points are deducted for missing subject, predicate or object; declarative sentences get 0 points; sentences that are not questions also get 0 points. Just give the score, no explanation.'
            self.CR_NEED = """In group chat scenarios, pronouns such as "this," "it," and "which" require examination of the context and other users' responses to determine their specific reference. Please complete the pronoun substitution task in the group chat scenario.
Here is the historical conversation, which may contain multiple people's statements:
{}
Input content: {}
Is the information in the input content complete, and is it necessary to extract pronouns or objects from the historical conversation to replace part of the vocabulary in content? A: No extraction needed, information is complete B: Necessary C: Uncertain
Analyze step by step, first identify which topics are included in the historical messages; second, determine which topic is most relevant to the question; if none are relevant, do not extract."""
            self.CR = """Please rewrite the input text based on the historical conversation.
Here is the historical conversation, which may include statements from multiple individuals:
{}
The input text
"{}"
Analyze step by step, first identify what topics are included in the historical conversation; secondly, determine which topic is most relevant to the pronoun in the input text; replace the pronoun and missing parts in the input with the relevant topic. Return the rewritten text directly without explanation."""

# self.CR_CHECK = """请判断用户意图，这位用户在做单选题，单选题答案有 3 个， A：不需要提取，信息完整  B：需要  C：不知道。
# 用户输入：
# {}
# 用户的答案是？不要解释，直接给 ABC 选项结果。"""

    def process(self, sess: Session):
        # check input
        if sess.query is None or len(sess.query) < 6:
            sess.code = ErrorCode.QUESTION_TOO_SHORT
            return

        prompt = self.SCORING_QUESTION_TEMPLTE.format(sess.query)
        truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=6, default=3)
        sess.debug['PreprocNode_is_question'] = logs
        if not truth:
            sess.code = ErrorCode.NOT_A_QUESTION
            return

        if not self.enable_cr:
            return
        
        if len(sess.groupchats) < 1:
            logger.debug('history conversation empty, skip CR')
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
            talks.append({
                'sender': name_map[sender],
                'content': msg.query
            })
        
        talk_str = json.dumps(talks, ensure_ascii=False)
        prompt = self.CR_NEED.format(talk_str, sess.query)

        # need coreference resolution or not
        response = ''
        try:
            completion = self.cr_client.chat.completions.create(model='coref-res',messages=[{"role": "user", "content": prompt}])
            response = completion.choices[0].message.content.lower()
        except Exception as e:
            logger.error(str(e))
            return
        sess.debug['PreprocNode_need_cr'] = response
        need_cr = False
        
        if response.startswith('b') or response == '需要':
            need_cr = True
        else:
            for sentence in ['因此需要', '因此选择b', '需要进行指代消解', '需要指代消解', 'b：需要']:
                if sentence in response:
                    need_cr = True
                    break

        if not need_cr:
            return

        prompt = self.CR.format(talk_str, sess.query)
        self.cr = self.llm.generate_response(prompt=prompt, backend='remote')
        if self.cr.startswith('“') and self.cr.endswith('”'):
            self.cr = self.cr[1:len(self.cr)-1]
        if self.cr.startswith('"') and self.cr.endswith('"'):
            self.cr = self.cr[1:len(self.cr)-1]
        sess.debug['cr'] = self.cr

        # rewrite query    
        queries = [sess.query, self.cr]
        self.query = '\n'.join(queries)
        logger.debug('merge query and cr, query: {} cr: {}'.format(self.query, self.cr))


class BCENode(Node):
    """
    BCENode is for retrieve from knowledge base
    """
    def __init__(self, config:dict, llm: ChatClient, retriever: Retriever, language: str):
        self.llm = llm
        self.retriever = retriever
        llm_config = config['llm']
        self.context_max_length = llm_config['server']['local_llm_max_text_length']
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server']['remote_llm_max_text_length']
        if language == 'zh':
            self.TOPIC_TEMPLATE = '告诉我这句话的主题，不要丢失主语和宾语，直接说主题不要解释：“{}”'
            self.SCORING_RELAVANCE_TEMPLATE = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'  # noqa E501
            self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'  # noqa E501
        else:
            self.TOPIC_TEMPLATE = 'Tell me the theme of this sentence, just state the theme without explanation: "{}"'  # noqa E501
            self.SCORING_RELAVANCE_TEMPLATE = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'  # noqa E501
            self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'  # noqa E501
        self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)

    def process(self, sess: Session):
        """
        Try get reply with text2vec & rerank model
        """
        
        # get query topic
        prompt = self.TOPIC_TEMPLATE.format(sess.query)
        sess.topic = self.llm.generate_response(prompt)
        for prefix in ['主题：', '这句话的主题是：']:
            if sess.topic.startswith(prefix):
                sess.topic = sess.topic[len(prefix):]

        sess.debug['BCENode_topic'] = sess.topic
        if len(sess.topic) < 2:
            # topic too short, return
            sess.code = ErrorCode.NO_TOPIC
            return

        # retrieve from knowledge base
        sess.chunk, sess.knowledge, sess.references = self.retriever.query(sess.topic, context_max_length=self.max_length)
        sess.debug['BCENode_chunk'] = sess.chunk
        if sess.knowledge is None:
            sess.code = ErrorCode.UNRELATED
            return

        # get relavance between query and knowledge base
        prompt = self.SCORING_RELAVANCE_TEMPLATE.format(sess.query, sess.chunk)
        truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=5, default=10)
        sess.debug['BCENode_chunk_relavance'] = logs
        if not truth:
            return

        # answer the question
        prompt = self.GENERATE_TEMPLATE.format(sess.knowledge, sess.query)
        # response = self.llm.generate_response(prompt=prompt, history=sess.history, backend='puyu')
        response = self.llm.generate_response(prompt=prompt, history=sess.history, backend='remote')
        
        sess.code = ErrorCode.SUCCESS
        sess.response = response
        return
    

class WebSearchNode(Node):
    """
    WebSearchNode is for web search, use `ddgs` or `serper`
    """
    def __init__(self, config:dict, config_path: str, llm: ChatClient, language: str):
        self.llm = llm
        self.config_path = config_path
        self.enable = config['worker']['enable_web_search']
        llm_config = config['llm']
        self.context_max_length = llm_config['server']['local_llm_max_text_length']
        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server']['remote_llm_max_text_length']
        if language == 'zh':
            self.SCORING_RELAVANCE_TEMPLATE = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'  # noqa E501
            self.KEYWORDS_TEMPLATE = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}交流群里的助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'  # noqa E501
            self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'  # noqa E501
        else:
            self.SCORING_RELAVANCE_TEMPLATE = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'  # noqa E501
            self.KEYWORDS_TEMPLATE = 'Google search is a general-purpose search engine that can be used to access the internet, look up encyclopedic knowledge, keep abreast of current affairs and more. Search parameters type: string, content consists of phrases or keywords separated by spaces.\nYou are now the assistant in the "{}" communication group. A user asked "{}", you plan to use Google search to find related information, please provide the keywords or phrases for the search, no explanation, just give the keywords or phrases.'  # noqa E501
            self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'  # noqa E501
        self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)


    def process(self, sess: Session):
        """Try web search"""
        if not self.enable:
            logger.debug('disable web_search')
            return

        engine = WebSearch(config_path=self.config_path)

        prompt = self.KEYWORDS_TEMPLATE.format(sess.groupname, sess.query)
        search_keywords = self.llm.generate_response(prompt)
        sess.debug['WebSearchNode_keywords'] = prompt
        articles, error = engine.get(query=search_keywords, max_article=2)

        if error is not None:
            sess.code = ErrorCode.WEB_SEARCH_FAIL
            return

        for article_id, article in enumerate(articles):
                article.cut(0, self.max_length)
                prompt = self.SCORING_RELAVANCE_TEMPLATE.format(sess.query, article.brief)
                # truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=5, default=10, backend='puyu')
                truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=5, default=10, backend='remote')
                sess.debug['WebSearchNode_relavance_{}'.format(article_id)] = logs
                if truth:
                    sess.web_knowledge += '\n'
                    sess.web_knowledge += article.content
                    sess.references.append(article.source)

        sess.web_knowledge = sess.web_knowledge[0:self.max_length].strip()
        if len(sess.web_knowledge) < 1:
            sess.code = ErrorCode.NO_SEARCH_RESULT
            return

        prompt = self.GENERATE_TEMPLATE.format(sess.web_knowledge, sess.query)
        # sess.response = self.llm.generate_response(prompt=prompt, history=sess.history, backend="puyu")
        sess.response = self.llm.generate_response(prompt=prompt, history=sess.history, backend="remote")
        sess.code = ErrorCode.SUCCESS


class SGSearchNode(Node):
    """
    SGSearchNode is for retrieve from source graph
    """
    def __init__(self, config:dict, config_path: str, llm: ChatClient, language: str):
        self.llm = llm
        self.language = language
        self.enable = config['worker']['enable_sg_search']
        self.config_path = config_path

        if language == 'zh':
            self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'  # noqa E501
        else:
            self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'  # noqa E501

    def process(self, sess: Session):
        """
        Try get reply with source graph
        """

        if not self.enable:
            logger.debug('disable sg_search')
            return

        # if exit for other status (SECURITY or SEARCH_FAIL), still quit `sg_search`
        if sess.code != ErrorCode.BAD_ANSWER and sess.code != ErrorCode.NO_SEARCH_RESULT and sess.code != ErrorCode.WEB_SEARCH_FAIL:
            return

        sg = SourceGraphProxy(config_path=self.config_path, language=self.language)
        sess.sg_knowledge = sg.search(llm_client=self.llm, question=sess.query, groupname=sess.groupname)

        sess.debug['SGSearchNode_knowledge'] = sess.sg_knowledge
        if sess.sg_knowledge is None or len(sess.sg_knowledge) < 1:
            sess.code = ErrorCode.SG_SEARCH_FAIL
            return

        prompt = self.GENERATE_TEMPLATE.format(sess.sg_knowledge, sess.query)
        # sess.response = self.llm.generate_response(prompt=prompt, history=sess.history, backend='puyu')
        sess.response = self.llm.generate_response(prompt=prompt, history=sess.history, backend='remote')
        if sess.response is None or len(sess.response) < 1:
            sess.code = ErrorCode.LLM_NOT_RESPONSE_SG
            return
        sess.code = ErrorCode.SUCCESS


class SecurityNode(Node):
    """
    SecurityNode is for result check
    """
    def __init__(self, llm: ChatClient, language: str):
        self.llm = llm
        if language == 'zh':
            self.PERPLESITY_TEMPLATE = '“question:{} answer:{}”\n阅读以上对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。\n判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。直接打分不要解释。'  # noqa E501
            self.SECURITY_TEMAPLTE = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 0～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'  # noqa E501
        else:
            self.PERPLESITY_TEMPLATE = 'Question: {} Answer: {}\nRead the dialogue above, does the answer express that they don\'t know? The more comprehensive the answer, the lower the score. Rate it on a scale of 0-10, no explanation, just give the score.\nThe scoring standard is as follows: an accurate answer to the question gets 0 points; a detailed answer gets 1 point; knowing some answers but having uncertain information gets 8 points; knowing a small part of the answer but recommends seeking help from others gets 9 points; not knowing any of the answers and directly recommending asking others for help gets 10 points. Just give the score, no explanation.'  # noqa E501
            self.SECURITY_TEMAPLTE = 'Evaluate whether the following sentence involves prohibited content such as politics, insult, pornography, terror, religion, cyber violence, racial discrimination, etc., rate it on a scale of 0-10, do not explain, just give the score. The scoring standard is as follows: any violation directly gets 10 points; completely unrelated gets 0 points. Give the score, no explanation: "{}"'  # noqa E501

    def process(self, sess: Session):
        """
        Check result with security.
        """
        prompt = self.PERPLESITY_TEMPLATE.format(sess.query, sess.response)
        truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=8, default=0)
        sess.debug['SecurityNode_qa_perplex'] = logs
        if truth:
            sess.code = ErrorCode.BAD_ANSWER
            return

        prompt = self.SECURITY_TEMAPLTE.format(sess.response)
        truth, logs = is_truth(llm=self.llm, prompt=prompt, throttle=8, default=0)
        sess.debug['SecurityNode_template'] = logs
        if truth:
            sess.code = ErrorCode.SECURITY
            return

class Worker:
    """The Worker class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A ChatClient instance that communicates with the language model.
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
        self.llm = ChatClient(config_path=config_path)
        self.retriever = CacheRetriever(config_path=config_path).get()

        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

    def direct_chat(self, query: str):
        """"Generate reply with LLM."""
        return self.llm.generate_response(prompt=query, backend='remote')

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

    def generate(self, query, history, groupname, groupchats=[]):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (str): User's query.
            history (str): Chat history.
            groupname (str): The group name in which user asked the query.
            groupchats (history): The history conversation in group before user query.

        Returns:
            ErrorCode: An error code indicating the status of response generation.  # noqa E501
            str: Generated response to the user query.
            references: List for referenced filename or web url
        """
        # build input session
        sess = Session(query=query, history=history, groupname=groupname, log_path=self.config['worker']['save_path'], groupchats=groupchats)

        # build pipeline
        preproc = PreprocNode(self.config, self.llm, self.language)
        text2vec = BCENode(self.config, self.llm, self.retriever, self.language)
        websearch = WebSearchNode(self.config, self.config_path, self.llm, self.language)
        sgsearch = SGSearchNode(self.config, self.config_path, self.llm, self.language)
        check = SecurityNode(self.llm, self.language)
        pipeline = [preproc, text2vec, websearch, sgsearch]

        # run
        exit_states = [ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION, ErrorCode.NO_TOPIC, ErrorCode.UNRELATED]
        for node in pipeline:
            node.process(sess)
            
            # unrelated to knowledge base or bad input, exit
            if sess.code in exit_states:
                break

            if sess.code == ErrorCode.SUCCESS:
                check.process(sess)
            
            # check success, return
            if sess.code == ErrorCode.SUCCESS:
                break

        logger.debug(sess.debug)
        return sess.code, sess.response, sess.references


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Worker configuration path. Default value is config.ini')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    bot = Worker(work_dir=args.work_dir, config_path=args.config_path)
    queries = ['茴香豆是怎么做的']
    for example in queries:
        print(bot.generate(query=example, history=[], groupname=''))
