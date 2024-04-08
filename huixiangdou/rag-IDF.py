#!/usr/bin/env python3
# Copyright (c) OpenMMLab. All rights reserved.
"""HuixiangDou binary."""
import argparse
import os
import time
from multiprocessing import Process, Value

import pytoml
import requests
from aiohttp import web
from loguru import logger

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
    parser.add_argument(
        '--input',
        default='sft-data/input.json',
        type=str,
        help='json filepath for user queries')

    parser.add_argument(
        '--output',
        default='sft-data/output.json',
        type=str,
        help='formatted output')
    args = parser.parse_args()
    return args

def run():
    """Automatically download config, start llm server and run examples."""
    args = parse_args()

    if not os.path.exists(args.input):
        logger.error('{} not exist'.format(args.input))
        return
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    
    queries = json.load(args.input)
    
    for query in queries:
        code, response, refs = assistant.generate(query=query, history=[], groupname='')
        result = {
            'query': query,
            'code': int(code),
            'refs': refs            
        }

        with open(args.output, 'a') as f:
            json_str = json.dumps(result, indent=2, enable_ascii=False)
            f.write(json_str)
            f.write('\n')

if __name__ == '__main__':
    run()
