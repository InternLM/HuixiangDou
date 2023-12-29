from loguru import logger
from .llm_client import ChatClient
from .feature_store import FeatureStore
from .web_search import WebSearch
from .sg_search import SourceGraphProxy
from .helper import ErrorCode, QueryTracker
import argparse
import pytoml
import datetime
import time
import re
import pdb


class Worker:

    def __init__(self, work_dir:str, config_path: str):
        self.llm = ChatClient(config_path=config_path)
        self.fs = FeatureStore(config_path=config_path)
        self.fs.load_feature(work_dir=work_dir)
        self.config_path = config_path
        self.config = None
        with open(config_path) as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception(f'worker config can not be None')

        self.context_max_length = -1
        llm_config = self.config['llm']
        if llm_config['enable_local']:
            self.context_max_length = llm_config['server'][
                'local_internlm_max_text_length']
        elif llm_config['enable_remote']:
            self.context_max_length = llm_config['server'][
                'remote_kimi_max_text_length']
        else:
            raise Exception(f'no llm enabled')

        # prompt might be truncated, control statements should be placed at the beginning.
        self.TOPIC_TEMPLATE = '告诉我这句话的主题，直接说主题不要解释：“{}”'
        self.SCORING_QUESTION_TEMPLTE = '判断以下句子是否是个有主题的疑问句，结果用 1～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。\n问题“{}”，得分是多少？直接提供得分不要解释。'
        self.SCORING_RELAVANCE_TEMPATE = '判断问题和材料的关联度，用1～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n问题：“{}”\n材料：“{}”'
        self.KEYWORDS_TEMPLATE = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}技术交流群里的技术助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'
        self.SECURITY_TEMAPLTE = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 1～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'
        self.PERPLESITY_TEMPLATE = '''阅读以下对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。
判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。

以下是一些 10 分示例：
answer: “从您提供的信息来看，这个问题似乎是关于某个技术问题的讨论，可能是在寻求帮助。然而，问题的具体内容并不清楚。为了给您提供更有针对性的帮助，能否请您详细描述一下您所遇到的问题或需要解答的疑问？这样我才能更好地理解您的需求并提供相应的解答。”
answer: “抱歉我不清楚 lmdeploy 是什么，请联系相关开发人员”
直接打分不要解释。

“question:{} answer:{}”'''
        self.SUMMARIZE_TEMPLATE = '{} \n 仔细阅读以上内容，总结到 500 字以内'
        self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题，材料可能和问题无关。如果材料和问题无关，尝试用你自己的理解来回答问题。如果无法确定答案，直接回答不知道。'

    def single_judge(self, prompt, tracker, throttle: int, default: int):
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
            pass
        if score >= throttle:
            return True
        return False

    def work_time(self):
        time_config = self.config['worker']['time']

        beginWork = datetime.datetime.now().strftime(
            "%Y-%m-%d") + ' ' + time_config['start']
        endWork = datetime.datetime.now().strftime(
            "%Y-%m-%d") + ' ' + time_config['end']
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
        response = ''

        if not self.work_time():
            return ErrorCode.NOT_WORK_TIME, response

        reborn_code = ErrorCode.SUCCESS
        tracker = QueryTracker(self.config['worker']['save_path'])
        tracker.log('input', [query, history, groupname])

        if not self.single_judge(
                prompt=self.SCORING_QUESTION_TEMPLTE.format(query),
                tracker=tracker,
                throttle=7,
                default=3):
            return ErrorCode.NOT_A_QUESTION, response

        topic = self.llm.generate_response(self.TOPIC_TEMPLATE.format(query))
        tracker.log('topic', topic)

        if len(topic) <= 2:
            return ErrorCode.NO_TOPIC, response

        db_context_part, db_context = self.fs.query_source(topic)
        if db_context == '<reject>':
            tracker.log('feature store reject')
            return ErrorCode.UNRELATED, response

        if self.single_judge(self.SCORING_RELAVANCE_TEMPATE.format(
                query, db_context_part),
                             tracker=tracker,
                             throttle=5,
                             default=10):
            prompt, history = self.llm.build_prompt(instruction=query,
                                               context=db_context,
                                               history_pair=history,
                                               template=self.GENERATE_TEMPLATE)
            response = self.llm.generate_response(prompt=prompt,
                                             history=history,
                                             remote=True)
            tracker.track('feature store doc', [db_context_part, response])
            return ErrorCode.SUCCESS, response

        else:
            prompt = self.KEYWORDS_TEMPLATE.format(groupname, query)
            web_keywords = self.llm.generate_response(prompt=prompt)
            # format keywords
            for symbol in ['"', ',', '  ']:
                web_keywords = web_keywords.replace(symbol, ' ')
            web_keywords = web_keywords.strip()
            tracker.log('web search keywords', web_keywords)

            if len(web_keywords) < 1:
                return ErrorCode.NO_SEARCH_KEYWORDS, response

            try:
                web_context = ''
                web_search = WebSearch(config_path=self.config_path)
                articles = web_search.get_with_cache(query=web_keywords,
                                                     max_article=2)

                tracker.log('search returned')
                for article in articles:
                    if article is not None and len(article) > 0:
                        if len(article) > self.context_max_length:
                            article = article[0:self.context_max_length]

                        if self.single_judge(
                                self.SECURITY_TEMAPLTE.format(article),
                                tracker=tracker,
                                throttle=3,
                                default=0):
                            tracker.log('跳过不安全的内容', article)
                            continue

                        if self.single_judge(
                                self.SCORING_RELAVANCE_TEMPATE.format(
                                    query, article),
                                tracker=tracker,
                                throttle=6,
                                default=10):
                            web_context += '\n\n'
                            web_context += article

                if len(web_context) >= self.context_max_length:
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
                                                     remote=False)
                else:
                    reborn_code = ErrorCode.NO_SEARCH_RESULT

                tracker.log('web response',
                            [web_context, response, reborn_code])
            except Exception as e:
                logger.error(e)

        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if self.single_judge(prompt=prompt,
                                 tracker=tracker,
                                 throttle=8,
                                 default=0):
                reborn_code = ErrorCode.BAD_ANSWER

        if self.config['worker']['enable_sg_search']:
            if reborn_code == ErrorCode.BAD_ANSWER or reborn_code == ErrorCode.NO_SEARCH_RESULT:
                # reborn
                sg = SourceGraphProxy(config_path=self.config_path)
                sg_context = sg.search(llm=llm,
                                       question=query,
                                       groupname=groupname)
                if sg_context != None and len(sg_context) > 0:
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
                        return ErrorCode.BAD_ANSWER, response

        if response is not None and len(response) >= 600:
            # 回复内容太长，总结一下
            response = self.llm.generate_response(
                prompt=self.SUMMARIZE_TEMPLATE.format(response))

        if len(response) > 0 and self.single_judge(
                self.SECURITY_TEMAPLTE.format(response),
                tracker=tracker,
                throttle=3,
                default=0):
            return ErrorCode.SECURITY, response

        if reborn_code != ErrorCode.SUCCESS:
            return reborn_code, response

        return ErrorCode.SUCCESS, response


def parse_args():
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Worker configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    bot = Worker(work_dir=args.work_dir, config_path=args.config_path)
    querys = ['茴香豆是怎么做的']
    for query in querys:
        print(bot.generate(query=query, history=[], groupname=''))
