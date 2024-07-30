# Check `huixiangdou.service.main` works
import json
import os
import tempfile
import time

import pytoml
from loguru import logger


def command(txt: str):
    """Executes a shell command and returns its output.

    Args:
        txt (str): Command to be executed in the shell.

    Returns:
        str: Output of the shell command execution.
    """
    logger.debug('cmd: {}'.format(txt))
    cmd = os.popen(txt)
    return cmd.read().rstrip().lstrip()


def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
    return kimi_token, serper_token


def build_config_path():
    config_path = 'config-2G.ini'
    kimi_token, _ = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['feature_store'][
            'embedding_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['feature_store'][
            'reranker_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['llm']['server']['remote_api_key'] = kimi_token

    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))

        config_path = temp_file.name

    return config_path


def run():
    config_path = build_config_path()

    actions = {
        'llm_server_hybrid':
        'python3 -m huixiangdou.service.llm_server_hybrid --config_path {}  --unittest',
        'feature_store':
        'python3 -m huixiangdou.service.feature_store --config_path {}',
        'main': 'python3 -m huixiangdou.main --standalone --config_path {}'
    }

    reports = ['HuixiangDou daily smoke:']
    for action, cmd in actions.items():
        cmd = cmd.format(config_path)
        log = command(cmd)

        if 'ConnectionResetError' in log:
            logger.info(f'*{action}, {cmd}')
            assert (0)
        else:
            logger.info(f'*{action}, passed')


if __name__ == '__main__':
    run()
