import argparse
import os
import time
import json
import random
import requests
from loguru import logger
import pytoml

class ChatClient:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load_remote_url(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            return config['llm']['server_url']
        raise Exception('llm.server url not found')

    def load_scoring_template(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            return config['llm']['client_scoring_template']
        raise Exception('llm.client scoring template not found')

    def build_prompt(self, history_pair, instruction: str, context: str = '', reject: str = '<reject>'):
        if context is not None and len(context) > 0:
            instruction = load_scoring_template().format(context, instruction)

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
        try:
            header = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {"prompt": prompt, "history": data_history, "remote": remote}
            resp = requests.post(self.load_remote_url(), headers=header, data=json.dumps(data))
            return resp.json()['text']
        except Exception as e:
            print(str(e))
            return ''        

def parse_args():
    parser = argparse.ArgumentParser(description='Client for hybrid llm service.')
    parser.add_argument('--config_path', default='config.ini',
                        help='Hybrid LLM Server configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    client = ChatClient(config_path=args.config_path)
    question = '“{}”\n请仔细阅读以上问题，提取其中的实体词，结果直接用 list 表示，不要解释。'.format('请问triviaqa 5shot结果怎么在summarizer里输出呢')
    print(client.generate_response(prompt=question))
