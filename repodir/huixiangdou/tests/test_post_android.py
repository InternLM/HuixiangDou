import json
import time

import requests

# base_url = 'https://p-172_dot_31_dot_0_dot_170_colon_18443.openxlab.space/api/v1/message/v1/wechat/fRHK'
base_url = 'http://139.224.198.162:18443/api/v1/message/v1/wechat/fRHK'

headers = {'Content-Type': 'application/json; charset=utf-8'}


def send():
    data_send = {
        'query_id': 'abb',
        'groupname': '茴香豆测试群',  # 完整的微信群名
        'username': '豆哥 123',  # 发送者的在这个群的微信昵称， 注意一个人可能在多个群里
        'query': {
            'type': 'text',  # 发的类型，  text or image, poll
            'content':
            '请问如何申请公寓？'  # 如果 type 是 text 就是文本； 如果是 image，就是个可公开访问的 oss_url
        }
    }
    resp = requests.post(base_url,
                         headers=headers,
                         data=json.dumps(data_send),
                         timeout=10)

    resp_json = resp.json()
    print(resp_json)


def get():
    data_wait = {
        'query_id': 'abb',  # 微信给的随机值，用于事后日志分析
        'groupname': '茴香豆测试群',  # 完整的微信群名
        'username': '豆哥 123',  # 发送者的在这个群的微信昵称， 注意一个人可能在多个群里
        'query': {
            'type': 'poll'  # 发的类型，  text or image, poll
        }
    }
    resp = requests.post(base_url,
                         headers=headers,
                         data=json.dumps(data_wait),
                         timeout=20)
    print(resp.text)


send()
send()

time.sleep(40)
get()
