from flask import Flask

import lark_oapi as lark
from lark_oapi.adapter.flask import *
from lark_oapi.api.im.v1 import *
from flask import request, jsonify
import pdb
app = Flask(__name__)
from loguru import logger
import os
import time
import argparse
from multiprocessing import Process
import json

# use your own APP_ID, APP_SECRET, ENCRYPT_KEY and VERIFICATION_TOKEN
# here **open source is just for test** !!!
APP_ID = 'cli_a53a34dcb778500e'
APP_SECRET = '2ajhg1ixSvlNm1bJkH4tJhPfTCsGGHT1'
ENCRYPT_KEY = 'abc'
VERIFICATION_TOKEN = 'def'

LARK_TENANT_KEY = None
FIFO_input_path = None
FIFO_output_path = None

def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    logger.info(lark.JSON.marshal(data))
    # if not group text message, retrun
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

    json_str = json.dumps({
        'source': 'lark',
        'msg_id': msg_id,
        'user_id': user_id,
        'content': content,
        'group_id': group_id,
        'msg_time': msg_time
    }, ensure_ascii=False) + '\n'
    logger.debug(f'save {json_str}')

    with open(FIFO_input_path, 'a') as pipe:
        pipe.write(json_str)
    return None

# use your own Encrypt Key and Verification Token !!!
handler = lark.EventDispatcherHandler.builder(ENCRYPT_KEY, VERIFICATION_TOKEN, lark.LogLevel.DEBUG) \
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1) \
    .build()

@app.route("/event", methods=["POST"])
def event():
    jsonstr = request.get_json()
    if type(jsonstr) is dict:
        param = jsonstr
    else:
        param = json.loads(jsonstr)
    logger.debug(param)
    
    req = parse_req()
    resp = handler.do(parse_req())
    return parse_resp(resp)

def listen_lark_group():
    app.run(debug=False, host='0.0.0.0', port=6666)


# SDK 使用说明: https://github.com/larksuite/oapi-sdk-python#readme
def send_to_lark_group():
    json_str = ''
    while True:
        with open(FIFO_output_path) as pipe:
            json_str = pipe.readline()

            if not json_str:
                time.sleep(2)
                continue

            try:
                json_obj = json.loads(json_str)
                source = json_obj['source']
                if source != 'lark':
                    raise Exception(f'unsupported source {source}')

                # send to lark group
                # 创建client
                client = lark.Client.builder() \
                    .app_id(APP_ID) \
                    .app_secret(APP_SECRET) \
                    .log_level(lark.LogLevel.DEBUG) \
                    .build()

                text_str = json.dumps({"text": json_obj['reply']}, ensure_ascii=False)
                # 构造请求对象
                request: ReplyMessageRequest = ReplyMessageRequest.builder() \
                    .message_id(json_obj['msg_id']) \
                    .request_body(ReplyMessageRequestBody.builder()
                        .content(text_str)
                        .msg_type("text")
                        .reply_in_thread(True)
                        .build()) \
                    .build()

                # 发起请求
                response: ReplyMessageResponse = client.im.v1.message.reply(request)

                # 处理失败返回
                if not response.success():
                    lark.logger.error(
                        f"client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
                    return

                # 处理业务结果
                lark.logger.info(lark.JSON.marshal(response.data, indent=2))
            except Exception as e:
                logger.error(str(e))

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--input',
                        type=str,
                        default='/tmp/lark-pipe-in',
                        help='Named pipe for group text message. Use `/tmp/lark-pip-in` by default.')
    parser.add_argument('--output',
                        type=str,
                        default='/tmp/lark-pipe-out',
                        help='Named pipe for the message send to group. Use `/tmp/lark-pip-out` by default.')
    parser.add_argument('--port',
                        type=int,
                        default=6666,
                        help='Listen port for lark group message. Use 6666 by default.')         
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if os.path.exists(args.input):
        os.remove(args.input)
    os.mkfifo(args.input)
    FIFO_input_path = args.input

    if os.path.exists(args.output):
        os.remove(args.output)
    os.mkfifo(args.output)
    FIFO_output_path = args.output
    
    listen_process = Process(target=listen_lark_group)
    listen_process.start()

    send_to_lark_group()
    send_proecss = Process(target=send_to_lark_group)
    send_proecss.start()

    listen_process.join()
    send_proecss.join()

if __name__ == "__main__":
    main()
