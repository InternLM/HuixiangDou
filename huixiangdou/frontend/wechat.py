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
import argparse
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
        self.global_user_id = ''
        self.timestamp = -1
        self.status = ''
        self.index = -1

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
        self.global_user_id = '{}|{}'.format(self.group_id, self.group_id data['fromUser'])
        self.timestamp = time.time()


class User:
    def __init__(self):
        # [(query, reply, refs)]
        self.history = []
        # meta
        self.last_msg_time = time.time()
        self.last_response_time = -1
        # groupid+userid
        self._id = ""

    def feed(self, msg: Message):
        self.history.append((msg.query, None, None))
        self.last_msg_time = time.time()
        self._id = msg.global_user_id

    def concat(self):
        # concat un-responsed query
        # 整理历史消息，把没有回复的消息合并
        if len(self.history) < 2:
            return
        ret = []
        merge_list = []
        for item in self.history:
            answer = item[1]
            if answer is not None and len(answer) > 0:
                ret.append(item)
            else:
                merge_list.append(item[0])
        ret.append(('。'.join(merge_list), ''))
        self.history = ret

    def update_history(self, query, reply, refs):
        item = (query, reply, refs)
        self.history[-1] = item
        self.last_response_time = time.time()


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
        self.users = dict()
        self.messages = []

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

    def send_message(self, groupId: str, text: str)
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wId": self.wId, "wcId": groupId, "content": text}

        resp = requests.post('http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        if resp.status_code != 200:
            return Exception('wkteam set callback fail {}'.format(json_str))

        sent = json.loads(json_str)
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)
            
    def serve_async(self):
        """
        Start a process to listen wechat message callback port
        """
        p = Process(target=bind, args=(self.record_path, self.wkteam_config.callback_port))
        p.start()

    def serve(self):
        bind(self.record_path, self.wkteam_config.callback_port)

    def loop(self, worker):
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

            # parse wx_msg, add it to group 
            que = Queue(name='wechat')
            for wx_msg in que.get_all():
                msg = Message()
                msg.parse(wx_msg)
                msg.index = len(self.messages)
                self.messages.append(msg)

                if msg.global_user_id not in self.users:
                    self.users[msg.global_user_id] = User()
                user = self.users[msg.global_user_id]
                user.feed(msg)
            
            # try concat all msgs in groups, fetch one to process
            for user in self.users.values():
                user.concat()
                now = time.time()
                # if a user not send new message in 18 seconds, process and mark it
                if now - user.last_msg_time >= 18 and user.last_response_time < user.last_msg_time:
                    assert len(user.history) > 0
                    item = user.history[-1]
                    assert item[1] is None
                    query = item[0]

                    code = ErrorCode.QUESTION_TOO_SHORT
                    resp = ''
                    refs = []
                    if len(query) >= 9:
                        code, resp, refs = worker.generate(query=query, history=user.history, groupname='')

                    # user history may affact normal conversation, so delete last query
                    if code in [ErrorCode.NOT_A_QUESTION, ErrorCode.SECURITY, ErrorCode.NO_SEARCH_RESULT, ErrorCode.NO_TOPIC]:
                        del user.history[-1]
                    else:
                        user.update_history(query=query, reply=reply, refs=refs)
                    
                    send = False
                    if code == ErrorCode.SUCCESS:
                        # save sent and send reply to WeChat group
                        formatted_reply = ''
                        if len(query) > 30:
                            formatted_reply = '{}..\n---\n{}'.format(query[0:30], resp)
                        else:
                            formatted_reply = '{}\n---\n{}'.format(query, answer)
                        self.send_message(groupId=user.group_id, text=formatted_reply)


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
        help='Configuration path. Default value is config.ini')
    parser.add_argument('--login',
                        action='store_true',
                        default=True,
                        help='Login wkteam')
    parser.add_argument('--serve',
                        action='store_true',
                        default=True,
                        help='Bind port and listen WeChat message callback')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    manager = WkteamManager(args.config_path)

    if args.login:
        manager.login()

    if args.servce:
        manager.serve()
