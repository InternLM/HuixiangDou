# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import json

import lark_oapi as lark
import pytoml
import redis
from flask import Flask, jsonify, request
from lark_oapi.adapter.flask import *  # noqa E403
from lark_oapi.api.im.v1 import *  # noqa E403
from loguru import logger

from huixiangdou.service.helper import Queue

app = Flask(__name__)
handler = None


def is_revert_command(content: str):
    if '豆哥撤回' in content:
        return True
    return False


def do_p2_im_message_receive_v1(
        data: P2ImMessageReceiveV1) -> None:  # noqa E405
    logger.info(lark.JSON.marshal(data))
    # if not group text message, return
    if data.header.event_type != 'im.message.receive_v1':
        return None

    msg = data.event.message
    if msg.chat_type != 'group':
        return None
    if msg.message_type != 'text':
        return None

    msg_id = msg.message_id
    group_id = msg.chat_id
    user_id = data.event.sender.sender_id.user_id
    content = json.loads(msg.content)['text']
    # milliseconds
    msg_time = msg.create_time

    json_str = json.dumps(
        {
            'source': 'lark',
            'msg_id': msg_id,
            'user_id': user_id,
            'content': content,
            'group_id': group_id,
            'msg_time': msg_time
        },
        ensure_ascii=False) + '\n'

    que = None
    if is_revert_command(content):
        # add to revert queue
        que = Queue(name='huixiangdou-high-priority')
    else:
        que = Queue(name='huixiangdou')
    que.put(json_str)
    logger.debug(f'save {json_str} to {que.key}')
    return None


@app.route('/event', methods=['POST'])
def event():
    jsonstr = request.get_json()
    if type(jsonstr) is dict:
        param = jsonstr
    else:
        param = json.loads(jsonstr)
    logger.debug(param)

    resp = handler.do(parse_req())  # noqa E405
    return parse_resp(resp)  # noqa E405


@app.route('/fetch', methods=['POST'])
def fetch():
    revert_que = Queue(name='huixiangdou-high-priority')
    json_str = revert_que.get(timeout=1)
    if json_str is not None and len(json_str) > 0:
        json_obj = json.loads(json_str)
        return jsonify(json_obj)

    msg_que = Queue(name='huixiangdou')
    json_str = msg_que.get(timeout=3)
    if json_str is not None and len(json_str) > 0:
        json_obj = json.loads(json_str)
        return jsonify(json_obj)
    return jsonify({})


def revert_from_lark_group(msg_id: str, app_id: str, app_secret: str):
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: DeleteMessageRequest = DeleteMessageRequest.builder(  # noqa E405
    ).message_id(  # noqa E405
        msg_id).build()

    # 发起请求
    response: DeleteMessageResponse = client.im.v1.message.delete(  # noqa E405
        request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f'client.im.v1.message.delete failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}'  # noqa E501
        )
        return Exception(response.msg)

    return None


# SDK 使用说明: https://github.com/larksuite/oapi-sdk-python#readme
def send_to_lark_group(json_obj: dict, app_id: str, app_secret: str):
    msg_id = ''
    try:
        source = json_obj['source']
        if source != 'lark':
            return Exception(f'unsupported source {source}')

        # send to lark group
        # 创建client
        client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

        text_str = json.dumps({'text': json_obj['reply']}, ensure_ascii=False)
        # 构造请求对象
        request: ReplyMessageRequest = ReplyMessageRequest.builder(  # noqa E405
        ).message_id(json_obj['msg_id']).request_body(
            ReplyMessageRequestBody.builder().content(  # noqa E405
                text_str).msg_type(  # noqa E405
                    'text').reply_in_thread(True).build()).build()

        # 发起请求
        response: ReplyMessageResponse = client.im.v1.message.reply(  # noqa E405
            request)  # noqa E405

        msg_id = response.data.message_id
        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f'client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}'  # noqa E501
            )
            return None, ''

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=2))
    except Exception as e:
        return e, ''
    return None, msg_id


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(
        description='Lark group for save group message.')
    parser.add_argument(
        '--port',
        type=int,
        default=6666,
        help='Listen port for lark group message. Use 6666 by default.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Lark group configuration path. Default value is config.ini')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    with open(args.config_path, encoding='utf8') as f:
        lark_group_config = pytoml.load(f)['frontend']['lark_group']

    handler = lark.EventDispatcherHandler.builder(
        lark_group_config['encrypt_key'],
        lark_group_config['verification_token'],
        lark.LogLevel.DEBUG).register_p2_im_message_receive_v1(
            do_p2_im_message_receive_v1).build()  # noqa E501
    app.run(debug=False, host='0.0.0.0', port=int(args.port))
