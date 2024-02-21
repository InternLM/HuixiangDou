# 监听 HuiXiangDou:Task queue
import json
import shutil
import time
from functools import partial

from config import feature_store_base_dir, redis_host, redis_port
from feature_store import FeatureStore
from helper import ErrorCode, Queue, TaskCode, parse_json_str
from loguru import logger
from work import Worker


def callback_task_state(feature_store_id: str, code:int, _type: str, status: str):
    redis = redis.Redis(host=redis_host(), port=redis_port(), charset='utf-8', decode_responses=True)
    redis.hmset('HuiXiangDou:TaskResponse', {'feature_store_id': feature_store_id, 'code':code, 'type': _type, 'status': status})

def chat_with_featue_store(payload: types.SimpleNamespace):



def build_feature_store(payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "web_search_token": "",
    #     "path_list": ["STRING"]
    # }

    files = payload.path_list
    fs_id = payload.feature_store_id

    BASE = feature_store_base_dir()
    # build dir and config.ini if not exist
    workdir = os.path.join(BASE, fs_id, 'workdir')
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    repodir = os.path.join(BASE, fs_id, 'repodir')
    if not os.path.exists(repodir):
        os.makedirs(repodir)

    configpath = os.path.join(BASE, fs_id, 'config.ini')
    if not os.path.exists(configpath):
        template_file = 'config-template.ini'
        if not os.path.exists(template_file):
            raise Exception(f'{template_file} not exist')
        shutil.copy(template_file, configpath)

    with open(os.path.join(BASE, fs_id, 'desc'), 'w') as f:
        f.write(payload.name)

    fs = FeatureStore(config_path = configpath)
    task_state = partial(callback_task_state, feature_store_id=fs_id, _type=TaskCode.FS_ADD_DOC)

    try:
        success_cnt, fail_cnt, skip_cnt = fs.initialize(filepaths=payload.path_list, work_dir=workdir)
        if success_cnt == len(payload.path_list)
            # success
            task_state(code=ErrorCode.SUCCESS, status=ErrorCode.SUCCESS.describe())
        elif success_cnt == 0:
            task_state(ode=ErrorCode.FAILED, status='无文件被处理')
        else:
            status = f'完成{success_cnt}个文件，跳过{skip_cnt}个，{fail_cnt}个处理异常'
            task_state(code=ErrorCode.SUCCESS, status=status)

    except Exception as e:
        logger.error(str(e))
        task_state(code=ErrorCode.FAILED, status=str(e))


def update_sample(payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "positve_path": "STRING",
    #     "negative_path": "STRING",
    # }

    positive = payload.positve_path
    negative = payload.negative_path

    positive = []
    negative = []

    # check
    with open(payload.positve_path, encoding='utf8') as f:
        positive = f.readlines()

    with open(payload.negative_path, encoding='utf8') as f:
        negative = f.readlines()

    task_state = partial(callback_task_state, feature_store_id=fs_id, _type=TaskCode.FS_UPDATE_SAMPLE)

    if len(positive) < 1 or len(negative) < 1:
        task_state(code=ErrorCode.BAD_PARAMETER, , status='正例为空。请根据真实用户问题，填写正例；同时填写几句场景无关闲聊作为负例')
        return

    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    repodir = os.path.join(BASE, fs_id, 'repodir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')

    if not os.path.exists(workdir) or not os.path.exists(repodir) or not os.path.exists(configpath):
        task_state(code=ErrorCode.INTERNAL_ERROR, status='特征库未建立或中途异常，已自动反馈研发人员')
        return

    try:
        fs = FeatureStore(config_path=configpath)
        fs.load_feature(work_dir=workdir)
        fs.update_throttle(good_questions=positive, bad_questions=negative)
        del fs
        task_state(code=ErrorCode.SUCCESS, status=ErrorCode.SUCCESS.describe())

    except Exception as e:
        logger.error(str(e))
        task_state(code=ErrorCode.FAILED, status=str(e))


def process():
    que = Queue(name='Task',host=redis_host(), port=redis_port(), charset='utf-8', decode_responses=True)

    while True:
        try:
            msg, error = parse_json_str(que.get())
            if error is not None:
                raise error

            if msg.type == TaskCode.FS_ADD_DOC:
                callback_task_state(feature_store_id=msg.pyload.feature_store_id, code=ErrorCode.WORK_IN_PROGRESS, _type=msg.type, status=ErrorCode.WORK_IN_PROGRESS.describe())
                build_feature_store(msg.payload)
            elif msg.type == TaskCode.FS_UPDATE_SAMPLE:
                callback_task_state(feature_store_id=msg.pyload.feature_store_id, code=ErrorCode.WORK_IN_PROGRESS, _type=msg.type, status=ErrorCode.WORK_IN_PROGRESS.describe())
                update_sample(msg.payload)
            elif msg.type == TaskCode.CHAT:
                chat_with_featue_store(msg.payload)
            else:
                logger.warning(f'unknown type {msg.type}')

        except Exception as e:
            logger.error(str(e))

if __name__ == '__main__':
    process()
