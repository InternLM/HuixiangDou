import json
import logging
import time

import requests
import urllib3

urllib3.disable_warnings()


# copy from https://github.com/tpoisonooo/cpp-syntactic-sugar/blob/master/github-lark-notifier/main.py  # noqa E501
class Lark:
    """Lark bot http proxy."""

    def __init__(self,
                 webhook,
                 secret=None,
                 pc_slide=False,
                 fail_notice=False):
        """Init with hook url."""
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        print('webhook {}'.format(webhook))
        self.webhook = webhook
        self.secret = secret
        self.pc_slide = pc_slide
        self.fail_notice = fail_notice

    def is_not_null_and_blank_str(self, content: str):
        """Is content empty."""
        if content and content.strip():
            return True
        else:
            return False

    def send_text(self, msg, open_id=[]):
        """Send text to hook url."""
        data = {'msg_type': 'text', 'at': {}}
        if self.is_not_null_and_blank_str(msg):  # 传入msg非空
            data['content'] = {'text': msg}
        else:
            logging.error('text类型，消息内容不能为空！')
            raise ValueError('text类型，消息内容不能为空！')

        logging.debug('text类型：%s' % data)
        return self.post(data)

    def post(self, data):
        """Post data to hook url."""
        try:
            post_data = json.dumps(data)
            response = requests.post(self.webhook,
                                     headers=self.headers,
                                     data=post_data,
                                     verify=False)
        except requests.exceptions.HTTPError as exc:
            logging.error('消息发送失败， HTTP error: %d, reason: %s' %
                          (exc.response.status_code, exc.response.reason))
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
        else:
            try:
                result = response.json()
            except json.JSONDecodeError:
                logging.error('服务器响应异常，状态码：%s，响应内容：%s' %
                              (response.status_code, response.text))
                return {'errcode': 500, 'errmsg': '服务器响应异常'}
            else:
                logging.debug('发送结果：%s' % result)
                # 消息发送失败提醒（errcode 不为 0，表示消息发送异常），默认不提醒，开发者可以根据返回的消息发送结果自行判断和处理  # noqa E501
                if self.fail_notice and result.get('errcode', True):
                    time_now = time.strftime('%Y-%m-%d %H:%M:%S',
                                             time.localtime(time.time()))
                    error_data = {
                        'msgtype': 'text',
                        'text': {
                            'content':
                            '[注意-自动通知]飞书机器人消息发送失败，时间：%s，原因：%s，请及时跟进，谢谢!' %
                            (time_now, result['errmsg'] if result.get(
                                'errmsg', False) else '未知异常')
                        },
                        'at': {
                            'isAtAll': False
                        }
                    }
                    logging.error('消息发送失败，自动通知：%s' % error_data)
                    requests.post(self.webhook,
                                  headers=self.headers,
                                  data=json.dumps(error_data))
                return result
