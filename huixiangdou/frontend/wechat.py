import redis
import requests
import json
from datetime import datetime
import pdb
import random
import string
import pytoml
import types
import argparse
from loguru import logger
import xml.etree.ElementTree as ET
from aiohttp import web
# from helper import Queue
import time
from multiprocessing import Process
import os
from loguru import logger
from readability import Document
from bs4 import BeautifulSoup as BS
import hashlib

def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host


def redis_port():
    port = os.getenv('REDIS_PORT')
    if port is None:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port


def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd

class Queue:

    def __init__(self, name, namespace='HuixiangDou', **redis_kwargs):
        self.__db = redis.Redis(host=redis_host(),
                                port=redis_port(),
                                password=redis_passwd(),
                                charset='utf-8',
                                decode_responses=True)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def peek_tail(self):
        return self.__db.lrange(self.key, -1, -1)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_all(self):
        """Get add messages in queue without block.
        """
        ret = []
        try:
            while len(ret) < 1:  # batchsize = 1 for debugging
                item = self.__db.lpop(self.key)
                if not item:
                    break
                ret.append(item)
        except Exception as e:
            logger.error(str(e))
        return ret

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

def is_revert_command(wx_msg):
    """
    Is wx_msg a revert command.
    """
    data = wx_msg['data']
    if 'content' not in data:
        return False
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
        # str or int
        msg_type = wx_msg['messageType']
        parse_type = 'unknown'
        if 'data' not in wx_msg:
            self.status = 'skip'
            return Exception('data not in wx_msg')

        data = wx_msg['data']

        # format user input
        query = ''
        if msg_type in ['80014', '60014']:
            # ref message
            # 群、私聊引用消息
            query = data['title']
            parse_type = 'ref'

        elif msg_type in ['80007', '60007', '90001']:
            # url message
            # 例如公众号文章。尝试解析提取内容，这个行为高概率会被服务器 ban
            parse_type = 'link'

            root = ET.fromstring(data['content'])
            url =  root.findall(".//url")[0].text
            title = root.findall(".//title")[0].text
            desc = root.findall(".//des")[0].text

            resp = requests.get(url)
            doc = Document(resp.text)
            soup = BS(doc.summary(), 'html.parser')

            if len(soup.text) > 100:
                query = '{}\n{}\n{}'.format(title, desc, soup.text)
            else:
                query = '{}\n{}\n{}'.format(title, desc, url)
            logger.debug('公众号解析：{}'.format(query)[0:256])

        elif msg_type in ['80002', '60002']:
            # image
            # 图片消息
            parse_type = 'image'

        elif msg_type in ['80001', '60001']:
            # text
            # 普通文本消息
            query = data['content']
            parse_type = 'text'

        elif type(msg_type) is int:
            logger.warning(wx_msg)

        else:
            return Exception('skip msg type {}'.format(msg_type))

        query = query.encode('UTF-8', 'ignore').decode('UTF-8')
        if query.startswith('@茴香豆'):
            query = query.replace('@茴香豆', '')
        self.query = query.strip()

        if '————————' in query:
            self.status = 'skip'
            return Exception("repo owner's message, skip")

        self.data = data
        self.type = parse_type
        self.group_id = data['fromGroup']
        self.global_user_id = '{}|{}'.format(self.group_id, data['fromUser'])
        self.timestamp = time.time()
        return None

class User:
    def __init__(self):
        # [(query, reply, refs)]
        self.history = []
        # meta
        self.last_msg_time = time.time()
        self.last_response_time = -1
        # groupid+userid
        self._id = ""
    
    def __str__(self):
        obj = {
            "history": self.history,
            "last_msg_time": self.last_msg_time,
            "last_response_time": self.last_response_time,
            "_id": self._id
        }
        return json.dumps(obj, indent=2, ensure_ascii=False)

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

def bind(logdir: str, port: int):

    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logpath = os.path.join(logdir, 'wechat_message.jsonl')

    async def msg_callback(request):
        """Save wechat message to redis, for revert command, use high priority."""
        input_json = await request.json()
        with open(logpath, 'a') as f:
            json_str = json.dumps(input_json, indent=2, ensure_ascii=False)
            f.write(json_str)
            f.write('\n')

        logger.debug(input_json)
        msg_que = Queue(name='wechat')
        revert_que = Queue(name='wechat-high-priority')

        if input_json['messageType'] == "00000":
            return web.json_response(text='done')
      
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

        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            assert len(config) > 1
            self.wkteam_config = types.SimpleNamespace(**config['frontend']['wechat_wkteam'])
        
        # set redis env
        if os.getenv('REDIS_HOST') is None:
            os.environ["REDIS_HOST"] = str(self.wkteam_config.redis_host)
        if os.getenv('REDIS_PORT') is None:
            os.environ["REDIS_PORT"] = str(self.wkteam_config.redis_port)
        if os.getenv('REDIS_PASSWORD') is None:
            os.environ["REDIS_PASSWORD"] = str(self.wkteam_config.redis_passwd)

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
        self.debug()


    def debug(self):
        logger.debug('auth {}'.format(self.auth))
        logger.debug('wId {}'.format(self.wId))
        logger.debug('wcId {}'.format(self.wcId))

        logger.debug('REDIS_HOST {}'.format(os.getenv('REDIS_HOST')))
        logger.debug('REDIS_PORT {}'.format(os.getenv('REDIS_PORT')))

    def post(self, url, data, headers):
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        logger.debug(json_str)
        if resp.status_code != 200:
            return None, Exception('wkteam auth fail {}'.format(json_str))
        json_obj = json.loads(json_str)
        if json_obj['code'] != '1000':
            return json_obj, Exception(json_str)
        
        return json_obj, None

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
                headers = {"Content-Type": "application/json", "Authorization": self.auth}
                
                self.post(url='http://{}/revokeMsg'.format(self.WKTEAM_IP_PORT), data=sent, headers=headers)
        del self.sent_msg[groupId]
    
    def download_image_async(self, param:dict):
        content = param['content']
        msgId = param['msgId']
        wId = param['wId']
       
        if len(self.auth) < 1:
            logger.error('Authentication empty')
            return
        
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wId": wId, "content": content, "msgId": msgId, "type": 0}

        def generate_hash_filename(data: dict):
            xstr = json.dumps(data)
            md5 = hashlib.md5()
            md5.update(xstr.encode('utf8'))
            return md5.hexdigest()[0:6] + ".jpg"

        def download(data:dict, headers:dict, dir:str):
            resp = requests.post('http://{}/getMsgImg'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
            json_str = resp.content.decode('utf8')
            
            if resp.status_code == 200:
                jsonobj = json.loads(json_str)
                if jsonobj['code'] != '1000':
                    logger.error('download {} {}'.format(data, json_str))
                    return
                
                image_url = jsonobj['data']['url']
                # download to local
                logger.info('image url {}'.format(image_url))
                resp = requests.get(image_url, stream=True)
                image_path = None
                if resp.status_code == 200:
                    image_dir = os.path.join(dir, 'images')
                    if not os.path.exists(image_dir):
                        os.makedirs(image_dir)
                    image_path = os.path.join(image_dir, generate_hash_filename(data=data))
                    logger.debug('local path {}'.format(image_path))
                    with open(image_path, 'wb') as image_file:
                        for chunk in resp.iter_content(1024):
                            image_file.write(chunk)

        download(data, headers, self.wkteam_config.dir)
        # download_task = Process(target=download, args=(data, headers, self.wkteam_config.dir))
        # download_task.start()

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
        data = {'account': self.wkteam_config.account, 'password': self.wkteam_config.password}

        json_obj, err = self.post(url='http://{}/member/login'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        self.auth = json_obj['data']['Authorization']

        # ipadLogin
        headers["Authorization"] = self.auth
        data = {"wcId": "", "proxy": self.wkteam_config.proxy}
        json_obj, err = self.post(url='http://{}/iPadLogin'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err

        x = json_obj['data']
        self.wId = x['wId']
        self.qrCodeUrl = x['qrCodeUrl']

        logger.info('浏览器打开这个地址、下载二维码。打开手机，扫描登录微信\n {}\n 请确认 proxy 地区正确，首次使用、24 小时后要再次登录，以后不需要登。'.format(self.qrCodeUrl))
        
        # getLoginInfo
        json_obj, err = self.post(url='http://{}/getIPadLoginInfo'.format(self.WKTEAM_IP_PORT), data={"wId": self.wId}, headers=headers)
        x = json_obj['data']
        self.wcId = x['wcId']

        # dump
        with open(self.license_path, 'w') as f:
            json_str = json.dumps({
                'auth': self.auth, 
                'wId': self.wId,
                'wcId': self.wcId,
                'qrCodeUrl': self.qrCodeUrl
            }, indent=2, ensure_ascii=False)
            f.write(json_str)

    def set_callback(self):
        # set callback url
        httpUrl = 'http://{}:{}/callback'.format(self.wkteam_config.callback_ip, self.wkteam_config.callback_port)
        logger.debug('set callback url {}'.format(httpUrl))
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"httpUrl": httpUrl, "type": 2}

        json_obj, err = self.post(url='http://{}/setHttpCallbackUrl'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err

        logger.info('login success, all license saved to {}'.format(self.license_path))
        return None

    def send_message(self, groupId: str, text: str):
        headers = {"Content-Type": "application/json", "Authorization": self.auth}
        data = {"wId": self.wId, "wcId": groupId, "content": text}

        json_obj, err = self.post(url='http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err

        sent = json_obj['data']
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)

        return None

    def serve(self):
        p = Process(target=bind, args=(self.wkteam_config.dir, self.wkteam_config.callback_port))
        # bind(self.wkteam_config.callback_port)
        p.start()
        self.set_callback()
        p.join()

    def loop(self, worker):
        """
        Fetch all messeges from redis, split it by groupId; concat by timestamp
        """
        from huixiangdou.service.helper import ErrorCode
        while True:
            time.sleep(2)
            # react to revert msg first
            revert_que = Queue(name='wechat-high-priority')

            for msg in revert_que.get_all():
                if 'fromGroup' in msg['data']:
                    self.revert(groupId = msg['data']['fromGroup'])

            # parse wx_msg, add it to group 
            que = Queue(name='wechat')

            for wx_msg_str in que.get_all():
                wx_msg = json.loads(wx_msg_str)
                msg = Message()
                msg.index = len(self.messages)
                err = msg.parse(wx_msg)
                if err is not None:
                    logger.debug(str(err))
                    continue
                if msg.type == 'image':
                    self.download_image_async(param=msg.data)
                    continue
                
                self.messages.append(msg)

                if msg.global_user_id not in self.users:
                    self.users[msg.global_user_id] = User()
                user = self.users[msg.global_user_id]
                user.feed(msg)
            
            # try concat all msgs in groups, fetch one to process
            for user in self.users.values():
                if len(user.history) < 1:
                    continue

                now = time.time()
                # if a user not send new message in 18 seconds, process and mark it
                if now - user.last_msg_time >= 18 and user.last_response_time < user.last_msg_time:
                    user.concat()
                    logger.debug('after concat {}'.format(user))
                    assert len(user.history) > 0

                    item = user.history[-1]

                    if item[1] is not None and len(item[1]) > 0:
                        pdb.set_trace()
                        print(item)
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
                        user.update_history(query=query, reply=resp, refs=refs)
                    
                    send = False
                    if code == ErrorCode.SUCCESS:
                        # save sent and send reply to WeChat group
                        formatted_reply = ''
                        if len(query) > 30:
                            formatted_reply = '{}..\n---\n{}'.format(query[0:30], resp)
                        else:
                            formatted_reply = '{}\n---\n{}'.format(query, resp)
                        
                        logger.warning('send {}'.format(formatted_reply))
                        # self.send_message(groupId=user.group_id, text=formatted_reply)


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
                        default=False,
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
        err = manager.login()
        if err is not None:
            logger.error(err)
        manager.set_callback()

    if args.serve:
        manager.serve()
