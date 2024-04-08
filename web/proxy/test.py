import json
from pathlib import Path

from config import feature_store_base_dir
from helper import ErrorCode, Queue, TaskCode, parse_json_str

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
    # "payload": {
    #     "feature_store_id": "STRING",
    #     "query_id": "STRING",
    #     "content": "STRING",
    #     "images": ["STRING"],
    #     "history": [{
    #         "sender": Integer,
    #         "content": "STRING"
    #     }]
    # }

    # queries = ['请问买下单位公寓，需要多少钱？']
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
    test_create_fs()
    test_update_sample()
    test_update_pipeline()
    test_chat()
