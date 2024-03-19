# Copyright (c) OpenMMLab. All rights reserved.
"""Pipeline."""
import argparse
import datetime
import re
import time

import pytoml
from loguru import logger

from .helper import ErrorCode, QueryTracker
from .llm_client import ChatClient
from .retriever import CacheRetriever
from .sg_search import SourceGraphProxy
from .web_search import WebSearch


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

        self.context_max_length = -1
        llm_config = self.config['llm']
        if llm_config['enable_local']:
            self.context_max_length = llm_config['server'][
                'local_llm_max_text_length']
        elif llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_llm_max_text_length']
        else:
            raise Exception('no llm enabled')

        # Switch languages according to the scenario.
        if self.language == 'zh':
            self.TOPIC_TEMPLATE = '告诉我这句话的主题，直接说主题不要解释：“{}”'
            self.SCORING_QUESTION_TEMPLTE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'  # noqa E501
            self.SCORING_RELAVANCE_TEMPLATE = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'  # noqa E501
            self.KEYWORDS_TEMPLATE = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}交流群里的技术助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'  # noqa E501
            self.SECURITY_TEMAPLTE = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 0～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'  # noqa E501
            self.PERPLESITY_TEMPLATE = '“question:{} answer:{}”\n阅读以上对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。\n判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。直接打分不要解释。'  # noqa E501
            self.SUMMARIZE_TEMPLATE = '{} \n 仔细阅读以上内容，总结得简短有力点'  # noqa E501
            # self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题，材料可能和问题无关。如果材料和问题无关，尝试用你自己的理解来回答问题。如果无法确定答案，直接回答不知道。'  # noqa E501
            self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'  # noqa E501
        else:
            self.TOPIC_TEMPLATE = 'Tell me the theme of this sentence, just state the theme without explanation: "{}"'  # noqa E501
            self.SCORING_QUESTION_TEMPLTE = '"{}"\nPlease read the content above carefully and judge whether the sentence is a thematic question. Rate it on a scale of 0-10. Only provide the score, no explanation.\nThe criteria are as follows: a sentence gets 10 points if it has a subject, predicate, object and is a question; points are deducted for missing subject, predicate or object; declarative sentences get 0 points; sentences that are not questions also get 0 points. Just give the score, no explanation.'  # noqa E501
            self.SCORING_RELAVANCE_TEMPLATE = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'  # noqa E501
            self.KEYWORDS_TEMPLATE = 'Google search is a general-purpose search engine that can be used to access the internet, look up encyclopedic knowledge, keep abreast of current affairs and more. Search parameters type: string, content consists of phrases or keywords separated by spaces.\nYou are now the assistant in the "{}" communication group. A user asked "{}", you plan to use Google search to find related information, please provide the keywords or phrases for the search, no explanation, just give the keywords or phrases.'  # noqa E501
            self.SECURITY_TEMAPLTE = 'Evaluate whether the following sentence involves prohibited content such as politics, insult, pornography, terror, religion, cyber violence, racial discrimination, etc., rate it on a scale of 0-10, do not explain, just give the score. The scoring standard is as follows: any violation directly gets 10 points; completely unrelated gets 0 points. Give the score, no explanation: "{}"'  # noqa E501
            self.PERPLESITY_TEMPLATE = 'Question: {} Answer: {}\nRead the dialogue above, does the answer express that they don\'t know? The more comprehensive the answer, the lower the score. Rate it on a scale of 0-10, no explanation, just give the score.\nThe scoring standard is as follows: an accurate answer to the question gets 0 points; a detailed answer gets 1 point; knowing some answers but having uncertain information gets 8 points; knowing a small part of the answer but recommends seeking help from others gets 9 points; not knowing any of the answers and directly recommending asking others for help gets 10 points. Just give the score, no explanation.'  # noqa E501
            self.SUMMARIZE_TEMPLATE = '"{}" \n Read the content above carefully, summarize it in a short and powerful way.'  # noqa E501
            self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'  # noqa E501

    def single_judge(self, prompt, tracker, throttle: int, default: int):
        """Generates a score based on the prompt, and then compares it to
        threshold.

        Args:
            prompt (str): The prompt for the language model.
            tracker (obj): An instance of QueryTracker logs the operations.
            throttle (int): Threshold value to compare the score against.
            default (int): Default score to be assigned in case of failure in score calculation.  # noqa E501

        Returns:
            bool: True if the score surpasses the throttle, otherwise False.
        """
        if prompt is None or len(prompt) == 0:
            return False

        score = default
        relation = self.llm.generate_response(prompt=prompt, remote=False)
        tracker.log('score', [relation, throttle, default])
        filtered_relation = ''.join([c for c in relation if c.isdigit()])
        try:
            score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
            score = int(score_str.split(' ')[0])
        except Exception as e:
            logger.error(str(e))
        if score >= throttle:
            return True
        return False

    def work_time(self):
        """Determines if the current time falls within the scheduled working
        hours of the chat assistant.

        Returns:
            bool: True if the current time is within working hours, otherwise False.  # noqa E501
        """
        time_config = self.config['worker']['time']

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

    def generate(self, query, history, groupname):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (str): User's query.
            history (str): Chat history.
            groupname (str): The group name in which user asked the query.

        Returns:
            ErrorCode: An error code indicating the status of response generation.  # noqa E501
            str: Generated response to the user query.
            references: List for referenced filename or web url
        """
        response = ''
        references = []

        if not self.work_time():
            return ErrorCode.NOT_WORK_TIME, response, references

        if query is None or len(query) < 6:
            return ErrorCode.NOT_A_QUESTION, response, references

        reborn_code = ErrorCode.SUCCESS
        tracker = QueryTracker(self.config['worker']['save_path'])
        tracker.log('input', [query, history, groupname])

        if not self.single_judge(
                prompt=self.SCORING_QUESTION_TEMPLTE.format(query),
                tracker=tracker,
                throttle=6,
                default=3):
            return ErrorCode.NOT_A_QUESTION, response, references

        topic = self.llm.generate_response(self.TOPIC_TEMPLATE.format(query))
        tracker.log('topic', topic)

        if len(topic) <= 2:
            return ErrorCode.NO_TOPIC, response, references

        chunk, db_context, references = self.retriever.query(
            topic,
            context_max_length=self.context_max_length -
            2 * len(self.GENERATE_TEMPLATE))
        if db_context is None:
            tracker.log('feature store reject')
            return ErrorCode.UNRELATED, response, references

        if self.single_judge(self.SCORING_RELAVANCE_TEMPLATE.format(
                query, chunk),
                             tracker=tracker,
                             throttle=5,
                             default=10):
            prompt, history = self.llm.build_prompt(
                instruction=query,
                context=db_context,
                history_pair=history,
                template=self.GENERATE_TEMPLATE)
            response = self.llm.generate_response(prompt=prompt,
                                                  history=history,
                                                  remote=True)
            tracker.log('feature store doc', [chunk, response])
            return ErrorCode.SUCCESS, response, references

        try:
            references = []
            web_context = ''
            web_search = WebSearch(config_path=self.config_path)

            articles, error = web_search.get(query=topic, max_article=2)
            if error is not None:
                return ErrorCode.SEARCH_FAIL, response, references

            tracker.log('search returned')
            web_context_max_length = self.context_max_length - 2 * len(
                self.SCORING_RELAVANCE_TEMPLATE)

            for article in articles:
                if len(article) > 0:
                    article.cut(0, web_context_max_length)

                    if self.single_judge(
                            self.SCORING_RELAVANCE_TEMPLATE.format(
                                query, article.content),
                            tracker=tracker,
                            throttle=5,
                            default=10):
                        web_context += '\n\n'
                        web_context += article.content
                        references.append(article.source)

            web_context = web_context[0:web_context_max_length]
            web_context = web_context.strip()

            if len(web_context) > 0:
                prompt, history = self.llm.build_prompt(
                    instruction=query,
                    context=web_context,
                    history_pair=history,
                    template=self.GENERATE_TEMPLATE)
                response = self.llm.generate_response(prompt=prompt,
                                                      history=history,
                                                      remote=False)
            else:
                reborn_code = ErrorCode.NO_SEARCH_RESULT

            tracker.log('web response', [web_context, response, reborn_code])
        except Exception as e:
            logger.error(e)

        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if self.single_judge(prompt=prompt,
                                 tracker=tracker,
                                 throttle=10,
                                 default=0):
                reborn_code = ErrorCode.BAD_ANSWER

        if self.config['worker']['enable_sg_search']:
            if reborn_code == ErrorCode.BAD_ANSWER or reborn_code == ErrorCode.NO_SEARCH_RESULT:  # noqa E501
                # reborn
                sg = SourceGraphProxy(config_path=self.config_path,
                                      language=self.language)
                sg_context = sg.search(llm_client=self.llm,
                                       question=query,
                                       groupname=groupname)
                if sg_context is not None and len(sg_context) > 2:
                    prompt, history = self.llm.build_prompt(
                        instruction=query,
                        context=sg_context,
                        history_pair=history,
                        template=self.GENERATE_TEMPLATE)

                    response = self.llm.generate_response(prompt=prompt,
                                                          history=history,
                                                          remote=True)
                    tracker.log('source graph', [sg_context, response])

                    prompt = self.PERPLESITY_TEMPLATE.format(query, response)
                    if self.single_judge(prompt=prompt,
                                         tracker=tracker,
                                         throttle=9,
                                         default=0):
                        return ErrorCode.BAD_ANSWER, response, references

        if response is not None and len(response) >= 800:
            # reply too long, summarize it
            response = self.llm.generate_response(
                prompt=self.SUMMARIZE_TEMPLATE.format(response))

        if len(response) > 0 and self.single_judge(
                self.SECURITY_TEMAPLTE.format(response),
                tracker=tracker,
                throttle=3,
                default=0):
            return ErrorCode.SECURITY, response, references

        if reborn_code != ErrorCode.SUCCESS:
            return reborn_code, response, references

        return ErrorCode.SUCCESS, response, references


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
