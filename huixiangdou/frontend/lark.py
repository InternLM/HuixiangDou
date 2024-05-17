# Copyright (c) OpenMMLab. All rights reserved.
# copy from https://github.com/tpoisonooo/cpp-syntactic-sugar/blob/master/github-lark-notifier/main.py  # noqa E501
"""Lark proxy."""
import json
import logging
import time

import requests
import urllib3
from loguru import logger

urllib3.disable_warnings()


class Lark:
    """Lark bot http proxy."""

    def __init__(self,
                 webhook,
                 secret=None,
                 pc_slide=False,
                 fail_notice=False):
        """Init with hook url."""
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        logger.debug(f'webhook {webhook}')
        logger.error('This class would be deprecated in 2024.10.10')
        self.webhook = webhook
        self.secret = secret
        self.pc_slide = pc_slide
        self.fail_notice = fail_notice

    def is_not_null_and_blank_str(self, content: str):
        """Is content empty."""
        if content is not None and content.strip():
            return True
        return False

    def send_text(self, msg):
        """Send text to hook url."""
        data = {'msg_type': 'text', 'at': {}}
        if self.is_not_null_and_blank_str(msg):  # 传入msg非空
            data['content'] = {'text': msg}
        else:
            logging.error('text类型，消息内容不能为空！')
            raise ValueError('text类型，消息内容不能为空！')

        logging.debug(f'text类型：{data}')
        return self.post(data)

    def post(self, data):
        """Post data to hook url."""
        try:
            post_data = json.dumps(data)
            response = requests.post(self.webhook,
                                     headers=self.headers,
                                     data=post_data,
                                     verify=False,
                                     timeout=60)
        except requests.exceptions.HTTPError as exc:
            code = exc.response.status_code
            reason = exc.response.reason
            logging.error(f'消息发送失败， HTTP error: {code}, reason: {reason}')
            raise
        except requests.exceptions.ConnectionError:
            logging.error('消息发送失败，HTTP connection error!')
            raise
        except requests.exceptions.Timeout:
            logging.error('消息发送失败，Timeout error!')
            raise
        except requests.exceptions.RequestException:
            logging.error('消息发送失败, Request Exception!')
            raise
        try:
            result = response.json()
        except json.JSONDecodeError:
            code = response.status_code
            text = response.text
            logging.error(f'服务器响应异常，状态码：{code}，响应内容：{text}')
            return {'errcode': 500, 'errmsg': '服务器响应异常'}
        logging.debug('发送结果：%s' % result)
        # 消息发送失败提醒（errcode 不为 0，表示消息发送异常），默认不提醒，开发者可以根据返回的消息发送结果自行判断和处理  # noqa E501
        if self.fail_notice and result.get('errcode', True):
            time_now = time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.localtime(time.time()))  # noqa E501
            reason_text = result['errmsg'] if result.get('errmsg',
                                                         False) else '未知异常'
            error_data = {
                'msgtype': 'text',
                'text': {
                    'content':
                    f'[注意-自动通知]飞书机器人消息发送失败，时间：{time_now}，原因：{reason_text}，请及时跟进，谢谢!'  # noqa E501
                },
                'at': {
                    'isAtAll': False
                }
            }
            logging.error('消息发送失败，自动通知：%s' % error_data)
            requests.post(self.webhook,
                          headers=self.headers,
                          data=json.dumps(error_data),
                          timeout=60)
        return result
