import argparse
import os

from transformers import AutoModelForCausalLM, AutoTokenizer
from loguru import logger
import time
import json
import torch
import random
from aiohttp import web
import pytoml


class HybridLLMServer(object):

    def __init__(self,
                 llm_config: dict,
                 device: str = "cuda",
                 retry=3) -> None:
        self.device = device
        self.retry = retry
        self.llm_config = llm_config
        self.local_max_length = llm_config[
            'server_local_internlm_max_text_length']
        self.remote_max_length = llm_config[
            'server_remote_kimi_max_text_length']

        model_path = llm_config['server_local_internlm_path']
        self.tokenizer = AutoTokenizer.from_pretrained(model_path,
                                                       trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            device_map="auto",
            fp16=True,
        ).eval()

    def generate_response(self, prompt, history=[], remote=False):
        output_text = ''
        time_tokenizer = time.time()

        if not llm_config['server_remote_kimi_enable'] and remote:
            remote = False
            logger.error(
                'llm.server_remote_kimi_enable off, auto set remote=False')

        if remote:
            prompt = prompt[0:self.remote_max_length]
            # call remote LLM
            from openai import OpenAI
            client = OpenAI(
                api_key=llm_config['server_remote_kimi_api_key'],
                base_url="https://api.moonshot.cn/v1",
            )

            messages = [{
                "role":
                "system",
                "content":
                "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力，政治宗教等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
            }]
            for item in history:
                messages.append({"role": "user", "content": item[0]})
                messages.append({"role": "system", "content": item[1]})
            messages.append({"role": "user", "content": prompt})

            life = 0
            while life < self.retry:
                try:
                    logger.debug('remote api sending: {}'.format(messages))
                    completion = client.chat.completions.create(
                        model="moonshot-v1-128k",
                        messages=messages,
                        temperature=0.3,
                    )
                    output_text = completion.choices[0].message.content
                except Exception as e:
                    logger.error(str(e))
                    log_message = str(e).lower()
                    # retry
                    life += 1
                    randval = random.randint(1, int(pow(2, life)))
                    time.sleep(randval)
                break
        else:
            prompt = prompt[0:self.local_max_length]
            output_text, _ = self.model.chat(self.tokenizer,
                                             prompt,
                                             history,
                                             top_k=1)
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
        help='Hybrid LLM Server configuration path. Default value is config.ini'
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logger.add('logs/server.log', rotation="4MB")

    args = parse_args()
    with open(args.config_path) as f:
        llm_config = pytoml.load(f)['llm']
        bind_port = int(llm_config['server_bind_port'])
        model_path = llm_config['server_local_internlm_path']

    server = HybridLLMServer(llm_config=llm_config)

    async def inference(request):
        input_json = await request.json()
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
    web.run_app(app, host='0.0.0.0', port=bind_port)
