# Listen HuiXiangDou:Task queue
import json
import os
import shutil
import time
import types
from datetime import datetime, timedelta
# implement time lru cache
from functools import lru_cache, partial, wraps
from multiprocessing import Pool, Process, Value

import pytoml
import redis
from BCEmbedding.tools.langchain import BCERerank
from loguru import logger

from huixiangdou.service import (CacheRetriever, ErrorCode, FeatureStore,
                                 FileName, FileOperation, Queue, Retriever,
                                 TaskCode, feature_store_base_dir,
                                 parse_json_str, redis_host, redis_passwd,
                                 redis_port)

from .web_worker import WebWorker


def callback_task_state(feature_store_id: str,
                        code: int,
                        _type: str,
                        state: str,
                        files_state: list = []):
    resp = Queue(name='TaskResponse')
    target = {
        'feature_store_id': feature_store_id,
        'code': code,
        'type': _type,
        'state': state,
        'status': state,
        'files_state': files_state
    }
    logger.debug(target)
    resp.put(json.dumps(
        target,
        ensure_ascii=False,
    ))


def callback_chat_state(feature_store_id: str, query_id: str, code: int,
                        state: str, text: str, ref: list):
    que = Queue(name='ChatResponse')

    target = {
        'feature_store_id': feature_store_id,
        'query_id': query_id,
        'response': {
            'code': code,
            'state': state,
            'text': text,
            'references': ref
        }
    }
    logger.debug(target)
    que.put(json.dumps(target, ensure_ascii=False))


def format_history(history):
    """format [{sender, content}] to [[user1, bot1],[user2,bot2]..] style."""
    ret = []
    last_id = -1

    user = ''
    concat_text = ''
    for item in history:
        if last_id == -1:
            last_id = item.sender
            concat_text = item.content
            continue
        if last_id == item.sender:
            # 和上一个相同， concat
            concat_text += '\n'
            concat_text += item.content
            continue

        # 和上一个不同，把目前所有的 concat_text 加到 user 或 bot 部分
        if last_id == 0:
            # user message
            user = concat_text
        elif last_id == 1:
            # bot reply
            ret.append([user, concat_text])
            user = ''

        # 把当前的 assign 给 last
        last_id = item.sender
        concat_text = item.content

    # 最后一个元素，处理一下
    if last_id == 0:
        # user message
        ret.append([concat_text, ''])
        logger.warning('chat history should not ends with user')
    elif last_id == 1:
        # bot reply
        ret.append([user, concat_text])

    return ret


def chat_with_featue_store(cache: CacheRetriever,
                           payload: types.SimpleNamespace):
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

    fs_id = payload.feature_store_id
    query_id = payload.query_id

    chat_state = partial(callback_chat_state,
                         feature_store_id=fs_id,
                         query_id=query_id)

    BASE = feature_store_base_dir()
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')
    db_reject = os.path.join(workdir, 'db_reject')
    db_response = os.path.join(workdir, 'db_response')

    if not os.path.exists(workdir) or not os.path.exists(
            configpath) or not os.path.exists(db_reject) or not os.path.exists(
                db_response):
        chat_state(code=ErrorCode.PARAMETER_ERROR.value,
                   text='',
                   state='知识库未建立或建立异常，此时不能 chat。',
                   ref=[])
        return
    retriever = cache.get(fs_id=fs_id,
                          config_path=configpath,
                          work_dir=workdir)

    worker = WebWorker(work_dir=workdir, config_path=configpath)

    history = format_history(payload.history)
    query_log = '{} {}\n'.format(fs_id, payload.content)
    with open('query.log', 'a') as f:
        f.write(query_log)
    error, response, references = worker.generate(query=payload.content,
                                                  history=history,
                                                  retriever=retriever,
                                                  groupname='')
    if error != ErrorCode.SUCCESS:
        chat_state(code=error.value,
                   state=error.describe(),
                   text=response,
                   ref=references)
        return
    chat_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe(),
               text=response,
               ref=references)


def build_feature_store(cache: CacheRetriever, payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "file_abs_base": "STRING",
    #     "path_list": ["STRING"]
    # }
    abs_base = payload.file_abs_base
    fs_id = payload.feature_store_id
    path_list = []
    files = []

    file_opr = FileOperation()
    for filename in payload.file_list:
        abs_path = os.path.join(abs_base, filename)
        _type = file_opr.get_type(abs_path)
        files.append(FileName(root=abs_base, filename=filename, _type=_type))

    BASE = feature_store_base_dir()
    # build dir and config.ini if not exist
    workdir = os.path.join(BASE, fs_id, 'workdir')
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    configpath = os.path.join(BASE, fs_id, 'config.ini')
    if not os.path.exists(configpath):
        template_file = 'config.ini'
        if not os.path.exists(template_file):
            raise Exception(f'{template_file} not exist')
        shutil.copy(template_file, configpath)

    with open(os.path.join(BASE, fs_id, 'desc'), 'w', encoding='utf8') as f:
        f.write(payload.name)

    fs = FeatureStore(config_path=configpath,
                      embeddings=cache.embeddings,
                      reranker=cache.reranker)
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_ADD_DOC.value)

    # try:
    fs.initialize(files=files, work_dir=workdir)
    files_state = []

    success_cnt = 0
    fail_cnt = 0
    skip_cnt = 0
    for file in files:
        files_state.append({
            'file': str(file.basename),
            'status': bool(file.state),
            'desc': str(file.reason)
        })

        if file.state:
            success_cnt += 1
        elif file.reason == 'skip':
            skip_cnt += 1
        else:
            fail_cnt += 1

    if success_cnt == len(files):
        task_state(code=ErrorCode.SUCCESS.value,
                   state=ErrorCode.SUCCESS.describe(),
                   files_state=files_state)

    elif success_cnt == 0:
        task_state(code=ErrorCode.FAILED.value,
                   state='无文件被处理',
                   files_state=files_state)

    else:
        state = f'完成{success_cnt}个文件，跳过{skip_cnt}个，{fail_cnt}个处理异常。请确认文件格式。'
        task_state(code=ErrorCode.SUCCESS.value,
                   state=state,
                   files_state=files_state)

    # except Exception as e:
    #     logger.error(str(e))
    #     task_state(code=ErrorCode.FAILED.value, state=str(e))


def update_sample(cache: CacheRetriever, payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "positve_path": "STRING",
    #     "negative_path": "STRING",
    # }

    positive = payload.positive
    negative = payload.negative
    fs_id = payload.feature_store_id

    # check
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_UPDATE_SAMPLE.value)

    if len(positive) < 1 or len(negative) < 1:
        task_state(code=ErrorCode.BAD_PARAMETER.value,
                   state='正例为空。请根据真实用户问题，填写正例；同时填写几句场景无关闲聊作负例')
        return

    for idx in range(len(positive)):
        if len(positive[idx]) < 1:
            positive[idx] += '.'

    for idx in range(len(negative)):
        if len(negative[idx]) < 1:
            negative[idx] += '.'

    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')

    db_reject = os.path.join(workdir, 'db_reject')
    db_response = os.path.join(workdir, 'db_response')

    if not os.path.exists(workdir) or not os.path.exists(
            configpath) or not os.path.exists(db_reject) or not os.path.exists(
                db_response):
        task_state(code=ErrorCode.INTERNAL_ERROR.value,
                   state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return

    # try:

    retriever = cache.get(fs_id=fs_id,
                          config_path=configpath,
                          work_dir=workdir)
    retriever.update_throttle(config_path=configpath,
                              good_questions=positive,
                              bad_questions=negative)
    del retriever
    task_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe())

    # except Exception as e:
    #     logger.error(str(e))
    #     task_state(code=ErrorCode.FAILED.value, state=str(e))


def update_pipeline(payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "web_search_token": ""
    # }
    fs_id = payload.feature_store_id
    token = payload.web_search_token

    # check
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_UPDATE_PIPELINE.value)

    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')

    if not os.path.exists(workdir) or not os.path.exists(configpath):
        task_state(code=ErrorCode.INTERNAL_ERROR.value,
                   state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return

    with open(configpath, encoding='utf8') as f:
        config = pytoml.load(f)
    config['web_search']['x_api_key'] = token
    with open(configpath, 'w', encoding='utf8') as f:
        pytoml.dump(config, f)
    task_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe())


def process():
    que = Queue(name='Task')
    fs_cache = CacheRetriever('config.ini')

    logger.info('start wait task queue..')
    while True:
        #        try:
        msg_pop = que.get(timeout=16)
        if msg_pop is None:
            continue
        msg, error = parse_json_str(msg_pop)
        logger.info(msg)
        if error is not None:
            raise error

        logger.debug(f'process {msg}')
        if msg.type == TaskCode.FS_ADD_DOC.value:
            fs_cache.pop(msg.payload.feature_store_id)
            build_feature_store(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_SAMPLE.value:
            fs_cache.pop(msg.payload.feature_store_id)
            update_sample(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_PIPELINE.value:
            update_pipeline(msg.payload)
        elif msg.type == TaskCode.CHAT.value:
            chat_with_featue_store(fs_cache, msg.payload)
        else:
            logger.warning(f'unknown type {msg}')


#        except Exception as e:
#            logger.error(str(e))
#            time.sleep(1)
#            que = Queue(name='Task')

if __name__ == '__main__':
    # single process
    process()

    # multiple process
    # CNT = 16
    # pool = Pool(processes=CNT)

    # ps = []

    # for i in range(CNT):
    #     logger.info('prepare process {}'.format(i))

    #     p = Process(target=process, args=())
    #     p.daemon = False
    #     p.start()
    #     ps.append(p)
    #     time.sleep(1)
    #     logger.info('started process {}'.format(i))

    # for p in ps:
    #     p.join()
