#!/usr/bin/env python3
# Copyright (c) OpenMMLab. All rights reserved.
"""HuixiangDou binary."""
import argparse
import json
import os
import time
from multiprocessing import Pool, Process, Value

import pytoml
import requests
from loguru import logger

from .service import ErrorCode, Worker, llm_serve


class Task:

    def __init__(self, id: int, query: str, direct_reply: str = ''):
        """Build rag task, direct_reply is original LLM response."""
        self.id = id
        self.query = query
        self.direct_reply = direct_reply
        self.rag_reply = ''
        self.code = -1
        self.reason = ''
        self.refs = []

    def to_json_str(self):
        obj = {
            'id': int(self.id),
            'query': str(self.query),
            'direct_reply': str(self.direct_reply),
            'rag_reply': str(self.rag_reply),
            'code': int(self.code),
            'reason': str(self.reason),
            'refs': self.refs
        }
        return json.dumps(obj, indent=2, ensure_ascii=False)


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config-alignment.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument(
        '--input',
        default='resource/rag_example_input.json',
        type=str,
        help=
        'JSON filepath for user queries. Default value is `resource/rag_example_input.json`'
    )
    parser.add_argument(
        '--output-dir',
        default='resource',
        type=str,
        help='Formatted JSON output dir, use `resource/` by default')
    parser.add_argument(
        '--processes',
        default=1,
        type=int,
        help='Process count considered LLM RPM. Default value is 2')
    args = parser.parse_args()
    return args


def rag(process_id: int, task: list, output_dir: str):
    """Extract structured output with RAG."""

    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)

    # assistant.TOPIC_TEMPLATE = '告诉我这句话的关键字和主题，直接说主题不要解释：“{}”'

    output_path = os.path.join(output_dir, 'output{}.json'.format(process_id))
    for item in task:
        query = item.query

        code, response, refs = assistant.generate(query=query,
                                                  history=[],
                                                  groupname='')

        item.rag_reply = response
        item.code = int(code)
        item.reason = str(code)
        item.refs = refs

        if item.code == 0:
            item.direct_reply = assistant.direct_chat(query=query)

        with open(output_path, 'a') as f:
            f.write(item.to_json_str())
            f.write('\n')


def split_tasks(json_path: str, processes: int):
    """Split queries for multiple processes."""
    queries = []
    tasks = []
    _all = []
    with open(json_path) as f:
        queries = json.load(f)

    for idx, query in enumerate(queries):
        _all.append(Task(idx, query))

    step = (len(_all) + processes - 1) // processes
    for idx in range(processes):
        start = idx * step
        tasks.append(_all[start:start + step])

    # check task number and assert
    _sum = 0
    for task in tasks:
        _sum += len(task)
    assert _sum == len(queries)

    return tasks


if __name__ == '__main__':
    args = parse_args()

    tasks = split_tasks(args.input, args.processes)

    if args.processes == 1:
        rag(0, tasks[0], args.output_dir)
    else:
        pool = Pool(args.processes)
        for process_id in range(args.processes):
            pool.apply_async(rag,
                             (process_id, tasks[process_id], args.output_dir))
        pool.close()
        logger.debug('waiting for preprocess read finish..')
        pool.join()
