import time
import json
import pytoml
import re
from loguru import logger

from huixiangdou.service.llm_server_hybrid import InferenceWrapper

PROMPT = "“huixiangdou 是什么？”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。"

def get_score(relation: str, default=0):
    score = default
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.warning('primitive is_truth: {}, use default value {}'.format(str(e), default))
    return score

def test_internlm_local():
    wrapper = InferenceWrapper('/workspace/models/internlm2-chat-7b')
    repeat = 10
    for i in range(repeat):
        resp = wrapper.chat(prompt=PROMPT)
        logger.info(resp)
        logger.info(get_score(relation = resp))

if __name__ == '__main__':
    test_internlm_local()