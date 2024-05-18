# Copyright (c) OpenMMLab. All rights reserved.
"""Pipeline."""
import argparse
import datetime
import json
import random
import re
import time

import pytoml
import requests
from loguru import logger

from huixiangdou.service import (ChatClient, ErrorCode, FeatureStore,
                                 QueryTracker, WebSearch)


def openxlab_security(query: str, retry=1):
    life = 0
    while life < retry:
        try:
            headers = {'Content-Type': 'application/json'}
            data = {
                'bizId': str('antiseed' + str(time.time())),
                'contents': [query],
                'scopes': [],
                'vendor': 1,
            }

            resp = requests.post(
                'https://openxlab.org.cn/gw/checkit/api/v1/audit/text',
                data=json.dumps(data),
                headers=headers)
            logger.debug((resp, resp.content))

            json_obj = json.loads(resp.content)
            items = json_obj['data']

            block = False
            for item in items:
                label = item['label']
                if label is not None and label in ['porn', 'politics']:
                    suggestion = item['suggestion']
                    if suggestion == 'block':
                        logger.debug(items)
                        block = True
                        break

            if block:
                return False
            return True
        except Exception as e:
            logger.debug(e)
            life += 1

            randval = random.randint(1, int(pow(2, life)))
            time.sleep(randval)
    return False


class WebWorker:
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
        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

        self.context_max_length = -1
        llm_config = self.config['llm']
        self.context_max_length = llm_config['server'][
            'local_llm_max_text_length']

        if llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_llm_max_text_length']

        # Switch languages according to the scenario.
        if self.language == 'zh':
            self.TOPIC_TEMPLATE = '告诉我这句话的主题，直接说主题不要解释：“{}”'
            self.SCORING_QUESTION_TEMPLTE = '“{}”\n请仔细阅读以上内容，判断句子是否是个疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'  # noqa E501
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

    def security_content(self, tracker, response: str):
        # 安全检查，通过为 true
        return True
        # if len(response) < 1:
        #     return True
        # if self.single_judge(self.SECURITY_TEMAPLTE.format(response),
        #     tracker=tracker,
        #     throttle=3,
        #     default=0):
        #     return False

        # if openxlab_security(response):
        #     return True
        # return False

    def single_judge(self, prompt, tracker, throttle: int, default: int,
                     backend: str):
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
        relation = self.llm.generate_response(prompt=prompt, backend=backend)
        tracker.log('score' + prompt[0:20], [relation, throttle, default])
        filtered_relation = ''.join([c for c in relation if c.isdigit()])
        try:
            score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
            score = int(score_str.split(' ')[0])
        except Exception as e:
            logger.error(str(e))
        if score >= throttle:
            return True
        return False

    def generate(self, query, history, retriever, groupname):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (str): User's query.
            history (list): Chat history.
            groupname (str): The group name in which user asked the query.

        Returns:
            ErrorCode: An error code indicating the status of response generation.  # noqa E501
            str: Generated response to the user query.
        """
        response = ''
        reborn_code = ErrorCode.SUCCESS
        tracker = QueryTracker(self.config['worker']['save_path'])
        tracker.log('input', [query, history, groupname])

        if not self.single_judge(
                prompt=self.SCORING_QUESTION_TEMPLTE.format(query),
                tracker=tracker,
                throttle=6,
                default=2,
                backend='remote'):
            # not a question, give LLM response
            response = self.llm.generate_response(prompt=query,
                                                  history=history,
                                                  backend='remote')
            return ErrorCode.NOT_A_QUESTION, response, []

        topic = self.llm.generate_response(self.TOPIC_TEMPLATE.format(query),
                                           backend='remote')
        tracker.log('topic', topic)

        if len(topic) < 2:
            return ErrorCode.NO_TOPIC, response, []

        chunk, db_context, retrieve_ref = retriever.query(
            topic,
            context_max_length=self.context_max_length -
            2 * len(self.GENERATE_TEMPLATE))

        if db_context is None or len(db_context) < 1:
            tracker.log('topic feature store reject')

            chunk, db_context, retrieve_ref = retriever.query(
                query,
                context_max_length=self.context_max_length -
                2 * len(self.GENERATE_TEMPLATE))
            if db_context is None or len(db_context) < 1:
                return ErrorCode.UNRELATED, response, retrieve_ref

        logger.info('fetch context length {}'.format(len(db_context)))
        # if self.single_judge(self.SCORING_RELAVANCE_TEMPLATE.format(
        #         query, chunk),
        #                      tracker=tracker,
        #                      throttle=5,
        #                      default=10,
        #                      backend='remote'):
        prompt, history = self.llm.build_prompt(
            instruction=query,
            context=db_context,
            history_pair=history,
            template=self.GENERATE_TEMPLATE)
        response = self.llm.generate_response(prompt=prompt,
                                              history=history,
                                              backend='remote')
        tracker.log('feature store doc', [chunk, response])
        if response is not None and len(response) < 1:
            # llm error
            return ErrorCode.INTERNAL_ERROR, 'LLM API 没给回复，见 https://github.com/InternLM/HuixiangDou/issues/214 ', retrieve_ref

        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if not self.single_judge(prompt=prompt,
                                     tracker=tracker,
                                     throttle=9,
                                     default=0,
                                     backend='remote'):
                # get answer, check security and return
                if not self.security_content(tracker, response):
                    return ErrorCode.SECURITY, '检测到敏感内容，无法显示', retrieve_ref
                return ErrorCode.SUCCESS, response, retrieve_ref

        # start web search
        web = WebSearch(config_path=self.config_path)
        if len(web.load_key()) < 1:
            return ErrorCode.BAD_ANSWER, response, []

        use_ref = []
        try:
            web_context = ''
            articles, error = web.get(query=topic, max_article=2)
            if error is not None:
                return ErrorCode.WEB_SEARCH_FAIL, response, []

            tracker.log('search returned')
            for article in articles:
                if len(article) > 0 and len(
                        web_context) < self.context_max_length:
                    if len(article) > self.context_max_length:
                        article.cut(
                            0, self.context_max_length -
                            2 * len(self.SCORING_RELAVANCE_TEMPLATE))

                    if self.single_judge(
                            self.SCORING_RELAVANCE_TEMPLATE.format(
                                query, str(article)),
                            tracker=tracker,
                            throttle=5,
                            default=10,
                            backend='remote'):
                        web_context += '\n'
                        web_context += str(article)
                        use_ref.append(article.source)

            web_context = web_context[0:self.context_max_length]
            web_context = web_context.strip()

            if len(web_context) > 0:
                prompt, history = self.llm.build_prompt(
                    instruction=query,
                    context=web_context,
                    history_pair=history,
                    template=self.GENERATE_TEMPLATE)
                response = self.llm.generate_response(prompt=prompt,
                                                      history=history,
                                                      backend='remote')
            else:
                reborn_code = ErrorCode.NO_SEARCH_RESULT

            tracker.log('web response', [web_context, response, reborn_code])
        except Exception as e:
            logger.error(e)

        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if self.single_judge(prompt=prompt,
                                 tracker=tracker,
                                 throttle=9,
                                 default=0,
                                 backend='remote'):
                reborn_code = ErrorCode.BAD_ANSWER

        # if response is not None and len(response) >= 800:
        #     # reply too long, summarize it
        #     response = self.llm.generate_response(
        #         prompt=self.SUMMARIZE_TEMPLATE.format(response))

        if not self.security_content(tracker, response):
            return ErrorCode.SECURITY, '回复可能包含不安全内容，无法显示', use_ref

        if reborn_code != ErrorCode.SUCCESS:
            return reborn_code, response, use_ref

        return ErrorCode.SUCCESS, response, use_ref


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
