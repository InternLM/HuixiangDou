#!/usr/bin/env python3
# Copyright (c) OpenMMLab. All rights reserved.
"""HuixiangDou binary."""
import argparse
import os
import time

import pytoml
import requests
from aiohttp import web
from loguru import logger

from .service import ErrorCode, Worker, start_llm_server


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
            response = requests.get(CONFIG_URL, timeout=60)
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


def build_reply_text(code, query: str, reply: str, refs: list):
    from texttable import Texttable
    table = Texttable()
    table.set_cols_valign(['t', 't', 't', 't'])
    table.header(['Query', 'State', 'Part of Reply', 'References'])
    table.add_row([query, str(code), reply[0:20] + '..', ','.join(refs)])
    return table.draw()


def show(assistant, fe_config: dict):
    queries = ['请问如何安装 mmpose ?', '请问明天天气如何？']
    for query in queries:
        code, reply, refs = assistant.generate(query=query,
                                               history=[],
                                               groupname='')
        reply_text = build_reply_text(code=code,
                                      query=query,
                                      reply=reply,
                                      refs=refs)
        logger.info('\n' + reply_text)

        if fe_config['type'] == 'lark':
            # send message to lark group
            logger.error(
                '!!!`lark_send_only` feature will be removed on October 10, 2024. If this function still helpful for you, please let me know: https://github.com/InternLM/HuixiangDou/issues'
            )
            from .frontend import Lark
            lark = Lark(webhook=fe_config['webhook_url'])
            logger.info(f'send {reply} and {refs} to lark group.')
            lark.send_text(msg=reply_text)


def lark_group_recv_and_send(assistant, fe_config: dict):
    from .frontend import (is_revert_command, revert_from_lark_group,
                           send_to_lark_group)
    msg_url = fe_config['webhook_url']
    lark_group_config = fe_config['lark_group']
    sent_msg_ids = []

    while True:
        # fetch a user message
        resp = requests.post(msg_url, timeout=10)
        resp.raise_for_status()
        json_obj = resp.json()
        if len(json_obj) < 1:
            # no user input, sleep
            time.sleep(2)
            continue

        logger.debug(json_obj)
        query = json_obj['content']

        if is_revert_command(query):
            for msg_id in sent_msg_ids:
                error = revert_from_lark_group(msg_id,
                                               lark_group_config['app_id'],
                                               lark_group_config['app_secret'])
                if error is not None:
                    logger.error(
                        f'revert msg_id {msg_id} fail, reason {error}')
                else:
                    logger.debug(f'revert msg_id {msg_id}')
                time.sleep(0.5)
            sent_msg_ids = []
            continue

        code, reply, references = assistant.generate(query=query,
                                                     history=[],
                                                     groupname='')
        if code == ErrorCode.SUCCESS:
            json_obj['reply'] = build_reply_text(reply=reply,
                                                 references=references)
            error, msg_id = send_to_lark_group(
                json_obj=json_obj,
                app_id=lark_group_config['app_id'],
                app_secret=lark_group_config['app_secret'])
            if error is not None:
                raise error
            sent_msg_ids.append(msg_id)
        else:
            logger.debug(f'{code} for the query {query}')


def wechat_personal_run(assistant, fe_config: dict):
    """Call assistant inference."""

    async def api(request):
        input_json = await request.json()
        logger.debug(input_json)

        query = input_json['query']

        if type(query) is dict:
            query = query['content']

        code, reply, references = assistant.generate(query=query,
                                                     history=[],
                                                     groupname='')
        reply_text = build_reply_text(reply=reply, references=references)

        return web.json_response({'code': int(code), 'reply': reply_text})

    bind_port = fe_config['wechat_personal']['bind_port']
    app = web.Application()
    app.add_routes([web.post('/api', api)])
    web.run_app(app, host='0.0.0.0', port=bind_port)


def run():
    """Automatically download config, start llm server and run examples."""
    args = parse_args()

    if args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=args.config_path)

    # query by worker
    with open(args.config_path, encoding='utf8') as f:
        fe_config = pytoml.load(f)['frontend']
    logger.info('Config loaded.')
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)

    fe_type = fe_config['type']
    if fe_type == 'none':
        show(assistant, fe_config)
    elif fe_type == 'lark_group':
        lark_group_recv_and_send(assistant, fe_config)
    elif fe_type == 'wechat_personal':
        wechat_personal_run(assistant, fe_config)
    elif fe_type == 'wechat_wkteam':
        from .frontend import WkteamManager
        manager = WkteamManager(args.config_path)
        manager.loop(assistant)
    else:
        logger.info(
            f'unsupported fe_config.type {fe_type}, please read `config.ini` description.'  # noqa E501
        )

    # server_process.join()


if __name__ == '__main__':
    run()
