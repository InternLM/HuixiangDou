import json
import pdb
import re
import time

import pytoml
from loguru import logger

from huixiangdou.services.llm_server_hybrid import (HybridLLMServer,
                                                   llm_serve)

PROMPT = '“huixiangdou 是什么？”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
# PROMPT = 'huixiangdou 是什么？'

def get_score(relation: str, default=0):
    score = default
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.warning('primitive is_truth: {}, use default value {}'.format(
            str(e), default))
    return score


def load_secret():
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        return json_obj


def test_llm_backend_fail():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    server = HybridLLMServer(llm_config=llm_config)

    _, error = server.chat(prompt='hello',
                                        history=[],
                                        backend='kimi')
    logger.error(error)
    assert error is not None

    _, error = server.chat(prompt='hello',
                                        history=[],
                                        backend='deepseek')
    logger.error(error)
    assert error is not None

    _, error = server.chat(prompt='hello',
                                        history=[],
                                        backend='zhipuai')
    logger.error(error)
    assert error is not None

    _, error = server.chat(prompt='hello',
                                        history=[],
                                        backend='xi-api')
    logger.error(error)
    assert error is not None


def test_kimi_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'kimi'
    llm_config['server']['remote_api_key'] = secrets['kimi']
    # llm_config['server']['remote_llm_model'] = 'auto'
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='kimi')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0


def test_zhipu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'zhipuai'
    llm_config['server']['remote_api_key'] = secrets['zhipuai']
    # llm_config['server']['remote_llm_model'] = 'glm-4'
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='zhipuai')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0


def test_deepseek_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'deepseek'
    llm_config['server']['remote_api_key'] = secrets['deepseek']
    # llm_config['server']['remote_llm_model'] = 'deepseek-chat'
    print('testing {}'.format(llm_config['server']))

    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='deepseek')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0


def test_step_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'step'
    llm_config['server']['remote_api_key'] = secrets['step']
    # llm_config['server']['remote_llm_model'] = 'auto'
    print('testing {}'.format(llm_config['server']))

    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='step')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0


def test_puyu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'puyu'
    llm_config['server']['remote_api_key'] = secrets['puyu']
    # llm_config['server']['remote_llm_model'] = 'internlm2-latest'
    print('testing {}'.format(llm_config['server']))

    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='puyu')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None


def test_siliconcloud_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'siliconcloud'
    # llm_config['server']['remote_llm_model'] = 'alibaba/Qwen1.5-110B-Chat'
    llm_config['server']['remote_api_key'] = secrets['siliconcloud']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.chat(prompt=PROMPT,
                                               history=[],
                                               backend='siliconcloud')
    logger.info('siliconcloud response {}'.format(response))
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0


if __name__ == '__main__':
    test_siliconcloud_pass()
    test_kimi_pass()
    test_step_pass()
    test_zhipu_pass()
    test_deepseek_pass()
    test_puyu_pass()
    test_llm_backend_fail()
