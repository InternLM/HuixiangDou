# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import random
import time
from multiprocessing import Process, Value

import openai
import pytoml
from aiohttp import web
from loguru import logger
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer


class HybridLLMServer(object):

    def __init__(self,
                 llm_config: dict,
                 device: str = 'cuda',
                 retry=3) -> None:
        self.device = device
        self.retry = retry
        self.llm_config = llm_config
        self.server_config = llm_config['server']
        self.enable_remote = llm_config['enable_remote']
        self.enable_local = llm_config['enable_local']

        self.local_max_length = self.server_config['local_llm_max_text_length']
        self.remote_max_length = self.server_config[
            'remote_llm_max_text_length']
        self.remote_type = self.server_config['remote_type']

        model_path = self.server_config['local_llm_path']

        self.tokenizer = None
        self.model = None

        if self.enable_local:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                device_map='auto',
                #                torch_dtype="auto",
                #                fp16=True,
            ).eval()
        else:
            logger.warning('local LLM disabled.')

    def call_kimi(self, prompt, history):
        client = OpenAI(
            api_key=self.server_config['remote_api_key'],
            base_url='https://api.moonshot.cn/v1',
        )

        messages = [{
            'role':
            'system',
            'content':
            '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力，政治宗教等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'  # noqa E501
        }]
        for item in history:
            messages.append({'role': 'user', 'content': item[0]})
            messages.append({'role': 'system', 'content': item[1]})
        messages.append({'role': 'user', 'content': prompt})

        life = 0
        while life < self.retry:
            try:
                logger.debug('remote api sending: {}'.format(messages))
                completion = client.chat.completions.create(
                    model=self.server_config['remote_llm_model'],
                    messages=messages,
                    temperature=0.3,
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.error(str(e))
                # retry
                life += 1
                randval = random.randint(1, int(pow(2, life)))
                time.sleep(randval)
        return ''

    def call_gpt(self, prompt, history):
        messages = []
        for item in history:
            messages.append({'role': 'user', 'content': item[0]})
            messages.append({'role': 'system', 'content': item[1]})
        messages.append({'role': 'user', 'content': prompt})
        completion = openai.ChatCompletion.create(
            model=self.server_config['remote_llm_model'], messages=messages)
        res = completion.choices[0].message.content
        return res

    def generate_response(self, prompt, history=[], remote=False):
        output_text = ''
        time_tokenizer = time.time()

        if not self.enable_remote and remote:
            remote = False
            logger.error('llm.enable_remote off, auto set remote=False')

        if remote:
            prompt = prompt[0:self.remote_max_length]
            # call remote LLM
            llm_type = self.server_config['remote_type']
            if llm_type == 'kimi':
                output_text = self.call_kimi(prompt=prompt, history=history)
            else:
                output_text = self.call_gpt(prompt=prompt, history=history)

        else:
            prompt = prompt[0:self.local_max_length]
            output_text, _ = self.model.chat(self.tokenizer,
                                             prompt,
                                             history,
                                             top_k=1)
            print((prompt, output_text))
        time_finish = time.time()

        logger.debug('Q:{} A:{} \t\t remote {} timecost {} '.format(
            prompt[-100:-1], output_text, remote,
            time_finish - time_tokenizer))
        return output_text


def parse_args():
    parser = argparse.ArgumentParser(description='Hybrid LLM Server.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help=  # noqa E251
        'Hybrid LLM Server configuration path. Default value is config.ini'  # noqa E501
    )
    args = parser.parse_args()
    return args


def llm_serve(config_path: str, server_ready: Value):
    # logger.add('logs/server.log', rotation="4MB")
    with open(config_path) as f:
        llm_config = pytoml.load(f)['llm']
        bind_port = int(llm_config['server']['bind_port'])

    server = HybridLLMServer(llm_config=llm_config)

    async def inference(request):

        input_json = await request.json()
        print(input_json)

        prompt = input_json['prompt']
        history = input_json['history']
        remote = False
        if 'remote' in input_json:
            remote = input_json['remote']
        text = server.generate_response(prompt=prompt,
                                        history=history,
                                        remote=remote)
        return web.json_response({'text': text})

    app = web.Application()
    app.add_routes([web.post('/inference', inference)])
    server_ready.value = True
    web.run_app(app, host='0.0.0.0', port=bind_port)


def main():
    args = parse_args()
    server_ready = Value('b', False)

    server_process = Process(target=llm_serve,
                             args=(args.config_path, server_ready))
    server_process.daemon = True
    server_process.start()

    from llm_client import ChatClient
    client = ChatClient(config_path=args.config_path)
    while not server_ready.value:
        logger.info('waiting for server to be ready..')
        time.sleep(3)
    print(client.generate_response(prompt='今天天气如何？', history=[], remote=False))


def simple_bind():
    args = parse_args()
    server_ready = Value('b', False)

    llm_serve(args.config_path, server_ready)


if __name__ == '__main__':
    simple_bind()
