import json
from pathlib import Path

from config import feature_store_base_dir, redis_host, redis_port
from helper import ErrorCode, Queue, TaskCode, parse_json_str

task_in = Queue(name='Task',
                host=redis_host(),
                port=redis_port(),
                charset='utf-8',
                decode_responses=True)

task_out = Queue(name='TaskResponse',
                 host=redis_host(),
                 port=redis_port(),
                 charset='utf-8',
                 decode_responses=True)
import pdb


def test_create_fs():
    target = {
        'type': TaskCode.FS_ADD_DOC.value,
        'payload': {
            'name': 'ailab 行政说明',
            'feature_store_id': '9527',
            'file_abs_base': '/data2/khj/test-data',
            'file_list': ['huixiangdou.md', '']
        }
    }
    base_dir = target['payload']['file_abs_base']

    file_list = [str(x) for x in list(Path(base_dir).glob('*'))]
    target['payload']['file_list'] = file_list
    print(target)
    task_in.put(json.dumps(target))

    out = task_out.get()
    print(out)

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
            'negative': ['今天中文吃什么', 'ncnn 的作者是谁']
        }
    }
    print(target)
    task_in.put(json.dumps(target))

    out = task_out.get()
    print(out)

    out = task_out.get()
    print(out)


if __name__ == '__main__':
    # test_create_fs()
    test_update_sample()
