import json
import os
import tempfile
import time

import pytoml
from loguru import logger

from huixiangdou.service.web_search import WebSearch, check_str_useful


def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
    return kimi_token, serper_token


def test_ddgs():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    articles, error = engine.get(query='mmpose installation')
    assert error is None
    assert len(articles[0]) > 100


def test_serper():
    config_path = 'config-2G.ini'
    _, serper_token = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['web_search']['engine'] = 'serper'
        config['web_search']['serper_x_api_key'] = serper_token

    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))

        config_path = temp_file.name

    engine = WebSearch(config_path=config_path)
    articles, error = engine.get(query='mmpose installation')
    assert error is None
    assert len(articles[0]) > 100
    assert articles[0].brief == articles[0].content
    # 删除临时文件，因为delete=False，所以需要手动删除
    os.remove(temp_file.name)

def test_parse_zhihu():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    article = engine.fetch_url(query='', target_link='https://zhuanlan.zhihu.com/p/699164101')
    assert check_str_useful(article.content)

def test_parse_hljnews():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    article = engine.fetch_url(query='', target_link='http://www.hljnews.cn/ljxw/content/2023-10/17/content_729976.html?vp-fm')
    assert check_str_useful(article.content)

if __name__ == '__main__':
    test_parse_zhihu()
    test_parse_hljnews()
