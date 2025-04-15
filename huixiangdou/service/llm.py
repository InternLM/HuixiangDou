"""LLM server proxy."""
import json
import os
from ..primitive.limitter import RPM, TPM
from ..primitive.token import encode_string, decode_tokens
import asyncio
from typing import Dict
import pytoml
from loguru import logger
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, Timeout, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from functools import wraps

os.environ["TOKENIZERS_PARALLELISM"] = "false"

backend2url = {
    "kimi": "https://api.moonshot.cn/v1",
    "step": "https://api.stepfun.com/v1",
    'xi-api': 'https://api.xi-ai.cn/v1',
    'deepseek': 'https://api.deepseek.com/v1',
    'zhipuai': 'https://open.bigmodel.cn/api/paas/v4/',
    'siliconcloud': 'https://api.siliconflow.cn/v1',
    'local': 'http://localhost:8000/v1',
    'vllm': 'http://localhost:8000/v1',
    'ppio': 'https://api.ppinfra.com/v3/openai',
    'internlm': 'https://chat.intern-ai.org.cn/api/v1'
}

backend2model = {
    "kimi": "auto",
    "step": "auto",
    "deepseek": "deepseek-chat",
    "zhipuai": "glm-4",
    "siliconcloud": "Qwen/Qwen2.5-14B-Instruct",
    "ppio": "thudm/glm-4-9b-chat"
}

def limit_async_func_call(max_size: int, waitting_time: float = 0.1):
    """Add restriction of maximum async calling times for a async func"""

    def final_decro(func):
        """Not using async.Semaphore to aovid use nest-asyncio"""
        __current_size = 0

        @wraps(func)
        async def wait_func(*args, **kwargs):
            nonlocal __current_size
            while __current_size >= max_size:
                await asyncio.sleep(waitting_time)
            __current_size += 1
            result = await func(*args, **kwargs)
            __current_size -= 1
            return result

        return wait_func

    return final_decro


class Backend:

    def __init__(self, name: str, data: Dict):
        self.api_key = data.get('remote_api_key', '')
        self._type = data.get('remote_type', '')
        self.max_token_size = data.get('remote_llm_max_text_length', 32000) - 4096
        if self.max_token_size < 0:
            raise Exception(f'{self.max_token_size} < 4096')
        self.rpm = RPM(int(data.get('rpm', 500)))
        self.tpm = TPM(int(data.get('tpm', 50000)))
        self.name = name
        self.port = int(data.get('port', 23333))
        self.model = data.get('remote_llm_model', '')
        self.base_url = data.get('base_url', '')
        if not self.base_url and name in backend2url:
            self.base_url = backend2url[name]

    def jsonify(self):
        return {"api_key": self.name, "model": self.model}

    def __str__(self):
        return json.dumps(self.jsonify())


class LLM:

    def __init__(self, config_path: str):
        """Initialize the LLM with the path of the configuration file."""
        self.config_path = config_path
        self.llm_config = None
        self.backends = dict()
        self.sum_input_token_size = 0
        self.sum_output_token_size = 0
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']['server']
            name = self.llm_config['remote_type']
            self.backends[name] = Backend(name=name, data=self.llm_config)

    def choose_model(self, backend: Backend, token_size: int) -> str:
        model = backend.model
        response_reserve_length = 2048
        if backend.name == 'kimi' and model == 'auto':
            if token_size <= 8192 - response_reserve_length:
                model = 'moonshot-v1-8k'
            elif token_size <= 32768 - response_reserve_length:
                model = 'moonshot-v1-32k'
            elif token_size <= 128000 - response_reserve_length:
                model = 'moonshot-v1-128k'
            else:
                raise ValueError('Input token length exceeds 128k')
        elif backend.name == 'step' and model == 'auto':
            if token_size <= 8192 - response_reserve_length:
                model = 'step-1-8k'
            elif token_size <= 32768 - response_reserve_length:
                model = 'step-1-32k'
            elif token_size <= 128000 - response_reserve_length:
                model = 'step-1-128k'
            elif token_size <= 256000 - response_reserve_length:
                model = 'step-1-256k'
            else:
                raise ValueError('Input token length exceeds 256k')
        elif not model and backend.name in backend2model:
            model = backend2model[backend.name]
        return model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=60),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, Timeout, APITimeoutError)),
    )
    @limit_async_func_call(16)
    async def chat(self,
                   prompt: str,
                   backend: str = 'default',
                   system_prompt='你是茴香豆，简称豆哥。是一个微信群机器人，用于回答群友的疑问。',
                   history=[],
                   allow_truncate=False,
                   max_tokens=1024,
                   timeout=600,
                   tools=[]) -> str:
        # choose backend
        # if user not specify model, use first one
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        instance = self.backends[backend]

        # try truncate input prompt
        input_tokens = encode_string(content=str(prompt)+str(history))
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(
                    f'input token size {input_token_size}, max {instance.max_token_size}'
                )

            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)

        await instance.tpm.wait(token_count=input_token_size)

        # build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        content = ''
        # try:
        model = self.choose_model(backend=instance,
                                  token_size=input_token_size)
        openai_async_client = AsyncOpenAI(base_url=instance.base_url,
                                          api_key=instance.api_key,
                                          timeout=timeout)

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.7,
            "tools": tools
        }
        if max_tokens:
            kwargs['max_tokens'] = max_tokens

        try:
            response = await openai_async_client.chat.completions.create(**kwargs)
        except Exception as e:
            import pdb
            pdb.set_trace()
            pass
        logger.info(response.choices[0].message.content)

        content = response.choices[0].message.content
        content_token_size = len(encode_string(content=content))

        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size

        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return content.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=60),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, Timeout, APITimeoutError)),
    )
    async def chat_stream(self,
                          prompt: str,
                          backend: str = 'default',
                          system_prompt=None,
                          history=[],
                          allow_truncate=False,
                          max_tokens=1024,
                          timeout=600):
        # choose backend
        # if user not specify model, use first one
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        instance = self.backends[backend]

        # try truncate input prompt
        input_tokens = encode_string(content=str(prompt)+str(history))
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(
                    f'input token size {input_token_size}, max {instance.max_token_size}'
                )

            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)

        await instance.tpm.wait(token_count=input_token_size)

        # build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        content = ''
        try:
            model = self.choose_model(backend=instance,
                                      token_size=input_token_size)
            openai_async_client = AsyncOpenAI(base_url=instance.base_url,
                                              api_key=instance.api_key,
                                              timeout=timeout)

            stream = await openai_async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                top_p=0.7,
                max_tokens=max_tokens,
                stream=True)

            content = ""
            async for chunk in stream:
                if chunk.choices is None:
                    raise Exception(str(chunk))
                delta = chunk.choices[0].delta
                if delta.content:
                    content += delta.content
                    yield delta.content

        except Exception as e:
            logger.error(str(e) + ' input len {}'.format(len(str(messages))))
            raise e
        content_token_size = len(encode_string(content=content))

        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size

        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return

    def default_model_info(self):
        backend = list(self.backends.keys())[0]
        instance = self.backends[backend]
        return instance.jsonify()
    
    def build_prompt(self,
                     history_pair,
                     instruction: str,
                     template: str,
                     context: str = '',
                     reject: str = '<reject>'):
        """Build a prompt for interaction.

        Args:
            history_pair (list): List of previous interactions.
            instruction (str): Instruction for the current interaction.
            template (str): Template for constructing the interaction.
            context (str, optional): Context of the interaction. Defaults to ''.  # noqa E501
            reject (str, optional): Text that indicates a rejected interaction. Defaults to '<reject>'.  # noqa E501

        Returns:
            tuple: A tuple containing the constructed instruction and real history.
        """
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
