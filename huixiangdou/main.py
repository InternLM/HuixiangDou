#!/usr/bin/env python3
# Copyright (c) OpenMMLab. All rights reserved.
"""HuixiangDou binary."""
import argparse
import os
import time
from multiprocessing import Process, Value

import pytoml
import requests
from loguru import logger

from .frontend import Lark
from .service import ErrorCode, Worker, llm_serve


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=False,
                        help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


def check_env(args):
    """Check or create config.ini and logs dir."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    CONFIG_NAME = 'config.ini'
    CONFIG_URL = 'https://raw.githubusercontent.com/InternLM/HuixiangDou/main/config.ini'  # noqa E501
    if not os.path.exists(CONFIG_NAME):
        logger.warning(
            f'{CONFIG_NAME} not found, download a template from {CONFIG_URL}.')

        try:
            response = requests.get(CONFIG_URL, timeout=5)
            response.raise_for_status()
            with open(CONFIG_NAME, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            logger.error(f'Failed to download file due to {e}')
            raise e

    if not os.path.exists(args.work_dir):
        logger.warning(
            f'args.work_dir dir not exist, auto create {args.work_dir}.')
        os.makedirs(args.work_dir)


def run():
    """Automatically download config, start llm server and run examples."""
    args = parse_args()
    check_env(args)

    if args.standalone:
        # hybrid llm serve
        server_ready = Value('i', 0)
        server_process = Process(target=llm_serve,
                                 args=(args.config_path, server_ready))
        server_process.daemon = True
        server_process.start()
        while True:
            if server_ready.value == 0:
                logger.info('waiting for server to be ready..')
                time.sleep(3)
            elif server_ready.value == 1:
                break
            else:
                logger.error('start local LLM server failed, quit.')
                raise Exception('local LLM path')
        logger.info('Hybrid LLM Server start.')

    # query by worker
    with open(args.config_path, encoding='utf8') as f:
        fe_config = pytoml.load(f)['frontend']
    logger.info('Config loaded.')
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    # queries = ['请教下视频流检测 跳帧  造成框一闪一闪的  有好的优化办法吗',
    #    '请教各位佬一个问题，虽然说注意力的长度等于上下文的长度。但是，增大上下文推理长度难道只有加长注意力机制一种方法吗？比如Rope啥的，应该不是吧',   # noqa E501
    #   '大佬们，现在要做一个轻量级的抬手放手检测，有什么好的模型吗？']
    queries = ['请教下视频流检测 跳帧  造成框一闪一闪的  有好的优化办法吗']

    for query in queries:
        code, reply = assistant.generate(query=query, history=[], groupname='')
        logger.info(f'{code}, {query}, {reply}')
        if fe_config['type'] == 'lark' and code == ErrorCode.SUCCESS:
            # send message to lark group
            lark = Lark(webhook=fe_config['webhook_url'])
            logger.info(f'send {reply} to lark group.')
            lark.send_text(msg=reply)

    # server_process.join()


if __name__ == '__main__':
    run()
