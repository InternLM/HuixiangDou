# Copyright (c) OpenMMLab. All rights reserved.
"""LLM client."""
import argparse
import json

import pytoml
import requests
from loguru import logger


class ChatClient:
    """A class to handle client-side interactions with a chat service.

    This class is responsible for loading configurations from a given path,
    building prompts, and generating responses by interacting with the chat
    service.
    """

    def __init__(self, config_path: str) -> None:
        """Initialize the ChatClient with the path of the configuration
        file."""
        self.config_path = config_path
        self.llm_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']

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

    def auto_fix(self, backend):
        """Choose real backend according to config.ini."""

        enable_local, enable_remote = (self.llm_config['enable_local'],
                                       self.llm_config['enable_remote'])
        local_len, remote_len = (
            self.llm_config['server']['local_llm_max_text_length'],
            self.llm_config['server']['remote_llm_max_text_length'])

        max_length = local_len
        if enable_remote:
            max_length = remote_len

        if backend == 'local' and not enable_local:
            backend = self.llm_config['server']['remote_type']
            max_length = remote_len
        elif backend != 'local' and not enable_remote:
            backend = 'local'
            max_length = local_len

        return backend, max_length

    def generate_response(self, prompt, history=[], backend='local'):
        """Generate a response from the chat service.

        Args:
            prompt (str): The prompt to send to the chat service.
            history (list, optional): List of previous interactions. Defaults to [].
            backend (str, optional): Determine which LLM should be called. Default to `local`

        Returns:
            str: Generated response from the chat service.
        """
        url = self.llm_config['client_url']
        real_backend, max_length = self.auto_fix(backend=backend)

        if len(prompt) > max_length:
            logger.warning(
                f'prompt length {len(prompt)}  > max_length {max_length}, truncated'  # noqa E501
            )
            prompt = prompt[0:max_length]

        try:
            header = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {
                'prompt': prompt,
                'history': data_history,
                'backend': real_backend
            }
            resp = requests.post(url,
                                 headers=header,
                                 data=json.dumps(data),
                                 timeout=300)
            if resp.status_code != 200:
                raise Exception(str((resp.status_code, resp.reason)))

            json_obj = resp.json()
            text = json_obj['text']
            if 'error' in json_obj:
                error = json_obj['error']
                if len(error) > 0:
                    logger.error(error)
            return text
        except Exception as e:
            logger.error(str(e))
            logger.error(
                'Do you forget `--standalone` when `python3 -m huixiangdou.main` ?'  # noqa E501
            )
            return ''


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Client for hybrid llm service.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Configuration path. Default value is config.ini'  # noqa E501
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    client = ChatClient(config_path=args.config_path)
    question = '“{}”\n请仔细阅读以上问题，提取其中的实体词，结果直接用 list 表示，不要解释。'.format(
        '请问triviaqa 5shot结果怎么在summarizer里输出呢')
    print(client.generate_response(prompt=question, backend='local'))

    print(
        client.generate_response(prompt='请问 ncnn 的全称是什么',
                                 history=[('ncnn 是什么',
                                           'ncnn中的n代表nihui，cnn代表卷积神经网络。')],
                                 backend='remote'))
