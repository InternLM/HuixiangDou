import json
import os

import requests

token = os.getenv('TOKEN')

url = 'https://puyu.openxlab.org.cn/puyu/api/v1/models'
header = {'Content-Type': 'application/json', 'Authorization': token}
data = {}

res = requests.get(url, headers=header, data=json.dumps(data))
print(res.status_code)
print(res.json())
print(res.json()['data'])
