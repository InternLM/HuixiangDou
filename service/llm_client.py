import argparse
import os
import time
import json
import random
import requests
from loguru import logger
import pytoml
import pdb


class ChatClient:

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load_config(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            return config['llm']

    def load_llm_config(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            return config['llm']['server']

    def build_prompt(self,
                     history_pair,
                     instruction: str,
                     template: str,
                     context: str = '',
                     reject: str = '<reject>'):
        if context is not None and len(context) > 0:
            instruction = template.format(context, instruction)

        real_history = []
        for pair in history_pair:
            if pair[1] == reject:
                continue
            if pair[0] is None or pair[1] is None:
                continue
            if len(pair[0]) < 1 or len(pair[1]) < 1:
                continue
            real_history.append(pair)

        return instruction, real_history

    def generate_response(self, prompt, history=[], remote=False):
        llm_config = self.load_config()
        url, enable_local, enable_remote = (llm_config['client_url'],
                                            llm_config['enable_local'],
                                            llm_config['enable_remote'])

        if remote and not enable_remote:
            remote = False
            logger.warning(
                f'disable remote LLM while set `remote=True`, auto fixed')
        elif not enable_local and not remote:
            remote = True
            logger.warning(
                f'diable local LLM while `remote=False`, auto fixed')

        if remote:
            max_length = llm_config['server']['remote_llm_max_text_length']
        else:
            max_length = llm_config['server']['local_llm_max_text_length']

        if len(prompt) > max_length:
            logger.warning(
                f'prompt length {len(prompt)}  > max_length {max_length}, truncated'
            )
            prompt = prompt[0:max_length]

        try:
            header = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {
                "prompt": prompt,
                "history": data_history,
                "remote": remote
            }
            resp = requests.post(url, headers=header, data=json.dumps(data))
            pdb.set_trace()
            if resp.status_code != 200:
                raise Exception(str((resp.status_code, resp.reason)))
            return resp.json()['text']
        except Exception as e:
            logger.error(str(e))
            return ''


def parse_args():
    parser = argparse.ArgumentParser(
        description='Client for hybrid llm service.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Hybrid LLM Server configuration path. Default value is config.ini'
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    client = ChatClient(config_path=args.config_path)
    question = '“{}”\n请仔细阅读以上问题，提取其中的实体词，结果直接用 list 表示，不要解释。'.format(
        '请问triviaqa 5shot结果怎么在summarizer里输出呢')
    print(client.generate_response(prompt=question))
