# coding=UTF-8
import requests
import json
import time
import pdb
import random
from loguru import logger

def security(query: str, retry=2):
    life = 0
    while life < retry:
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                'bizId': str('antiseed' + str(time.time())),
                'contents': [query],
                'scopes': [],
                'vendor': 1,
            }

            resp = requests.post('https://openxlab.org.cn/gw/checkit/api/v1/audit/text', data=json.dumps(data), headers=headers)
            logger.debug((resp, resp.content))

            json_obj = json.loads(resp.content)
            items = json_obj['data']

            block = False
            for item in items:
                label = item['label']
                if label is not None and label in ['porn', 'politics']:
                    suggestion = item['suggestion']
                    if suggestion == 'block':
                        logger.debug(items)
                        block = True
                        break

            if block:
                return False
            return True
        except Exception as e:
            logger.debug(e)
            life += 1

            randval = random.randint(1, int(pow(2, life)))
            time.sleep(randval)
    return False


if __name__ == '__main__':
    print(check('安装 mmdeploy 需要从 gayhub 下载 whl 包'))
