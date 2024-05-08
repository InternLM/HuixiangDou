import redis
import requests
import json
from datetime import datetime
import pdb
import os
import random
import string
import pytoml
import types
import process
from loguru import logger
import xml.etree.ElementTree as ET
from aiohttp import web
from helper import Queue
import time

def is_revert_command(wx_msg):
    """
    Is wx_msg a revert command.
    """
    data = wx_msg['data']
    content = data['content']
    if content != None and len(content) > 0:
        content = content.encode('UTF-8', 'ignore').decode('UTF-8')
    messageType = wx_msg['messageType']

    if messageType == 5 or messageType == 9 or messageType == '80001':
        if '@茴香豆' in content and '撤回' in content:
            return True
    elif messageType == 14 or messageType == '80014':
        # 对于引用消息，如果要求撤回
        if 'title' in data:
            if '撤回' in data['title']:
                return True
        elif '撤回' in content:
            return True
    return False

def bind(logpath, port):
    async def msg_callback(request):
        """Save wechat message to redis, for revert command, use high priority."""
        input_json = await request.json()
        with open(logpath, 'a') as f:
            json_str = json.dump(input_json, indent=2, ensure_ascii=False)
            f.write(json_str)

        logger.debug(input_json)
        msg_que = Queue(name='wechat')
        revert_que = Queue(name='wechat-high-priority')

        try:
            json_str = json.dumps(input_json)
            if is_revert_command(input_json):
                revert_que.put(json_str)
            else:
                msg_que.put(json_str)

        except Exception as e:
            logger.error(str(e))
        
        return web.json_response(text='done')

    app = web.Application()
    app.add_routes([web.post('/callback', msg_callback)])
    web.run_app(app, host='0.0.0.0', port=port)


class Message:
    def __init__(self):
        self.data = dict()
        self.type = None
        self.query = ''
        self.group_id = ''
        self.user_id = ''
        self.timestamp = -1
        self.status = ''

    def parse(self, wx_msg: dict):
        data = wx_msg['data']
        # str or int
        _type = wx_msg['messageType']

        # format user input
        query = ''
        if _type in [14, '80014']:
            query = data['title']
        else:
            query = data['content']
        query = query.encode('UTF-8', 'ignore').decode('UTF-8')
        if query.startswith('@茴香豆'):
            query = question.replace('@茴香豆', '')
        self.query = query.strip()

        if '————————' in query:
            self.status = 'skip'

        self.data = data
        self.type = _type
        self.group_id = data['fromGroup']
        self.user_id = data['fromUser']
        self.timestamp = time.time()

class User:
    def __init__(self):
        # class Message
        self.messages = []
        # [(send, recv, refs)]
        self.history = []
        # meta
        self.last_msg_time = -1
        self.last_response_time = -1
        # groupid+userid
        self._id = ""

    def concat(self):
        # concat un-responsed query


class Group:
    def __init__(self):
        # class Message
        self.messages = []
        # users
        self.users = dict()
        # id
        self._id = ""

class WkteamManager:
"""
1. wkteam Login, see https://wkteam.cn/
2. Handle wkteam wechat message call back
"""
    def __init__(self, config_path: str):
        """
        init with config
        """
        self.WKTEAM_IP_PORT = '121.229.29.88:9899'
        self.auth = ""
        self.wId = ""
        self.wcId = ""
        self.qrCodeUrl = ""
        self.wkteam_config = dict()
        self.groups = dict()

        with open(config_path) as f:
            config = pytoml.load(f)
            self.wkteam_config = types.SimpleNamespace(**cconfig['frontend']['wkteam'])
        
        # set redis env
        if os.getenv('REDIS_HOST') is None:
            os.environ["REDIS_HOST"] = str(self.wkteam_config.redis_host)
        if os.getenv('REDIS_PORT') is None:
            os.environ["REDIS_PORT"] = str(self.wkteam_config.redis_port)
        if os.getenv('REDIS_PASSWORD') is None:
            os.environ["REDIS_PASSWORD"] = str(self.wkteam_config.redis_passwd)
        assert len(self.wkteam_config) > 1

        # load wkteam license
        if not os.path.exists(self.wkteam_config.dir):
            os.makedirs(self.wkteam_config.dir)
        self.license_path = os.path.join(self.wkteam_config.dir, 'license.json')
        self.record_path = os.path.join(self.wkteam_config.dir, 'record.jsonl')
        if os.path.exists(self.license_path):
            with open(self.license_path) as f:
                jsonobj = json.load(f)
                self.auth = jsonobj['auth']
                self.wId = jsonobj['wId']
                self.wcId = jsonobj['wcId']
                self.qrCodeUrl = jsonobj['qrCodeUrl']
                logger.debug(jsonobj)

        # messages sent
        # {groupId: [wx_msg]}
        self.sent_msg = dict()

    def revert(self, groupId: str):
        """
        Revert all msgs in this group
        """
        # 撤回在本群 2 分钟内发出的所有消息
        logger.debug('revert message')
        if groupId not in self.sent_msg:
            return

        group_sent_list = self.sent_msg[groupId]
        for sent in group_sent_list:
            logger.info(sent)
            time_diff = abs(time.time() - int(sent['createTime']))
            if time_diff <= 120:
            # real revert
            try:
                headers = {"Content-Type": "application/json", "Authorization": self.auth}
                requests.post('http://{}/revokeMsg'.format(ip_port), data=json.dumps(sent), headers=headers)
            except Exception as e:
                logger.error(str(e))
                time.sleep(0.1)
        del self.sent_msg[groupId]
        

    def login(self):
        """
        user login, need scan qr code on mobile phone
        """
        # check input
        if len(self.wkteam_config.account) < 1 or len(self.wkteam_config.password) < 1:
            return Exception('wkteam account or password not set')

        if len(self.wkteam_config.callback_ip) < 1:
            return Exception('wkteam wechat message public callback ip not set, try FRP or buy cloud service ?')
        
        if self.wkteam_config.proxy <= 0:
            return Exception('wkteam proxy not set')

        # auth
        headers = {"Content-Type": "application/json"}
        data = {'account': wkteam_config.account, 'password': wkteam_config.password}

        resp = requests.post('http://{}/member/login'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')

        logger.debug(('auth', json_str))
        if resp.status_code != 200:
            return Exception('wkteam auth fail {}'.format(json_str))
        self.auth = json.loads(json_str)['data']['Authorization']

        # ipadLogin
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wcId": "", "proxy": self.wkteam_config.proxy}

        resp = requests.post('http://{}/iPadLogin'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
      
        if resp.status_code != 200:
            return Exception('wkteam ipadLogin fail {}'.format(json_str))

        x = json.loads(json_str)['data']
        self.wId = x['wId']
        self.qrCodeUrl = x['qrCodeUrl']

        logger.info('浏览器打开这个地址、下载二维码。打开手机，扫描登录微信\n {}\n 请确认 proxy 地区正确，首次使用、24 小时后要再次登录，以后不需要登。'.format(self.qrCodeUrl))
        
        # getLoginInfo
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wId": self.wId}
        resp = requests.post('http://{}/getIPadLoginInfo'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        if resp.status_code != 200:
            return Exception('wkteam ipadLogin fail {}'.format(json_str))
        x = json.loads(json_str)['data']
        self.wcId = x['wcId']

        # set callback url
        httpUrl = 'http://{}:{}/callback'.format(self.wkteam_config.callback_ip, self.wkteam_config.callback_port)
        logger.debug('set callback url {}'.format(httpUrl))
        headers = {"Content-Type": "application/json", "Authorization": auth}
        data = {"httpUrl": httpUrl, "type": 2}
        resp = requests.post('http://{}/setHttpCallbackUrl'.format(ip_port), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        if resp.status_code != 200:
            return Exception('wkteam set callback fail {}'.format(json_str))

        # dump
        with open(self.license_path, 'w') as f:
            json_str = json.dumps({
                'auth': self.auth, 
                'wId': self.wId,
                'wcId': self.wcId,
                'qrCodeUrl': self.qrCodeUrl
            }, indent=2, ensure_ascii=False
            f.write(json_str)

        logger.info('login success, all license saved to {}'.format(self.license_path))
        
        # initAddrList
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wId": self.wId}

        resp = requests.post('http://{}/getAddressList'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        logger.info(json_str)
        return None

    def serve_async(self):
        """
        Start a process to listen wechat message callback port
        """
        p = Process(target=bind, args=(self.record_path, self.wkteam_config.callback_port))
        p.start()

    def serve(self):
        bind(self.record_path, self.wkteam_config.callback_port)

    def loop(self):
        """
        Fetch all messeges from redis, split it by groupId; concat by timestamp
        """

        while True:
            time.sleep(2)
            # react to revert msg first
            revert_que = Queue(name='wechat-high-priority')
            for msg in revert_que.get_all():
                if 'fromGroup' in msg['data']:
                    self.revert(groupId = msg['data']['fromGroup'])

            # parse and add wx_msg 
            que = Queue(name='wechat')
            for wx_msg in que.get_all():
                msg = Message()
                msg.parse(wx_msg)



if __name__ == '__main__':
    manager = WkteamManager('config.ini')
    manager.login()
    manager.serve()
