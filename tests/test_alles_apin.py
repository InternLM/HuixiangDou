import json
import os

import requests

url = 'https://openxlab.org.cn/gw/alles-apin-hub/v1/openai/v2/text/chat'
api_token = os.getenv('ALLES_APIN_TOKEN')
headers = {'content-type': 'application/json', 'alles-apin-token': api_token}

payload = {
    'model':
    'gpt-4-1106-preview',
    'messages': [{
        'role':
        'user',
        'content':
        '帮我写个 python 代码，用 time.time() 和 datetime 获取当前时间。把当前时间的秒数设成 0，毫秒数也设成 0， 分钟数加 1，输出新时间对应的毫秒数，格式和 time.time() 相同'
    }]
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
resp_json = response.json()
if resp_json['msgCode'] == '10000':
    data = resp_json['data']
    if len(data['choices']) > 0:
        text = data['choices'][0]['message']['content']
        print(text)
