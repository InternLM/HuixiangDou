import json
import os
import tempfile
import time

import pytoml
from loguru import logger

from huixiangdou.service.llm_client import ChatClient
from huixiangdou.service.llm_server_hybrid import llm_serve, start_llm_server
from huixiangdou.service.sg_search import SourceGraphProxy


def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
        sg_token = json_obj['sg']
    return kimi_token, serper_token, sg_token


def build_config_path():
    config_path = 'config-2G.ini'
    kimi_token, serper_token, sg_token = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['web_search']['engine'] = 'serper'
        config['web_search']['serper_x_api_key'] = serper_token
        config['feature_store'][
            'embedding_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['feature_store'][
            'reranker_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['llm']['server']['remote_api_key'] = kimi_token
        config['worker']['enable_sg_search'] = 1
        config['sg_search']['src_access_token'] = sg_token

    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))
        config_path = temp_file.name

    return config_path


def test_sg():
    config_path = build_config_path()
    start_llm_server(config_path)

    llm = ChatClient(config_path=config_path)
    proxy = SourceGraphProxy(config_path=config_path)
    content = proxy.search(llm_client=llm,
                           question='mmpose installation',
                           groupname='mmpose dev group')
    assert len(content) > 0
