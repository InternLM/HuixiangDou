import json
from pathlib import Path
from enum import Enum
import redis
import os


def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host


def redis_port():
    port = os.getenv('REDIS_PORT')
    if not port:
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
        """Get add messages in queue without block."""
        ret = []
        while True:
            item = self.__db.lpop(self.key)
            if not item:
                break
            ret.append(item)
        return ret

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)


class TaskCode(Enum):
    FS_ADD_DOC = 'add_doc'
    FS_UPDATE_SAMPLE = 'update_sample'
    FS_UPDATE_PIPELINE = 'update_pipeline'
    CHAT = 'chat'
    CHAT_RESPONSE = 'chat_response'


task_in = Queue(name='Task')
task_out = Queue(name='TaskResponse')
chat_out = Queue(name='ChatResponse')


def test_create_fs():
    target = {
        'type': TaskCode.FS_ADD_DOC.value,
        'payload': {
            'name': 'ailab 行政说明',
            'feature_store_id': '9527',
            'file_abs_base': '/root/huixiangdou-res/test-data',
            'file_list': ['huixiangdou.md', '']
        }
    }
    base_dir = target['payload']['file_abs_base']

    file_list = [str(x) for x in list(Path(base_dir).glob('*'))]
    target['payload']['file_list'] = file_list
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))

    out = task_out.get()
    print(out)


def test_update_sample():
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "positive": "[STRING]",
    #     "negative": "[STRING]",
    # }

    target = {
        'type': TaskCode.FS_UPDATE_SAMPLE.value,
        'payload': {
            'name': 'ailab 行政说明',
            'feature_store_id': '9527',
            'positive':
            ['请问如何申请公寓？我是实习生但名下有房还行么？', '几十万的科研仪器不小心打碎了，我得自己付钱赔偿么'],
            'negative': ['今天中午吃什么', 'ncnn 的作者是谁']
        }
    }
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))

    out = task_out.get()
    print(out)


def test_update_pipeline():
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "web_search_token": ""
    # }

    target = {
        'type': TaskCode.FS_UPDATE_PIPELINE.value,
        'payload': {
            'name': 'ailab 行政说明',
            'feature_store_id': '9527',
            'web_search_token': ''
        }
    }
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))

    out = task_out.get()
    print(out)

def test_chat():

    queries = ['请问公寓退房需要注意哪些事情？']

    for query in queries:
        target = {
            'type': TaskCode.CHAT.value,
            'payload': {
                'query_id':
                'ae86',
                'feature_store_id':
                '9527',
                'content':
                query,
                'images': [],
                'history': [{
                    'sender': 0,
                    'content': '你好'
                }, {
                    'sender': 0,
                    'content': '你是谁'
                }, {
                    'sender': 1,
                    'content': '我是行政助手茴香豆'
                }]
            }
        }
        task_in.put(json.dumps(target, ensure_ascii=False))
        print(chat_out.get())


if __name__ == '__main__':
    # test_create_fs()
    # test_update_sample()
    # test_update_pipeline()
    test_chat()

