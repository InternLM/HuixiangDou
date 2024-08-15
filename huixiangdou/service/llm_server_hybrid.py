# Copyright (c) OpenMMLab. All rights reserved.
"""LLM server proxy."""
import argparse
import json
import os
import random
import time
from multiprocessing import Process, Value, set_start_method
import torch
import pdb
import pytoml
import requests
from loguru import logger
from openai import OpenAI
from huixiangdou.primitive import RPM
import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

import uvicorn
from typing import List, Tuple

def os_run(cmd: str):
    ret = os.popen(cmd)
    ret = ret.read().rstrip().lstrip()
    return ret

def check_gpu_max_memory_gb():
    try:
        import torch
        device = torch.device('cuda')
        return torch.cuda.get_device_properties(
            device).total_memory / (  # noqa E501
                1 << 30)
    except Exception as e:
        logger.error(str(e))
    return -1


def build_messages(prompt, history, system: str = None):
    messages = []
    if system is not None and len(system) > 0:
        messages.append({'role': 'system', 'content': system})
    for item in history:
        messages.append({'role': 'user', 'content': item[0]})
        messages.append({'role': 'assistant', 'content': item[1]})
    messages.append({'role': 'user', 'content': prompt})
    return messages


class InferenceWrapper:
    """A class to wrapper kinds of inference framework."""

    def __init__(self, model_path: str):
        """Init model handler."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path,
                                                       trust_remote_code=True)

        model_path_lower = model_path.lower()

        if 'qwen2' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype='auto',
                device_map='auto',
                trust_remote_code=True).eval()
        elif 'qwen1.5' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path, device_map='auto', trust_remote_code=True).eval()
        elif 'qwen' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map='auto',
                trust_remote_code=True,
                use_cache_quantization=True,
                use_cache_kernel=True,
                use_flash_attn=False).eval()
        elif 'internlm2_5' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                trust_remote_code=True).cuda().eval()
        elif 'internlm2' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                device_map='auto',
                torch_dtype='auto').eval()
        else:
            raise ValueError('Unknown model path {}'.format(model_path))

    async def chat_stream(self, prompt: str, history=[]):
        """Generate a stream response from local LLM. Wrap transformer API to async generator

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        output_text = ''

        if type(self.model).__name__ == 'Qwen2ForCausalLM':
            messages = build_messages(
                prompt=prompt,
                history=history,
                system='You are a helpful assistant')  # noqa E501
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            model_inputs = self.tokenizer([text],
                                          return_tensors='pt').to('cuda')
            generated_ids = self.model.generate(model_inputs.input_ids,
                                                max_new_tokens=512,
                                                top_k=1)
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(
                    model_inputs.input_ids, generated_ids)
            ]

            output_text = self.tokenizer.batch_decode(
                generated_ids, skip_special_tokens=True)[0]
            yield output_text

        elif type(self.model).__name__ == 'InternLM2ForCausalLM':

            if '请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。' in prompt:
                prompt = '你是一个语言专家，擅长分析语句并打分。\n' + prompt

            length = 0
            for response, _ in self.model.stream_chat(self.tokenizer, prompt, history, top_k=1, do_sample=False):
                part = response[length:]
                length = len(response)
                yield part

        else:
            raise ValueError('Unknown model type {}'.format(type(self.model).__name__))

    def chat(self, prompt: str, history=[]):
        """Generate a sync response from local LLM. Sync chat.

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        loop = asyncio.get_event_loop()

        async def coroutine_wrapper():
            messages = []
            async for part in self.chat_stream(prompt=prompt, history=history):
                messages.append(part)
            return ''.join(messages)
        content = loop.run_until_complete(coroutine_wrapper())
        return content


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
                 retry=2) -> None:
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

        _rpm = 500
        if 'rpm' in self.server_config:
            _rpm = self.server_config['rpm']
        self.rpm = RPM(_rpm)

        if self.enable_local:
            self.inference = InferenceWrapper(model_path)
        else:
            self.inference = None
            logger.warning('local LLM disabled.')

    async def call_kimi(self, prompt, history):
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

        SYSTEM = '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力，政治宗教等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'  # noqa E501
        # 20240531 hacking for kimi API incompatible
        # it is very very tricky, please do not change this magic prompt !!!
        if '请仔细阅读以上内容，判断句子是否是个有主题的疑问句' in prompt:
            SYSTEM = '你是一个语文专家，擅长对句子的结构进行分析'

        messages = build_messages(prompt=prompt,
                                  history=history,
                                  system=SYSTEM)

        logger.debug('remote api sending: {}'.format(messages))
        model = self.server_config['remote_llm_model']

        if model == 'auto':
            prompt_len = len(prompt)
            if prompt_len <= int(8192 * 1.5) - 1024:
                model = 'moonshot-v1-8k'
            elif prompt_len <= int(32768 * 1.5) - 1024:
                model = 'moonshot-v1-32k'
            else:
                prompt = prompt[0:int(128000 * 1.5) - 1024]
                model = 'moonshot-v1-128k'

        logger.info('choose kimi model {}'.format(model))

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            stream=True
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def call_step(self, prompt, history):
        """Generate a response from step, see
        https://platform.stepfun.com/docs/overview/quickstart.

        Args:
            prompt (str): The prompt to send to LLM.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from LLM.
        """
        client = OpenAI(
            api_key=self.server_config['remote_api_key'],
            base_url='https://api.stepfun.com/v1',
        )

        SYSTEM = '你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容'  # noqa E501
        messages = build_messages(prompt=prompt,
                                  history=history,
                                  system=SYSTEM)

        logger.debug('remote api sending: {}'.format(messages))

        model = self.server_config['remote_llm_model']

        if model == 'auto':
            prompt_len = len(prompt)
            if prompt_len <= int(8192 * 1.5) - 1024:
                model = 'step-1-8k'
            elif prompt_len <= int(32768 * 1.5) - 1024:
                model = 'step-1-32k'
            elif prompt_len <= int(128000 * 1.5) - 1024:
                model = 'step-1-128k'
            else:
                prompt = prompt[0:int(256000 * 1.5) - 1024]
                model = 'step-1-256k'

        logger.info('choose step model {}'.format(model))

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def call_openai(self,
                 prompt: str,
                 history: List,
                 base_url: str = None,
                 system: str = None):
        """Generate a response from openai API.

        Args:
            prompt (str): The prompt to send to openai API.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from RPC.
        """
        if base_url is not None:
            client = OpenAI(api_key=self.server_config['remote_api_key'],
                            base_url=base_url)
        else:
            client = OpenAI(api_key=self.server_config['remote_api_key'])

        messages = build_messages(prompt=prompt,
                                  history=history,
                                  system=system)

        logger.debug('remote api sending: {}'.format(messages))
        stream = client.chat.completions.create(
            model=self.server_config['remote_llm_model'],
            messages=messages,
            temperature=0.0,
            stream=True
        )
        for chunk in stream:
            if chunk.choices is None:
                raise Exception(str(chunk))
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def chat_stream(self, prompt, history=[], backend='local'):
        """Generate a response from the appropriate LLM based on the
        configuration. If failed, use exponential backoff. Async generator.

        Args:
            prompt (str): The prompt to send to the LLM.
            history (list, optional): List of previous interactions. Defaults to [].  # noqa E501
            remote (bool, optional): Flag to determine whether to use a remote server. Defaults to False.  # noqa E501
            backend (str): LLM type to call. Support 'local', 'remote' and specified LLM name ('kimi', 'deepseek' and so on)

        Returns:
            str: Generated response from the LLM. If LLM not support stream reply, just reply once.
        """

        if backend == 'local' and self.inference is None:
            logger.error(
                "!!! fatal error.  !!! \n Detect `enable_local=0` in `config.ini` while backend='local', please immediately stop the service and check it. \n For this request, autofix the backend to '{}' and proceed."
                .format(self.server_config['remote_type']))
            backend = self.server_config['remote_type']

        if backend == 'remote':
            # not specify remote LLM type, use config
            backend = self.server_config['remote_type']

        if backend == 'local':
            prompt = prompt[0:self.local_max_length]
            """# Caution: For the results of this software to be reliable and verifiable,  # noqa E501
            it's essential to ensure reproducibility. Thus `GenerationMode.GREEDY_SEARCH`  # noqa E501
            must enabled."""

            async for value in self.inference.chat_stream(prompt, history):
                yield value

        else:
            output_text = ''
            prompt = prompt[0:self.remote_max_length]

            map_fn = {
                'kimi': self.call_kimi,
                'step': self.call_step,
                'puyu': self.call_openai,
                'deepseek': self.call_openai,
                'zhipuai': self.call_openai,
                'xi-api': self.call_openai,
                'gpt': self.call_openai,
                'siliconcloud': self.call_openai
            }

            map_base_url = {
                'xi-api': 'https://api.xi-ai.cn/v1',
                'deepseek': 'https://api.deepseek.com/v1',
                'zhipuai': 'https://open.bigmodel.cn/api/paas/v4/',
                'puyu': 'https://puyu.openxlab.org.cn/puyu/api/v1/',
                'siliconcloud': 'https://api.siliconflow.cn/v1'
            }

            if backend not in map_fn:
                raise ValueError('unknown backend {}'.format(backend))
            
            target_fn = map_fn[backend]
            args = {'prompt': prompt, 'history': history}

            if backend in map_base_url:
                args['base_url'] = map_base_url[backend]

            if backend in ['xi-api', 'deepseek']:
                args['system'] = 'You are a helpful assistant.'

            life = 0
            while life < self.retry:
                try:
                    self.rpm.wait()
                    async for value in target_fn(**args):
                        yield value                     
                    # skip retry
                    break

                except Exception as e:
                    # exponential backoff
                    error = str(e)
                    logger.error(error)

                    if 'Error code: 401' in error or 'invalid api_key' in error or 'Authentication Fails' in error:
                        raise e

                    life += 1
                    randval = random.randint(1, int(pow(2, life)))
                    time.sleep(randval)

            yield output_text

    def chat(self, prompt: str, history=[], backend:str='local'):
        """Generate a sync response from local LLM.

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        time_tokenizer = time.time()
        
        async def coroutine_wrapper():
            messages = []
            async for part in self.chat_stream(prompt=prompt, history=history, backend=backend):
                messages.append(part)
                print(part, end='')
            return ''.join(messages)

        loop = asyncio.get_event_loop()
        try:
            output_text = loop.run_until_complete(coroutine_wrapper())
        except Exception as e:
            return '', e

        time_finish = time.time()

        logger.debug('Q:{} A:{} \t\t backend {} timecost {} '.format(
            prompt[-100:-1], output_text, backend,
            time_finish - time_tokenizer))
        return output_text, None

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

class Talk(BaseModel):
    prompt: str
    backend: str = 'local'
    history: List[Tuple[str, str]] = []

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

    async def inference(talk: Talk):
        """Call local llm inference."""

        prompt = talk.prompt
        history = talk.history
        backend = talk.backend

        parts = []
        try:
            async for text in server.chat_stream(prompt=prompt, history=history, backend=backend):
                parts.append(text)
            return {'text': ''.join(parts), 'error': ''}
        except Exception as e:
            return {'text': '', 'error': str(e)}

    async def stream(talk: Talk):
        """Call local llm inference."""

        prompt = talk.prompt
        history = talk.history
        backend = talk.backend

        async def generate():
            async for text in server.chat_stream(prompt=prompt, history=history, backend=backend):
                yield text
        return EventSourceResponse(generate())

    app = FastAPI(docs_url='/')
    app.add_middleware(CORSMiddleware,
                    allow_origins=['*'],
                    allow_credentials=True,
                    allow_methods=['*'],
                    allow_headers=['*'])
    router = APIRouter()
    router.add_api_route('/inference', inference, methods=['POST'])
    router.add_api_route('/stream', stream, methods=['POST'])
    app.include_router(router)
    uvicorn.run(app, host='0.0.0.0', port=bind_port, log_level='info')


def start_llm_server(config_path: str):
    set_start_method('spawn')
    server_ready = Value('i', 0)
    server_process = Process(target=llm_serve,
                             args=(config_path, server_ready))
    server_process.daemon = True
    server_process.start()
    while True:
        if server_ready.value == 0:
            logger.info('waiting for server to be ready..')
            time.sleep(2)
        elif server_ready.value == 1:
            break
        else:
            logger.error('start local LLM server failed, quit.')
            raise Exception('local LLM path')
    logger.info('Hybrid LLM Server start.')


def main():
    """Function to start the server without running a separate process."""
    args = parse_args()
    server_ready = Value('i', 0)
    if not args.unittest:
        llm_serve(args.config_path, server_ready)
    else:
        queries = ['今天天气如何？']
        start_llm_server(config_path=args.config_path)

        from .llm_client import ChatClient
        client = ChatClient(config_path=args.config_path)
        for query in queries:
            print(
                client.generate_response(prompt=query,
                                         history=[],
                                         backend='local'))

if __name__ == '__main__':
    main()
