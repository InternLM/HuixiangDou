import time
import json
import pytoml
from loguru import logger

from huixiangdou.service.llm_server_hybrid import (RPM, HybridLLMServer,
                                                   llm_serve)

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

    _, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='kimi')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='deepseek')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='zhipuai')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='xi-api')
    logger.error(error)
    assert len(error) > 0

def test_kimi_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'kimi'
    llm_config['server']['remote_api_key'] = secrets['kimi']
    llm_config['server']['remote_llm_model'] = 'auto'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='kimi')
    
    assert len(error) == 0
    assert len(response) > 0


def test_zhipu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'zhipuai'
    llm_config['server']['remote_api_key'] = secrets['zhipuai']
    llm_config['server']['remote_llm_model'] = 'glm-4'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='zhipuai')
    
    assert len(error) == 0
    assert len(response) > 0


def test_deepseek_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'deepseek'
    llm_config['server']['remote_api_key'] = secrets['deepseek']
    llm_config['server']['remote_llm_model'] = 'deepseek-chat'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='deepseek')
    
    assert len(error) == 0
    assert len(response) > 0

def test_step_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'step'
    llm_config['server']['remote_api_key'] = secrets['step']
    llm_config['server']['remote_llm_model'] = 'auto'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='step')
    
    assert len(error) == 0
    assert len(response) > 0

def test_puyu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'puyu'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='puyu')
    
    assert len(error) == 0
    assert len(response) > 0

def test_internlm_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']

    secrets = load_secret()
    llm_config['server']['remote_type'] = 'internlm'
    server = HybridLLMServer(llm_config=llm_config)

    response, error = server.generate_response(prompt='hello',
                                        history=[],
                                        backend='internlm')
    
    assert len(error) == 0
    assert len(response) > 0

def test_rpm():
    rpm = RPM(30)

    for i in range(40):
        rpm.wait()
        print(i)

    time.sleep(5)

    for i in range(40):
        rpm.wait()
        print(i)

if __name__ == '__main__':
    test_step_pass()
    test_zhipu_pass()
    test_deepseek_pass()
    test_puyu_pass()
    test_internlm_pass()