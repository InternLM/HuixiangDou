# Copyright (c) OpenMMLab. All rights reserved.
"""LLM server proxy."""
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

class InferenceWrapper:
    """A class to wrapper kinds of inference framework"""
    def __init__(self, model_path: str, local_max_length: int = 8000):
        """Init model handler."""
        self.inference = 'huggingface'

        # try:
        #     import lmdeploy
        #     from lmdeploy import pipeline, GenerationConfig, TurbomindEngineConfig
        #     self.inference = 'lmdeploy'
        # except ImportError:
        #     logger.warning(
        #         "Warning: auto enable lmdeploy for higher efficiency"  # noqa E501
        #         "https://github.com/internlm/lmdeploy"
        #     )
        
        # if self.inference == 'huggingface':
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            device_map='auto',
            torch_dtype='auto'
        ).eval()

        # else:
            # backend_config = TurbomindEngineConfig(rope_scaling_factor=2.0, session_len=local_max_length)
            # self.pipe = pipeline(model_path, backend_config=backend_config)
            # self.gen_config = GenerationConfig(top_p=0.8,
            #                             top_k=1,
            #                             temperature=0.8,
            #                             max_new_tokens=1024)
    
    def chat(self, prompt:str, history=[]):
        """Generate a response from local LLM.

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        output_text = ''
        # if self.inference == 'huggingface':
        output_text, _ = self.model.chat(self.tokenizer,
                                            prompt,
                                            history,
                                            top_k=1,
                                            do_sample=False)
        # elif self.inference == 'lmdeploy':
        #     output_text = pipe(prompt, gen_config=self.gen_config)
        # else:
        #     raise Exception(f'unknown inference framework {self.inference}')
        return output_text


class HybridLLMServer:
    """A class to handle server-side interactions with a hybrid language
    learning model (LLM) service.

    This class is responsible for initializing the local and remote LLMs,
    generating responses from these models as per the provided configuration,
    and handling retries in case of failures.
    """

    def __init__(self,
                 llm_config: dict,
                 device: str = 'cuda',
                 retry=3) -> None:
        """Initialize the HybridLLMServer with the given configuration, device,
        and number of retries."""
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

        if self.enable_local:
            self.inference = InferenceWrapper(model_path)
        else:
            logger.warning('local LLM disabled.')

    def call_kimi(self, prompt, history):
        """Generate a response from Kimi (a remote LLM).

        Args:
            prompt (str): The prompt to send to Kimi.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from Kimi.
        """
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
        """Generate a response from GPT (a remote LLM).

        Args:
            prompt (str): The prompt to send to GPT-3.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from GPT-3.
        """
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
        """Generate a response from the appropriate LLM based on the
        configuration.

        Args:
            prompt (str): The prompt to send to the LLM.
            history (list, optional): List of previous interactions. Defaults to [].  # noqa E501
            remote (bool, optional): Flag to determine whether to use a remote server. Defaults to False.  # noqa E501

        Returns:
            str: Generated response from the LLM.
        """
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
            """# Caution: For the results of this software to be reliable and verifiable,  # noqa E501
            it's essential to ensure reproducibility. Thus `GenerationMode.GREEDY_SEARCH`  # noqa E501
            must enabled."""

            output_text = self.inference.chat(prompt, history)

            logger.info((prompt, output_text))
        time_finish = time.time()

        logger.debug('Q:{} A:{} \t\t remote {} timecost {} '.format(
            prompt[-100:-1], output_text, remote,
            time_finish - time_tokenizer))
        return output_text


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Hybrid LLM Server.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help=  # noqa E251
        'Hybrid LLM Server configuration path. Default value is config.ini'  # noqa E501
    )
    parser.add_argument('--unittest',
                        action='store_true',
                        default=False,
                        help='Test with samples.')
    args = parser.parse_args()
    return args


def llm_serve(config_path: str, server_ready: Value):
    """Start the LLM server.

    Args:
        config_path (str): Path to the configuration file.
        server_ready (multiprocessing.Value): Shared variable to indicate when the server is ready.  # noqa E501
    """
    # logger.add('logs/server.log', rotation="4MB")
    with open(config_path, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
        bind_port = int(llm_config['server']['local_llm_bind_port'])

    try:
        server = HybridLLMServer(llm_config=llm_config)
        server_ready.value = 1
    except Exception as e:
        server_ready.value = -1
        raise (e)

    async def inference(request):
        """Call local llm inference."""

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
    web.run_app(app, host='0.0.0.0', port=bind_port)


def main():
    """Function to start the server without running a separate process."""
    args = parse_args()
    server_ready = Value('i', 0)

    if not args.unittest:
        llm_serve(args.config_path, server_ready)
    else:
        server_process = Process(target=llm_serve,
                                args=(args.config_path, server_ready))
        server_process.daemon = True
        server_process.start()

        from .llm_client import ChatClient
        client = ChatClient(config_path=args.config_path)
        while server_ready.value == 0:
            logger.info('waiting for server to be ready..')
            time.sleep(3)

        queries = ['今天天气如何？']
        for query in queries:
            print(client.generate_response(prompt=query, history=[], remote=False))


if __name__ == '__main__':
    main()
